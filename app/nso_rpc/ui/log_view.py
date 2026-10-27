"""Pestaña Registro: salida de nxapi y de la app, para soporte."""

from datetime import datetime

from PySide6.QtCore import Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr

MAX_LINES = 2000


class LogView(QWidget):
    def __init__(self):
        super().__init__()
        self.text = QPlainTextEdit(readOnly=True)
        self.text.setMaximumBlockCount(MAX_LINES)
        self.text.setStyleSheet("font-family: Consolas, monospace; font-size: 9pt;")

        copy = QPushButton(tr("Copiar registro"))
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.text.toPlainText()))
        clear = QPushButton(tr("Limpiar"))
        clear.clicked.connect(self.text.clear)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(clear)
        buttons.addWidget(copy)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text, 1)
        layout.addLayout(buttons)

    @Slot(str)
    def append(self, line: str) -> None:
        self.text.appendPlainText(f"[{datetime.now():%H:%M:%S}] {line}")
