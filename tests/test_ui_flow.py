"""Flujo de UI sin red: cliente falso, plataforma Qt offscreen."""

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from nso_rpc.config import Config
from nso_rpc.nxapi import Friend
from nso_rpc.runtime import Runtime

FRIEND = Friend("1a6e258084006b16", "Salieri", None, True, "Mario Kart World", False)


class FakeClient:
    def __init__(self, tmp_path):
        self.rt = Runtime(tmp_path)
        self.added = []

    def whoami(self):
        return {"id": "bot", "nickname": "Salieri2", "screen_name": None, "nso_name": "111"}

    def friends(self):
        return [FRIEND]

    def friend_code(self):
        return "7397-2772-5792"

    def add_friend(self, code):
        self.added.append(code)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))


def wait_for(qapp, cond, timeout=5.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        qapp.processEvents()
        if cond():
            return True
        time.sleep(0.01)
    return False


def test_wizard_existing_bot_and_choose_friend(qapp, tmp_path):
    from nso_rpc.ui.wizard import Wizard

    cfg = Config()
    wiz = Wizard(FakeClient(tmp_path), cfg)
    assert wait_for(qapp, lambda: wiz.bot is not None)
    wiz._go(2)
    assert wiz.next.isEnabled()

    wiz._go(4)
    assert not wiz.next.isEnabled()
    assert wait_for(qapp, lambda: bool(wiz.friends_view.friends))
    card = wiz.friends_view.list.itemAt(0).widget()
    card.button.click()
    assert wiz.next.isEnabled()
    assert wiz.next.text() == "Terminar"

    wiz.next.click()
    assert wiz.completed
    saved = Config.load()
    assert saved.friend_nsaid == FRIEND.nsa_id and saved.tutorial_done


def test_wizard_skip_marks_done(qapp, tmp_path):
    from nso_rpc.ui.wizard import Wizard

    cfg = Config()
    wiz = Wizard(FakeClient(tmp_path), cfg)
    wiz._skip()
    assert Config.load().tutorial_done and not wiz.completed


def test_main_window_choose_saves_and_header(qapp, tmp_path):
    from nso_rpc.presence import PresenceSupervisor
    from nso_rpc.ui.main_window import MainWindow

    cfg = Config(tutorial_done=True, autostart_presence=False)
    client = FakeClient(tmp_path)
    sup = PresenceSupervisor(None, cfg)  # sin motor: start() -> ERROR, sin procesos
    win = MainWindow(client, sup, cfg)
    assert "Todavía no eliges" in win.detail.text()
    win.friends.reload()
    assert wait_for(qapp, lambda: bool(win.friends.friends))
    win.friends.list.itemAt(0).widget().button.click()
    assert Config.load().friend_nsaid == FRIEND.nsa_id
    assert "Salieri" in win.detail.text() and "Jugando Mario Kart World" in win.detail.text()


def test_wizard_can_start_at_choose_step(qapp, tmp_path):
    from nso_rpc.onboarding import STEP_CHOOSE
    from nso_rpc.ui.wizard import Wizard

    wiz = Wizard(FakeClient(tmp_path), Config(), start=STEP_CHOOSE)
    assert wiz.stack.currentIndex() == STEP_CHOOSE
    assert "Paso 5 de 5" in wiz.progress.text()


def test_settings_restart_flow_resets_tutorial(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from nso_rpc.presence import PresenceSupervisor
    from nso_rpc.ui.main_window import MainWindow

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    cfg = Config(tutorial_done=True, autostart_presence=False, friend_nsaid=FRIEND.nsa_id)
    cfg.save()
    win = MainWindow(FakeClient(tmp_path), PresenceSupervisor(None, cfg), cfg)
    opened = []
    win.open_wizard.connect(lambda: opened.append(True))
    win.settings.restart_btn.click()
    assert opened == [True]
    assert not Config.load().tutorial_done
    assert Config.load().friend_nsaid == FRIEND.nsa_id  # la cuenta elegida no se pierde
