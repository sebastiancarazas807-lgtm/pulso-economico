#!/usr/bin/env python3
"""
Noticias de Sebastián
---------------------
Recoge noticias reales (RSS) de:
  1. Economía del Perú
  2. Economía internacional
  3. Inteligencia artificial
Luego:
  - actualiza la página web (docs/index.html + docs/noticias.json)
  - envía una notificación por Telegram: "Sebastián, tus noticias del día son…"

Solo usa la biblioteca estándar de Python (no hay que instalar nada).
Variables de entorno (se configuran como "secrets" en GitHub):
  TELEGRAM_TOKEN    -> token del bot que te da @BotFather
  TELEGRAM_CHAT_ID  -> tu número de chat (ver GUIA.md)
  PAGINA_URL        -> (opcional) dirección de tu página web
"""

import email.utils
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

LIMA = timezone(timedelta(hours=-5))
NOMBRE = "Sebastián"
POR_CATEGORIA = 5          # noticias por sección en el mensaje
MAX_HORAS = 36             # ignorar noticias más antiguas que esto
RAIZ = Path(__file__).resolve().parent
DOCS = RAIZ / "docs"


def google_news(consulta: str) -> str:
    q = urllib.parse.quote(consulta)
    return f"https://news.google.com/rss/search?q={q}+when:1d&hl=es-419&gl=PE&ceid=PE:es-419"


# Todo lo personalizable vive en config.json
CONFIG = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
NOMBRE = CONFIG.get("nombre", NOMBRE)
SALUDO = CONFIG.get("saludo", "{nombre}, tus noticias del día son…").format(nombre=NOMBRE)
POR_CATEGORIA = int(CONFIG.get("noticias_por_seccion_en_telegram", POR_CATEGORIA))


def _url(u: str) -> str:
    return google_news(u[len("busqueda:"):]) if u.startswith("busqueda:") else u


CATEGORIAS = [{
    "id": c["id"], "titulo": c["titulo"],
    "fuentes": [(n, _url(u)) for n, u in c["fuentes"]],
    "filtro": c.get("solo_si_contiene"),
    "filtrar": c.get("filtrar_solo_estas_fuentes", []),
} for c in CONFIG["secciones"]]


