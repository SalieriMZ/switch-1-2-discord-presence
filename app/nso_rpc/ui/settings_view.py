"""Pestaña Configuración: arranque, opciones de presencia, actualizar nxapi y repetir la configuración inicial."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .. import startup
from ..config import MIN_UPDATE_INTERVAL, Config
from ..nxapi import NxapiClient
from .workers import run_async


class SettingsView(QWidget):
    changed = Signal()          # la config cambió (ya guardada)
    presence_changed = Signal()  # cambió algo que requiere reiniciar la presencia
    update_started = Signal()    # hay que soltar los archivos de nxapi (Windows los bloquea en uso)
    update_finished = Signal(bool)
    restart_flow = Signal()      # el usuario pidió repetir la configuración inicial
    log = Signal(str)

    def __init__(self, config: Config, client: NxapiClient | None):
        super().__init__()
        self.config = config
        self.client = client

        self.startup = QCheckBox("Arrancar con Windows (minimizada en la bandeja)")
        self.startup.setChecked(startup.is_enabled())
        self.startup.toggled.connect(self._on_startup)

        self.autostart = QCheckBox("Iniciar la presencia automáticamente al abrir la app")
        self.autostart.setChecked(config.autostart_presence)
        self.autostart.toggled.connect(lambda v: self._set("autostart_presence", v))

        self.play_time = QCheckBox("Mostrar tiempo de juego en Discord")
        self.play_time.setChecked(config.show_play_time)
        self.play_time.toggled.connect(lambda v: self._set("show_play_time", v, presence=True))

        self.inactive = QCheckBox("Mostrar aunque la consola esté inactiva (en suspensión)")
        self.inactive.setChecked(config.show_inactive)
        self.inactive.toggled.connect(lambda v: self._set("show_inactive", v, presence=True))

        self.interval = QSpinBox()
        self.interval.setRange(MIN_UPDATE_INTERVAL, 600)
        self.interval.setSuffix(" s")
        self.interval.setValue(config.update_interval)
        self.interval.editingFinished.connect(
            lambda: self._set("update_interval", self.interval.value(), presence=True))
        interval_help = QLabel("Cada cuánto se consulta a Nintendo. No bajes de 30 s (riesgo de bloqueo).")
        interval_help.setObjectName("muted")
        interval_help.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Intervalo de actualización", self.interval)

        self.update_btn = QPushButton("Actualizar nxapi")
        self.update_btn.clicked.connect(self._update_nxapi)
        self.update_status = QLabel("Úsalo si Nintendo actualizó su app y la presencia dejó de funcionar.")
        self.update_status.setObjectName("muted")
        self.update_status.setWordWrap(True)
        upd = QHBoxLayout()
        upd.addWidget(self.update_btn)
        upd.addWidget(self.update_status, 1)

        self.restart_btn = QPushButton("Repetir configuración inicial")
        self.restart_btn.clicked.connect(self._restart_flow)
        restart_help = QLabel("Vuelve a abrir el tutorial desde el principio: cuenta-bot, amistad y cuenta a mostrar.")
        restart_help.setObjectName("muted")
        restart_help.setWordWrap(True)
        rst = QHBoxLayout()
        rst.addWidget(self.restart_btn)
        rst.addWidget(restart_help, 1)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        for w in (self.startup, self.autostart, self.play_time, self.inactive):
            layout.addWidget(w)
        layout.addSpacing(6)
        layout.addLayout(form)
        layout.addWidget(interval_help)
        layout.addSpacing(12)
        layout.addLayout(upd)
        layout.addLayout(rst)
        layout.addStretch(1)

    def _set(self, field: str, value, presence: bool = False) -> None:
        if getattr(self.config, field) == value:
            return
        setattr(self.config, field, value)
        self.config.save()
        self.changed.emit()
        if presence:
            self.presence_changed.emit()

    def _on_startup(self, enabled: bool) -> None:
        try:
            startup.set_enabled(enabled)
        except OSError as e:
            self.log.emit(f"No se pudo cambiar el arranque con Windows: {e}")
            self.startup.blockSignals(True)
            self.startup.setChecked(startup.is_enabled())
            self.startup.blockSignals(False)
            return
        self._set("start_with_windows", enabled)

    def _restart_flow(self) -> None:
        answer = QMessageBox.question(
            self, "Repetir configuración inicial",
            "Se detendrá la presencia y se abrirá el tutorial desde el principio. "
            "Tu cuenta-bot y la cuenta elegida se mantienen hasta que las cambies. ¿Continuar?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._set("tutorial_done", False)
        self.restart_flow.emit()

    def _update_nxapi(self) -> None:
        if self.client is None:
            return
        self.update_btn.setEnabled(False)
        self.update_status.setText("Actualizando… (mira la pestaña Registro)")
        self.update_started.emit()
        self.log.emit("> npm install nxapi@next")
        run_async(lambda: self.client.update_nxapi(lambda l: self.log.emit(l)),
                  self._update_done, self._update_failed)

    def _update_done(self, _r) -> None:
        self.update_btn.setEnabled(True)
        self.update_status.setText("nxapi actualizado.")
        self.update_finished.emit(True)

    def _update_failed(self, e: Exception) -> None:
        self.update_btn.setEnabled(True)
        self.update_status.setText(f"Falló la actualización: {e}")
        self.update_finished.emit(False)
