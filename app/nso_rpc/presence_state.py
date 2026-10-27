"""Máquina de estados de la presencia, sin Qt (igual que run-once.ps1 + el bucle de 3-start-presence.ps1).

Los métodos devuelven la acción que el supervisor debe ejecutar: "spawn", "kill" o None.
"""

from enum import Enum

CONNECT_SECS = 30  # sobrevivir esto = pasó el token f y la primera actualización
RETRY_SECS = 15


class State(Enum):
    STOPPED = "stopped"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RETRYING = "retrying"
    ERROR = "error"


class PresenceMachine:
    def __init__(self, connect_secs: float = CONNECT_SECS, retry_secs: float = RETRY_SECS):
        self.connect_secs = connect_secs
        self.retry_secs = retry_secs
        self.state = State.STOPPED
        self.attempt = 0
        self.retry_in = 0.0
        self.was_connected = False
        self.error: str | None = None
        self._wanted = False

    def start(self):
        if self._wanted and self.state is not State.ERROR:
            return None
        self._wanted = True
        self.attempt = 0
        self.error = None
        return self._spawn()

    def _spawn(self):
        self.attempt += 1
        self.state = State.CONNECTING
        return "spawn"

    def stop(self):
        running = self.state in (State.CONNECTING, State.CONNECTED)
        self._wanted = False
        self.state = State.STOPPED
        return "kill" if running else None

    def tick(self, elapsed_s: float) -> None:
        """Segundos que lleva vivo el proceso actual."""
        if self.state is State.CONNECTING and elapsed_s >= self.connect_secs:
            self.state = State.CONNECTED

    def exited(self, code: int):
        if not self._wanted or self.state is State.ERROR:
            return None
        self.was_connected = self.state is State.CONNECTED
        self.state = State.RETRYING
        self.retry_in = self.retry_secs
        return None

    def tick_retry(self, waited_s: float) -> None:
        """Segundos esperados desde la caída."""
        if self.state is State.RETRYING:
            self.retry_in = max(0.0, self.retry_secs - waited_s)

    def retry_due(self):
        if self.state is State.RETRYING and self._wanted and self.retry_in <= 0:
            return self._spawn()
        return None

    def fatal(self, msg: str) -> None:
        self.state = State.ERROR
        self.error = msg
