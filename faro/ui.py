"""Desktop presentation console for the Faro *simulator*.

This module deliberately knows nothing about industrial devices. It renders a
snapshot from the demo engine and emits operator intent for the controller to
validate. No widget can directly change the simulated operational state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from faro.demo_scene import DemoScene


def _label(text: str, role: str = "") -> QLabel:
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(True)
    return widget


def _card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 13, 16, 13)
    layout.setSpacing(6)
    return frame, layout


class FaroWindow(QWidget):
    """Read-only simulator HMI with intent signals for an external controller.

    ``command_submitted`` is emitted for typed commands. ``listening_toggled``
    requests microphone activation; the controller must call ``render_state``
    with the actual listening state after its voice service responds.
    """

    command_submitted = Signal(str)
    listening_toggled = Signal(bool)
    recovery_requested = Signal()
    zone_clear_toggled = Signal(bool)

    VIEW_INDEX = {"operacion": 0, "malla": 1, "registro": 2}

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SafeFlow AI · Faro | Simulación de carguío")
        self.setMinimumSize(1000, 640)
        self.resize(1280, 720)
        self._listening = False
        self._build()
        self._style()
        self.render_state({})

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 15, 20, 12)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title_group.setSpacing(3)
        title_group.addWidget(_label("SAFEFLOW AI  /  FARO", "title"))
        title_group.addWidget(
            _label("Asistente de voz para el flujo de carguío por taladro", "subtitle")
        )
        header.addLayout(title_group, 1)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)

        main_column = QVBoxLayout()
        main_column.setSpacing(10)
        body.addLayout(main_column, 7)

        nav = QHBoxLayout()
        nav.setSpacing(4)
        self.nav_buttons = []
        for index, text in enumerate(("OPERACIÓN", "PLAN DE DEMO", "BITÁCORA")):
            item = QPushButton(text)
            item.setProperty("role", "nav")
            item.setCheckable(True)
            item.clicked.connect(lambda _checked=False, page=index: self._set_view(page))
            self.nav_buttons.append(item)
            nav.addWidget(item)
        main_column.addLayout(nav)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_operation_page())
        self.pages.addWidget(self._build_plan_page())
        self.pages.addWidget(self._build_history_page())
        main_column.addWidget(self.pages, 1)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)
        body.addLayout(sidebar, 4)

        voice_card, voice_layout = _card()
        voice_layout.addWidget(_label("CONTROL POR VOZ · LOCAL", "eyebrow"))
        self.voice_status = _label("Micrófono inactivo", "voice-status")
        voice_layout.addWidget(self.voice_status)
        self.voice_button = QPushButton("Activar escucha  ·  F8")
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.clicked.connect(self._toggle_listening)
        voice_layout.addWidget(self.voice_button)
        voice_layout.addWidget(_label("Con la escucha activa, di «Oye Faro» antes de la orden. Faro descarta transcripciones sin esa frase.", "caption"))
        sidebar.addWidget(voice_card)

        self.manual_toggle = QPushButton("Mostrar entrada manual de prueba")
        self.manual_toggle.setProperty("role", "subtle")
        self.manual_toggle.clicked.connect(self._toggle_manual_controls)
        sidebar.addWidget(self.manual_toggle)

        command_card, command_layout = _card()
        command_layout.addWidget(_label("CONTROL MANUAL PARA LA DEMO", "eyebrow"))
        command_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Escribe un comando de prueba")
        self.command_input.returnPressed.connect(self._submit_command)
        command_row.addWidget(self.command_input, 1)
        send_button = QPushButton("Enviar")
        send_button.clicked.connect(self._submit_command)
        command_row.addWidget(send_button)
        command_layout.addLayout(command_row)
        self.manual_card = command_card
        self.manual_card.setVisible(False)
        sidebar.addWidget(command_card)

        decision_card, decision_layout = _card()
        decision_header = QHBoxLayout()
        decision_header.addWidget(_label("RESPUESTA DEL SISTEMA", "eyebrow"), 1)
        self.decision_state = _label("EN ESPERA", "decision-state")
        decision_header.addWidget(self.decision_state)
        decision_layout.addLayout(decision_header)
        self.transcript_label = _label("Sin comando recibido", "caption")
        self.decision_label = _label("Esperando una solicitud", "decision-message")
        decision_layout.addWidget(self.transcript_label)
        decision_layout.addWidget(self.decision_label)
        self.execution_status = _label("Estado de ejecución: en espera", "caption")
        decision_layout.addWidget(self.execution_status)
        self.confirmation_controls = QWidget()
        self.confirmation_controls.setObjectName("confirmControls")
        confirmation_row = QHBoxLayout(self.confirmation_controls)
        confirmation_row.setContentsMargins(0, 0, 0, 0)
        confirm_button = QPushButton("Confirmar")
        confirm_button.clicked.connect(lambda: self.command_submitted.emit("confirmar"))
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(lambda: self.command_submitted.emit("cancelar"))
        confirmation_row.addWidget(confirm_button)
        confirmation_row.addWidget(cancel_button)
        self.confirmation_controls.setVisible(False)
        decision_layout.addWidget(self.confirmation_controls)
        self.recovery_button = QPushButton("Registrar revisión manual")
        self.recovery_button.setEnabled(False)
        self.recovery_button.setVisible(False)
        self.recovery_button.clicked.connect(self.recovery_requested.emit)
        decision_layout.addWidget(self.recovery_button)
        sidebar.addWidget(decision_card)

        self.simulation_notice = _label(
            "SAFEFLOW AI / FARO  ·  PLAN Y EQUIPO SIMULADOS  ·  SIN CONTROL DE MAQUINARIA",
            "footer",
        )
        root.addWidget(self.simulation_notice)
        self._voice_shortcut = QShortcut(QKeySequence("F8"), self)
        self._voice_shortcut.activated.connect(self._toggle_listening)
        self._set_view(0)

    def _build_operation_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        self.operation_scene = DemoScene(height=280)
        layout.addWidget(self.operation_scene)
        self.status_card, status_layout = _card()
        status_layout.addWidget(_label("ESTADO DE LA TAREA", "eyebrow"))
        self.workflow_status = _label("Sin taladro seleccionado", "hero")
        status_layout.addWidget(self.workflow_status)
        self.workflow_detail = _label("Seleccione un taladro de la malla ficticia para comenzar.", "workflow-detail")
        status_layout.addWidget(self.workflow_detail)
        self.next_command = _label("PRÓXIMA ORDEN · Oye Faro, seleccionar taladro 101", "next-command")
        status_layout.addWidget(self.next_command)
        zone_row = QHBoxLayout()
        self.zone_clear_checkbox = QCheckBox("Zona despejada · simulación")
        self.zone_clear_checkbox.toggled.connect(self.zone_clear_toggled.emit)
        zone_row.addWidget(self.zone_clear_checkbox)
        self.zone_clear_note = _label(
            "Condición ficticia, sin sensor conectado.", "caption")
        zone_row.addWidget(self.zone_clear_note, 1)
        status_layout.addLayout(zone_row)
        layout.addWidget(self.status_card)
        layout.addStretch(1)
        return self._scroll(page)

    def _build_plan_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro, intro_layout = _card()
        intro_layout.addWidget(_label("02 / PLAN PRECARGADO", "eyebrow"))
        self.plan_name_label = _label("Plan de demostración", "page-title")
        intro_layout.addWidget(self.plan_name_label)
        intro_layout.addWidget(
            _label("Cada ficha representa un taladro de ejemplo. El orden es ilustrativo; no indica posiciones reales.", "caption")
        )
        layout.addWidget(intro)
        self.plan_scene = DemoScene(height=310)
        layout.addWidget(self.plan_scene)
        overview, overview_layout = _card()
        overview_layout.addWidget(_label("AVANCE DEL PLAN", "eyebrow"))
        self.plan_progress = QProgressBar()
        self.plan_progress.setTextVisible(True)
        overview_layout.addWidget(self.plan_progress)
        self.plan_tiles = QHBoxLayout()
        self.plan_tiles.setSpacing(8)
        overview_layout.addLayout(self.plan_tiles)
        layout.addWidget(overview)
        self.plan_summary = _label("Taladros ficticios", "caption")
        layout.addWidget(self.plan_summary)
        layout.addStretch(1)
        return self._scroll(page)

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro, intro_layout = _card()
        intro_layout.addWidget(_label("ÓRDENES DE ESTA SESIÓN", "eyebrow"))
        intro_layout.addWidget(_label("Historial de decisiones", "page-title"))
        intro_layout.addWidget(
            _label("Se muestran las transcripciones, aceptaciones y rechazos de la interfaz.", "caption")
        )
        layout.addWidget(intro)
        history_card, history_layout = _card()
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(False)
        history_layout.addWidget(self.history_list, 1)
        layout.addWidget(history_card, 1)
        layout.addStretch(1)
        return page

    def _set_view(self, index: int) -> None:
        if not 0 <= index < self.pages.count():
            return
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    @staticmethod
    def _scroll(page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    def _toggle_listening(self) -> None:
        self.listening_toggled.emit(not self._listening)

    def _toggle_manual_controls(self) -> None:
        visible = self.manual_card.isHidden()
        self.manual_card.setVisible(visible)
        self.manual_toggle.setText("Ocultar entrada manual de prueba" if visible
                                   else "Mostrar entrada manual de prueba")

    def _submit_command(self) -> None:
        command = self.command_input.text().strip()
        if command:
            self.command_submitted.emit(command)
            self.command_input.clear()

    def set_voice_status(self, message: str) -> None:
        """Display a service message without changing the engine state."""
        self.voice_status.setText(message or "Micrófono inactivo")

    def render_state(self, snapshot: Mapping[str, Any]) -> None:
        """Render a snapshot from the active per-hole simulator."""
        view = str(snapshot.get("view", "")).lower()
        if view in self.VIEW_INDEX:
            self._set_view(self.VIEW_INDEX[view])

        self._listening = bool(snapshot.get("listening", self._listening))
        self.voice_button.setText("Detener escucha  ·  F8" if self._listening else "Activar escucha  ·  F8")
        self.voice_button.setProperty("listening", self._listening)
        self.voice_button.style().unpolish(self.voice_button)
        self.voice_button.style().polish(self.voice_button)
        if "voice_status" in snapshot:
            self.set_voice_status(str(snapshot["voice_status"]))
        else:
            self.set_voice_status("Escuchando comandos…" if self._listening else "Micrófono inactivo")

        transcript = snapshot.get("transcript")
        if transcript is not None:
            self.transcript_label.setText(f"Reconocido: {transcript}" if transcript else "Sin comando recibido")
        decision = snapshot.get("decision")
        if decision is not None:
            self.decision_label.setText(str(decision) or "Esperando una solicitud")
        command_status = snapshot.get("command_status")
        if command_status is not None:
            self.execution_status.setText(f"Estado de ejecución: {command_status}")
            normalized_status = str(command_status).lower()
            operation = snapshot.get("operation")
            if isinstance(operation, Mapping) and "state" in operation:
                can_recover = operation["state"] == "resultado_desconocido"
            else:
                can_recover = ("requiere revisión" in normalized_status
                               or "timeout" in normalized_status
                               or "resultado desconocido" in normalized_status)
            self.recovery_button.setEnabled(can_recover)
            self.recovery_button.setVisible(can_recover)
        alert = snapshot.get("alert")
        if isinstance(alert, Mapping):
            reason = alert.get("reason", "revisión requerida")
            blocking = " · BLOQUEANTE" if alert.get("blocking") else ""
            self.execution_status.setText(f"Estado de ejecución: requiere revisión · {reason}{blocking}")

        workflow = snapshot.get("workflow", {})
        if isinstance(workflow, Mapping):
            active = bool(workflow.get("active", False))
            default_detail = (
                "La simulación está lista para recibir una orden."
                if active else "Seleccione un taladro de la malla ficticia para comenzar."
            )
            self.workflow_status.setText(str(workflow.get("status", "Sin taladro seleccionado")))
            self.workflow_detail.setText(str(workflow.get("detail", default_detail)))
            total = workflow.get("total", 0)
            step = workflow.get("step", 0)
            self.plan_summary.setText(f"{total} taladros del escenario · siguiente posición {step}")

        operation_state = str(snapshot.get("operation", {}).get("state", "sin_seleccion")) if isinstance(snapshot.get("operation"), Mapping) else "sin_seleccion"
        operation_data = snapshot.get("operation", {})
        if isinstance(operation_data, Mapping):
            hole_id = operation_data.get("hole_id") or "101"
            method = str(operation_data.get("delivery_method") or "brazo")
            next_orders = {
                "sin_seleccion": f"Oye Faro, seleccionar taladro {hole_id}",
                "seleccionado": "Oye Faro, consultar plan",
                "consultado": "Oye Faro, preparar carga",
                "preparado": (
                    f"Marca «Zona despejada · simulación» y di: Oye Faro, extender {method}"
                    if operation_data.get("plan_validated") else
                    f"Oye Faro, validar {operation_data.get('product') or 'producto alfa'}, {operation_data.get('planned_kg') or '100'} kilos"
                ),
                "confirmacion_pendiente": "Confirma o cancela la orden pendiente",
                "posicionado": "Oye Faro, iniciar carga",
                "cargado": f"Oye Faro, retraer {method}",
                "retraido": "Oye Faro, cerrar taladro",
            }
            instruction = next_orders.get(operation_state, "Espera el resultado del equipo simulado")
            self.next_command.setText(f"PRÓXIMO PASO  ·  {instruction}")

        confirmation = snapshot.get("confirmation")
        self.confirmation_controls.setVisible(isinstance(confirmation, Mapping))
        if isinstance(confirmation, Mapping):
            action = str(confirmation.get("action", "")).replace("_", " ")
            summary = f"Confirmación pendiente: {action} · taladro {confirmation.get('hole_id', '—')}"
            if confirmation.get("product"):
                summary += f" · {confirmation['product']}"
            self.workflow_status.setText("CONFIRMACIÓN REQUERIDA")
            self.workflow_detail.setText(summary)

        zone_clear = bool(snapshot.get("zone_clear", False))
        if self.zone_clear_checkbox.isChecked() != zone_clear:
            self.zone_clear_checkbox.blockSignals(True)
            self.zone_clear_checkbox.setChecked(zone_clear)
            self.zone_clear_checkbox.blockSignals(False)
        self.zone_clear_checkbox.setEnabled(bool(snapshot.get("zone_clear_enabled", True)))
        if "zone_clear_note" in snapshot:
            self.zone_clear_note.setText(str(snapshot["zone_clear_note"]))

        plan = snapshot.get("plan", [])
        if isinstance(plan, (list, tuple)):
            if isinstance(operation_data, Mapping):
                self.operation_scene.set_snapshot(plan, operation_data)
                self.plan_scene.set_snapshot(plan, operation_data)
            self.plan_name_label.setText(str(snapshot.get("plan_name") or "Plan de demostración"))
            available = sum(1 for item in plan if isinstance(item, Mapping)
                            and item.get("status") != "bloqueado")
            self.plan_progress.setMaximum(max(available, 1))
            self.plan_progress.setValue(sum(1 for item in plan if isinstance(item, Mapping)
                                            and item.get("status") == "completado"))
            self.plan_progress.setFormat("%v / %m taladros disponibles completados")
            while self.plan_tiles.count():
                child = self.plan_tiles.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            for item in plan:
                if not isinstance(item, Mapping):
                    continue
                status = str(item.get("status", "pendiente")).replace("_", " ").upper()
                tile = QFrame()
                tile.setObjectName("holeTile")
                tile.setProperty("holeStatus", str(item.get("status", "pendiente")))
                tile_layout = QVBoxLayout(tile)
                tile_layout.setContentsMargins(12, 10, 12, 10)
                tile_layout.addWidget(_label("TALADRO", "eyebrow"))
                tile_layout.addWidget(_label(str(item.get("id", "—")), "tile-id"))
                tile_layout.addWidget(_label(status, "tile-status"))
                tile_layout.addWidget(_label(
                    f"{item.get('product', '—')} · {item.get('planned_kg', '—')} kg", "tile-detail"))
                tile_layout.addWidget(_label(
                    f"Entrega por {item.get('delivery_method', '—')}", "tile-detail"))
                self.plan_tiles.addWidget(tile, 1)

        history = snapshot.get("history")
        if isinstance(history, (list, tuple)):
            self.history_list.clear()
            for event in reversed(history[-30:]):
                self.history_list.addItem(QListWidgetItem(self._format_event(event)))
            if history and isinstance(history[-1], Mapping):
                accepted = bool(history[-1].get("accepted"))
                self.decision_state.setText("ACEPTADO" if accepted else "RECHAZADO")
                self.decision_state.setProperty("outcome", "accepted" if accepted else "rejected")
            else:
                self.decision_state.setText("EN ESPERA")
                self.decision_state.setProperty("outcome", "waiting")
            self.decision_state.style().unpolish(self.decision_state)
            self.decision_state.style().polish(self.decision_state)

    @staticmethod
    def _format_event(event: Mapping[str, Any] | str) -> str:
        if not isinstance(event, Mapping):
            return str(event)
        time = event.get("time", event.get("timestamp", ""))
        command = event.get("command", event.get("transcript", event.get("text", "")))
        decision = event.get("decision", event.get("result", ""))
        parts = [str(x) for x in (time, command, decision) if x]
        return "  ·  ".join(parts) or str(dict(event))

    def _style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background: #171b20; color: #f1f0eb; font-family: 'Segoe UI'; font-size: 13px; }
            QLabel[role='title'] { color: #faf8f2; font-size: 25px; font-weight: 800; letter-spacing: 1px; }
            QLabel[role='subtitle'] { color: #b8b4ab; font-size: 12px; }
            QFrame#card { background: #242a30; border: 1px solid #414951; border-radius: 9px; }
            QFrame#card QLabel { background: transparent; }
            QPushButton[role='nav'] { background: #292f35; color: #c2beb4; border: 1px solid #414951;
                                      border-radius: 5px; padding: 11px 4px; font-size: 11px; font-weight: 700; }
            QPushButton[role='nav']:checked { background: #39352e; color: #f5c36a;
                                               border-bottom: 3px solid #e5a33f; }
            QLabel[role='eyebrow'] { color: #d8ae69; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel[role='page-title'] { color: #f4f1e9; font-size: 22px; font-weight: 700; }
            QLabel[role='hero'] { font-size: 34px; font-weight: 800; color: #ffffff; }
            QLabel[role='workflow-detail'] { color: #ccc8be; font-size: 16px; }
            QLabel[role='voice-status'] { color: #f4f1e9; font-size: 23px; font-weight: 700; }
            QLabel[role='decision-message'] { color: #f4f1e9; font-size: 20px; font-weight: 700; }
            QFrame#card QLabel[role='next-command'] { color: #ffd48b; background: #3c301e;
                           border: 1px solid #976d36; border-radius: 5px; padding: 13px; font-size: 18px; font-weight: 700; }
            QFrame#holeTile { background: #2d343a; border: 1px solid #50575d; border-radius: 7px; }
            QFrame#holeTile[holeStatus='activo'] { background: #433a2b; border: 2px solid #e5a33f; }
            QFrame#holeTile[holeStatus='completado'] { background: #304039; border-color: #80b492; }
            QFrame#holeTile[holeStatus='bloqueado'] { background: #49323a; border-color: #c76f6b; }
            QFrame#holeTile QLabel { background: transparent; }
            QLabel[role='tile-id'] { color: #ffffff; font-size: 29px; font-weight: 800; }
            QLabel[role='tile-status'] { color: #e5b663; font-size: 10px; font-weight: 700; }
            QLabel[role='tile-detail'] { color: #c8c4bb; font-size: 11px; }
            QProgressBar { background: #343a3f; border: 0; border-radius: 5px; height: 18px;
                           text-align: center; color: #f4f1e9; font-size: 10px; font-weight: 700; }
            QProgressBar::chunk { background: #bd832d; border-radius: 5px; }
            QLabel[role='caption'] { color: #bcb7ad; font-size: 12px; }
            QLabel[role='footer'] { color: #9d988e; font-size: 10px; font-weight: 600; }
            QLabel[role='decision-state'] { color: #d3cfc6; background: #3c4145; padding: 5px 7px;
                                            font-size: 10px; font-weight: 700; }
            QLabel[role='decision-state'][outcome='accepted'] { color: #9df0c9; background: #235443; }
            QLabel[role='decision-state'][outcome='rejected'] { color: #ffb4a3; background: #603a38; }
            QPushButton { background: #ad7425; color: #171b20; border: 1px solid #d69a45; border-radius: 5px;
                          padding: 9px 11px; font-weight: 700; }
            QPushButton:hover { background: #d69538; }
            QPushButton#voiceButton { font-size: 19px; padding: 16px; }
            QPushButton[role='subtle'] { background: #30363b; color: #d2cdc2; border-color: #515a61;
                                         font-size: 11px; padding: 8px; }
            QPushButton[listening='true'] { background: #944c43; border-color: #b8665b; }
            QLineEdit { background: #1c2227; color: #f4f1e9; border: 1px solid #596068; border-radius: 4px; padding: 9px;
                        selection-background-color: #986a31; }
            QLineEdit:focus { border-color: #e5a33f; }
            QCheckBox { background: transparent; spacing: 9px; font-size: 15px; font-weight: 700; }
            QListWidget { background: #1c2227; color: #f1f0eb; border: 1px solid #50575d; outline: 0; }
            QListWidget::item { padding: 7px 5px; border-bottom: 1px solid #414951; }
            QListWidget::item:selected { background: #70532c; color: #ffffff; }
            QScrollArea { background: transparent; border: none; }
            QWidget#confirmControls { background: transparent; }
            """
        )
