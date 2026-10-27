"""Cliente de nxapi: corre la CLI y bridge.mjs como subprocesos. Todo es bloqueante: llamar desde workers."""

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

from .config import Config
from .i18n import tr
from .runtime import CREATE_NO_WINDOW, Runtime, env

DEFAULT_TIMEOUT = 120


class NxapiError(RuntimeError):
    pass


def parse_json_output(stdout: str) -> Any:
    """nxapi a veces imprime avisos antes del JSON: prueba línea por línea y luego desde el primer [ o {."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line[:1] in ("[", "{") or line == "null":
            try:
                return json.loads(line)
            except ValueError:
                pass
    starts = [i for i in (stdout.find("["), stdout.find("{")) if i >= 0]
    if starts:
        try:
            return json.loads(stdout[min(starts):])
        except ValueError:
            pass
    raise NxapiError(tr("Respuesta inesperada de nxapi (no es JSON)."))


@dataclass(frozen=True)
class Friend:
    nsa_id: str
    name: str
    image_url: str | None
    online: bool
    game_name: str | None
    is_favorite: bool

    @classmethod
    def from_coral(cls, d: dict) -> "Friend":
        presence = d.get("presence") or {}
        game = presence.get("game") or {}
        return cls(
            nsa_id=d["nsaId"],
            name=d.get("name") or d["nsaId"],
            image_url=d.get("imageUri") or d.get("image"),
            online=presence.get("state") in ("ONLINE", "PLAYING"),
            game_name=game.get("name") or None,
            is_favorite=bool(d.get("isFavoriteFriend")),
        )

    @property
    def status_text(self) -> str:
        if self.game_name and self.online:
            return tr("Jugando {game}", game=self.game_name)
        return tr("En línea") if self.online else tr("Desconectado")


def normalize_friend_id(raw: str) -> str:
    """Acepta 'SW-1234-5678-9012', '123456789012' o un NSA ID; devuelve lo que espera `nso add-friend`."""
    text = raw.strip().lower().removeprefix("sw-").strip()
    digits = re.sub(r"[\s-]", "", text)
    if re.fullmatch(r"\d{12}", digits):
        return f"{digits[0:4]}-{digits[4:8]}-{digits[8:12]}"
    if re.fullmatch(r"[0-9a-f]{16}", text):
        return text
    raise NxapiError(tr("Código no válido: usa el código de amigo (SW-1234-5678-9012) o el NSA ID."))


def _last_error_line(stderr: str) -> str:
    lines = [l.strip() for l in stderr.splitlines() if l.strip()]
    for line in reversed(lines):
        if "error" in line.lower():
            return line
    return lines[-1] if lines else tr("error desconocido")


class NxapiClient:
    def __init__(self, rt: Runtime):
        self.rt = rt

    def _run(self, args: list[str], timeout: int = DEFAULT_TIMEOUT) -> str:
        try:
            proc = subprocess.run(
                [str(self.rt.node), *args], cwd=self.rt.root, env=env(self.rt),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, creationflags=CREATE_NO_WINDOW,
            )
        except subprocess.TimeoutExpired:
            raise NxapiError(tr("nxapi tardó demasiado en responder (¿servidor de tokens caído?)."))
        except OSError as e:
            raise NxapiError(tr("No se pudo ejecutar nxapi: {error}", error=e))
        if proc.returncode != 0:
            # bridge.mjs reporta {"error": ...} en stdout; la CLI de nxapi escribe el error en stderr.
            try:
                data = parse_json_output(proc.stdout)
            except NxapiError:
                data = None
            if isinstance(data, dict) and data.get("error"):
                raise NxapiError(data["error"])
            raise NxapiError(_last_error_line(proc.stderr))
        return proc.stdout

    def _cli(self, *args: str) -> str:
        return self._run([str(self.rt.nxapi_bin), *args])

    def _bridge(self, *args: str) -> Any:
        return parse_json_output(self._run([str(self.rt.bridge), *args]))

    def friends(self) -> list[Friend]:
        data = parse_json_output(self._cli("nso", "friends", "--json"))
        return [Friend.from_coral(d) for d in data if d.get("nsaId")]

    def friend_code(self) -> str:
        return parse_json_output(self._cli("nso", "friendcode", "--json"))["friendCode"]

    def whoami(self) -> dict | None:
        return self._bridge("whoami")

    def auth_url(self) -> tuple[str, str]:
        data = self._bridge("auth-url")
        return data["url"], data["state_file"]

    def auth_complete(self, state_file: str, link: str) -> dict:
        return self._bridge("auth-complete", state_file, link)

    def add_friend(self, code: str) -> None:
        self._cli("nso", "add-friend", normalize_friend_id(code))

    def update_nxapi(self, on_line: Callable[[str], None]) -> None:
        proc = subprocess.Popen(
            [str(self.rt.node), str(self.rt.npm_cli), "install", "nxapi@next",
             "--omit=dev", "--no-audit", "--no-fund"],
            cwd=self.rt.root, env=env(self.rt), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            on_line(line.rstrip())
        if proc.wait() != 0:
            raise NxapiError(tr("npm install falló (código {code}).", code=proc.returncode))

    def presence_args(self, nsaid: str, cfg: Config) -> list[str]:
        args = [str(self.rt.node), str(self.rt.nxapi_bin), "nso", "presence",
                "--friend-nsaid", nsaid, "--update-interval", str(cfg.update_interval)]
        if cfg.show_play_time:
            args.append("--show-play-time")
        if cfg.show_inactive:
            args.append("--show-inactive-presence")
        return args
