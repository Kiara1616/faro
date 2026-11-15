"""Composition root for Faro's fictional end-to-end workflow."""

from __future__ import annotations

from dataclasses import dataclass, replace
import time
from pathlib import Path

from faro.audit import AuditStore
from faro.confirmation import ConfirmationGate
from faro.domain import Command, EventStatus, FaroDomain, Intent, Mode, Source, State
from faro.plan import DemoPlan
from faro.simulator import SimEvent, SimStatus, SimulatedMMU
from faro.scenarios import Scenario, build_simulator
from faro.voice_pipeline import PipelineResult, VoicePipeline


@dataclass
class FaroController:
    plan: DemoPlan
    audit: AuditStore
    domain: FaroDomain
    simulator: SimulatedMMU
    session_id: str = "demo-session"
    scenario_name: str = "normal"
    confirmation_ttl: float = 10.0

    @classmethod
    def create(cls, plan: DemoPlan, audit_path: str | Path,
               *, scenario: Scenario | None = None) -> "FaroController":
        domain = FaroDomain(plan)
        domain.begin_session("demo-session", "Operador de prueba", Mode.MANUAL)
        selected = scenario or Scenario("normal", "flujo normal")
        return cls(plan, AuditStore(audit_path), domain, build_simulator(plan, selected),
                   scenario_name=selected.name)

    def __post_init__(self) -> None:
        self.pipeline = VoicePipeline(self.plan, self.domain)
        self.confirmation_gate = ConfirmationGate(ttl_seconds=self.confirmation_ttl)
        self._confirmation_request = None
        self._confirmation_state_before = None
        self.pipeline.control_handler = self._handle_control

    @property
    def confirmation_pending(self) -> bool:
        """Whether a critical request is waiting for explicit operator approval."""
        return self.confirmation_gate.pending is not None and self._confirmation_request is not None

    def confirmation_snapshot(self) -> dict | None:
        """Return a UI-safe summary without exposing the confirmation token."""
        pending = self.confirmation_gate.pending
        if pending is None or not self.confirmation_pending:
            return None
        return {
            "hole_id": pending.hole_id,
            "action": pending.action,
            "product": pending.product,
            "planned_kg": pending.planned_kg,
            "expires_at": pending.expires_at,
        }

    CONFIRMATION_ACTIONS = frozenset({
        "extender_brazo", "extender_manguera", "iniciar_carga",
        "retraer_brazo", "retraer_manguera",
    })

    @staticmethod
    def _control_decision(accepted, reason, command_id, before, after=None):
        from faro.domain import Decision
        return Decision(accepted, reason, command_id, before, after or before, None)

    def _live_confirmation_context(self, request):
        session = self.domain.session
        hole = self.domain.selected_hole
        action = request.action
        product = hole.product if action == "iniciar_carga" and hole else None
        planned_kg = hole.planned_kg if action == "iniciar_carga" and hole else None
        return {
            "session_id": session.session_id if session else "",
            "mode": session.mode.value if session else "",
            "hole_id": hole.id if hole else "",
            "action": action,
            "product": product,
            "planned_kg": planned_kg,
        }

    def _handle_control(self, intent: str, *, session_id: str, source: Source,
                        generation: int | None = None):
        if intent in {"modo_manual", "modo_voz"}:
            return self.domain.handle_control(intent, session_id=session_id,
                                              source=source, generation=generation)
        if intent == "pausar" and not self.confirmation_pending:
            return self.domain.handle_input(Command(Intent.PAUSAR), source=source,
                                            session_id=session_id, generation=generation)
        before = self.domain.state
        control_id = f"control-{time.monotonic_ns()}"
        pending = self.confirmation_gate.pending
        pause_cancelled_confirmation = intent == "pausar" and self.confirmation_pending
        if pause_cancelled_confirmation:
            # A request waiting for authorization has never reached the
            # simulator; pausing it must not create a cancellation command for
            # an action that does not exist there yet.
            intent = "cancelar_confirmacion"
        if intent == "cancelar_confirmacion":
            if pending is None or self._confirmation_request is None:
                return self._control_decision(False, "no_confirmation_pending", control_id, before)
            request = self._confirmation_request
            restored = self.domain.cancel_pending_confirmation(request.command_id,
                                                               self._confirmation_state_before)
            if not restored:
                return self._control_decision(False, "confirmation_cancel_failed", control_id, before)
            self.confirmation_gate.cancel()
            self._confirmation_request = None
            self._confirmation_state_before = None
            reason = ("confirmation_cancelled_by_pause" if pause_cancelled_confirmation
                      else "confirmation_cancelled")
            self.audit.record_event(request.command_id, "confirmation_cancelled", reason)
            return self._control_decision(True, reason, control_id, before)
        if intent == "confirmar":
            if pending is None or self._confirmation_request is None:
                return self._control_decision(False, "no_confirmation_pending", control_id, before)
            request = self._confirmation_request
            live = self._live_confirmation_context(request)
            accepted, reason = self.confirmation_gate.confirm(
                token=pending.token, session_id=session_id,
                mode=live["mode"], hole_id=live["hole_id"],
                action=live["action"], product=live["product"],
                planned_kg=live["planned_kg"], now=time.monotonic())
            state_before = self._confirmation_state_before
            if not accepted:
                self.domain.cancel_pending_confirmation(request.command_id, state_before)
                self._confirmation_request = None
                self._confirmation_state_before = None
                event_status = reason if reason.startswith("confirmation_") else f"confirmation_{reason}"
                self.audit.record_event(request.command_id, event_status, reason)
                return self._control_decision(False, reason, control_id, before)
            authorized = self.domain.authorize_pending_action(request.command_id)
            if not authorized:
                self.domain.cancel_pending_confirmation(request.command_id, state_before)
                self._confirmation_request = None
                self._confirmation_state_before = None
                self.audit.record_event(request.command_id,
                                        "confirmation_authorization_failed",
                                        "domain_authorization_failed")
                return self._control_decision(False, "confirmation_authorization_failed",
                                              control_id, before)
            event = self.simulator.submit(request)
            self._confirmation_request = None
            self._confirmation_state_before = None
            if event.status is SimStatus.REJECTED:
                self.domain.reject_submission(request.command_id, event.reason)
                self.audit.record_event(request.command_id, event.status.value, event.reason)
                return self._control_decision(False, "simulator_rejected", control_id, before)
            self.audit.record_event(request.command_id, "confirmation_accepted", "confirmed_by_operator")
            self.audit.record_event(request.command_id, event.status.value, event.reason)
            return self._control_decision(True, "confirmed", control_id, before,
                                          self.domain.state)
        return self.domain.handle_control(intent, session_id=session_id, source=source,
                                          generation=generation)

    def process(self, text: str, *, source: Source = Source.TEXT,
                generation: int | None = None, zone_clear: bool = False) -> PipelineResult:
        result = self.pipeline.process(text, source=source, session_id=self.session_id,
                                       generation=generation, zone_clear=zone_clear)
        decision = result.decision
        if decision is None:
            return result
        if (decision.request is not None and decision.accepted
                and decision.request.action in self.CONFIRMATION_ACTIONS):
            # The low-level domain validates the request; the composition root
            # owns the authorization boundary and exposes the explicit pending
            # state until the operator confirms or cancels it.
            self.domain.state = State.CONFIRMACION_PENDIENTE
            decision = replace(decision, state_after=State.CONFIRMACION_PENDIENTE)
            result = replace(result, decision=decision)
        self.audit.record_decision(
            command_id=decision.command_id, session_id=self.session_id,
            operator_label=self.domain.session.operator_label if self.domain.session else None,
            source=source.value, transcript=text, intent=result.parsed.intent or "unknown",
            hole_id=decision.hole_id, state_before=decision.state_before.value,
            state_after=decision.state_after.value, accepted=decision.accepted,
            decision="accepted" if decision.accepted else "rejected", reason=decision.reason,
        )
        if decision.request is not None and decision.accepted:
            if decision.request.action in self.CONFIRMATION_ACTIONS:
                request = decision.request
                hole = self.domain.selected_hole
                session = self.domain.session
                self.confirmation_gate.request(
                    token=request.command_id, session_id=self.session_id,
                    mode=session.mode.value if session else "manual",
                    hole_id=request.hole_id, action=request.action,
                    product=request.product or (hole.product if hole and request.action == "iniciar_carga" else None),
                    planned_kg=request.planned_kg, now=time.monotonic())
                self._confirmation_request = request
                self._confirmation_state_before = decision.state_before
                self.audit.record_event(request.command_id, "confirmation_pending", "confirmation_required")
                return result
            event = self.simulator.submit(decision.request)
            if event.status is SimStatus.REJECTED:
                if decision.request.action == "cancel":
                    self.domain.reject_cancellation(decision.request.target_command_id or "", event.reason)
                else:
                    self.domain.reject_submission(decision.command_id, event.reason)
                self.audit.record_event(decision.command_id, event.status.value,
                                        f"scenario={self.scenario_name}; {event.reason}".strip("; "))
            else:
                self.audit.record_event(decision.command_id, event.status.value,
                                        f"scenario={self.scenario_name}; {event.reason}".strip("; "))
        return result

    def tick(self) -> SimEvent | None:
        event = self.simulator.tick()
        if event is None:
            return None
        status_map = {
            SimStatus.IN_PROGRESS: EventStatus.IN_PROGRESS,
            SimStatus.COMPLETED: EventStatus.COMPLETED,
            SimStatus.FAILED: EventStatus.FAILED,
            SimStatus.CANCELLED: EventStatus.CANCELLED,
        }
        if event.status is SimStatus.TIMEOUT:
            self._last_unknown_command_id = event.command_id
            self.domain.mark_unknown(event.command_id, event.reason or "simulator_timeout")
            self.audit.record_event(event.command_id, event.status.value,
                                    f"scenario={self.scenario_name}; {event.reason}".strip("; "))
            return event
        if event.status in status_map:
            self.domain.apply_event(event.command_id, status_map[event.status])
            self.audit.record_event(event.command_id, event.status.value,
                                    f"scenario={self.scenario_name}; {event.reason}".strip("; "))
        return event

    def recover_unknown(self, reason: str = "manual_review") -> bool:
        """Explicitly acknowledge an unknown simulator result; never auto-retry."""
        if self.domain.state is not State.RESULTADO_DESCONOCIDO:
            return False
        self.domain.last_failure_reason = reason
        self.domain.state = State.FALLO
        command_id = getattr(self, "_last_unknown_command_id", None)
        if command_id:
            self.audit.record_event(command_id, "recovered",
                                    f"scenario={self.scenario_name}; {reason}")
        return True
