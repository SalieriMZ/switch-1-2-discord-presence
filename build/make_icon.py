"""Genera build/work/icon.ico a partir del ícono dibujado en ui/theme.py."""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication

from nso_rpc.ui import theme

app = QGuiApplication(sys.argv)
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
if not theme.base_pixmap(256).save(str(out), "ICO"):
    sys.exit(f"no se pudo escribir {out}")
print(out)
