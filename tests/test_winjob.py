import subprocess
import sys
import textwrap
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="solo Windows")


def _alive(pid: int) -> bool:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in out


def test_children_die_with_parent(tmp_path):
    """El padre adopta a un hijo; al matar al padre (sin limpieza) el hijo adoptado muere y el otro no."""
    pidfile = tmp_path / "child.pid"
    parent = textwrap.dedent(f"""
        import subprocess, sys, time
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parents[1] / 'app')!r})
        from nso_rpc import winjob
        sleeper = [sys.executable, "-c", "import time; time.sleep(60)"]
        child = subprocess.Popen(sleeper)
        free = subprocess.Popen(sleeper)  # p. ej. el navegador del login: no debe morir
        assert winjob.adopt(child.pid)
        open({str(pidfile)!r}, "w").write(f"{{child.pid}} {{free.pid}}")
        time.sleep(60)
    """)
    proc = subprocess.Popen([sys.executable, "-c", parent])
    deadline = time.monotonic() + 15
    while not pidfile.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    child_pid, free_pid = map(int, pidfile.read_text().split())
    assert _alive(child_pid)

    proc.kill()  # TerminateProcess: no corre ningún finally/atexit
    proc.wait()
    deadline = time.monotonic() + 5
    while _alive(child_pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    try:
        assert not _alive(child_pid)
        assert _alive(free_pid)
    finally:
        subprocess.run(["taskkill", "/F", "/PID", str(free_pid)], capture_output=True)
