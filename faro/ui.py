"""Desktop presentation console for the Faro *simulator*.

This module deliberately knows nothing about industrial devices. It renders a
snapshot from the demo engine and emits operator intent for the controller to
validate. No widget can directly change the simulated operational state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import Qt, Signal
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
        self.connection_badge = _label("SIMULACIÓN - SIN CONEXIÓN A EQUIPO", "badge")
        self.connection_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.connection_badge)
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

        hint_card, hint_layout = _card()
        hint_layout.addWidget(_label("RECORRIDO SUGERIDO · DI «OYE FARO» ANTES DE CADA ORDEN", "eyebrow"))
        hint_layout.addWidget(
            _label(
                "1 Seleccionar taladro 101   →   2 Consultar plan   →   3 Preparar carga   →   "
                "4 Validar producto alfa, cien kilos   →   5 Extender brazo"
            )
        )
        main_column.addWidget(hint_card)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)
        body.addLayout(sidebar, 4)

        voice_card, voice_layout = _card()
        voice_layout.addWidget(_label("CONTROL POR VOZ · LOCAL", "eyebrow"))
        self.voice_status = _label("Micrófono inactivo", "value")
        voice_layout.addWidget(self.voice_status)
        self.voice_button = QPushButton("Activar escucha  ·  F8")
        self.voice_button.clicked.connect(self._toggle_listening)
        voice_layout.addWidget(self.voice_button)
        voice_layout.addWidget(_label("Con la escucha activa, di «Oye Faro» antes de la orden. Faro descarta transcripciones sin esa frase.", "caption"))
        sidebar.addWidget(voice_card)

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
        confirmation_row = QHBoxLayout()
        confirm_button = QPushButton("Confirmar orden")
        confirm_button.clicked.connect(lambda: self.command_submitted.emit("confirmar"))
        cancel_button = QPushButton("Cancelar orden")
        cancel_button.clicked.connect(lambda: self.command_submitted.emit("cancelar"))
        confirmation_row.addWidget(confirm_button)
        confirmation_row.addWidget(cancel_button)
        command_layout.addLayout(confirmation_row)
        sidebar.addWidget(command_card)

        decision_card, decision_layout = _card()
        decision_header = QHBoxLayout()
        decision_header.addWidget(_label("ÚLTIMA DECISIÓN", "eyebrow"), 1)
        self.decision_state = _label("EN ESPERA", "decision-state")
        decision_header.addWidget(self.decision_state)
        decision_layout.addLayout(decision_header)
        self.transcript_label = _label("Sin comando recibido", "caption")
        self.decision_label = _label("Esperando una solicitud", "value")
        decision_layout.addWidget(self.transcript_label)
        decision_layout.addWidget(self.decision_label)
        self.execution_status = _label("Estado de ejecución: en espera", "caption")
        decision_layout.addWidget(self.execution_status)
        self.recovery_button = QPushButton("Registrar revisión manual")
        self.recovery_button.setEnabled(False)
        self.recovery_button.clicked.connect(self.recovery_requested.emit)
        decision_layout.addWidget(self.recovery_button)
        sidebar.addWidget(decision_card)

        root.addWidget(
            _label(
                "SAFEFLOW AI / FARO  ·  PLAN Y EQUIPO SIMULADOS  ·  SIN CONTROL DE MAQUINARIA",
                "footer",
            )
        )
        self._voice_shortcut = QShortcut(QKeySequence("F8"), self)
        self._voice_shortcut.activated.connect(self._toggle_listening)
        self._set_view(0)

    def _build_operation_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title_card, title_layout = _card()
        title_layout.addWidget(_label("01 / CONSOLA DEL OPERADOR", "eyebrow"))
        title_layout.addWidget(_label("Una orden. Un taladro. Un resultado visible.", "page-title"))
        title_layout.addWidget(
            _label("Consulta el plan, solicita la acción por voz y sigue la respuesta del equipo simulado.", "caption")
        )
        layout.addWidget(title_card)
        self.status_card, status_layout = _card()
        status_layout.addWidget(_label("ESTADO DE LA TAREA", "eyebrow"))
        self.workflow_status = _label("Sin taladro seleccionado", "hero")
        status_layout.addWidget(self.workflow_status)
        self.workflow_detail = _label("Seleccione un taladro de la malla ficticia para comenzar.", "caption")
        status_layout.addWidget(self.workflow_detail)
        layout.addWidget(self.status_card)
        stage_card, stage_layout = _card()
        stage_layout.addWidget(_label("SECUENCIA DE TRABAJO", "eyebrow"))
        stages = QHBoxLayout()
        stages.setSpacing(6)
        self.stage_labels = []
        for title in ("01 IDENTIFICAR", "02 CONSULTAR", "03 VALIDAR", "04 POSICIONAR", "05 CARGAR"):
            stage = _label(title, "stage")
            stage.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stage_labels.append(stage)
            stages.addWidget(stage, 1)
        stage_layout.addLayout(stages)
        layout.addWidget(stage_card)
        operation_card, operation_layout = _card()
        operation_layout.addWidget(_label("TALADRO Y PLAN ACTIVO", "eyebrow"))
        self.operation_labels = {}
        operation_row = QHBoxLayout()
        for key, title in (("hole_id", "TALADRO"), ("product", "PRODUCTO"),
                           ("planned_kg", "KG PREVISTOS"), ("delivery_method", "MÉTODO"),
                           ("scenario", "ESCENARIO")):
            metric = QFrame()
            metric.setObjectName("metric")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(10, 8, 10, 8)
            metric_layout.addWidget(_label(title, "eyebrow"))
            value = _label("—", "value")
            metric_layout.addWidget(value)
            self.operation_labels[key] = value
            operation_row.addWidget(metric, 1)
        operation_layout.addLayout(operation_row)
        self.session_label = _label("Sesión: no iniciada · Modo: deshabilitado", "caption")
        operation_layout.addWidget(self.session_label)
        layout.addWidget(operation_card)

        zone_card, zone_layout = _card()
        zone_layout.addWidget(_label("CONDICIÓN FICTICIA PARA LA DEMO", "eyebrow"))
        self.zone_clear_checkbox = QCheckBox("Simular zona despejada")
        self.zone_clear_checkbox.toggled.connect(self.zone_clear_toggled.emit)
        zone_layout.addWidget(self.zone_clear_checkbox)
        self.zone_clear_note = _label(
            "Este control no lee sensores. Sin marcarlo, Faro rechaza el movimiento simulado.", "caption")
        zone_layout.addWidget(self.zone_clear_note)
        layout.addWidget(zone_card)
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
        overview, overview_layout = _card()
        overview_layout.addWidget(_label("AVANCE DEL PLAN", "eyebrow"))
        self.plan_progress = QProgressBar()
        self.plan_progress.setTextVisible(True)
        overview_layout.addWidget(self.plan_progress)
        self.plan_tiles = QHBoxLayout()
        self.plan_tiles.setSpacing(8)
        overview_layout.addLayout(self.plan_tiles)
        layout.addWidget(overview)
        plan_card, plan_layout = _card()
        plan_layout.addWidget(_label("DETALLE DE TALADROS · DATOS FICTICIOS", "eyebrow"))
        self.plan_summary = _label("Taladros ficticios", "eyebrow")
        plan_layout.addWidget(self.plan_summary)
        self.plan_list = QListWidget()
        self.plan_list.setAlternatingRowColors(False)
        self.plan_list.setMaximumHeight(210)
        plan_layout.addWidget(self.plan_list, 1)
        layout.addWidget(plan_card)
        layout.addWidget(_label("La lista es informativa. Las órdenes se validan por el motor de reglas.", "caption"))
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
        stage_index = {
            "seleccionado": 0, "consultado": 1, "preparado": 2,
            "confirmacion_pendiente": 3, "movimiento_en_curso": 3,
            "posicionado": 3, "carga_en_curso": 4, "cargado": 4,
            "retraccion_en_curso": 4, "retraido": 4, "cerrado": 5,
        }.get(operation_state, -1)
        for index, stage in enumerate(self.stage_labels):
            stage.setProperty("stageState", "done" if index < stage_index else
                              "current" if index == stage_index else "waiting")
            stage.style().unpolish(stage)
            stage.style().polish(stage)

        confirmation = snapshot.get("confirmation")
        if isinstance(confirmation, Mapping):
            action = str(confirmation.get("action", "")).replace("_", " ")
            summary = f"Confirmación pendiente: {action} · taladro {confirmation.get('hole_id', '—')}"
            if confirmation.get("product"):
                summary += f" · {confirmation['product']}"
            self.workflow_status.setText("CONFIRMACIÓN REQUERIDA")
            self.workflow_detail.setText(summary)

        operation = snapshot.get("operation", {})
        if isinstance(operation, Mapping):
            for key, label in self.operation_labels.items():
                value = operation.get(key, "—")
                label.setText("—" if value in (None, "") else str(value))
            session = snapshot.get("session", {})
            if isinstance(session, Mapping):
                mode = session.get("mode", "deshabilitado")
                operator = session.get("operator_label") or "no iniciada"
                listening = " · escucha activa" if session.get("listening") else ""
                self.session_label.setText(f"Sesión: {operator} · Modo: {mode}{listening}")

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
            self.plan_list.clear()
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
                self.plan_tiles.addWidget(tile, 1)
                row = (
                    f"Taladro {item.get('id', '—')} · {item.get('product', '—')} · "
                    f"{item.get('planned_kg', '—')} kg · {item.get('delivery_method', '—')} · {status}"
                )
                self.plan_list.addItem(QListWidgetItem(row))
            if not self.plan_list.count():
                self.plan_list.addItem("No hay taladros ficticios disponibles.")

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
            QWidget { background: #edf3f5; color: #183246; font-family: 'Segoe UI'; font-size: 13px; }
            QLabel[role='title'] { color: #102e42; font-size: 23px; font-weight: 800; letter-spacing: 1px; }
            QLabel[role='subtitle'] { color: #526c7c; font-size: 12px; }
            QLabel[role='badge'] { color: #ffffff; background: #153e50; border: 1px solid #153e50;
                                   border-radius: 5px; padding: 9px 14px; font-size: 11px; font-weight: 700; }
            QFrame#card { background: #ffffff; border: 1px solid #d7e4e9; border-radius: 8px; }
            QFrame#card QLabel { background: transparent; }
            QFrame#metric { background: #f3f8fa; border: 1px solid #dbe9ed; border-radius: 5px; }
            QFrame#metric QLabel { background: transparent; }
            QPushButton[role='nav'] { background: #dfe9ed; color: #536e7d; border: 1px solid #d3e2e7;
                                      border-radius: 5px; padding: 11px 4px; font-size: 11px; font-weight: 700; }
            QPushButton[role='nav']:checked { background: #ffffff; color: #0f5167;
                                               border-bottom: 3px solid #e59a36; }
            QLabel[role='eyebrow'] { color: #4a7182; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel[role='page-title'] { color: #1d3544; font-size: 22px; font-weight: 700; }
            QLabel[role='hero'] { font-size: 25px; font-weight: 700; color: #183a4a; }
            QFrame#card QLabel[role='stage'] { color: #78919b; background: #ecf2f4; border: 1px solid #e0ebee;
                                    border-radius: 5px; padding: 9px 2px; font-size: 10px; font-weight: 700; }
            QFrame#card QLabel[role='stage'][stageState='current'] { color: #714408; background: #fff1d8; border-color: #eab662; }
            QFrame#card QLabel[role='stage'][stageState='done'] { color: #0e665c; background: #dff4ed; border-color: #a9dfce; }
            QFrame#holeTile { background: #f1f7f8; border: 1px solid #d9e9ec; border-radius: 6px; }
            QFrame#holeTile[holeStatus='activo'] { background: #fff4e2; border: 2px solid #e59a36; }
            QFrame#holeTile[holeStatus='completado'] { background: #e5f5ef; border-color: #9dd7bf; }
            QFrame#holeTile[holeStatus='bloqueado'] { background: #f9ecea; border-color: #eac5bd; }
            QFrame#holeTile QLabel { background: transparent; }
            QLabel[role='tile-id'] { color: #163d50; font-size: 27px; font-weight: 800; }
            QLabel[role='tile-status'] { color: #56717e; font-size: 10px; font-weight: 700; }
            QProgressBar { background: #e6eff2; border: 0; border-radius: 5px; height: 12px;
                           text-align: center; color: #17394a; font-size: 10px; }
            QProgressBar::chunk { background: #2d9285; border-radius: 5px; }
            QLabel[role='metric-value'] { font-size: 22px; font-weight: 700; color: #183a4a; }
            QLabel[role='value'] { font-size: 16px; font-weight: 600; }
            QLabel[role='caption'] { color: #627783; font-size: 12px; }
            QLabel[role='footer'] { color: #70838e; font-size: 10px; font-weight: 600; }
            QLabel[role='decision-state'] { color: #627783; background: #e5eaed; padding: 5px 7px;
                                            font-size: 10px; font-weight: 700; }
            QLabel[role='decision-state'][outcome='accepted'] { color: #1f6b50; background: #e0f1e8; }
            QLabel[role='decision-state'][outcome='rejected'] { color: #a54131; background: #fae8e4; }
            QPushButton { background: #1b5269; color: white; border: 1px solid #1b5269; border-radius: 5px;
                          padding: 9px 11px; font-weight: 700; }
            QPushButton:hover { background: #123f52; }
            QPushButton[listening='true'] { background: #a14e3d; border-color: #a14e3d; }
            QLineEdit { background: #ffffff; border: 1px solid #b8c9d2; border-radius: 3px; padding: 9px;
                        selection-background-color: #2e7274; }
            QLineEdit:focus { border-color: #2e7274; }
            QCheckBox { background: transparent; spacing: 8px; font-weight: 700; }
            QListWidget { background: #ffffff; border: 1px solid #dae2e5; outline: 0; }
            QListWidget::item { padding: 7px 5px; border-bottom: 1px solid #e1e7ea; }
            QListWidget::item:selected { background: #dfe9eb; color: #243544; }
            QScrollArea { background: transparent; border: none; }
            """
        )
