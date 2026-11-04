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


@dataclass
class FaroDomain:
    plan: DemoPlan
    state: State = State.SIN_SELECCION
    selected_hole_id: str | None = None
    plan_validated: bool = False
    pending: ActionRequest | None = None
    cancel_requested: bool = False
    expected_next_hole_id: str | None = None
    completed_holes: set[str] = field(default_factory=set)

    @property
    def selected_hole(self) -> Hole | None:
        return next((h for h in self.plan.holes if h.id == self.selected_hole_id), None)

    def snapshot(self) -> tuple[State, str | None, bool, str | None, bool, str | None, frozenset[str]]:
        """Operational state for invariant checks; decision IDs do not alter it."""
        return (self.state, self.selected_hole_id, self.plan_validated,
                self.pending.command_id if self.pending else None,
                self.cancel_requested, self.expected_next_hole_id,
                frozenset(self.completed_holes))

    def handle(self, command: Command) -> Decision:
        before = self.state
        command_id = uuid4().hex

        def reject(reason: str) -> Decision:
            return Decision(False, reason, command_id, before, self.state, self.selected_hole_id)

        def accept(reason: str, request: ActionRequest | None = None) -> Decision:
            return Decision(True, reason, command_id, before, self.state,
                            self.selected_hole_id, request)

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
            if self.state is not State.CARGADO or hole.delivery_method != method:
                return reject("wrong_state_or_method")
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
        elif status is EventStatus.COMPLETED:
            if action in {Intent.EXTENDER_BRAZO.value, Intent.EXTENDER_MANGUERA.value}:
                self.state = State.POSICIONADO
            elif action == Intent.INICIAR_CARGA.value:
                self.state = State.CARGADO
            else:
                self.state = State.RETRAIDO
        else:
            self.state = State.FALLO
        return True
