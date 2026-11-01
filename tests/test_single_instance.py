"""Instancia única: el mutex lo tiene un solo proceso y se libera al terminar."""

import os
import subprocess
import sys
from pathlib import Path

from nso_rpc.single_instance import acquire

APP = str(Path(__file__).resolve().parents[1] / "app")


def _acquire_elsewhere(name: str) -> bool:
    code = f"from nso_rpc.single_instance import acquire; raise SystemExit(0 if acquire({name!r}) else 1)"
    proc = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONPATH": APP})
    assert proc.returncode in (0, 1)
    return proc.returncode == 0


def test_second_process_is_refused_while_first_holds_it():
    name = f"Local\\nso-rpc-test-{os.getpid()}-a"
    assert acquire(name)
    assert not _acquire_elsewhere(name)


def test_released_when_the_process_ends():
    name = f"Local\\nso-rpc-test-{os.getpid()}-b"
    assert _acquire_elsewhere(name)
    assert _acquire_elsewhere(name)
