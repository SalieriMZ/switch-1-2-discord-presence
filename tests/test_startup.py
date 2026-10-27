import sys
import winreg

import pytest

from nso_rpc import startup

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")

KEY = r"Software\NSO-Discord-RPC-tests\Run"


@pytest.fixture
def key():
    yield KEY
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KEY)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\NSO-Discord-RPC-tests")
    except OSError:
        pass


def test_startup_set_and_clear(key):
    exe = r"C:\Users\Sebastián R\NSO-Discord-RPC.exe"
    assert startup.is_enabled(key_path=key) is False
    startup.set_enabled(True, exe, key_path=key)
    assert startup.is_enabled(key_path=key) is True
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
        value, _ = winreg.QueryValueEx(k, "NSO-Discord-RPC")
    assert value == f'"{exe}" --minimized'
    startup.set_enabled(False, exe, key_path=key)
    assert startup.is_enabled(key_path=key) is False
    startup.set_enabled(False, exe, key_path=key)  # idempotente
