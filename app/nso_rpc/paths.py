"""Rutas de la app. Se leen de APPDATA/LOCALAPPDATA en cada llamada para que los tests las redirijan."""

import os
from pathlib import Path

from . import APP_NAME


def _env_dir(var: str, fallback: str) -> Path:
    base = os.environ.get(var)
    return Path(base) if base else Path.home() / fallback


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    return _ensure(_env_dir("APPDATA", "AppData/Roaming") / APP_NAME)


def local_dir() -> Path:
    return _ensure(_env_dir("LOCALAPPDATA", "AppData/Local") / APP_NAME)


def runtime_root() -> Path:
    return _ensure(local_dir() / "runtime")


def avatar_cache_dir() -> Path:
    return _ensure(local_dir() / "avatars")
