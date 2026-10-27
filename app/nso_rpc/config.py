"""Configuración persistente de la app (JSON en %APPDATA%\\NSO-Discord-RPC)."""

import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import paths

MIN_UPDATE_INTERVAL = 30


def default_path() -> Path:
    return paths.config_dir() / "config.json"


@dataclass
class Config:
    friend_nsaid: str | None = None
    friend_name: str | None = None
    tutorial_done: bool = False
    autostart_presence: bool = True
    start_with_windows: bool = False
    update_interval: int = 120
    show_play_time: bool = False
    show_inactive: bool = False

    def __post_init__(self):
        # Menos de 30 s arriesga rate-limit en el servidor de tokens.
        self.update_interval = max(MIN_UPDATE_INTERVAL, int(self.update_interval))

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = path or default_path()
        try:
            # utf-8-sig: tolera el BOM que agregan el Bloc de notas y PowerShell 5.1.
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        known = {f.name for f in fields(cls)}
        try:
            return cls(**{k: v for k, v in data.items() if k in known})
        except (TypeError, ValueError):
            return cls()

    def save(self, path: Path | None = None) -> None:
        path = path or default_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
