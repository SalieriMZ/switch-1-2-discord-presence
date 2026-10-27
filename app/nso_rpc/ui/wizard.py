"""Tutorial de primer uso: 5 pasos, con "Omitir tutorial" siempre visible."""

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from ..authlink import extract_auth_link
from ..config import Config
from ..i18n import tr
from ..nxapi import Friend, NxapiClient
from . import theme
from .friends_view import FriendsView
from .workers import run_async

# En español: se traducen con tr() al mostrarlos.
STEPS = ["Bienvenida", "Cuenta-bot", "Iniciar sesión", "Amistad", "Elegir cuenta"]


def _text(html: str) -> QLabel:
    label = QLabel(html)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    return label


def _page(title: str, *widgets) -> QWidget:
    page = QWidget()
    l = QVBoxLayout(page)
    l.setContentsMargins(0, 0, 0, 0)
    l.setSpacing(12)
    t = QLabel(title)
    t.setObjectName("title")
    l.addWidget(t)
    for w in widgets:
        if isinstance(w, QWidget):
            l.addWidget(w)
        else:
            l.addLayout(w)
    l.addStretch(1)
    return page


def _set_kind(label: QLabel, kind: str, text: str) -> None:
    label.setObjectName(kind)
    label.style().unpolish(label)
    label.style().polish(label)
    label.setText(text)


