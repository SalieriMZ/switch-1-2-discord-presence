import json

import pytest

from nso_rpc.config import Config


@pytest.fixture(autouse=True)
def _appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))


def test_roundtrip(tmp_path):
    path = tmp_path / "c.json"
    cfg = Config(friend_nsaid="1a6e258084006b16", friend_name="Seba", tutorial_done=True, update_interval=90)
    cfg.save(path)
    assert Config.load(path) == cfg


def test_missing_file_defaults(tmp_path):
    assert Config.load(tmp_path / "nope.json") == Config()


def test_corrupt_file_defaults(tmp_path):
    path = tmp_path / "c.json"
    path.write_text("{no es json", encoding="utf-8")
    assert Config.load(path) == Config()


def test_utf8_bom_file_loads(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"friend_nsaid": "abc", "tutorial_done": True}), encoding="utf-8-sig")
    cfg = Config.load(path)
    assert cfg.friend_nsaid == "abc" and cfg.tutorial_done is True


def test_interval_clamped_to_30(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"update_interval": 10}), encoding="utf-8")
    assert Config.load(path).update_interval == 30


def test_unknown_keys_ignored(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"foo": 1, "show_play_time": True}), encoding="utf-8")
    cfg = Config.load(path)
    assert cfg.show_play_time is True


def test_default_path_under_appdata(tmp_path):
    Config(friend_name="x").save()
    assert (tmp_path / "roaming" / "NSO-Discord-RPC" / "config.json").exists()
    assert Config.load().friend_name == "x"


def test_default_update_interval_is_120():
    assert Config().update_interval == 120
