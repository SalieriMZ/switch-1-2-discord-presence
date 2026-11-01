"""Instancia única con un mutex de Windows con nombre.

Revisar si otra instancia escucha en el socket deja una ventana: dos aperturas a la vez pasan las dos y
cada una publica su propia presencia. Crear el mutex es atómico, y Windows lo libera aunque la app se caiga.
"""

import ctypes
from ctypes import wintypes

from . import APP_NAME

ERROR_ALREADY_EXISTS = 183
DEFAULT_NAME = f"Local\\{APP_NAME}"

_held = []  # el handle debe vivir mientras viva el proceso


def acquire(name: str = DEFAULT_NAME) -> bool:
    """True si esta es la única instancia. Si Windows no deja crear el mutex, no se impide abrir la app."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateMutexW.restype = wintypes.HANDLE
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k32.CreateMutexW(None, False, name)
    if not handle:
        return True
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        k32.CloseHandle(handle)
        return False
    _held.append(handle)
    return True
