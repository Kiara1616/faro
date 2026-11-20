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
    QSizePolicy,
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
    frame.setObjectName("section")
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
    ALERT_LABELS = {
        "unknown_hole": "El taladro no está incluido en el plan.",
        "hole_blocked": "El taladro está bloqueado en el plan.",
        "hole_mismatch": "La instrucción indica un taladro distinto del activo.",
        "next_hole_mismatch": "Selecciona el siguiente taladro indicado por el plan.",
        "invalid_plan_values": "Indica el producto y la cantidad completos.",
        "plan_mismatch": "El producto o la cantidad no coincide con el plan ficticio.",
        "wrong_delivery_method": "El método no coincide con el plan ficticio.",
        "fictional_zone_occupied": "La zona simulada no está marcada como despejada.",
    }

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Faro | Consola de simulación")
        self.setMinimumSize(1000, 640)
        self.resize(1280, 720)
        self._listening = False
        self._build()
        self._style()
        self.render_state({})

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 14, 24, 12)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title_group.setSpacing(3)
        title_group.addWidget(_label("FARO", "title"))
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
        for index, text in enumerate(("OPERACIÓN", "PLAN", "BITÁCORA")):
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
        voice_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        voice_layout.addWidget(_label("VOZ", "eyebrow"))
        self.voice_status = _label("Micrófono inactivo", "voice-status")
        voice_layout.addWidget(self.voice_status)
        self.voice_button = QPushButton("Activar escucha  ·  F8")
        self.voice_button.setObjectName("voiceButton")
        self.voice_button.clicked.connect(self._toggle_listening)
        voice_layout.addWidget(self.voice_button)
        voice_layout.addWidget(_label("Di «Oye Faro» antes de cada orden.", "caption"))
        sidebar.addWidget(voice_card)

        self.manual_toggle = QPushButton("Mostrar comando escrito")
        self.manual_toggle.setProperty("role", "subtle")
        self.manual_toggle.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.manual_toggle.clicked.connect(self._toggle_manual_controls)
        sidebar.addWidget(self.manual_toggle)

        command_card, command_layout = _card()
        command_layout.addWidget(_label("COMANDO ESCRITO", "eyebrow"))
        command_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Escribe una instrucción")
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
        decision_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        decision_header = QHBoxLayout()
        decision_header.addWidget(_label("ÚLTIMA RESPUESTA", "eyebrow"), 1)
        self.decision_state = _label("EN ESPERA", "decision-state")
        decision_header.addWidget(self.decision_state)
        decision_layout.addLayout(decision_header)
        self.transcript_label = _label("", "caption")
        self.transcript_label.setVisible(False)
        self.decision_label = _label("Esperando primera orden", "decision-message")
        decision_layout.addWidget(self.transcript_label)
        decision_layout.addWidget(self.decision_label)
        self.execution_status = _label("", "caption")
        self.execution_status.setVisible(False)
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
        sidebar.addStretch(1)

        self.simulation_notice = _label(
            "FARO  ·  DATOS FICTICIOS  ·  SIN CONTROL FÍSICO",
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
        self.workflow_detail = _label("Selecciona un taladro para comenzar el recorrido.", "workflow-detail")
        status_layout.addWidget(self.workflow_detail)
        self.next_command = _label("PRÓXIMA ORDEN · Oye Faro, seleccionar taladro 101", "next-command")
        status_layout.addWidget(self.next_command)
        zone_row = QHBoxLayout()
        self.zone_clear_checkbox = QCheckBox("Zona despejada")
        self.zone_clear_checkbox.toggled.connect(self.zone_clear_toggled.emit)
        zone_row.addWidget(self.zone_clear_checkbox)
        self.zone_clear_note = _label(
            "Marca de demostración; no proviene de un sensor.", "caption")
        zone_row.addWidget(self.zone_clear_note, 1)
        status_layout.addLayout(zone_row)
        layout.addWidget(self.status_card)
        progress_section, progress_layout = _card()
        progress_layout.addWidget(_label("RECORRIDO", "eyebrow"))
        progress_heading = QHBoxLayout()
        self.operation_stage = _label("Seleccionar taladro", "stage-title")
        self.operation_stage_count = _label("0 / 8", "caption")
        progress_heading.addWidget(self.operation_stage, 1)
        progress_heading.addWidget(self.operation_stage_count)
        progress_layout.addLayout(progress_heading)
        self.operation_progress = QProgressBar()
        self.operation_progress.setRange(0, 8)
        self.operation_progress.setTextVisible(False)
        progress_layout.addWidget(self.operation_progress)
        layout.addWidget(progress_section)
        layout.addStretch(1)
        return self._scroll(page)

    def _build_plan_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro, intro_layout = _card()
        intro_layout.addWidget(_label("PLAN PRECARGADO", "eyebrow"))
        self.plan_name_label = _label("Plan de demostración", "page-title")
        intro_layout.addWidget(self.plan_name_label)
        intro_layout.addWidget(
            _label("El plan muestra los taladros disponibles y el avance de la simulación.", "caption")
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
            _label("Instrucciones recibidas y decisiones del simulador.", "caption")
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
        self.manual_toggle.setText("Ocultar comando escrito" if visible
                                   else "Mostrar comando escrito")

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
            self.transcript_label.setText(f"Orden: {transcript}" if transcript else "")
            self.transcript_label.setVisible(bool(transcript))
        decision = snapshot.get("decision")
        if decision is not None:
            self.decision_label.setText(str(decision) or "Esperando una solicitud")
        command_status = snapshot.get("command_status")
        if command_status is not None:
            show_execution = str(command_status).strip().lower() not in {"", "en espera"}
            self.execution_status.setText(f"Estado de ejecución: {command_status}" if show_execution else "")
            self.execution_status.setVisible(show_execution)
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
            reason = self.ALERT_LABELS.get(str(reason), str(reason).replace("_", " "))
            blocking = " · BLOQUEANTE" if alert.get("blocking") else ""
            self.execution_status.setText(f"Estado de ejecución: requiere revisión · {reason}{blocking}")
            self.execution_status.setVisible(True)

        workflow = snapshot.get("workflow", {})
        if isinstance(workflow, Mapping):
            active = bool(workflow.get("active", False))
            default_detail = (
                "La simulación está lista para recibir una orden."
                if active else "Selecciona un taladro para comenzar el recorrido."
            )
            self.workflow_status.setText(str(workflow.get("status", "Sin taladro seleccionado")))
            self.workflow_detail.setText(str(workflow.get("detail", default_detail)))
            total = workflow.get("total", 0)
            step = workflow.get("step", 0)
            self.plan_summary.setText(f"{total} taladros del escenario · siguiente posición {step}")

        operation_state = str(snapshot.get("operation", {}).get("state", "sin_seleccion")) if isinstance(snapshot.get("operation"), Mapping) else "sin_seleccion"
        operation_data = snapshot.get("operation", {})
        if isinstance(operation_data, Mapping):
            completed_steps = {
                "sin_seleccion": 0, "seleccionado": 1, "consultado": 2,
                "confirmacion_pendiente": 4, "movimiento_en_curso": 4,
                "posicionado": 5, "carga_en_curso": 5, "cargado": 6,
                "retraccion_en_curso": 6, "retraido": 7, "cerrado": 8,
            }.get(operation_state, self.operation_progress.value())
            if operation_state == "preparado":
                completed_steps = 4 if operation_data.get("plan_validated") else 3
            stage_names = (
                "Seleccionar taladro", "Consultar plan", "Preparar carga",
                "Validar producto y kg", "Extender equipo", "Simular carga",
                "Retraer equipo", "Cerrar taladro", "Taladro completo",
            )
            self.operation_progress.setValue(completed_steps)
            self.operation_stage.setText(stage_names[completed_steps])
            self.operation_stage_count.setText(f"{completed_steps} / 8")
            hole_id = operation_data.get("hole_id") or "101"
            method = str(operation_data.get("delivery_method") or "brazo")
            next_orders = {
                "sin_seleccion": f"Oye Faro, seleccionar taladro {hole_id}",
                "seleccionado": "Oye Faro, consultar plan",
                "consultado": "Oye Faro, preparar carga",
                "preparado": (
                    f"Marca «Zona despejada» y di: Oye Faro, extender {method}"
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
            QWidget { background: #f7f8fc; color: #0f172a; font-family: 'Inter'; font-size: 14px; }
            QLabel[role='title'] { color: #0f172a; font-size: 29px; font-weight: 800; letter-spacing: 1px; }
            QLabel[role='subtitle'] { color: #64748b; font-size: 14px; }
            QFrame#section { background: transparent; border: 0; border-bottom: 1px solid #cbd5e1; border-radius: 0; }
            QFrame#section QLabel { background: transparent; }
            QPushButton[role='nav'] { background: transparent; color: #64748b; border: 0; border-bottom: 2px solid transparent; border-radius: 0; padding: 10px 12px; min-height: 48px; font-size: 14px; font-weight: 700; }
            QPushButton[role='nav']:checked { background: transparent; color: #2563eb; border-bottom: 2px solid #2563eb; }
            QLabel[role='eyebrow'] { color: #2563eb; font-size: 12px; font-weight: 800; letter-spacing: 1px; }
            QLabel[role='page-title'] { color: #0f172a; font-size: 24px; font-weight: 700; }
            QLabel[role='hero'] { font-size: 34px; font-weight: 800; color: #0f172a; }
            QLabel[role='workflow-detail'] { color: #64748b; font-size: 16px; }
            QLabel[role='voice-status'] { color: #0f172a; font-size: 22px; font-weight: 700; }
            QLabel[role='decision-message'] { color: #0f172a; font-size: 19px; font-weight: 700; }
            QLabel[role='stage-title'] { color: #0f172a; font-size: 18px; font-weight: 700; }
            QFrame#section QLabel[role='next-command'] { color: #1d4ed8; background: transparent; border: 0; border-left: 3px solid #2563eb; border-radius: 0; padding: 9px 12px; font-size: 17px; font-weight: 700; }
            QFrame#holeTile { background: transparent; border: 0; border-top: 2px solid #cbd5e1; border-radius: 0; }
            QFrame#holeTile[holeStatus='activo'] { background: transparent; border-top: 2px solid #2563eb; }
            QFrame#holeTile[holeStatus='completado'] { background: transparent; border-top: 2px solid #64748b; }
            QFrame#holeTile[holeStatus='bloqueado'] { background: transparent; border-top: 2px solid #d66b60; }
            QFrame#holeTile QLabel { background: transparent; }
            QLabel[role='tile-id'] { color: #0f172a; font-size: 29px; font-weight: 800; }
            QLabel[role='tile-status'] { color: #2563eb; font-size: 12px; font-weight: 800; }
            QLabel[role='tile-detail'] { color: #64748b; font-size: 13px; }
            QProgressBar { background: #e4e9f0; border: 0; border-radius: 8px; height: 21px;
                           text-align: center; color: #0f172a; font-size: 12px; font-weight: 700; }
            QProgressBar::chunk { background: #2563eb; border-radius: 8px; }
            QLabel[role='caption'] { color: #64748b; font-size: 14px; }
            QLabel[role='footer'] { color: #8290a3; font-size: 12px; font-weight: 700; }
            QLabel[role='decision-state'] { color: #64748b; background: transparent; border: 0; padding: 7px 0; font-size: 12px; font-weight: 800; }
            QLabel[role='decision-state'][outcome='accepted'] { color: #1f6b50; background: #e1f2e9; }
            QLabel[role='decision-state'][outcome='rejected'] { color: #a54131; background: #fae8e4; }
            QPushButton { background: #2563eb; color: #ffffff; border: 1px solid #2563eb; border-radius: 10px;
                          padding: 12px 15px; min-height: 48px; font-weight: 700; }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:disabled { background: #94a3b8; border-color: #94a3b8; }
            QPushButton#voiceButton { font-size: 18px; padding: 15px; }
            QPushButton[role='subtle'] { background: transparent; color: #2563eb; border: 0; border-radius: 0; text-align: left; min-height: 36px; font-size: 14px; padding: 6px 14px; }
            QPushButton[role='subtle']:hover { background: #eaf1ff; }
            QPushButton#voiceButton[listening='true'] { background: #b42318; border-color: #b42318; }
            QPushButton#voiceButton[listening='true']:hover { background: #912018; border-color: #912018; }
            QLineEdit { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 9px; padding: 11px;
                        min-height: 44px; selection-background-color: #2563eb; }
            QLineEdit:focus { border-color: #2563eb; }
            QCheckBox { background: transparent; spacing: 10px; font-size: 15px; font-weight: 700; }
            QCheckBox::indicator { width: 22px; height: 22px; }
            QListWidget { background: transparent; color: #0f172a; border: 0; outline: 0; }
            QListWidget::item { padding: 10px 7px; border-bottom: 1px solid #e4e9f0; }
            QListWidget::item:selected { background: #eaf1ff; color: #0f172a; }
            QScrollArea { background: transparent; border: none; }
            QWidget#confirmControls { background: transparent; }
            """
        )
