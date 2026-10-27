"""Corre `nxapi nso presence` como QProcess y lo mantiene vivo con PresenceMachine."""

from PySide6.QtCore import QElapsedTimer, QObject, QProcess, QProcessEnvironment, QTimer, Signal

from . import winjob
from .config import Config
from .i18n import tr
from .nxapi import NxapiClient
from .presence_state import PresenceMachine, State
from .runtime import env as runtime_env


class PresenceSupervisor(QObject):
    state_changed = Signal(object, int)  # State, intento
    log_line = Signal(str)
    connected = Signal()
    dropped = Signal()

    def __init__(self, client: NxapiClient | None, config: Config, parent=None):
        super().__init__(parent)
        self.client = client
        self.config = config
        self.machine = PresenceMachine()
        self.proc: QProcess | None = None
        self._age = QElapsedTimer()
        self._down = QElapsedTimer()
        self._timer = QTimer(self, interval=1000)
        self._timer.timeout.connect(self._on_tick)
        self._last = (self.machine.state, 0)

    @property
    def state(self) -> State:
        return self.machine.state

    def start(self) -> None:
        if self.client is None:
            self.machine.start()
            self.machine.fatal(tr("No se encontró el motor nxapi."))
        elif not self.config.friend_nsaid:
            self.machine.start()
            self.machine.fatal(tr("Elige primero qué cuenta mostrar (pestaña Amigos)."))
        elif self.machine.start() == "spawn":
            self._spawn()
        self._emit()

    def stop(self) -> None:
        if self.machine.stop() == "kill":
            self._kill()
        self._timer.stop()
        self._emit()

    def restart(self) -> None:
        if self.machine.state in (State.STOPPED, State.ERROR):
            return
        self.stop()
        self.start()

    def _spawn(self) -> None:
        args = self.client.presence_args(self.config.friend_nsaid, self.config)
        self.log_line.emit("> nxapi " + " ".join(args[2:]))
        proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        for k, v in runtime_env(self.client.rt).items():
            env.insert(k, v)
        proc.setProcessEnvironment(env)
        proc.setWorkingDirectory(str(self.client.rt.root))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda p=proc: self._read(p))
        proc.finished.connect(lambda code, _status, p=proc: self._on_finished(p, code))
        proc.errorOccurred.connect(lambda err, p=proc: self._on_error(p, err))
        proc.started.connect(lambda p=proc: winjob.adopt(p.processId()))
        self.proc = proc
        proc.start(args[0], args[1:])
        self._age.start()
        self._timer.start()

    def _kill(self) -> None:
        proc, self.proc = self.proc, None
        if proc and proc.state() != QProcess.ProcessState.NotRunning:
            proc.kill()
            proc.waitForFinished(3000)

    def _read(self, proc: QProcess) -> None:
        text = bytes(proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in text.splitlines():
            if line.strip():
                self.log_line.emit(line)

    def _on_finished(self, proc: QProcess, code: int) -> None:
        if proc is not self.proc:
            return  # proceso viejo que matamos a propósito
        self.proc = None
        was = self.machine.state
        self.machine.exited(code)
        if self.machine.state is State.RETRYING:
            secs = int(self._age.elapsed() / 1000)
            if was is State.CONNECTED:
                self.log_line.emit(tr("Se cayó tras {secs}s (había conectado). Reintentando…", secs=secs))
                self.dropped.emit()
            else:
                self.log_line.emit(tr("Falló tras {secs}s sin conectar (¿servidor de tokens caído?). Reintentando…", secs=secs))
            self._down.start()
        self._emit()

    def _on_error(self, proc: QProcess, err) -> None:
        if proc is self.proc and err == QProcess.ProcessError.FailedToStart:
            self.proc = None
            self.machine.fatal(tr("No se pudo iniciar nxapi: {error}", error=proc.errorString()))
            self._timer.stop()
            self._emit()

    def _on_tick(self) -> None:
        if self.machine.state is State.CONNECTING:
            self.machine.tick(self._age.elapsed() / 1000)
            if self.machine.state is State.CONNECTED:
                self.log_line.emit(tr("CONECTADO: la presencia está activa en Discord."))
                self.connected.emit()
        elif self.machine.state is State.RETRYING:
            self.machine.tick_retry(self._down.elapsed() / 1000)
            if self.machine.retry_due() == "spawn":
                self._spawn()
        self._emit()

    def _emit(self) -> None:
        cur = (self.machine.state, self.machine.attempt)
        if cur != self._last:
            self._last = cur
            self.state_changed.emit(*cur)

    def shutdown(self) -> None:
        self.machine.stop()
        self._timer.stop()
        self._kill()
