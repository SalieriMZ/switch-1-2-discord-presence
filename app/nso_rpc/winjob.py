"""Job Object de Windows para que `node` (la presencia) muera con la app.

Sin esto, si la app se cae o la matan, el proceso de nxapi queda huérfano publicando en Discord
y al volver a abrirla habría dos. Solo se adoptan esos procesos, no la app entera: lo que la app
abre con el shell (el navegador del login) no debe cerrarse con ella.
"""

import ctypes
import sys
from ctypes import wintypes

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9

_job = None  # el handle debe vivir mientras viva el proceso


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _BASIC_LIMIT(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _EXTENDED_LIMIT(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BASIC_LIMIT),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


PROCESS_SET_QUOTA = 0x0100
PROCESS_TERMINATE = 0x0001


def _kernel32():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateJobObjectW.restype = wintypes.HANDLE
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    return k32


def _get_job(k32):
    global _job
    if _job is None:
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _EXTENDED_LIMIT()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                           ctypes.byref(info), ctypes.sizeof(info)):
            k32.CloseHandle(job)
            return None
        _job = job
    return _job


def adopt(pid: int) -> bool:
    """El proceso `pid` morirá cuando termine este proceso (de cualquier forma). False si no se pudo."""
    if sys.platform != "win32" or not pid:
        return False
    k32 = _kernel32()
    job = _get_job(k32)
    if not job:
        return False
    handle = k32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)
    if not handle:
        return False
    try:
        return bool(k32.AssignProcessToJobObject(job, handle))
    finally:
        k32.CloseHandle(handle)
