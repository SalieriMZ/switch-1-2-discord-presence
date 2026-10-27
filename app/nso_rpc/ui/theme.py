"""Tema oscuro, colores de estado e íconos generados (no hay assets binarios que mantener)."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap

from ..presence_state import State

ACCENT = "#e60012"  # rojo Nintendo
BG = "#1e1f22"
SURFACE = "#2b2d31"
SURFACE_HI = "#35373c"
TEXT = "#f2f3f5"
MUTED = "#a0a4ab"

STATE_COLORS = {
    State.CONNECTED: "#3ba55d",
    State.CONNECTING: "#faa61a",
    State.RETRYING: "#faa61a",
    State.STOPPED: "#80848e",
    State.ERROR: "#ed4245",
}

QSS = f"""
* {{ font-family: "Segoe UI"; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QDialog, QWidget#page {{ background: {BG}; }}
QTabWidget::pane {{ border: none; background: {BG}; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 16px; border: none;
               border-bottom: 2px solid transparent; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}
QFrame#card {{ background: {SURFACE}; border-radius: 10px; }}
QFrame#card[selected="true"] {{ background: {SURFACE_HI}; border: 2px solid {ACCENT}; }}
QFrame#header {{ background: {SURFACE}; border-radius: 12px; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#title {{ font-size: 16pt; font-weight: 600; }}
QLabel#h2 {{ font-size: 12pt; font-weight: 600; }}
QLabel#warn {{ color: #faa61a; }}
QLabel#error {{ color: #ed4245; }}
QPushButton {{ background: {SURFACE_HI}; border: none; border-radius: 6px; padding: 7px 14px; }}
QPushButton:hover {{ background: #404249; }}
QPushButton:disabled {{ color: #6d6f78; background: {SURFACE}; }}
QPushButton#primary {{ background: {ACCENT}; font-weight: 600; }}
QPushButton#primary:hover {{ background: #ff1a2b; }}
QPushButton#primary:disabled {{ background: #5c1a1f; color: #b5b5b5; }}
QPushButton#link {{ background: transparent; color: {MUTED}; text-decoration: underline; padding: 4px; }}
QPushButton#link:hover {{ color: {TEXT}; }}
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {{ background: #111214; border: 1px solid #3f4147;
                                       border-radius: 6px; padding: 6px; selection-background-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: #111214; border: 1px solid #3f4147; }}
QCheckBox {{ spacing: 8px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #3f4147; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""


def base_pixmap(size: int = 64) -> QPixmap:
    """Ícono base: cuadrado redondeado rojo con dos 'joy-cons'."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size / 64
    p.setBrush(QColor(ACCENT))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(2 * s, 2 * s, 60 * s, 60 * s), 14 * s, 14 * s)
    p.setBrush(QColor("white"))
    left = QPainterPath()
    left.addRoundedRect(QRectF(14 * s, 14 * s, 15 * s, 36 * s), 7 * s, 7 * s)
    p.drawPath(left)
    p.setPen(QPen(QColor("white"), 3 * s))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(35.5 * s, 15.5 * s, 13 * s, 33 * s), 6 * s, 6 * s)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(ACCENT))
    p.drawEllipse(QRectF(18.5 * s, 21 * s, 6 * s, 6 * s))
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(39 * s, 35 * s, 6 * s, 6 * s))
    p.end()
    return pm


def app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(base_pixmap(size))
    return icon


def status_icon(state: State, size: int = 64) -> QIcon:
    pm = base_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    d = size * 0.46
    rect = QRectF(size - d - 1, size - d - 1, d, d)
    p.setPen(QPen(QColor(BG), size * 0.07))
    p.setBrush(QBrush(QColor(STATE_COLORS[state])))
    p.drawEllipse(rect)
    p.end()
    return QIcon(pm)


def dot(color: str, size: int = 12) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(0, 0, size, size)
    p.end()
    return pm


def circular(pm: QPixmap, size: int) -> QPixmap:
    pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                   Qt.TransformationMode.SmoothTransformation)
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pm)
    p.end()
    return out


def initials_avatar(name: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(SURFACE_HI))
    p.drawEllipse(0, 0, size, size)
    p.setPen(QColor(TEXT))
    f = QFont("Segoe UI", int(size * 0.32), QFont.Weight.DemiBold)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, (name[:1] or "?").upper())
    p.end()
    return pm
