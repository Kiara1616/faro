"""Composition root for Faro's fictional end-to-end workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faro.audit import AuditStore
from faro.domain import EventStatus, FaroDomain, Mode, Source, State
from faro.plan import DemoPlan
from faro.simulator import SimEvent, SimStatus, SimulatedMMU
from faro.voice_pipeline import PipelineResult, VoicePipeline


@dataclass
class FaroController:
    plan: DemoPlan
    audit: AuditStore
    domain: FaroDomain
    simulator: SimulatedMMU
    session_id: str = "demo-session"

    @classmethod
    def create(cls, plan: DemoPlan, audit_path: str | Path) -> "FaroController":
        domain = FaroDomain(plan)
        domain.begin_session("demo-session", "Operador de prueba", Mode.MANUAL)
        return cls(plan, AuditStore(audit_path), domain, SimulatedMMU(plan))

    def __post_init__(self) -> None:
        self.pipeline = VoicePipeline(self.plan, self.domain)

    def process(self, text: str, *, source: Source = Source.TEXT,
                generation: int | None = None, zone_clear: bool = False) -> PipelineResult:
        result = self.pipeline.process(text, source=source, session_id=self.session_id,
                                       generation=generation, zone_clear=zone_clear)
        decision = result.decision
        if decision is None:
            return result
        self.audit.record_decision(
            command_id=decision.command_id, session_id=self.session_id,
            operator_label=self.domain.session.operator_label if self.domain.session else None,
            source=source.value, transcript=text, intent=result.parsed.intent or "unknown",
            hole_id=decision.hole_id, state_before=decision.state_before.value,
            state_after=decision.state_after.value, accepted=decision.accepted,
            decision="accepted" if decision.accepted else "rejected", reason=decision.reason,
        )
        if decision.request is not None and decision.accepted:
            event = self.simulator.submit(decision.request)
            if event.status is SimStatus.REJECTED:
                if decision.request.action == "cancel":
                    self.domain.reject_cancellation(decision.request.target_command_id or "", event.reason)
                else:
                    self.domain.reject_submission(decision.command_id, event.reason)
                self.audit.record_event(decision.command_id, event.status.value, event.reason)
            else:
                self.audit.record_event(decision.command_id, event.status.value, event.reason)
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
            self.audit.record_event(event.command_id, event.status.value, event.reason)
            return event
        if event.status in status_map:
            self.domain.apply_event(event.command_id, status_map[event.status])
            self.audit.record_event(event.command_id, event.status.value, event.reason)
        return event

    def recover_unknown(self, reason: str = "manual_review") -> bool:
        """Explicitly acknowledge an unknown simulator result; never auto-retry."""
        if self.domain.state is not State.RESULTADO_DESCONOCIDO:
            return False
        self.domain.last_failure_reason = reason
        self.domain.state = State.FALLO
        command_id = getattr(self, "_last_unknown_command_id", None)
        if command_id:
            self.audit.record_event(command_id, "recovered", reason)
        return True
