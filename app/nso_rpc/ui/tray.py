"""Ícono de bandeja: color según estado, menú y notificaciones."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..presence import PresenceSupervisor
from ..presence_state import State
from . import theme
from ..i18n import tr
from .main_window import state_text


class Tray(QObject):
    open_requested = Signal()
    quit_requested = Signal()

    def __init__(self, supervisor: PresenceSupervisor, parent=None):
        super().__init__(parent)
        self.supervisor = supervisor
        self.icon = QSystemTrayIcon(theme.status_icon(State.STOPPED), self)

        self.menu = QMenu()
        self.status_action = QAction(tr("Detenido"), self.menu, enabled=False)
        self.open_action = QAction(tr("Abrir"), self.menu, triggered=self.open_requested.emit)
        self.toggle_action = QAction(tr("Iniciar"), self.menu, triggered=self._toggle)
        self.quit_action = QAction(tr("Salir"), self.menu, triggered=self.quit_requested.emit)
        for a in (self.status_action, None, self.open_action, self.toggle_action, None, self.quit_action):
            self.menu.addSeparator() if a is None else self.menu.addAction(a)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._on_activated)

        supervisor.state_changed.connect(self._on_state)
        supervisor.connected.connect(
            lambda: self.notify(tr("Presencia activa"), tr("Tu actividad de Switch ya se muestra en Discord.")))
        supervisor.dropped.connect(
            lambda: self.notify(tr("Se perdió la conexión"), tr("Reintentando automáticamente…")))
        self._on_state(supervisor.state, supervisor.machine.attempt)
        self.icon.show()

    def notify(self, title: str, msg: str) -> None:
        self.icon.showMessage(title, msg, theme.status_icon(self.supervisor.state), 5000)

    def _on_state(self, state: State, attempt: int) -> None:
        text = state_text(state, attempt, self.supervisor.machine.error)
        self.icon.setIcon(theme.status_icon(state))
        self.icon.setToolTip(f"NSO → Discord: {text}"[:127])
        self.status_action.setText(text)
        running = state in (State.CONNECTING, State.CONNECTED, State.RETRYING)
        self.toggle_action.setText(tr("Detener") if running else tr("Iniciar"))
        if state is State.ERROR:
            self.notify(tr("Error"), text)

    def _toggle(self) -> None:
        if self.supervisor.state in (State.STOPPED, State.ERROR):
            self.supervisor.start()
        else:
            self.supervisor.stop()

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_requested.emit()
