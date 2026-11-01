"""Menú de la bandeja: cada opción tiene que llegar a su señal."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from nso_rpc.config import Config
from nso_rpc.presence import PresenceSupervisor
from nso_rpc.ui.tray import Tray


@pytest.fixture
def tray():
    QApplication.instance() or QApplication([])
    t = Tray(PresenceSupervisor(None, Config()))
    yield t
    t.icon.hide()


def _fires(signal, action) -> bool:
    hits = []
    signal.connect(lambda: hits.append(True))
    action.trigger()
    return bool(hits)


def test_quit_action_requests_quit(tray):
    assert _fires(tray.quit_requested, tray.quit_action)


def test_open_action_requests_open(tray):
    assert _fires(tray.open_requested, tray.open_action)


def test_help_button_opens_wizard(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from PySide6.QtWidgets import QPushButton

    from nso_rpc.ui.main_window import MainWindow

    QApplication.instance() or QApplication([])
    cfg = Config()
    win = MainWindow(None, PresenceSupervisor(None, cfg), cfg)
    hits = []
    win.open_wizard.connect(lambda: hits.append(True))
    button = next(b for b in win.findChildren(QPushButton) if b.text() == "Abrir el tutorial")
    button.click()
    assert hits
