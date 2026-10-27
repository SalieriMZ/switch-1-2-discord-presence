# NSO Discord RPC — app de bandeja en Python (diseño)

Fecha: 2026-10-27

## Intención

Reemplazar los scripts de consola anteriores (`nso-discord-rpc`) por una app de
escritorio para Windows, entregada como **un solo ejecutable fácil de usar**. Debe permitir hacer todo
el flujo desde la UI, sin terminal. Muestra en Discord lo que juega la cuenta principal de la Switch.

La app Electron oficial de nxapi v1.6.1 está rota: queda en blanco y no responde. Los scripts de consola
sí funcionan, porque usan la CLI de nxapi `1.6.1-next.257`. Esta app es la UI sobre ese mismo motor que
ya funciona.

## Por qué Python y no Electron (decisión del usuario)

El usuario no tiene experiencia con Electron y prefiere una UI hecha en Python. El motor sigue siendo
nxapi (Node). No se reescribe en Python porque Nintendo exige el token `f` y cifrar los requests de
Coral v4 (vía fancy.org.uk), y nxapi mantiene eso al día.

## Objetivos

1. **Tutorial de primer uso** con un botón visible de "Omitir tutorial". Explica:
   - qué hace la app;
   - por qué hace falta la cuenta-bot: Coral no devuelve tu propia presencia, solo la de tus amigos;
   - que la bot debe ser una cuenta desechable, y que nunca se loguea la cuenta principal (riesgo ToS);
   - que la privacidad de la cuenta principal debe estar en "Todos los amigos";
   - que la bot y la principal deben ser amigos aceptados (con agregar amigo por código desde la app);
   - que hace falta Discord de escritorio abierto.
2. **Login de la cuenta-bot desde la UI.** Botón "Abrir login de Nintendo", que abre el navegador con la
   URL de `nxapi nso auth`. La app vigila el portapapeles: cuando el usuario copia el link
   `npf71b963c1b7b6d119://auth...`, lo detecta y lo envía solo. También hay un campo para pegarlo a mano.
3. **Lista de amigos clara**, con avatar, nombre, estado (en línea / jugando X / desconectado) y NSA ID.
   El usuario elige uno con un clic y queda marcado como "cuenta mostrada en Discord".
4. **Presencia en segundo plano** con reintento automático, igual que `3-start-presence.ps1` y
   `run-once.ps1`:
   - se considera conectada si `nso presence` sobrevive 30 s;
   - si cae, reintenta cada 15 s;
   - usa `--update-interval 120` por defecto (configurable, mínimo 30).
5. **Bandeja del sistema.**
   - El ícono cambia de color según el estado: conectado, conectando/reintentando, detenido o error.
   - Menú: Iniciar/Detener, Abrir ventana, Salir.
   - Cerrar la ventana la minimiza a la bandeja.
   - Hay una notificación de Windows al conectar y al caerse; reemplaza los pitidos.
6. **Configuración.**
   - Arrancar con Windows.
   - Iniciar la presencia automáticamente al abrir.
   - Intervalo de actualización (mínimo 30 s).
   - Mostrar tiempo de juego (`--show-play-time`).
   - Mostrar aunque esté inactivo (`--show-inactive-presence`).
7. **Pestaña de registro** con la salida de nxapi y un botón "Copiar registro", para soporte.
8. **Actualizar nxapi desde la app.** Botón que corre el `npm` incluido:
   `npm install nxapi@next` sobre el runtime local. Nintendo cambia la app seguido y nxapi tiene que
   ponerse al día.

## No-objetivos

- Reescribir la API de Nintendo en Python.
- SplatNet, NookLink, webservices o eventos: solo presencia en Discord.
- macOS y Linux: solo Windows 10/11.
- Varias cuentas-bot a la vez. La CLI ya lo soporta con `--user`, pero la UI maneja una.
- Modo headless o servidor 24/7.

## Anti-objetivos (fallaría aunque funcione)

- Que el usuario tenga que abrir una terminal o instalar Node/npm/Python.
- Que la UI se congele: toda llamada a nxapi va en un hilo o proceso aparte.
- Pedir o guardar la contraseña de Nintendo. El login es solo en el sitio de Nintendo.
- Spamear a fancy.org.uk con intervalos menores a 30 s o reintentos sin pausa.

## Restricciones

- Motor: nxapi `next` (≥ `1.6.1-next.257`), por CLI y como subproceso. El canal `latest` de npm es de
  2023 y no sirve.
- La salida de la CLI para `friends` y `friendcode` se lee con `--json`. `nso user` no tiene `--json`:
  los datos de la bot se obtienen desde `bridge.mjs`.
- `nso auth` lee el link por stdin. La app hace el login en dos pasos con la librería de nxapi a través
  de un script helper en Node (ver "Puente con nxapi"), porque la URL se necesita antes de pedir el link.
