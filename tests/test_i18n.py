"""Traducciones: cada tr("...") del código tiene su versión en inglés con los mismos marcadores."""

import ast
import os
import string
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from nso_rpc import i18n
from nso_rpc.nxapi import Friend
from nso_rpc.ui.wizard import STEPS

APP = Path(__file__).resolve().parents[1] / "app" / "nso_rpc"


def _tr_literals() -> set[str]:
    found = set()
    for path in APP.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "tr"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                found.add(node.args[0].value)
    return found | set(STEPS)


def _fields(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


@pytest.fixture
def english():
    i18n.set_language("en")
    yield
    i18n.set_language("es")


def test_every_string_has_english():
    literals = _tr_literals()
    assert len(literals) > 50
    missing = sorted(literals - i18n.EN.keys())
    assert not missing, missing


def test_placeholders_match():
    for es, en in i18n.EN.items():
        assert _fields(es) == _fields(en), es


def test_tr_spanish_by_default():
    assert i18n.tr("Jugando {game}", game="Zelda") == "Jugando Zelda"


def test_tr_english(english):
    assert i18n.tr("Jugando {game}", game="Zelda") == "Playing Zelda"
    assert Friend("x", "n", None, False, None, False).status_text == "Offline"


def test_set_language_auto_resolves():
    assert i18n.set_language("auto") in ("es", "en")
    assert i18n.set_language("fr") in ("es", "en")
    i18n.set_language("es")


def test_settings_language_saves(english, tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    from PySide6.QtWidgets import QApplication

    from nso_rpc.config import Config
    from nso_rpc.ui.settings_view import SettingsView

    QApplication.instance() or QApplication([])
    cfg = Config()
    view = SettingsView(cfg, None)
    assert view.update_btn.text() == "Update nxapi"
    view.language.setCurrentIndex(view.language.findData("es"))
    assert Config.load().language == "es"
    assert not view.language_help.isHidden()
