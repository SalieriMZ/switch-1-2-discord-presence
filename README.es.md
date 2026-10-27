# NSO Discord RPC

[English](README.md) · **Español**

App de bandeja para Windows 10/11 que muestra en Discord (Rich Presence) lo que estás jugando en la
Nintendo Switch. Es una interfaz en Python (PySide6) sobre [nxapi](https://github.com/samuelthomas2774/nxapi).

## Cómo funciona

Nintendo Switch Online (Coral) no devuelve tu propia presencia, solo la de tus amigos. Por eso la app
usa una **cuenta-bot**: una cuenta de Nintendo desechable, amiga de tu cuenta principal. La bot lee tu
presencia y nxapi la publica en Discord.

> [!WARNING]
> Usa una cuenta-bot desechable. Nunca inicies sesión con tu cuenta principal: usar la API de Nintendo
> de forma no oficial puede infringir sus términos de servicio.

## Requisitos

- Windows 10 u 11.
- Discord de escritorio abierto.
- Una cuenta de Nintendo desechable (la bot), amiga de tu cuenta principal.
- En tu cuenta principal, privacidad del estado en línea en **Todos los amigos**.

## Uso

1. Descarga el `.zip` de [Releases](../../releases) y descomprímelo.
2. Ejecuta `NSO-Discord-RPC.exe`. No hace falta instalar Node ni Python.
3. Sigue el tutorial:
   1. Inicia sesión con la bot (se abre el sitio de Nintendo; la app nunca pide tu contraseña).
   2. Agrega la bot como amiga de tu cuenta principal.
   3. Elige tu cuenta principal en la lista de amigos.
4. La presencia corre en segundo plano. Cerrar la ventana la deja en la bandeja.

En **Configuración** puedes elegir el idioma (español o inglés), activar el arranque con Windows, el inicio
automático de la presencia y el intervalo de actualización (mínimo 30 s).

## Desarrollo

Requiere Python ≥ 3.12.

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

### Compilar

```bat
compilar.bat
```

Genera `dist\NSO-Discord-RPC\`. La primera vez descarga Node portable y `nxapi@next` en
`build\runtime\`. Opciones:

- `compilar.bat -Zip` también crea el `.zip` para compartir.
- `compilar.bat -Clean` recompila desde cero.

El diseño está en [docs/design.md](docs/design.md).

## Licencia

[AGPL-3.0](LICENSE). El ejecutable incluye nxapi, que también es AGPL-3.0.

Este proyecto no está afiliado a Nintendo ni a Discord.
