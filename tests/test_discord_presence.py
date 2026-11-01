"""Regresión con el cliente real de nxapi contra un Discord falso (requiere build/fetch-runtime.ps1)."""

import subprocess
from pathlib import Path

import pytest

from nso_rpc.runtime import DEV_RUNTIME, Runtime

FAKE_DISCORD = Path(__file__).parent / "fake_discord.mjs"
RT = Runtime(DEV_RUNTIME)

pytestmark = pytest.mark.skipif(not RT.is_valid(), reason="falta build/runtime")


@pytest.mark.parametrize("scenario", ["absent", "closing", "restart-closing"])
def test_activity_reaches_discord_once_it_is_ready(scenario):
    proc = subprocess.run(
        [str(RT.node), "--import", RT.discord_fix.as_uri(), str(FAKE_DISCORD), scenario,
         str(RT.root / "node_modules" / "nxapi" / "dist")],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