class Wizard(QDialog):
    def __init__(self, client: NxapiClient | None, config: Config, start: int = 0):
        super().__init__()
        self.client = client
        self.config = config
        self.completed = False
        self.bot: dict | None = None
        self.state_file: str | None = None
        self.chosen: Friend | None = None
        self._submitting = False

        self.setWindowTitle("NSO → Discord · Tutorial")
        self.setWindowIcon(theme.app_icon())
        self.resize(640, 600)

        self.progress = QLabel()
        self.progress.setObjectName("muted")
        skip = QPushButton(tr("Omitir tutorial"))
        skip.setObjectName("link")
        skip.clicked.connect(self._skip)
        top = QHBoxLayout()
        top.addWidget(self.progress, 1)
        top.addWidget(skip)

        self.stack = QStackedWidget()
        for page in (self._welcome(), self._bot_page(), self._login_page(), self._friend_page(), self._choose_page()):
            self.stack.addWidget(page)

        self.back = QPushButton(tr("Atrás"))
        self.back.clicked.connect(lambda: self._go(self.stack.currentIndex() - 1))
        self.next = QPushButton(tr("Siguiente"))
        self.next.setObjectName("primary")
        self.next.clicked.connect(self._on_next)
        nav = QHBoxLayout()
        nav.addWidget(self.back)
        nav.addStretch(1)
        nav.addWidget(self.next)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 18)
        layout.addLayout(top)
        layout.addWidget(self.stack, 1)
        layout.addLayout(nav)

        QGuiApplication.clipboard().dataChanged.connect(self._on_clipboard)
        self._go(start)
        if client is not None:
            run_async(client.whoami, self._on_whoami, lambda e: self._on_whoami(None))

    # --- páginas ----------------------------------------------------------------

    def _welcome(self) -> QWidget:
        return _page(
            tr("Muestra en Discord lo que juegas en tu Switch"),
            _text(tr(
                "<p>Esta app publica en tu perfil de Discord el juego que estás jugando en tu Nintendo "
                "Switch, como “Jugando a …”.</p>"
                "<p>Necesitas:</p><ul>"
                "<li><b>Discord de escritorio</b> abierto en este PC.</li>"
                "<li>Una <b>cuenta Nintendo extra</b> (la “cuenta-bot”). Te explicamos por qué en el "
                "siguiente paso.</li>"
                "<li>Unos 5 minutos.</li></ul>"
                "<p>Una vez configurada, la app vive en la <b>bandeja del sistema</b> (junto al reloj) y "
                "se reconecta sola.</p>")
            ),
        )

    def _bot_page(self) -> QWidget:
        return _page(
            tr("¿Por qué una cuenta-bot?"),
            _text(tr(
                "<p>Nintendo <b>no deja leer tu propia actividad</b>: su API solo entrega la de tus "
                "<b>amigos</b>. Por eso usamos una segunda cuenta Nintendo, la <b>cuenta-bot</b>, que te "
                "tiene como amiga y “mira” lo que juegas.</p>"
                "<p><b>Cómo crearla:</b></p><ol>"
                "<li>Crea una cuenta nueva en "
                "<a href='https://accounts.nintendo.com/'>accounts.nintendo.com</a> con un correo "
                "dedicado.</li>"
                "<li>No necesita suscripción de pago ni estar en tu consola.</li></ol>")
            ),
        )

    def _login_page(self) -> QWidget:
        self.login_status = QLabel()
        self.login_status.setWordWrap(True)

        self.continue_btn = QPushButton(tr("Continuar con esta cuenta"))
        self.continue_btn.setObjectName("primary")
        self.continue_btn.clicked.connect(lambda: self._go(3))
        self.other_btn = QPushButton(tr("Usar otra cuenta"))
        self.other_btn.clicked.connect(self._show_login_form)
        existing = QHBoxLayout()
        existing.addWidget(self.continue_btn)
        existing.addWidget(self.other_btn)
        existing.addStretch(1)
        self.existing_box = QWidget()
        self.existing_box.setLayout(existing)
        self.existing_box.hide()

        self.open_login = QPushButton(tr("1 · Abrir inicio de sesión de Nintendo"))
        self.open_login.setObjectName("primary")
        self.open_login.clicked.connect(self._open_login)
        steps = _text(tr(
            "<ol>"
            "<li>Pulsa el botón: se abre tu navegador. Inicia sesión con la <b>cuenta-bot</b>.</li>"
            "<li>En la página “Vincular una cuenta externa”, haz <b>clic derecho</b> sobre "
            "<b>“Elegir esta cuenta”</b> → <b>Copiar dirección del enlace</b>.</li>"
            "<li>Listo: la app detecta el enlace copiado sola. Si no, pégalo abajo.</li>"
            "</ol>")
        )
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("npf71b963c1b7b6d119://auth#session_token_code=…")
        self.link_input.returnPressed.connect(lambda: self._submit_link(self.link_input.text()))
        send = QPushButton(tr("Enviar"))
        send.clicked.connect(lambda: self._submit_link(self.link_input.text()))
        manual = QHBoxLayout()
        manual.addWidget(self.link_input, 1)
        manual.addWidget(send)

        form = QVBoxLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addWidget(self.open_login, 0, Qt.AlignmentFlag.AlignLeft)
        form.addWidget(steps)
        form.addLayout(manual)
        self.login_form = QWidget()
        self.login_form.setLayout(form)
        self.login_form.hide()

        return _page(tr("Inicia sesión con la cuenta-bot"), self.login_status, self.existing_box, self.login_form)

    def _friend_page(self) -> QWidget:
        self.code_label = QLabel(tr("Cargando código de amigo…"))
        self.code_label.setObjectName("h2")
        self.code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        copy = QPushButton(tr("Copiar"))
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self._friend_code or ""))
        code_row = QHBoxLayout()
        code_row.addWidget(QLabel(tr("Código de amigo de la bot:")))
        code_row.addWidget(self.code_label)
        code_row.addWidget(copy)
        code_row.addStretch(1)
        self._friend_code: str | None = None

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText(tr("Código de amigo de tu cuenta principal (SW-XXXX-XXXX-XXXX)"))
        self.add_btn = QPushButton(tr("Enviar solicitud"))
        self.add_btn.clicked.connect(self._send_request)
        add_row = QHBoxLayout()
        add_row.addWidget(self.add_input, 1)
        add_row.addWidget(self.add_btn)
        self.add_status = QLabel()
        self.add_status.setWordWrap(True)

        self.check_privacy = QCheckBox(tr("En la consola, con tu cuenta principal: Configuración de usuario → "
                                          "Ajustes de amigos → “Mostrar estado en línea a” = Todos los amigos"))
        self.check_friends = QCheckBox(tr("La bot y tu cuenta principal son amigos (solicitud aceptada)"))
        for c in (self.check_privacy, self.check_friends):
            c.setStyleSheet("QCheckBox { padding: 2px; }")

        return _page(
            tr("Hazte amigo de la bot"),
            _text(tr("<p>La bot tiene que ser <b>amiga</b> de tu cuenta principal. Haz una de las dos:</p><ul>"
                     "<li>Desde tu Switch, agrega a la bot con su código de amigo, <b>o</b></li>"
                     "<li>Envía la solicitud desde la bot a tu código de amigo y acéptala en la Switch.</li></ul>")),
            code_row, add_row, self.add_status,
            _text(tr("<p><b>Revisa también:</b></p>")), self.check_privacy, self.check_friends,
        )

    def _choose_page(self) -> QWidget:
        self.friends_view = FriendsView(
            self.client, self.config.friend_nsaid,
            tr("Elige tu cuenta principal: es la que se mostrará en Discord."))
        self.friends_view.chosen.connect(self._on_chosen)
        page = _page(tr("Elige qué cuenta mostrar"))
        page.layout().insertWidget(1, self.friends_view, 1)
        return page

    # --- navegación -----------------------------------------------------------------

    def _go(self, index: int) -> None:
        index = max(0, min(index, self.stack.count() - 1))
        self.stack.setCurrentIndex(index)
        self.progress.setText(tr("Paso {n} de {total} · {name}",
                                 n=index + 1, total=len(STEPS), name=tr(STEPS[index])))
        self.back.setEnabled(index > 0)
        last = index == self.stack.count() - 1
        self.next.setText(tr("Terminar") if last else tr("Siguiente"))
        if index == 3 and self._friend_code is None and self.client:
            run_async(self.client.friend_code, self._on_code,
                      lambda e: self.code_label.setText(tr("no disponible")))
        if last and not self.friends_view.friends:
            self.friends_view.reload()
        self._update_next()

    def _update_next(self) -> None:
        i = self.stack.currentIndex()
        if i == 2:
            self.next.setEnabled(self.bot is not None)
        elif i == 4:
            self.next.setEnabled(self.chosen is not None or bool(self.config.friend_nsaid))
        else:
            self.next.setEnabled(True)

    def _on_next(self) -> None:
        if self.stack.currentIndex() == self.stack.count() - 1:
            self._finish()
        else:
            self._go(self.stack.currentIndex() + 1)

    def _skip(self) -> None:
        self.config.tutorial_done = True
        self.config.save()
        self.reject()

    def _finish(self) -> None:
        if self.chosen:
            self.config.friend_nsaid = self.chosen.nsa_id
            self.config.friend_name = self.chosen.name
        self.config.tutorial_done = True
        self.config.save()
        self.completed = True
        self.accept()

    def done(self, result: int) -> None:
        try:
            QGuiApplication.clipboard().dataChanged.disconnect(self._on_clipboard)
        except (RuntimeError, TypeError):
            pass
        super().done(result)

    # --- login ------------------------------------------------------------------------

    def _on_whoami(self, bot: dict | None) -> None:
        if self.client is None:
            _set_kind(self.login_status, "error", tr("No se encontró el motor nxapi."))
            return
        if bot:
            self.bot = bot
            _set_kind(self.login_status, "", tr("Ya hay una cuenta-bot conectada: <b>{name}</b>", name=bot.get("nickname"))
                      + (tr(" (Switch: {name})", name=bot["nso_name"]) if bot.get("nso_name") else "") + ".")
            self.existing_box.show()
            self.login_form.hide()
        else:
            self._show_login_form()
        self._update_next()

    def _show_login_form(self) -> None:
        self.existing_box.hide()
        self.login_form.show()
        if self.bot is None:
            _set_kind(self.login_status, "muted", tr("Todavía no hay una cuenta-bot conectada."))
        else:
            _set_kind(self.login_status, "muted", tr("Inicia sesión con la otra cuenta-bot."))

    def _open_login(self) -> None:
        self.open_login.setEnabled(False)
        _set_kind(self.login_status, "muted", tr("Preparando el enlace de Nintendo…"))

        def ok(result):
            url, self.state_file = result
            self.open_login.setEnabled(True)
            QDesktopServices.openUrl(QUrl(url))
            _set_kind(self.login_status, "muted", tr("Navegador abierto. Esperando el enlace copiado…"))

        def err(e):
            self.open_login.setEnabled(True)
            _set_kind(self.login_status, "error", tr("No se pudo generar el enlace: {error}", error=e))

        run_async(self.client.auth_url, ok, err)

    def _on_clipboard(self) -> None:
        if self.stack.currentIndex() != 2 or not self.login_form.isVisible():
            return
        link = extract_auth_link(QGuiApplication.clipboard().text())
        if link:
            self.link_input.setText(link)
            self._submit_link(link)

    def _submit_link(self, text: str) -> None:
        if self._submitting:
            return
        link = extract_auth_link(text)
        if not link:
            _set_kind(self.login_status, "error",
                      tr("Ese no parece el enlace correcto. Debe empezar con npf71b963c1b7b6d119://auth y "
                         "contener session_token_code."))
            return
        if not self.state_file:
            _set_kind(self.login_status, "error", tr("Primero pulsa “Abrir inicio de sesión de Nintendo”."))
            return
        self._submitting = True
        _set_kind(self.login_status, "muted", tr("Iniciando sesión… (puede tardar unos segundos)"))

        def ok(bot):
            self._submitting = False
            self.state_file = None
            self.bot = bot
            self.friends_view.friends = []  # otra bot = otra lista
            self._friend_code = None
            _set_kind(self.login_status, "", tr("✓ Sesión iniciada como <b>{name}</b>.", name=bot.get("nickname")))
            self._update_next()

        def err(e):
            self._submitting = False
            self.state_file = None  # el enlace es de un solo uso: pedir uno nuevo
            _set_kind(self.login_status, "error",
                      tr("No se pudo iniciar sesión: {error}. Vuelve a pulsar “Abrir inicio de sesión” e "
                         "inténtalo de nuevo.", error=e))

        state_file = self.state_file
        run_async(lambda: self.client.auth_complete(state_file, link), ok, err)

    # --- amistad / elección ---------------------------------------------------------------

    def _on_code(self, code: str) -> None:
        self._friend_code = code
        self.code_label.setText(f"SW-{code}")

    def _send_request(self) -> None:
        code = self.add_input.text().strip()
        if not code:
            return
        self.add_btn.setEnabled(False)
        _set_kind(self.add_status, "muted", tr("Enviando solicitud…"))

        def ok(_):
            self.add_btn.setEnabled(True)
            _set_kind(self.add_status, "", tr("✓ Solicitud enviada. Acéptala en tu Switch "
                                             "(Perfil → Amigos → Solicitudes recibidas)."))

        def err(e):
            self.add_btn.setEnabled(True)
            _set_kind(self.add_status, "error", tr("No se pudo enviar: {error}", error=e))

        run_async(lambda: self.client.add_friend(code), ok, err)

    def _on_chosen(self, friend: Friend) -> None:
        self.chosen = friend
        self._update_next()
