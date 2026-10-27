"""Entrada de la app: instancia única, bandeja, ventana y tutorial."""

import argparse
import sys

from PySide6.QtCore import QThreadPool
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from . import runtime
from .config import Config
from .nxapi import NxapiClient
from .onboarding import wizard_start
from .presence import PresenceSupervisor
from .presence_state import State
from .ui import theme
from .ui.main_window import MainWindow
from .ui.tray import Tray
from .ui.wizard import Wizard
from .ui.workers import run_async

SERVER_NAME = "nso-discord-rpc"


def _signal_existing_instance() -> bool:
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if sock.waitForConnected(500):
        sock.write(b"show")
        sock.waitForBytesWritten(500)
        sock.disconnectFromServer()
        return True
    return False


class App:
    def __init__(self, qapp: QApplication, minimized: bool):
        self.qapp = qapp
        self.config = Config.load()
        try:
            self.client: NxapiClient | None = NxapiClient(runtime.locate())
        except runtime.RuntimeMissing as e:
            self.client = None
            QMessageBox.critical(None, "NSO → Discord", str(e))

        self.supervisor = PresenceSupervisor(self.client, self.config)
        self.window = MainWindow(self.client, self.supervisor, self.config)
        self.window.open_wizard.connect(lambda: self.show_wizard())
        self.tray = Tray(self.supervisor)
        self.tray.open_requested.connect(self.window.show_and_raise)
        self.tray.quit_requested.connect(self.quit)
        self.wizard: Wizard | None = None

        self.server = QLocalServer()
        QLocalServer.removeServer(SERVER_NAME)
        self.server.listen(SERVER_NAME)
        self.server.newConnection.connect(self._on_other_instance)

        self.minimized = minimized
        self._pending_route = not self.config.tutorial_done
        if not self._pending_route:
            self._open_main()
        if self.client is not None:
            run_async(self.client.whoami, self._on_whoami, lambda _e: self._on_whoami(None))
            run_async(runtime.cleanup_legacy_cache, lambda _r: None, lambda _e: None)
        else:
            self._on_whoami(None)

    def _open_main(self) -> None:
        if not self.minimized:
            self.window.show_and_raise()
        if self.config.autostart_presence and self.config.friend_nsaid:
            self.supervisor.start()

    def _on_whoami(self, bot: dict | None) -> None:
        if bot:
            self.supervisor.log_line.emit(f"Cuenta-bot: {bot.get('nickname')} ({bot.get('id')})")
        if not self._pending_route:
            return
        self._pending_route = False
        start = wizard_start(self.config, bot)
        if start is None:
            # Ya estaba todo listo (p. ej. usó la versión de consola o reinstaló): sin tutorial.
            self.config.tutorial_done = True
            self.config.save()
            self.supervisor.log_line.emit("Cuenta-bot y cuenta elegida ya configuradas: se omite el tutorial.")
            self._open_main()
        else:
            self.show_wizard(start)

    def _on_other_instance(self) -> None:
        conn = self.server.nextPendingConnection()
        if conn:
            conn.readyRead.connect(conn.readAll)
            conn.disconnected.connect(conn.deleteLater)
        if self.wizard and self.wizard.isVisible():
            self.wizard.raise_()
            self.wizard.activateWindow()
        else:
            self.window.show_and_raise()

    def show_wizard(self, start: int = 0) -> None:
        if self.wizard and self.wizard.isVisible():
            self.wizard.raise_()
            self.wizard.activateWindow()
            return
        self.window.hide()
        self.wizard = Wizard(self.client, self.config, start)
        self.wizard.finished.connect(self._wizard_done)
        self.wizard.show()

    def _wizard_done(self, _result: int) -> None:
        completed = self.wizard.completed if self.wizard else False
        self.wizard = None
        self.window.friends.set_selected(self.config.friend_nsaid)
        self.window.show_and_raise()
        if not self.config.friend_nsaid:
            return
        if self.supervisor.state in (State.STOPPED, State.ERROR):
            # Al omitir también se reanuda (p. ej. tras "Repetir configuración inicial", que la detiene).
            if completed or self.config.autostart_presence:
                self.supervisor.start()
        elif completed:
            self.supervisor.restart()

    def quit(self) -> None:
        self.supervisor.shutdown()
        self.tray.icon.hide()
        self.window.allow_quit()
        QThreadPool.globalInstance().waitForDone(3000)
        self.qapp.quit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="NSO-Discord-RPC")
    parser.add_argument("--minimized", action="store_true", help="arrancar solo en la bandeja")
    args, qt_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    qapp = QApplication([sys.argv[0], *qt_args])
    qapp.setApplicationName("NSO-Discord-RPC")
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setWindowIcon(theme.app_icon())
    qapp.setStyleSheet(theme.QSS)

    if _signal_existing_instance():
        return 0

    app = App(qapp, args.minimized)
    code = qapp.exec()
    del app
    return code


if __name__ == "__main__":
    sys.exit(main())
