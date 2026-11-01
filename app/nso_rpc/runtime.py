"""Ubica el runtime Node + nxapi que usa la app (runtime/ junto al .exe, o build/runtime en desarrollo)."""

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from . import paths
from .i18n import tr

USER_AGENT = "nso-discord-rpc/1.0"
DEV_RUNTIME = Path(__file__).resolve().parents[2] / "build" / "runtime"


class RuntimeMissing(RuntimeError):
    pass


@dataclass(frozen=True)
class Runtime:
    root: Path

    @property
    def node(self) -> Path:
        return self.root / "node" / "node.exe"

    @property
    def npm_cli(self) -> Path:
        return self.root / "node" / "node_modules" / "npm" / "bin" / "npm-cli.js"

    @property
    def nxapi_bin(self) -> Path:
        return self.root / "node_modules" / "nxapi" / "bin" / "nxapi.js"

    @property
    def bridge(self) -> Path:
        return self.root / "bridge.mjs"

    @property
    def discord_fix(self) -> Path:
        return self.root / "discord-fix.mjs"

    def is_valid(self) -> bool:
        return all(p.is_file() for p in (self.node, self.nxapi_bin, self.bridge, self.discord_fix))


def cleanup_legacy_cache() -> None:
    """Borra la copia del runtime que dejaban las versiones de un solo .exe (ya no se usa)."""
    shutil.rmtree(paths.runtime_root(), ignore_errors=True)


def locate() -> Runtime:
    override = os.environ.get("NSO_RPC_RUNTIME")
    if override:
        candidates = [Path(override).resolve()]
    elif getattr(sys, "frozen", False):
        # Carpeta de la app: NSO-Discord-RPC.exe + runtime/ al lado (sin extraer nada al arrancar).
        candidates = [Path(sys.executable).resolve().parent / "runtime"]
    else:
        candidates = [DEV_RUNTIME]

    for root in candidates:
        rt = Runtime(root)
        if rt.is_valid():
            return rt
    raise RuntimeMissing(
        tr("No se encontró el motor nxapi (Node). ")
        + (tr("Reinstala la app.") if getattr(sys, "frozen", False) else tr("Corre build/fetch-runtime.ps1."))
    )


def env(rt: Runtime) -> dict[str, str]:
    e = dict(os.environ)
    e["NXAPI_USER_AGENT"] = USER_AGENT
    e["PATH"] = str(rt.node.parent) + ";" + e.get("PATH", "")
    return e


# Sin ventana de consola para los subprocesos de node en Windows.
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
