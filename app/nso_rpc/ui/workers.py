"""Corre funciones bloqueantes (nxapi, descargas) fuera del hilo de la UI."""

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

_alive: set["_Task"] = set()


class _Signals(QObject):
    ok = Signal(object)
    err = Signal(object)


class _Task(QRunnable):
    def __init__(self, fn: Callable[[], Any]):
        super().__init__()
        self.fn = fn
        self.signals = _Signals()
        self.setAutoDelete(False)

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception as e:  # se informa a la UI, nunca se traga
            signal, value = self.signals.err, e
        else:
            signal, value = self.signals.ok, result
        try:
            signal.emit(value)
        except RuntimeError:
            pass  # la app se está cerrando: ya no hay quién reciba el resultado


def run_async(fn: Callable[[], Any], on_ok: Callable[[Any], None] | None = None,
              on_err: Callable[[Exception], None] | None = None) -> None:
    """Las señales cruzan al hilo de la UI (conexión en cola), así que los callbacks pueden tocar widgets."""
    task = _Task(fn)
    _alive.add(task)

    def done(cb, value):
        _alive.discard(task)
        if cb:
            cb(value)

    task.signals.ok.connect(lambda v: done(on_ok, v))
    task.signals.err.connect(lambda e: done(on_err, e))
    QThreadPool.globalInstance().start(task)
