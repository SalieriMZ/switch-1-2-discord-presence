# NSO Discord RPC

**English** · [Español](README.es.md)

A Windows 10/11 tray app that shows what you're playing on your Nintendo Switch on Discord (Rich Presence).
It's a Python (PySide6) interface on top of [nxapi](https://github.com/samuelthomas2774/nxapi).

The interface is available in English and Spanish. By default it follows the Windows language.

## How it works

Nintendo Switch Online (Coral) does not return your own presence, only your friends'. So the app uses a
**bot account**: a throwaway Nintendo account that is friends with your main account. The bot reads your
presence and nxapi publishes it on Discord.

> [!WARNING]
> Use a throwaway bot account. Never sign in with your main account: using Nintendo's API unofficially may
> break their terms of service.

## Requirements

- Windows 10 or 11.
- Discord desktop running.
- A throwaway Nintendo account (the bot) that is friends with your main account.
- On your main account, online status privacy set to **All Friends**.

## Usage

1. Download the `.zip` from [Releases](../../releases) and extract it.
2. Run `NSO-Discord-RPC.exe`. You don't need to install Node or Python.
3. Follow the tutorial:
   1. Sign in with the bot (Nintendo's website opens; the app never asks for your password).
   2. Add the bot as a friend of your main account.
   3. Choose your main account in the friends list.
4. The presence runs in the background. Closing the window keeps the app in the tray.

In **Settings** you can choose the language (English or Spanish), start with Windows, start the presence
automatically and set the update interval (minimum 30 s).

## Development

Requires Python ≥ 3.12.

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

### Build

```bat
compilar.bat
```

This creates `dist\NSO-Discord-RPC\`. The first time, it downloads a portable Node and `nxapi@next` into
`build\runtime\`. Options:

- `compilar.bat -Zip` also creates the `.zip` to share.
- `compilar.bat -Clean` rebuilds from scratch.

### CI and releases

GitHub Actions ([build.yml](.github/workflows/build.yml)) runs the tests and builds the `.zip` on every push
to `main` and on pull requests. The `.zip` is attached to the run as an artifact.

To publish a release:

1. Bump `__version__` in [app/nso_rpc/\_\_init\_\_.py](app/nso_rpc/__init__.py).
2. Push a tag with the same version:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

The workflow creates the GitHub release with the `.zip`. It fails if the tag does not match `__version__`.

### Translations

UI strings are written in Spanish and wrapped in `tr()`. The English text lives in the `EN` dictionary in
[app/nso_rpc/i18n.py](app/nso_rpc/i18n.py). `tests/test_i18n.py` fails if a `tr()` string has no English
entry.

The design notes ([docs/design.md](docs/design.md)) are in Spanish.

## License

[AGPL-3.0](LICENSE). The executable bundles nxapi, which is also AGPL-3.0.

This project is not affiliated with Nintendo or Discord.