# ----------------------------------------------------------------- lectura RSS
def descargar(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NoticiasSebastian/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        print(f"  ! No se pudo leer {url[:70]}…: {e}", file=sys.stderr)
        return None


def limpiar(texto: str | None) -> str:
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()


def fecha(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        d = email.utils.parsedate_to_datetime(texto)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def leer_fuente(nombre: str, url: str) -> list[dict]:
    datos = descargar(url)
    if not datos:
        return []
    try:
        raiz = ET.fromstring(datos)
    except ET.ParseError as e:
        print(f"  ! XML inválido en {nombre}: {e}", file=sys.stderr)
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = []
    for it in raiz.iter("item"):
        titulo = limpiar(it.findtext("title"))
        medio = nombre
        src = it.find("source")
        if src is not None and src.text:          # Google Noticias indica el medio real
            medio = src.text.strip()
            titulo = re.sub(r"\s+-\s+" + re.escape(medio) + r"$", "", titulo)
        items.append({
            "titulo": titulo,
            "enlace": (it.findtext("link") or "").strip(),
            "resumen": limpiar(it.findtext("description"))[:280],
            "fecha": fecha(it.findtext("pubDate")),
            "medio": medio,
        })
    for it in raiz.iter("{http://www.w3.org/2005/Atom}entry"):
        link = it.find("atom:link", ns)
        items.append({
            "titulo": limpiar(it.findtext("atom:title", namespaces=ns)),
            "enlace": link.get("href", "") if link is not None else "",
            "resumen": limpiar(it.findtext("atom:summary", namespaces=ns))[:280],
            "fecha": fecha(it.findtext("atom:updated", namespaces=ns)),
            "medio": nombre,
        })
    return [i for i in items if i["titulo"] and i["enlace"]]


def clave(titulo: str) -> str:
    return re.sub(r"[^a-z0-9]", "", titulo.lower())[:60]


def recoger(cat: dict) -> list[dict]:
    ahora = datetime.now(timezone.utc)
    limite = ahora - timedelta(hours=MAX_HORAS)
    filtro = re.compile(cat["filtro"], re.I) if cat.get("filtro") else None
    vistos, todas = set(), []
    for nombre, url in cat["fuentes"]:
        noticias = leer_fuente(nombre, url)
        print(f"  {cat['id']:5} {nombre:16} {len(noticias):3} noticias")
        for n in noticias:
            if n["fecha"] and n["fecha"] < limite:
                continue
            if filtro and nombre in cat["filtrar"] and not filtro.search(n["titulo"] + " " + n["resumen"]):
                continue
            k = clave(n["titulo"])
            if k in vistos:
                continue
            vistos.add(k)
            todas.append(n)
    todas.sort(key=lambda n: n["fecha"] or limite, reverse=True)
    return todas[:25]


# ------------------------------------------------------------------- Telegram
def momento_del_dia(h: int) -> str:
    return "buenos días" if h < 12 else ("buenas tardes" if h < 19 else "buenas noches")


def mensaje_telegram(secciones: list[dict], ahora: datetime) -> str:
    e = html.escape
    partes = [f"<b>{html.escape(CONFIG.get('titulo_app', 'Noticias').upper())}</b>",
              f"👋 <b>{html.escape(SALUDO)}</b>",
              f"<i>{momento_del_dia(ahora.hour).capitalize()} · {ahora:%d/%m/%Y %H:%M} (Lima)</i>"]
    for s in secciones:
        partes.append(f"\n<b>{e(s['titulo'])}</b>")
        if not s["noticias"]:
            partes.append("— Sin noticias nuevas por ahora.")
        for n in s["noticias"][:POR_CATEGORIA]:
            partes.append(f'• <a href="{e(n["enlace"], quote=True)}">{e(n["titulo"])}</a> <i>({e(n["medio"])})</i>')
    url = os.environ.get("PAGINA_URL", "").strip()
    if url:
        partes.append(f'\n📰 <a href="{e(url, quote=True)}">Abrir Pulso Económico</a>')
    texto = "\n".join(partes)
    return texto[:4000]  # límite de Telegram: 4096 caracteres


def enviar_telegram(texto: str) -> None:
    token = os.environ.get("TELEGRAM_TOKEN", "").strip().strip('"').removeprefix("bot")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip().strip('"')
    faltan = [n for n, v in (("TELEGRAM_TOKEN", token), ("TELEGRAM_CHAT_ID", chat)) if not v]
    if faltan:
        sys.exit("FALTA CONFIGURAR en Settings → Secrets and variables → Actions → pestaña Secrets "
                 "(Repository secrets): " + ", ".join(faltan) + ". La página sí se actualizó.")
    datos = urllib.parse.urlencode({
        "chat_id": chat, "text": texto, "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=datos)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("Telegram: mensaje enviado ✓", json.loads(r.read()).get("ok"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")
        sys.exit(f"Telegram rechazó el envío ({e.code}): {detalle}\n"
                 "401 = token incorrecto · 400 'chat not found' = chat ID incorrecto o no le escribiste al bot.")


# --------------------------------------------------------------- página web
def guardar_web(secciones: list[dict], ahora: datetime) -> None:
    DOCS.mkdir(exist_ok=True)
    edicion = {
        "generado": ahora.isoformat(),
        "saludo": SALUDO,
        "secciones": [{
            "id": s["id"], "titulo": s["titulo"],
            "noticias": [{**n, "fecha": n["fecha"].isoformat() if n["fecha"] else None} for n in s["noticias"]],
        } for s in secciones],
    }
    (DOCS / "config.json").write_text(json.dumps({
        "titulo_app": CONFIG.get("titulo_app", "Noticias"),
        "secciones": [{"id": c["id"], "titulo": c["titulo"]} for c in CONFIG["secciones"]],
    }, ensure_ascii=False), encoding="utf-8")
    titulo = CONFIG.get("titulo_app", "Noticias")
    (DOCS / "manifest.json").write_text(json.dumps({
        "name": titulo, "short_name": titulo, "start_url": ".", "display": "standalone",
        "background_color": "#000000", "theme_color": "#000000", "lang": "es",
        "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOCS / "noticias.json").write_text(json.dumps(edicion, ensure_ascii=False, indent=1), encoding="utf-8")

    # Historial: guardamos cada edición (mañana, tarde, noche) por 30 días
    hist_dir = DOCS / "historial"
    hist_dir.mkdir(exist_ok=True)
    (hist_dir / f"{ahora:%Y-%m-%d_%H}.json").write_text(json.dumps(edicion, ensure_ascii=False), encoding="utf-8")
    archivos = sorted(hist_dir.glob("*.json"))
    for viejo in archivos[:-90]:
        viejo.unlink()
    indice = [p.stem for p in sorted(hist_dir.glob("*.json"), reverse=True)]
    (DOCS / "historial.json").write_text(json.dumps(indice), encoding="utf-8")


def main() -> None:
    ahora = datetime.now(LIMA)
    if "--solo-enviar" in sys.argv:
        edicion = json.loads((DOCS / "noticias.json").read_text(encoding="utf-8"))
        enviar_telegram(mensaje_telegram(edicion["secciones"], datetime.fromisoformat(edicion["generado"])))
        return
    print(f"Recogiendo noticias · {ahora:%Y-%m-%d %H:%M} Lima")
    secciones = [{"id": c["id"], "titulo": c["titulo"], "noticias": recoger(c)} for c in CATEGORIAS]
    total = sum(len(s["noticias"]) for s in secciones)
    print(f"Total: {total} noticias")
    if total == 0:
        sys.exit("No se obtuvo ninguna noticia: revisa la conexión o las fuentes.")
    guardar_web(secciones, ahora)
    if "--sin-enviar" not in sys.argv:
        enviar_telegram(mensaje_telegram(secciones, ahora))


if __name__ == "__main__":
    main()
