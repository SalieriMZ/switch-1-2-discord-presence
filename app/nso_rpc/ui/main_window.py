"""Ventana principal: cabecera de estado + pestañas Amigos · Configuración · Registro · Ayuda."""

import subprocess

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from ..config import Config
from ..nxapi import Friend, NxapiClient
from ..presence import PresenceSupervisor
from ..presence_state import State
from ..runtime import CREATE_NO_WINDOW
from . import theme
from .friends_view import FriendsView
from .log_view import LogView
from .settings_view import SettingsView
from .workers import run_async

DISCORD_CHECK_MS = 15_000


def discord_running() -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Discord.exe", "/NH"],
                             capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return True  # si no se puede saber, no molestar con el aviso
    return "discord.exe" in out.lower()


def state_text(state: State, attempt: int, error: str | None) -> str:
    return {
        State.CONNECTED: "Conectado",
        State.CONNECTING: "Conectando…" if attempt <= 1 else f"Conectando… (intento {attempt})",
        State.RETRYING: f"Reintentando (intento {attempt + 1})",
        State.STOPPED: "Detenido",
        State.ERROR: f"Error: {error}",
    }[state]


class MainWindow(QMainWindow):
    open_wizard = Signal()
    quit_requested = Signal()

    def __init__(self, client: NxapiClient | None, supervisor: PresenceSupervisor, config: Config,
                 bot_label: str | None = None):
        super().__init__()
        self.client = client
        self.supervisor = supervisor
        self.config = config
        self._really_quit = False
        self._resume_after_update = False
        self.setWindowTitle("NSO → Discord")
        self.setWindowIcon(theme.app_icon())
        self.resize(640, 620)
        self.setMinimumSize(520, 480)

        # Cabecera
        self.dot = QLabel()
        self.state_label = QLabel()
        self.state_label.setObjectName("title")
        self.detail = QLabel()
        self.detail.setObjectName("muted")
        self.detail.setWordWrap(True)
        self.discord_warn = QLabel("⚠ No detecto Discord de escritorio abierto: ábrelo para que se vea la actividad.")
        self.discord_warn.setObjectName("warn")
        self.discord_warn.setWordWrap(True)
        self.discord_warn.hide()
        self.toggle = QPushButton()
        self.toggle.setObjectName("primary")
        self.toggle.setMinimumWidth(110)
        self.toggle.clicked.connect(self._on_toggle)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(self.dot)
        title_row.addWidget(self.state_label, 1)
        title_row.addWidget(self.toggle)
        header = QFrame()
        header.setObjectName("header")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(16, 14, 16, 14)
        hl.addLayout(title_row)
        hl.addWidget(self.detail)
        hl.addWidget(self.discord_warn)

        # Pestañas
        self.friends = FriendsView(client, config.friend_nsaid)
        self.friends.chosen.connect(self._on_friend_chosen)
        self.friends.loaded.connect(lambda _f: self._refresh_header())
        self.settings = SettingsView(config, client)
        self.log = LogView()
        self.settings.log.connect(self.log.append)
        self.settings.presence_changed.connect(self.supervisor.restart)
        self.settings.update_started.connect(self._on_update_started)
        self.settings.update_finished.connect(self._on_update_finished)
        self.settings.restart_flow.connect(self._on_restart_flow)
        supervisor.log_line.connect(self.log.append)
        supervisor.state_changed.connect(lambda *_: self._refresh_header())
        supervisor.connected.connect(self.friends.reload)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._padded(self.friends), "Amigos")
        self.tabs.addTab(self._padded(self.settings), "Configuración")
        self.tabs.addTab(self._padded(self.log), "Registro")
        self.tabs.addTab(self._padded(self._help_page(bot_label)), "Ayuda")

        central = QWidget()
        central.setObjectName("page")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(10)
        layout.addWidget(header)
        layout.addWidget(self.tabs, 1)
        self.setCentralWidget(central)

        self._discord_timer = QTimer(self, interval=DISCORD_CHECK_MS)
        self._discord_timer.timeout.connect(self._check_discord)
        self._discord_timer.start()
        self._check_discord()
        self._refresh_header()

    @staticmethod
    def _padded(w: QWidget) -> QWidget:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(4, 12, 4, 4)
        l.addWidget(w)
        return box

    def _help_page(self, bot_label: str | None) -> QWidget:
        page = QWidget()
        text = QLabel(
            "<p><b>Cómo funciona.</b> Nintendo no deja leer tu propia actividad, solo la de tus amigos. "
            "Por eso una <b>cuenta-bot</b> (una cuenta Nintendo desechable) te tiene como amigo y "
            "“mira” lo que juegas; esta app lo publica en tu Discord.</p>"
            "<p><b>Si no aparece nada en Discord:</b> Discord de escritorio abierto · tu cuenta principal "
            "jugando y en línea · privacidad de la principal en “Todos los amigos” · bot y principal "
            "son amigos aceptados.</p>"
            "<p><b>Seguridad:</b> nunca inicies sesión aquí con tu cuenta principal; el riesgo lo absorbe "
            "la bot.</p>"
            + (f"<p>Cuenta-bot actual: <b>{bot_label}</b></p>" if bot_label else "")
        )
        text.setWordWrap(True)
        text.setTextFormat(Qt.TextFormat.RichText)
        wizard = QPushButton("Abrir el tutorial")
        wizard.clicked.connect(self.open_wizard.emit)
        l = QVBoxLayout(page)
        l.addWidget(text)
        l.addWidget(wizard, 0, Qt.AlignmentFlag.AlignLeft)
        l.addStretch(1)
        return page

    def _on_restart_flow(self) -> None:
        self.supervisor.stop()
        self.open_wizard.emit()

    # --- estado ---------------------------------------------------------------

    def _refresh_header(self) -> None:
        m = self.supervisor.machine
        self.dot.setPixmap(theme.dot(theme.STATE_COLORS[m.state], 14))
        self.state_label.setText(state_text(m.state, m.attempt, m.error))
        running = m.state in (State.CONNECTING, State.CONNECTED, State.RETRYING)
        self.toggle.setText("Detener" if running else "Iniciar")

        friend = self.friends.friend(self.config.friend_nsaid)
        name = (friend.name if friend else None) or self.config.friend_name
        if not self.config.friend_nsaid:
            self.detail.setText("Todavía no eliges qué cuenta mostrar: hazlo en la pestaña Amigos.")
        else:
            parts = [f"Mostrando a <b>{name or self.config.friend_nsaid}</b>"]
            if friend:
                parts.append(friend.status_text)
            self.detail.setText(" · ".join(parts))

    def _on_toggle(self) -> None:
        if self.supervisor.state in (State.STOPPED, State.ERROR):
            self.supervisor.start()
        else:
            self.supervisor.stop()

    def _on_friend_chosen(self, friend: Friend) -> None:
        changed = friend.nsa_id != self.config.friend_nsaid
        self.config.friend_nsaid = friend.nsa_id
        self.config.friend_name = friend.name
        self.config.save()
        self._refresh_header()
        if changed and self.supervisor.state not in (State.STOPPED, State.ERROR):
            self.supervisor.restart()
        elif self.supervisor.state in (State.STOPPED, State.ERROR):
            self.supervisor.start()

    def _on_update_started(self) -> None:
        self._resume_after_update = self.supervisor.state not in (State.STOPPED, State.ERROR)
        self.supervisor.stop()

    def _on_update_finished(self, _ok: bool) -> None:
        if self._resume_after_update:
            self.supervisor.start()

    def _check_discord(self) -> None:
        run_async(discord_running, lambda ok: self.discord_warn.setVisible(not ok))

    # --- ventana / bandeja ----------------------------------------------------

    def show_and_raise(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if not self.friends.friends:
            self.friends.reload()

    def allow_quit(self) -> None:
        self._really_quit = True

    def closeEvent(self, event) -> None:
        if self._really_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()
