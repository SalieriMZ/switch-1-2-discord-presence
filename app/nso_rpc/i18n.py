"""Idioma de la interfaz. El texto en español es la clave; EN tiene su traducción al inglés.

`tr()` se llama al construir cada texto, así que el idioma se fija una vez al arrancar (antes de crear la UI).
"""

from PySide6.QtCore import QLocale

LANGUAGES = {"auto": "Automático / Automatic", "es": "Español", "en": "English"}

_lang = "es"


def system_language() -> str:
    return "es" if QLocale.system().language() == QLocale.Language.Spanish else "en"


def set_language(code: str) -> str:
    """Acepta "auto", "es" o "en"; devuelve el idioma efectivo."""
    global _lang
    _lang = code if code in ("es", "en") else system_language()
    return _lang


def current() -> str:
    return _lang


def tr(text: str, **kwargs) -> str:
    if _lang == "en":
        text = EN.get(text, text)
    return text.format(**kwargs) if kwargs else text


EN = {
    # --- estado / bandeja ---
    "Conectado": "Connected",
    "Conectando…": "Connecting…",
    "Conectando… (intento {n})": "Connecting… (attempt {n})",
    "Reintentando (intento {n})": "Retrying (attempt {n})",
    "Detenido": "Stopped",
    "Error: {error}": "Error: {error}",
    "Abrir": "Open",
    "Iniciar": "Start",
    "Detener": "Stop",
    "Salir": "Quit",
    "Presencia activa": "Presence active",
    "Tu actividad de Switch ya se muestra en Discord.": "Your Switch activity is now showing on Discord.",
    "Se perdió la conexión": "Connection lost",
    "Reintentando automáticamente…": "Retrying automatically…",
    "Error": "Error",
    # --- amigos ---
    "Jugando {game}": "Playing {game}",
    "En línea": "Online",
    "Desconectado": "Offline",
    "  ★ favorito": "  ★ favorite",
    "Mostrando en Discord": "Showing on Discord",
    "Mostrar en Discord": "Show on Discord",
    "Elige la cuenta cuya actividad quieres mostrar en Discord (normalmente tu cuenta principal).":
        "Choose the account whose activity you want to show on Discord (usually your main account).",
    "Recargar": "Reload",
    "No se encontró el motor nxapi.": "The nxapi engine was not found.",
    "Cargando amigos… (puede tardar unos segundos la primera vez)":
        "Loading friends… (may take a few seconds the first time)",
    "No se pudo cargar la lista: {error}": "Could not load the list: {error}",
    "La cuenta-bot no tiene amigos todavía. Envía la solicitud desde la bot (o desde tu consola) y asegúrate "
    "de que esté aceptada en ambos lados; luego pulsa Recargar.":
        "The bot account has no friends yet. Send the request from the bot (or from your console), make sure "
        "it is accepted on both sides, then press Reload.",
    # --- ventana principal ---
    "⚠ No detecto Discord de escritorio abierto: ábrelo para que se vea la actividad.":
        "⚠ Discord desktop doesn't seem to be running: open it so your activity shows up.",
    "Amigos": "Friends",
    "Configuración": "Settings",
    "Registro": "Log",
    "Ayuda": "Help",
    "<p><b>Cómo funciona.</b> Nintendo no deja leer tu propia actividad, solo la de tus amigos. Por eso una "
    "<b>cuenta-bot</b> (una cuenta Nintendo desechable) te tiene como amigo y “mira” lo que juegas; esta app "
    "lo publica en tu Discord.</p><p><b>Si no aparece nada en Discord:</b> Discord de escritorio abierto · tu "
    "cuenta principal jugando y en línea · privacidad de la principal en “Todos los amigos” · bot y principal "
    "son amigos aceptados.</p><p><b>Seguridad:</b> nunca inicies sesión aquí con tu cuenta principal; el "
    "riesgo lo absorbe la bot.</p>":
        "<p><b>How it works.</b> Nintendo doesn't let you read your own activity, only your friends'. So a "
        "<b>bot account</b> (a throwaway Nintendo account) has you as a friend and “watches” what you play; "
        "this app publishes it on your Discord.</p><p><b>If nothing shows up on Discord:</b> Discord desktop "
        "is open · your main account is online and playing · main account privacy set to “All friends” · bot "
        "and main account are accepted friends.</p><p><b>Security:</b> never sign in here with your main "
        "account; the bot takes the risk.</p>",
    "<p>Cuenta-bot actual: <b>{name}</b></p>": "<p>Current bot account: <b>{name}</b></p>",
    "Abrir el tutorial": "Open the tutorial",
    "Todavía no eliges qué cuenta mostrar: hazlo en la pestaña Amigos.":
        "You haven't chosen which account to show yet: do it in the Friends tab.",
    "Mostrando a <b>{name}</b>": "Showing <b>{name}</b>",
    # --- configuración ---
    "Arrancar con Windows (minimizada en la bandeja)": "Start with Windows (minimized to the tray)",
    "Iniciar la presencia automáticamente al abrir la app": "Start the presence automatically when the app opens",
    "Mostrar tiempo de juego en Discord": "Show play time on Discord",
    "Mostrar aunque la consola esté inactiva (en suspensión)": "Show even when the console is idle (sleep mode)",
    "Cada cuánto se consulta a Nintendo. No bajes de 30 s (riesgo de bloqueo).":
        "How often Nintendo is queried. Don't go below 30 s (risk of being blocked).",
    "Intervalo de actualización": "Update interval",
    "Idioma": "Language",
    "El cambio de idioma se aplica al reiniciar la app.": "The language change applies after restarting the app.",
    "Actualizar nxapi": "Update nxapi",
    "Úsalo si Nintendo actualizó su app y la presencia dejó de funcionar.":
        "Use it if Nintendo updated its app and the presence stopped working.",
    "Repetir configuración inicial": "Redo initial setup",
    "Vuelve a abrir el tutorial desde el principio: cuenta-bot, amistad y cuenta a mostrar.":
        "Reopens the tutorial from the start: bot account, friendship and account to show.",
    "No se pudo cambiar el arranque con Windows: {error}": "Could not change start with Windows: {error}",
    "Se detendrá la presencia y se abrirá el tutorial desde el principio. Tu cuenta-bot y la cuenta elegida "
    "se mantienen hasta que las cambies. ¿Continuar?":
        "The presence will stop and the tutorial will open from the start. Your bot account and chosen "
        "account are kept until you change them. Continue?",
    "Actualizando… (mira la pestaña Registro)": "Updating… (see the Log tab)",
    "nxapi actualizado.": "nxapi updated.",
    "Falló la actualización: {error}": "Update failed: {error}",
    # --- registro ---
    "Copiar registro": "Copy log",
    "Limpiar": "Clear",
    # --- tutorial ---
    "Bienvenida": "Welcome",
    "Cuenta-bot": "Bot account",
    "Iniciar sesión": "Sign in",
    "Amistad": "Friendship",
    "Elegir cuenta": "Choose account",
    "Omitir tutorial": "Skip tutorial",
    "Atrás": "Back",
    "Siguiente": "Next",
    "Terminar": "Finish",
    "Paso {n} de {total} · {name}": "Step {n} of {total} · {name}",
    "Muestra en Discord lo que juegas en tu Switch": "Show what you play on your Switch on Discord",
    "<p>Esta app publica en tu perfil de Discord el juego que estás jugando en tu Nintendo Switch, como "
    "“Jugando a …”.</p><p>Necesitas:</p><ul><li><b>Discord de escritorio</b> abierto en este PC.</li><li>Una "
    "<b>cuenta Nintendo extra</b> (la “cuenta-bot”). Te explicamos por qué en el siguiente paso.</li><li>Unos "
    "5 minutos.</li></ul><p>Una vez configurada, la app vive en la <b>bandeja del sistema</b> (junto al reloj) "
    "y se reconecta sola.</p>":
        "<p>This app shows the game you're playing on your Nintendo Switch on your Discord profile, as "
        "“Playing …”.</p><p>You need:</p><ul><li><b>Discord desktop</b> running on this PC.</li><li>An "
        "<b>extra Nintendo account</b> (the “bot account”). We explain why in the next step.</li><li>About 5 "
        "minutes.</li></ul><p>Once set up, the app lives in the <b>system tray</b> (next to the clock) and "
        "reconnects on its own.</p>",
    "¿Por qué una cuenta-bot?": "Why a bot account?",
    "<p>Nintendo <b>no deja leer tu propia actividad</b>: su API solo entrega la de tus <b>amigos</b>. Por eso "
    "usamos una segunda cuenta Nintendo, la <b>cuenta-bot</b>, que te tiene como amiga y “mira” lo que "
    "juegas.</p><p><b>Cómo crearla:</b></p><ol><li>Crea una cuenta nueva en <a "
    "href='https://accounts.nintendo.com/'>accounts.nintendo.com</a> con un correo dedicado.</li><li>No "
    "necesita suscripción de pago ni estar en tu consola.</li></ol>":
        "<p>Nintendo <b>doesn't let you read your own activity</b>: its API only returns your <b>friends'</b>. "
        "So we use a second Nintendo account, the <b>bot account</b>, which has you as a friend and “watches” "
        "what you play.</p><p><b>How to create it:</b></p><ol><li>Create a new account at <a "
        "href='https://accounts.nintendo.com/'>accounts.nintendo.com</a> with a dedicated email.</li><li>It "
        "doesn't need a paid subscription or to be on your console.</li></ol>",
    "Continuar con esta cuenta": "Continue with this account",
    "Usar otra cuenta": "Use another account",
    "1 · Abrir inicio de sesión de Nintendo": "1 · Open Nintendo sign-in",
    "<ol><li>Pulsa el botón: se abre tu navegador. Inicia sesión con la <b>cuenta-bot</b>.</li><li>En la "
    "página “Vincular una cuenta externa”, haz <b>clic derecho</b> sobre <b>“Elegir esta cuenta”</b> → "
    "<b>Copiar dirección del enlace</b>.</li><li>Listo: la app detecta el enlace copiado sola. Si no, pégalo "
    "abajo.</li></ol>":
        "<ol><li>Press the button: your browser opens. Sign in with the <b>bot account</b>.</li><li>On the "
        "“Linking an External Account” page, <b>right-click</b> <b>“Select this person”</b> → <b>Copy link "
        "address</b>.</li><li>Done: the app detects the copied link by itself. If not, paste it below.</li></ol>",
    "Enviar": "Send",
    "Inicia sesión con la cuenta-bot": "Sign in with the bot account",
    "Cargando código de amigo…": "Loading friend code…",
    "Copiar": "Copy",
    "Código de amigo de la bot:": "Bot's friend code:",
    "Código de amigo de tu cuenta principal (SW-XXXX-XXXX-XXXX)": "Your main account's friend code (SW-XXXX-XXXX-XXXX)",
    "Enviar solicitud": "Send request",
    "En la consola, con tu cuenta principal: Configuración de usuario → Ajustes de amigos → “Mostrar estado en "
    "línea a” = Todos los amigos":
        "On the console, with your main account: User Settings → Friend Settings → “Display Online Status "
        "To” = All Friends",
    "La bot y tu cuenta principal son amigos (solicitud aceptada)":
        "The bot and your main account are friends (request accepted)",
    "Hazte amigo de la bot": "Befriend the bot",
    "<p>La bot tiene que ser <b>amiga</b> de tu cuenta principal. Haz una de las dos:</p><ul><li>Desde tu "
    "Switch, agrega a la bot con su código de amigo, <b>o</b></li><li>Envía la solicitud desde la bot a tu "
    "código de amigo y acéptala en la Switch.</li></ul>":
        "<p>The bot has to be <b>friends</b> with your main account. Do one of these:</p><ul><li>From your "
        "Switch, add the bot with its friend code, <b>or</b></li><li>Send the request from the bot to your "
        "friend code and accept it on the Switch.</li></ul>",
    "<p><b>Revisa también:</b></p>": "<p><b>Also check:</b></p>",
    "Elige tu cuenta principal: es la que se mostrará en Discord.":
        "Choose your main account: it's the one that will show on Discord.",
    "Elige qué cuenta mostrar": "Choose which account to show",
    "no disponible": "unavailable",
    "Ya hay una cuenta-bot conectada: <b>{name}</b>": "A bot account is already signed in: <b>{name}</b>",
    " (Switch: {name})": " (Switch: {name})",
    "Todavía no hay una cuenta-bot conectada.": "No bot account is signed in yet.",
    "Inicia sesión con la otra cuenta-bot.": "Sign in with the other bot account.",
    "Preparando el enlace de Nintendo…": "Preparing the Nintendo link…",
    "Navegador abierto. Esperando el enlace copiado…": "Browser opened. Waiting for the copied link…",
    "No se pudo generar el enlace: {error}": "Could not create the link: {error}",
    "Ese no parece el enlace correcto. Debe empezar con npf71b963c1b7b6d119://auth y contener "
    "session_token_code.":
        "That doesn't look like the right link. It must start with npf71b963c1b7b6d119://auth and contain "
        "session_token_code.",
    "Primero pulsa “Abrir inicio de sesión de Nintendo”.": "First press “Open Nintendo sign-in”.",
    "Iniciando sesión… (puede tardar unos segundos)": "Signing in… (may take a few seconds)",
    "✓ Sesión iniciada como <b>{name}</b>.": "✓ Signed in as <b>{name}</b>.",
    "No se pudo iniciar sesión: {error}. Vuelve a pulsar “Abrir inicio de sesión” e inténtalo de nuevo.":
        "Could not sign in: {error}. Press “Open Nintendo sign-in” again and retry.",
    "Enviando solicitud…": "Sending request…",
    "✓ Solicitud enviada. Acéptala en tu Switch (Perfil → Amigos → Solicitudes recibidas).":
        "✓ Request sent. Accept it on your Switch (Profile → Friends → Received Friend Requests).",
    "No se pudo enviar: {error}": "Could not send: {error}",
    # --- motor / presencia ---
    "Respuesta inesperada de nxapi (no es JSON).": "Unexpected response from nxapi (not JSON).",
    "Código no válido: usa el código de amigo (SW-1234-5678-9012) o el NSA ID.":
        "Invalid code: use the friend code (SW-1234-5678-9012) or the NSA ID.",
    "error desconocido": "unknown error",
    "nxapi tardó demasiado en responder (¿servidor de tokens caído?).":
        "nxapi took too long to respond (token server down?).",
    "No se pudo ejecutar nxapi: {error}": "Could not run nxapi: {error}",
    "npm install falló (código {code}).": "npm install failed (code {code}).",
    "Elige primero qué cuenta mostrar (pestaña Amigos).": "First choose which account to show (Friends tab).",
    "Se cayó tras {secs}s (había conectado). Reintentando…": "Dropped after {secs}s (had connected). Retrying…",
    "Falló tras {secs}s sin conectar (¿servidor de tokens caído?). Reintentando…":
        "Failed after {secs}s without connecting (token server down?). Retrying…",
    "No se pudo iniciar nxapi: {error}": "Could not start nxapi: {error}",
    "CONECTADO: la presencia está activa en Discord.": "CONNECTED: the presence is active on Discord.",
    "No se encontró el motor nxapi (Node). ": "The nxapi engine (Node) was not found. ",
    "Reinstala la app.": "Reinstall the app.",
    "Corre build/fetch-runtime.ps1.": "Run build/fetch-runtime.ps1.",
    "Cuenta-bot: {name} ({id})": "Bot account: {name} ({id})",
    "Cuenta-bot y cuenta elegida ya configuradas: se omite el tutorial.":
        "Bot account and chosen account already set up: skipping the tutorial.",
}