- `NXAPI_USER_AGENT=nso-discord-rpc/1.0`, igual que `_env.ps1`.
- Licencia: nxapi es AGPL-3.0. Se distribuye sin modificar, con su LICENSE incluida.
- Interfaz en español e inglés (`i18n.py`; por defecto, el idioma de Windows).

## Cómo se construye (decisiones mías; el usuario puede cambiarlas)

- **UI: PySide6 (Qt).** Trae bandeja (`QSystemTrayIcon`), notificaciones, listas con avatar y tema
  oscuro, y es estable en Windows. Lo prefiero sobre Tkinter/CustomTkinter, que es más feo para listas
  con imágenes, y sobre pywebview, que es otra capa web.
- **Datos de nxapi (decisión del usuario):** usar su ruta por defecto (`%LOCALAPPDATA%\nxapi-nodejs`)
  para reutilizar el login de la bot que el usuario ya hizo con los scripts.
  - Al abrir, `bridge.mjs whoami` revisa si ya hay una bot logueada (`SelectedUser`).
  - Si la hay, el paso de login del tutorial muestra "Ya conectada como <bot>", con dos botones:
    "Continuar" y "Usar otra cuenta".
- **Config de la app:** JSON en `%APPDATA%\NSO-Discord-RPC\config.json`, con el NSA ID elegido, las
  opciones y si el tutorial ya se completó u omitió.
- **Arranque con Windows:** clave `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, con el flag
  `--minimized`.
- **Empaquetado.** Carpeta `dist\NSO-Discord-RPC\` generada con PyInstaller `--onedir` (arranca sin
  extraer nada): `NSO-Discord-RPC.exe`, `_internal\` y `runtime\` con `node.exe` portable (Node 24 x64),
  `npm` y `node_modules` de nxapi. Se comparte como `.zip` (`compilar.bat -Zip`).
  - `compilar.bat` recompila de forma incremental; `runtime\` se sincroniza con robocopy.
  - El botón "Actualizar nxapi" actúa sobre `runtime\` junto al exe.
  - La app borra la caché `%LOCALAPPDATA%\NSO-Discord-RPC\runtime` que dejaban las versiones `--onefile`.
- **Arranque sin tutorial repetido.** Si la config no marca el tutorial como hecho pero nxapi ya tiene
  una cuenta-bot (esta app o la versión de consola): con cuenta elegida se omite el tutorial; sin ella,
  se abre directo en "Elegir cuenta". "Repetir configuración inicial" (Configuración) lo reabre desde el
  principio.
- **Puente con nxapi.** Un script `bridge.mjs` corre con el node incluido e importa `nxapi` como
  librería. Comandos: `auth-url`, que imprime la URL y guarda el verifier en un archivo temporal, y
  `auth-complete <link>`, que replica `src/cli/nso/auth.ts` y devuelve JSON con la bot logueada.
  También `whoami`. Así el login no depende del prompt interactivo de la CLI.
  - `getToken` no está en el mapa `exports` de nxapi, así que el bridge lo importa por ruta de archivo
    (`node_modules/nxapi/dist/common/auth/coral.js`).
  - Amigos y código de amigo: `nxapi nso friends --json` y `nxapi nso friendcode --json`.
  - Presencia: `nxapi nso presence` como proceso largo.
- **Avatares:** se descargan de la URL `image` del JSON de amigos y se cachean en disco.

## Pantallas

1. **Tutorial** (asistente de 5 pasos, con "Omitir tutorial" arriba a la derecha):
   - Bienvenida y qué hace.
   - Cuenta-bot: por qué hace falta y advertencia de riesgo.
   - Privacidad y amistad bot ↔ principal: muestra el código de amigo de la bot (`nso friendcode`) y un
     campo para enviar una solicitud.
   - Login de la bot.
   - Elegir la cuenta principal en la lista de amigos.
2. **Principal**:
   - Arriba: estado grande (Conectado / Reintentando N / Detenido), el amigo mostrado y el juego actual,
     con el botón Iniciar/Detener.
   - Pestañas: Amigos · Configuración · Registro · Ayuda (vuelve a abrir el tutorial).
3. **Bandeja**: ícono y menú.

## Qué queda a criterio del constructor

- Estructura de módulos, estilo visual exacto e íconos.
- Cómo detectar "Discord no abierto": proceso `Discord.exe`, como hoy.
- Texto exacto de los pasos del tutorial, basado en el README actual.

## Criterio de terminado

En un PC limpio, sin Node ni Python, se ejecuta el `.exe` y se hace esto sin terminal:

1. Tutorial.
2. Login de la bot.
3. Elegir la cuenta principal.
4. La presencia aparece en Discord.

Después: cerrar la ventana la deja en la bandeja, el arranque con Windows funciona, y si se corta la
red, reintenta solo y vuelve.
