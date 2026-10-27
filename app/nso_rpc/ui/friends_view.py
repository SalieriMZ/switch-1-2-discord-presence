"""Lista de amigos de la cuenta-bot: avatar, nombre, estado, NSA ID y botón para elegir cuál mostrar."""

import hashlib
import urllib.request
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .. import paths
from ..i18n import tr
from ..nxapi import Friend, NxapiClient
from . import theme
from .workers import run_async

AVATAR = 48


def _download_avatar(url: str) -> Path:
    name = hashlib.sha1(url.encode()).hexdigest() + ".img"
    target = paths.avatar_cache_dir() / name
    if not target.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "nso-discord-rpc/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        tmp = target.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(target)
    return target


class FriendCard(QFrame):
    chosen = Signal(object)  # Friend

    def __init__(self, friend: Friend, selected: bool):
        super().__init__()
        self.friend = friend
        self.setObjectName("card")
        self.setProperty("selected", selected)

        self.avatar = QLabel()
        self.avatar.setFixedSize(AVATAR, AVATAR)
        self.avatar.setPixmap(theme.initials_avatar(friend.name, AVATAR))

        name = QLabel(friend.name)
        name.setObjectName("h2")
        color = theme.STATE_COLORS[theme.State.CONNECTED] if friend.online else theme.MUTED
        status = QLabel(f'<span style="color:{color}">●</span> {friend.status_text}')
        nsa = QLabel(f"NSA ID {friend.nsa_id}" + (tr("  ★ favorito") if friend.is_favorite else ""))
        nsa.setObjectName("muted")
        nsa.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(name)
        info.addWidget(status)
        info.addWidget(nsa)

        self.button = QPushButton(tr("Mostrando en Discord") if selected else tr("Mostrar en Discord"))
        self.button.setObjectName("primary" if not selected else "")
        self.button.setEnabled(not selected)
        self.button.clicked.connect(lambda: self.chosen.emit(self.friend))

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)
        row.addWidget(self.avatar)
        row.addLayout(info, 1)
        row.addWidget(self.button)

        if friend.image_url:
            run_async(lambda: _download_avatar(friend.image_url), self._set_avatar, lambda _e: None)

    def _set_avatar(self, path: Path) -> None:
        pm = QPixmap(str(path))
        if not pm.isNull():
            self.avatar.setPixmap(theme.circular(pm, AVATAR))


class FriendsView(QWidget):
    """Emite `chosen(Friend)` al elegir. `select_text` cambia la ayuda de arriba (tutorial vs. pestaña)."""

    chosen = Signal(object)
    loaded = Signal(list)

    def __init__(self, client: NxapiClient | None, selected_nsaid: str | None = None,
                 help_text: str | None = None):
        super().__init__()
        self.client = client
        self.selected_nsaid = selected_nsaid
        self.friends: list[Friend] = []

        self.help = QLabel(help_text or tr("Elige la cuenta cuya actividad quieres mostrar en Discord "
                                           "(normalmente tu cuenta principal)."))
        self.help.setWordWrap(True)
        self.help.setObjectName("muted")
        self.reload_btn = QPushButton(tr("Recargar"))
        self.reload_btn.clicked.connect(self.reload)
        top = QHBoxLayout()
        top.addWidget(self.help, 1)
        top.addWidget(self.reload_btn)

        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.hide()

        self.list = QVBoxLayout()
        self.list.setSpacing(8)
        self.list.addStretch(1)
        holder = QWidget()
        holder.setLayout(self.list)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self.message)
        layout.addWidget(scroll, 1)

    def _show_message(self, text: str, kind: str = "muted") -> None:
        self.message.setObjectName(kind)
        self.message.style().unpolish(self.message)  # re-aplica el selector por objectName
        self.message.style().polish(self.message)
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def reload(self) -> None:
        if self.client is None:
            self._show_message(tr("No se encontró el motor nxapi."), "error")
            return
        self.reload_btn.setEnabled(False)
        self._show_message(tr("Cargando amigos… (puede tardar unos segundos la primera vez)"))
        run_async(self.client.friends, self._on_loaded, self._on_error)

    def _on_error(self, e: Exception) -> None:
        self.reload_btn.setEnabled(True)
        self._show_message(tr("No se pudo cargar la lista: {error}", error=e), "error")

    def _on_loaded(self, friends: list[Friend]) -> None:
        self.reload_btn.setEnabled(True)
        self.friends = sorted(friends, key=lambda f: (not f.online, not f.is_favorite, f.name.lower()))
        if not self.friends:
            self._show_message(
                tr("La cuenta-bot no tiene amigos todavía. Envía la solicitud desde la bot (o desde tu "
                   "consola) y asegúrate de que esté aceptada en ambos lados; luego pulsa Recargar."), "warn")
        else:
            self._show_message("")
        self._render()
        self.loaded.emit(self.friends)

    def set_selected(self, nsaid: str | None) -> None:
        self.selected_nsaid = nsaid
        self._render()

    def friend(self, nsaid: str | None) -> Friend | None:
        return next((f for f in self.friends if f.nsa_id == nsaid), None)

    def _render(self) -> None:
        while self.list.count() > 1:
            item = self.list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, f in enumerate(self.friends):
            card = FriendCard(f, f.nsa_id == self.selected_nsaid)
            card.chosen.connect(self._on_chosen)
            self.list.insertWidget(i, card)

    def _on_chosen(self, friend: Friend) -> None:
        self.set_selected(friend.nsa_id)
        self.chosen.emit(friend)
