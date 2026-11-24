# Guía para activar tu app de noticias

Tu app hace dos cosas, sola y gratis:

1. **Te manda un mensaje por Telegram** a las **8:00, 14:00 y 19:00 (hora de Lima)** que empieza con *"Sebastián, tus noticias del día son…"*, con las noticias de **Economía del Perú**, **Economía internacional** e **Inteligencia artificial**.
2. **Actualiza tu página web de noticias** (el "apartado de noticias"), donde puedes filtrar por sección y ver ediciones anteriores. En el celular puedes usar "Añadir a pantalla de inicio" para que se vea como una app.

Las noticias son reales: salen de Gestión, El Comercio, Andina, RPP, El País, BBC Mundo, DW, Xataka y Google Noticias.

Son unos 15 minutos de configuración, una sola vez.

---

## Paso 1. Crea tu bot de Telegram (3 min)

1. Abre Telegram y busca **@BotFather** (tiene un check azul).
2. Escríbele `/newbot`.
3. Te pide un nombre: por ejemplo `Noticias de Sebastián`.
4. Te pide un usuario que termine en `bot`: por ejemplo `noticias_sebastian_bot`.
5. Te responde con un **token** parecido a `7123456789:AAH...`. **Cópialo y guárdalo**: es la "llave" de tu bot. No lo compartas con nadie.

## Paso 2. Averigua tu número de chat (2 min)

1. En Telegram, busca tu bot nuevo (el usuario que elegiste) y pulsa **Iniciar** o escríbele `hola`.
2. En el navegador abre esta dirección, cambiando `TU_TOKEN` por el token del paso 1:
   `https://api.telegram.org/botTU_TOKEN/getUpdates`
3. Verás un texto con algo como `"chat":{"id":123456789,...`. Ese número es tu **chat ID**. Cópialo.
   (Si sale vacío, vuelve a escribirle al bot y recarga la página.)

## Paso 3. Crea el repositorio en GitHub (3 min)

1. Entra a [github.com/new](https://github.com/new).
2. Nombre: `pulso-economico` (o el que quieras).
3. Márcalo como **Public** (la página web gratuita de GitHub necesita que sea público; tus claves de Telegram igual quedan ocultas y protegidas).
4. Pulsa **Create repository**.
5. Sube todos los archivos de la carpeta `app-noticias` (incluida la carpeta oculta `.github`). Lo más fácil: pulsa **uploading an existing file** y arrastra los archivos y carpetas. Luego **Commit changes**.
   *Alternativa: dime el nombre del repositorio y lo subo yo por ti.*

## Paso 4. Guarda tus claves en GitHub (2 min)

En tu repositorio: **Settings → Secrets and variables → Actions → New repository secret**. Crea dos:

| Nombre | Valor |
|---|---|
| `TELEGRAM_TOKEN` | el token del paso 1 |
| `TELEGRAM_CHAT_ID` | el número del paso 2 |

## Paso 5. Activa la página web (1 min)

**Settings → Pages**. En "Branch" elige **main** y la carpeta **/docs**, y pulsa **Save**.
Tu página quedará en: `https://TU_USUARIO.github.io/pulso-economico/`

## Paso 6. Haz la primera prueba (1 min)

**Actions → Enviar noticias → Run workflow**. En 1 o 2 minutos te debe llegar el mensaje a Telegram y la página se llenará de noticias.
Desde ahí todo funciona solo, tres veces al día.

---

## Instalar Pulso Económico como app

**Celular Android (Chrome):** abre tu página → menú ⋮ → **Instalar app** (o "Añadir a pantalla de inicio").
**iPhone (Safari):** abre tu página → botón **Compartir** → **Añadir a pantalla de inicio**.
**Laptop (Chrome o Edge):** abre tu página → en la barra de direcciones pulsa el ícono **Instalar** (una pantallita con flecha) → **Instalar**. Queda en tu menú de inicio o escritorio como cualquier programa.

La app se abre en su propia ventana, en negro, sin barra del navegador, y muestra la última edición aunque estés sin internet.

*(Opcional)* Para que tu bot de Telegram tenga la misma imagen: en @BotFather escribe `/setuserpic` y envía el archivo `docs/icon-512.png`.

## Personalizar

Todo lo que se puede cambiar está en **`config.json`** (lo editas en GitHub con el ícono del lápiz):

- `nombre` y `saludo`: cómo te saluda el mensaje.
- `titulo_app`: el nombre de tu app (aparece en la página y en el mensaje).
- `noticias_por_seccion_en_telegram`: cuántas noticias por sección llegan al mensaje.
- `secciones`: los temas y sus fuentes. Puedes añadir una fuente con su RSS, o una búsqueda de Google Noticias escribiendo `"busqueda:tu tema"`.

Los horarios están en `.github/workflows/noticias.yml` (en hora UTC: Lima + 5 horas).

## Bueno saber

- GitHub a veces atrasa los envíos programados entre 5 y 20 minutos en horas de mucho uso. Es normal.
- Si alguna fuente falla un día, el programa sigue con las demás.
- La página guarda el historial de los últimos 30 días.
