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
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
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

    VIEW_INDEX = {"estado": 0, "indicadores": 1, "revision": 2}

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Faro V1 | Consola de simulación")
        self.setMinimumSize(1000, 640)
        self.resize(1280, 720)
        self._listening = False
        self._history_count = 0
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
        title_group.addWidget(_label("FARO  /  V1", "title"))
        title_group.addWidget(
            _label("Consola de operación por taladro · Prototipo académico", "subtitle")
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
        self.nav_labels = []
        for text in ("OPERACIÓN POR TALADRO", "PLAN FICTICIO", "REGISTRO"):
            item = _label(text, "nav")
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.nav_labels.append(item)
            nav.addWidget(item)
        main_column.addLayout(nav)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_status_page())
        self.pages.addWidget(self._build_indicators_page())
        self.pages.addWidget(self._build_review_page())
        main_column.addWidget(self.pages, 1)

        hint_card, hint_layout = _card()
        hint_layout.addWidget(_label("COMANDOS DE DEMOSTRACIÓN", "eyebrow"))
        hint_layout.addWidget(
            _label(
                "Seleccionar taladro 101  /  Consultar plan  /  Preparar carga  /  "
                "Validar producto alfa, cien kilos  /  Extender brazo"
            )
        )
        main_column.addWidget(hint_card)

        sidebar = QVBoxLayout()
        sidebar.setSpacing(10)
        body.addLayout(sidebar, 4)

        voice_card, voice_layout = _card()
        voice_layout.addWidget(_label("CANAL DE VOZ", "eyebrow"))
        self.voice_status = _label("Micrófono inactivo", "value")
        voice_layout.addWidget(self.voice_status)
        self.voice_button = QPushButton("Activar escucha  ·  F8")
        self.voice_button.clicked.connect(self._toggle_listening)
        voice_layout.addWidget(self.voice_button)
        voice_layout.addWidget(_label("Con la escucha activa: «Oye Faro, mostrar estado». La frase no enciende el micrófono.", "caption"))
        sidebar.addWidget(voice_card)

        command_card, command_layout = _card()
        command_layout.addWidget(_label("ENTRADA MANUAL DE PRUEBA", "eyebrow"))
        command_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Escribe un comando de prueba")
        self.command_input.returnPressed.connect(self._submit_command)
        command_row.addWidget(self.command_input, 1)
        send_button = QPushButton("Enviar")
        send_button.clicked.connect(self._submit_command)
        command_row.addWidget(send_button)
        command_layout.addLayout(command_row)
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
        sidebar.addWidget(decision_card)

        history_card, history_layout = _card()
        history_layout.addWidget(_label("REGISTRO DE EVENTOS", "eyebrow"))
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(False)
        history_layout.addWidget(self.history_list, 1)
        sidebar.addWidget(history_card, 1)

        root.addWidget(
            _label(
                "PROTOTIPO ACADÉMICO  ·  DATOS FICTICIOS  ·  SIN CONTROL DE MAQUINARIA",
                "footer",
            )
        )
        self._voice_shortcut = QShortcut(QKeySequence("F8"), self)
        self._voice_shortcut.activated.connect(self._toggle_listening)

    def _build_status_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        title_card, title_layout = _card()
        title_layout.addWidget(_label("OPERACIÓN POR TALADRO · SIMULACIÓN", "eyebrow"))
        title_layout.addWidget(_label("Unidad móvil ficticia", "page-title"))
        title_layout.addWidget(
            _label("La malla, el plan y los sensores son ficticios; no existe conexión con maquinaria real.", "caption")
        )
        layout.addWidget(title_card)
        self.status_card, status_layout = _card()
        status_layout.addWidget(_label("SECUENCIA ACTUAL", "eyebrow"))
        self.workflow_status = _label("Sin revisión iniciada", "hero")
        status_layout.addWidget(self.workflow_status)
        self.workflow_detail = _label("Puede iniciar una revisión auxiliar.", "caption")
        status_layout.addWidget(self.workflow_detail)
        layout.addWidget(self.status_card)
        operation_card, operation_layout = _card()
        operation_layout.addWidget(_label("TALADRO Y PLAN ACTIVO", "eyebrow"))
        self.operation_labels = {}
        operation_row = QHBoxLayout()
        for key, title in (("hole_id", "TALADRO"), ("product", "PRODUCTO"),
                           ("planned_kg", "KG PREVISTOS"), ("delivery_method", "MÉTODO")):
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
        summary_card, summary_layout = _card()
        summary_layout.addWidget(_label("RESUMEN DE LECTURAS SIMULADAS", "eyebrow"))
        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)
        self.summary_value_labels = {}
        for key, title in (
            ("temperatura", "TEMPERATURA"),
            ("presion", "PRESIÓN"),
            ("bateria", "BATERÍA"),
        ):
            metric = QFrame()
            metric.setObjectName("metric")
            metric_layout = QVBoxLayout(metric)
            metric_layout.setContentsMargins(12, 10, 12, 10)
            metric_layout.setSpacing(3)
            metric_layout.addWidget(_label(title, "eyebrow"))
            value_label = _label("—", "metric-value")
            metric_layout.addWidget(value_label)
            self.summary_value_labels[key] = value_label
            summary_row.addWidget(metric, 1)
        summary_layout.addLayout(summary_row)
        layout.addWidget(summary_card)
        layout.addStretch(1)
        return page

    def _build_indicators_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro, intro_layout = _card()
        intro_layout.addWidget(_label("INDICADORES FICTICIOS", "eyebrow"))
        intro_layout.addWidget(_label("Lecturas para la demostración", "page-title"))
        intro_layout.addWidget(
            _label("Los valores no son límites ni parámetros de operación de ORICA.", "caption")
        )
        layout.addWidget(intro)
        self.indicator_container = QVBoxLayout()
        self.indicator_container.setSpacing(12)
        layout.addLayout(self.indicator_container)
        layout.addStretch(1)
        return page

    def _build_review_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        intro, intro_layout = _card()
        intro_layout.addWidget(_label("REVISIÓN AUXILIAR SIMULADA", "eyebrow"))
        intro_layout.addWidget(_label("Secuencia guiada", "page-title"))
        intro_layout.addWidget(
            _label("Faro verifica el paso actual antes de aceptar una navegación o registro.", "caption")
        )
        layout.addWidget(intro)
        steps_card, steps_layout = _card()
        self.review_step = _label("Esperando inicio", "hero")
        self.review_progress = _label("0 de 3 pasos completados", "caption")
        steps_layout.addWidget(self.review_step)
        steps_layout.addWidget(self.review_progress)
        layout.addWidget(steps_card)
        layout.addStretch(1)
        return page

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

    def append_event(self, event: Mapping[str, Any] | str) -> None:
        """Append a single event when the controller does not send full history."""
        self.history_list.insertItem(0, self._format_event(event))
        self._history_count += 1

    def render_state(self, snapshot: Mapping[str, Any]) -> None:
        """Render a tolerant snapshot supplied by the controller/engine."""
        view = str(snapshot.get("view", "estado")).lower()
        if view in self.VIEW_INDEX:
            active = self.VIEW_INDEX[view]
            self.pages.setCurrentIndex(active)
            for index, nav in enumerate(self.nav_labels):
                nav.setProperty("active", index == active)
                nav.style().unpolish(nav)
                nav.style().polish(nav)

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
        alert = snapshot.get("alert")
        if isinstance(alert, Mapping):
            reason = alert.get("reason", "revisión requerida")
            blocking = " · BLOQUEANTE" if alert.get("blocking") else ""
            self.execution_status.setText(f"Estado de ejecución: requiere revisión · {reason}{blocking}")

        workflow = snapshot.get("workflow", {})
        if isinstance(workflow, Mapping):
            active = bool(workflow.get("active", False))
            completed = bool(workflow.get("completed", False))
            step_number = workflow.get("step", 0)
            label = workflow.get("label", "")
            status = workflow.get("status", "Revisión en curso" if active else "Revisión completada" if completed else "Sin revisión iniciada")
            step = workflow.get("current_step", f"Paso {step_number}: {label}" if active else str(label or "Esperando inicio"))
            if workflow.get("requires_human"):
                default_detail = "Discrepancia detectada: se requiere revisión humana."
            elif workflow.get("recorded"):
                default_detail = "Lectura registrada; puede confirmar el paso."
            elif workflow.get("inspected"):
                default_detail = "Indicador consultado; registre la lectura para continuar."
            elif active:
                default_detail = "Consulte el indicador del paso actual."
            else:
                default_detail = "Puede iniciar una revisión auxiliar."
            detail = workflow.get("detail", workflow.get("message", default_detail))
            progress = workflow.get("progress", step_number - 1 if active and isinstance(step_number, int) else 3 if completed else 0)
            total = workflow.get("total", 3)
            self.workflow_status.setText(str(status))
            self.workflow_detail.setText(str(detail))
            self.review_step.setText(str(step))
            self.review_progress.setText(
                str(progress) if isinstance(progress, str) else f"{progress} de {total} pasos completados"
            )

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

        indicators = snapshot.get("indicators", {})
        if isinstance(indicators, Mapping):
            self._render_indicators(indicators)
        history = snapshot.get("history")
        if isinstance(history, (list, tuple)):
            self.history_list.clear()
            for event in reversed(history[-30:]):
                self.history_list.addItem(QListWidgetItem(self._format_event(event)))
            self._history_count = len(history)
            if history and isinstance(history[-1], Mapping):
                accepted = bool(history[-1].get("accepted"))
                self.decision_state.setText("ACEPTADO" if accepted else "RECHAZADO")
                self.decision_state.setProperty("outcome", "accepted" if accepted else "rejected")
            else:
                self.decision_state.setText("EN ESPERA")
                self.decision_state.setProperty("outcome", "waiting")
            self.decision_state.style().unpolish(self.decision_state)
            self.decision_state.style().polish(self.decision_state)

    def _render_indicators(self, indicators: Mapping[str, Any]) -> None:
        for key, label in self.summary_value_labels.items():
            raw = indicators.get(key)
            label.setText(
                f"{raw.get('value', '—')} {raw.get('unit', '')}".strip()
                if isinstance(raw, Mapping) else "—"
            )
        while self.indicator_container.count():
            item = self.indicator_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not indicators:
            empty, inner = _card()
            inner.addWidget(_label("Sin lecturas simuladas", "caption"))
            self.indicator_container.addWidget(empty)
            return
        for name, raw in indicators.items():
            card, inner = _card()
            inner.addWidget(_label(str(name).replace("_", " ").upper(), "eyebrow"))
            if isinstance(raw, Mapping):
                value = raw.get("value", "—")
                unit = raw.get("unit", "")
                updated = raw.get("updated_at", raw.get("timestamp", ""))
                state = raw.get("status", "")
                source = raw.get("source", "")
                inner.addWidget(_label(f"{value} {unit}".strip(), "hero"))
                metadata = " · ".join(str(part) for part in (state, source, updated) if part)
                if metadata:
                    inner.addWidget(_label(metadata, "caption"))
            else:
                inner.addWidget(_label(str(raw), "hero"))
            self.indicator_container.addWidget(card)

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
            QWidget { background: #eef1f3; color: #243544; font-family: 'Segoe UI'; font-size: 13px; }
            QLabel[role='title'] { color: #183a4a; font-size: 22px; font-weight: 700; letter-spacing: 1px; }
            QLabel[role='subtitle'] { color: #617681; font-size: 12px; }
            QLabel[role='badge'] { color: #ffffff; background: #315c68; border: 1px solid #315c68;
                                   padding: 9px 11px; font-size: 11px; font-weight: 700; }
            QFrame#card { background: #ffffff; border: 1px solid #d5dde2; border-radius: 3px; }
            QFrame#card QLabel { background: transparent; }
            QFrame#metric { background: #f5f8f9; border: 1px solid #dbe4e8; border-radius: 2px; }
            QFrame#metric QLabel { background: transparent; }
            QLabel[role='nav'] { background: #e3e8eb; color: #627783; border: 1px solid #d4dce1;
                                 padding: 11px 4px; font-size: 11px; font-weight: 700; }
            QLabel[role='nav'][active='true'] { background: #ffffff; color: #183d51;
                                                 border-bottom: 3px solid #2b7779; }
            QLabel[role='eyebrow'] { color: #56717e; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
            QLabel[role='page-title'] { color: #1d3544; font-size: 22px; font-weight: 700; }
            QLabel[role='hero'] { font-size: 25px; font-weight: 700; color: #183a4a; }
            QLabel[role='metric-value'] { font-size: 22px; font-weight: 700; color: #183a4a; }
            QLabel[role='value'] { font-size: 16px; font-weight: 600; }
            QLabel[role='caption'] { color: #627783; font-size: 12px; }
            QLabel[role='footer'] { color: #70838e; font-size: 10px; font-weight: 600; }
            QLabel[role='decision-state'] { color: #627783; background: #e5eaed; padding: 5px 7px;
                                            font-size: 10px; font-weight: 700; }
            QLabel[role='decision-state'][outcome='accepted'] { color: #1f6b50; background: #e0f1e8; }
            QLabel[role='decision-state'][outcome='rejected'] { color: #a54131; background: #fae8e4; }
            QPushButton { background: #315c6d; color: white; border: 1px solid #315c6d; border-radius: 3px;
                          padding: 9px 11px; font-weight: 700; }
            QPushButton:hover { background: #254b5c; }
            QPushButton[listening='true'] { background: #a14e3d; border-color: #a14e3d; }
            QLineEdit { background: #ffffff; border: 1px solid #b8c9d2; border-radius: 3px; padding: 9px;
                        selection-background-color: #2e7274; }
            QLineEdit:focus { border-color: #2e7274; }
            QListWidget { background: #ffffff; border: 1px solid #dae2e5; outline: 0; }
            QListWidget::item { padding: 7px 5px; border-bottom: 1px solid #e1e7ea; }
            QListWidget::item:selected { background: #dfe9eb; color: #243544; }
            """
        )
