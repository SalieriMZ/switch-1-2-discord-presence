import sys

import pytest

from nso_rpc import runtime


def _fake_runtime(root):
    (root / "node").mkdir(parents=True)
    (root / "node" / "node.exe").write_bytes(b"")
    (root / "node" / "node_modules" / "npm" / "bin").mkdir(parents=True)
    (root / "node" / "node_modules" / "npm" / "bin" / "npm-cli.js").write_text("")
    (root / "node_modules" / "nxapi" / "bin").mkdir(parents=True)
    (root / "node_modules" / "nxapi" / "bin" / "nxapi.js").write_text("")
    (root / "bridge.mjs").write_text("")
    (root / "discord-fix.mjs").write_text("")
    return root


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("NSO_RPC_RUNTIME", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def test_locate_env_override(tmp_path, monkeypatch):
    root = _fake_runtime(tmp_path / "rt")
    monkeypatch.setenv("NSO_RPC_RUNTIME", str(root))
    rt = runtime.locate()
    assert rt.root == root
    assert rt.node == root / "node" / "node.exe"
    assert rt.nxapi_bin == root / "node_modules" / "nxapi" / "bin" / "nxapi.js"
    assert rt.bridge == root / "bridge.mjs"


def test_locate_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("NSO_RPC_RUNTIME", str(tmp_path / "vacio"))
    monkeypatch.setattr(runtime, "DEV_RUNTIME", tmp_path / "tampoco")
    with pytest.raises(runtime.RuntimeMissing):
        runtime.locate()


def test_env_has_user_agent_and_node_on_path(tmp_path, monkeypatch):
    root = _fake_runtime(tmp_path / "rt")
    monkeypatch.setenv("NSO_RPC_RUNTIME", str(root))
    env = runtime.env(runtime.locate())
    assert env["NXAPI_USER_AGENT"] == "nso-discord-rpc/1.0"
    assert env["PATH"].split(";")[0] == str(root / "node")


def test_frozen_uses_runtime_next_to_exe(tmp_path, monkeypatch):
    app_dir = tmp_path / "NSO-Discord-RPC"
    _fake_runtime(app_dir / "runtime")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(app_dir / "NSO-Discord-RPC.exe"))
    assert runtime.locate().root == app_dir / "runtime"


def test_cleanup_legacy_cache(tmp_path):
    old = tmp_path / "local" / "NSO-Discord-RPC" / "runtime" / "0.1.0"
    old.mkdir(parents=True)
    (old / "x").write_text("x")
    runtime.cleanup_legacy_cache()
    assert not (tmp_path / "local" / "NSO-Discord-RPC" / "runtime").exists()
    runtime.cleanup_legacy_cache()  # sin caché: no falla
