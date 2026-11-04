"""Deterministic state machine for Faro's fictional hole-loading cycle.

This module has no audio, Qt, network, industrial controller, or persistence I/O.
It authorizes *simulated* requests; completion requires a correlated event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from faro.plan import DemoPlan, Hole


class State(str, Enum):
    SIN_SELECCION = "sin_seleccion"
    SELECCIONADO = "seleccionado"
    CONSULTADO = "consultado"
    PREPARADO = "preparado"
    MOVIMIENTO_EN_CURSO = "movimiento_en_curso"
    POSICIONADO = "posicionado"
    CARGA_EN_CURSO = "carga_en_curso"
    CARGADO = "cargado"
    RETRACCION_EN_CURSO = "retraccion_en_curso"
    RETRAIDO = "retraido"
    CERRADO = "cerrado"
    FALLO = "fallo"
    RESULTADO_DESCONOCIDO = "resultado_desconocido"


class Intent(str, Enum):
    CONSULTAR_ESTADO = "consultar_estado"
    SELECCIONAR_TALADRO = "seleccionar_taladro"
    CONSULTAR_TALADRO = "consultar_taladro"
    CONSULTAR_PLAN = "consultar_plan"
    PREPARAR_CARGA = "preparar_carga"
    DECLARAR_PLAN = "declarar_plan"
    EXTENDER_BRAZO = "extender_brazo"
    EXTENDER_MANGUERA = "extender_manguera"
    INICIAR_CARGA = "iniciar_carga"
    RETRAER_BRAZO = "retraer_brazo"
    RETRAER_MANGUERA = "retraer_manguera"
    PAUSAR = "pausar"
    CERRAR_TALADRO = "cerrar_taladro"
    SIGUIENTE_TALADRO = "siguiente_taladro"


class EventStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Mode(str, Enum):
    VOZ = "voz"
    MANUAL = "manual"
    DESHABILITADO = "deshabilitado"


class Source(str, Enum):
    VOICE = "voice"
    TEXT = "text"


@dataclass
class Session:
    """Fictitious operator session; it is not voice biometric authentication."""

    session_id: str
    operator_label: str
    mode: Mode = Mode.MANUAL
    listening: bool = False
    generation: int = 0
    transfers: list[tuple[Mode, Mode, int]] = field(default_factory=list)


@dataclass(frozen=True)
class Command:
    intent: Intent
    hole_id: str | None = None
    product: str | None = None
    kg: int | None = None
    zone_clear: bool = False  # Fail closed until the fictional signal is explicit.


@dataclass(frozen=True)
class ActionRequest:
    command_id: str
    hole_id: str
    action: str
    target_command_id: str | None = None
    product: str | None = None
    planned_kg: int | None = None


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reason: str
    command_id: str
    state_before: State
    state_after: State
    hole_id: str | None
    request: ActionRequest | None = None
    alert_before: Alert | None = None
    alert_after: Alert | None = None


@dataclass(frozen=True)
class Alert:
    """An exception for human review, separate from operational state."""

    reason: str
    hole_id: str | None
    expected_hole_id: str | None = None
    received_hole_id: str | None = None
    expected_product: str | None = None
    received_product: str | None = None
    expected_kg: int | None = None
    received_kg: int | None = None
    expected_method: str | None = None
    received_method: str | None = None
    requires_human: bool = False
    blocking: bool = False


@dataclass
class FaroDomain:
    plan: DemoPlan
    session: Session | None = None
    state: State = State.SIN_SELECCION
    selected_hole_id: str | None = None
    plan_validated: bool = False
    pending: ActionRequest | None = None
    cancel_requested: bool = False
    expected_next_hole_id: str | None = None
    last_failure_reason: str | None = None
    alert: Alert | None = None
    alert_history: list[Alert] = field(default_factory=list)
    completed_holes: set[str] = field(default_factory=set)

    def begin_session(self, session_id: str, operator_label: str, mode: Mode = Mode.MANUAL) -> bool:
        """Start or replace a fictitious session only while no action is pending."""
        if not isinstance(session_id, str) or not session_id.strip() or not isinstance(operator_label, str) or not operator_label.strip():
            return False
        if not isinstance(mode, Mode) or self.pending is not None:
            return False
        self.session = Session(session_id.strip(), operator_label.strip(), mode, False, 0)
        return True

    def set_listening(self, session_id: str, enabled: bool) -> bool:
        """Listening is explicit; a mode change never starts the microphone."""
        if self.session is None or self.session.session_id != session_id or type(enabled) is not bool:
            return False
        if self.session.mode is not Mode.VOZ and enabled:
            return False
        self.session.listening = enabled
        self.session.generation += 1
        return True

    def set_mode(self, session_id: str, mode: Mode) -> bool:
        """Switch channels only when no simulated action is in flight."""
        if self.session is None or self.session.session_id != session_id or not isinstance(mode, Mode):
            return False
        if self.pending is not None:
            return False
        previous = self.session.mode
        if previous is mode:
            return True
        self.session.listening = False
        self.session.generation += 1
        self.session.transfers.append((previous, mode, self.session.generation))
        self.session.mode = mode
        return True

    def handle_input(self, command: Command, *, source: Source, session_id: str,
                     generation: int | None = None) -> Decision:
        """Mandatory input boundary enforcing session, mode and capture generation."""
        before = self.state
        command_id = uuid4().hex
        if self.session is None or self.session.session_id != session_id:
            return Decision(False, "invalid_session", command_id, before, self.state, self.selected_hole_id)
        if not isinstance(source, Source):
            return Decision(False, "invalid_source", command_id, before, self.state, self.selected_hole_id)
        if source is Source.VOICE:
            if self.session.mode is not Mode.VOZ:
                return Decision(False, "voice_disabled_in_manual", command_id, before, self.state, self.selected_hole_id)
            if not self.session.listening:
                return Decision(False, "listening_disabled", command_id, before, self.state, self.selected_hole_id)
            if generation is None or generation != self.session.generation:
                return Decision(False, "stale_listening_generation", command_id, before, self.state, self.selected_hole_id)
        elif source is Source.TEXT and self.session.mode is Mode.VOZ:
            # Text is the explicit manual test channel; it cannot enable capture.
            pass
        return self.handle(command)

    @property
    def selected_hole(self) -> Hole | None:
        return next((h for h in self.plan.holes if h.id == self.selected_hole_id), None)

    def snapshot(self) -> tuple[State, str | None, bool, str | None, bool, str | None, str | None, frozenset[str]]:
        """Operational state for invariant checks; decision IDs do not alter it."""
        return (self.state, self.selected_hole_id, self.plan_validated,
                self.pending.command_id if self.pending else None,
                self.cancel_requested, self.expected_next_hole_id,
                self.last_failure_reason,
                frozenset(self.completed_holes))

    def handle(self, command: Command) -> Decision:
        before = self.state
        command_id = uuid4().hex
        alert_before = self.alert

        def raise_alert(reason: str) -> None:
            hole = self.selected_hole
            attempted_id = command.hole_id if isinstance(command.hole_id, str) else None
            method = ("brazo" if command.intent in {Intent.EXTENDER_BRAZO, Intent.RETRAER_BRAZO}
                      else "manguera" if command.intent in {Intent.EXTENDER_MANGUERA, Intent.RETRAER_MANGUERA}
                      else None)
            alert = Alert(
                reason=reason,
                hole_id=hole.id if hole else attempted_id,
                expected_hole_id=self.expected_next_hole_id or self.selected_hole_id,
                received_hole_id=attempted_id,
                expected_product=hole.product if hole else None,
                received_product=command.product if isinstance(command.product, str) else None,
                expected_kg=hole.planned_kg if hole else None,
                received_kg=command.kg if type(command.kg) is int else None,
                expected_method=hole.delivery_method if hole else None,
                received_method=method,
                blocking=reason == "plan_mismatch",
            )
            self.alert = alert
            self.alert_history.append(alert)

        def reject(reason: str) -> Decision:
            alert_reasons = {"unknown_hole", "hole_blocked", "hole_mismatch",
                             "next_hole_mismatch", "invalid_plan_values", "plan_mismatch",
                             "wrong_delivery_method"}
            incomplete_correction = (self.alert is not None and self.alert.blocking
                                     and reason == "invalid_plan_values")
            if reason in alert_reasons and not incomplete_correction:
                raise_alert(reason)
            return Decision(False, reason, command_id, before, self.state,
                            self.selected_hole_id, alert_before=alert_before,
                            alert_after=self.alert)

        def accept(reason: str, request: ActionRequest | None = None) -> Decision:
            correction = {
                "unknown_hole": {Intent.SELECCIONAR_TALADRO},
                "hole_blocked": {Intent.SELECCIONAR_TALADRO},
                "next_hole_mismatch": {Intent.SELECCIONAR_TALADRO},
                "hole_mismatch": {Intent.CONSULTAR_TALADRO},
                "invalid_plan_values": {Intent.DECLARAR_PLAN},
                "plan_mismatch": {Intent.DECLARAR_PLAN},
                "wrong_delivery_method": {Intent.EXTENDER_BRAZO, Intent.EXTENDER_MANGUERA,
                                          Intent.RETRAER_BRAZO, Intent.RETRAER_MANGUERA},
            }
            if self.alert is not None and command.intent in correction.get(self.alert.reason, set()):
                self.alert = None
            return Decision(True, reason, command_id, before, self.state,
                            self.selected_hole_id, request, alert_before, self.alert)

        if not isinstance(command.intent, Intent):
            return reject("unknown_intent")
        intent = command.intent
        if intent in {Intent.CONSULTAR_ESTADO, Intent.CONSULTAR_PLAN}:
            if intent is Intent.CONSULTAR_PLAN and self.selected_hole is None:
                return reject("no_hole_selected")
            return accept("read_only")
        if intent is Intent.PAUSAR:
            if self.pending is None or self.cancel_requested:
                return reject("no_active_action")
            self.cancel_requested = True
            return accept("cancel_requested", ActionRequest(
                command_id, self.selected_hole_id or "", "cancel",
                target_command_id=self.pending.command_id))
        if self.pending is not None:
            return reject("action_in_progress")
        if self.alert is not None and self.alert.blocking:
            correction = {
                "plan_mismatch": Intent.DECLARAR_PLAN,
            }
            allowed = correction[self.alert.reason]
            if intent != allowed:
                return reject("alert_pending")

        if intent is Intent.SELECCIONAR_TALADRO:
            if self.state not in {State.SIN_SELECCION, State.CERRADO}:
                return reject("current_hole_not_closed")
            hole = next((h for h in self.plan.holes if h.id == command.hole_id), None)
            if hole is None:
                return reject("unknown_hole")
            if hole.blocked:
                return reject("hole_blocked")
            if hole.id in self.completed_holes:
                return reject("hole_already_closed")
            if self.expected_next_hole_id is not None and hole.id != self.expected_next_hole_id:
                return reject("next_hole_mismatch")
            if self.state is State.CERRADO and self.selected_hole_id is not None:
                # The explicit next-hole step is mandatory.
                return reject("next_hole_required")
            self.selected_hole_id = hole.id
            self.expected_next_hole_id = None
            self.last_failure_reason = None
            self.plan_validated = False
            self.state = State.SELECCIONADO
            return accept("hole_selected")

        hole = self.selected_hole
        if hole is None:
            return reject("no_hole_selected")
        if intent is Intent.CONSULTAR_TALADRO:
            if command.hole_id != hole.id:
                return reject("hole_mismatch")
            if self.state is not State.SELECCIONADO:
                return reject("wrong_state")
            self.state = State.CONSULTADO
            return accept("plan_consulted")
        if intent is Intent.PREPARAR_CARGA:
            if self.state is not State.CONSULTADO:
                return reject("wrong_state")
            if hole.blocked:
                return reject("hole_blocked")
            self.state = State.PREPARADO
            return accept("prepared")
        if intent is Intent.DECLARAR_PLAN:
            if self.state is not State.PREPARADO or self.plan_validated:
                return reject("wrong_state")
            if type(command.kg) is not int or command.kg <= 0 or not isinstance(command.product, str):
                return reject("invalid_plan_values")
            if command.product != hole.product or command.kg != hole.planned_kg:
                return reject("plan_mismatch")
            self.plan_validated = True
            return accept("plan_validated")
        if intent in {Intent.EXTENDER_BRAZO, Intent.EXTENDER_MANGUERA}:
            method = "brazo" if intent is Intent.EXTENDER_BRAZO else "manguera"
            if self.state is not State.PREPARADO or not self.plan_validated:
                return reject("not_prepared_or_validated")
            if hole.delivery_method != method:
                return reject("wrong_delivery_method")
            if command.zone_clear is not True:
                return reject("fictional_zone_occupied")
            request = ActionRequest(command_id, hole.id, intent.value)
            self.pending = request
            self.state = State.MOVIMIENTO_EN_CURSO
            return accept("submitted", request)
        if intent is Intent.INICIAR_CARGA:
            if self.state is not State.POSICIONADO or not self.plan_validated:
                return reject("not_positioned_or_validated")
            request = ActionRequest(command_id, hole.id, intent.value,
                                    product=hole.product, planned_kg=hole.planned_kg)
            self.pending = request
            self.state = State.CARGA_EN_CURSO
            return accept("submitted", request)
        if intent in {Intent.RETRAER_BRAZO, Intent.RETRAER_MANGUERA}:
            method = "brazo" if intent is Intent.RETRAER_BRAZO else "manguera"
            if self.state is not State.CARGADO:
                return reject("wrong_state")
            if hole.delivery_method != method:
                return reject("wrong_delivery_method")
            request = ActionRequest(command_id, hole.id, intent.value)
            self.pending = request
            self.state = State.RETRACCION_EN_CURSO
            return accept("submitted", request)
        if intent is Intent.CERRAR_TALADRO:
            if self.state is not State.RETRAIDO:
                return reject("not_retracted")
            self.state = State.CERRADO
            self.completed_holes.add(hole.id)
            return accept("hole_closed")
        if intent is Intent.SIGUIENTE_TALADRO:
            if self.state is not State.CERRADO:
                return reject("hole_not_closed")
            current = next(i for i, item in enumerate(self.plan.holes) if item.id == hole.id)
            next_hole = next((item for item in self.plan.holes[current + 1:]
                              if not item.blocked and item.id not in self.completed_holes), None)
            if next_hole is None:
                return reject("end_of_plan")
            self.selected_hole_id = None
            self.expected_next_hole_id = next_hole.id
            self.plan_validated = False
            self.state = State.SIN_SELECCION
            return accept("select_next_hole")
        return reject("unknown_intent")

    def apply_event(self, command_id: str, status: EventStatus) -> bool:
        """Apply only a terminal event for the current pending request."""
        if self.pending is None or self.pending.command_id != command_id:
            return False
        if not isinstance(status, EventStatus):
            return False
        if status is EventStatus.IN_PROGRESS:
            return True
        action = self.pending.action
        cancellation_was_requested = self.cancel_requested
        self.pending = None
        self.cancel_requested = False
        if status is EventStatus.COMPLETED and cancellation_was_requested:
            # A completion racing with cancellation needs explicit reconciliation.
            self.state = State.RESULTADO_DESCONOCIDO
            self.last_failure_reason = "completion_after_cancel_request"
        elif status is EventStatus.COMPLETED:
            if action in {Intent.EXTENDER_BRAZO.value, Intent.EXTENDER_MANGUERA.value}:
                self.state = State.POSICIONADO
            elif action == Intent.INICIAR_CARGA.value:
                self.state = State.CARGADO
            else:
                self.state = State.RETRAIDO
        else:
            self.state = State.FALLO
            self.last_failure_reason = "simulator_failed" if status is EventStatus.FAILED else "simulator_cancelled"
        return True

    def reject_submission(self, command_id: str, reason: str) -> bool:
        """Reconcile a simulator refusal of the currently authorized request.

        The request was never executed. A refusal for another command cannot
        change the active cycle. UI and audit may use ``last_failure_reason``.
        """
        if self.pending is None or self.pending.command_id != command_id:
            return False
        if not isinstance(reason, str) or not reason.strip():
            return False
        self.pending = None
        self.cancel_requested = False
        self.last_failure_reason = reason
        self.state = State.FALLO
        return True

    def reject_cancellation(self, target_command_id: str, reason: str) -> bool:
        """Conservatively reconcile a refused cancellation request.

        The original action may still execute. No later completion can be
        applied until a separate recovery procedure resolves its outcome.
        """
        if (self.pending is None or self.pending.command_id != target_command_id
                or not self.cancel_requested):
            return False
        if not isinstance(reason, str) or not reason.strip():
            return False
        self.pending = None
        self.cancel_requested = False
        self.last_failure_reason = reason
        self.state = State.RESULTADO_DESCONOCIDO
        return True
