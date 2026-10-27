"""Arranque con Windows vía HKCU\\...\\Run."""

import sys
import winreg

from . import APP_NAME

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launch_command() -> str:
    """Comando a registrar: el .exe congelado, o pythonw -m nso_rpc en desarrollo."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pythonw}" -m nso_rpc --minimized'


def set_enabled(enabled: bool, exe: str | None = None, key_path: str = RUN_KEY) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        if enabled:
            command = f'"{exe}" --minimized' if exe else launch_command()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def is_enabled(key_path: str = RUN_KEY) -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
