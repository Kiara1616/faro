"""Deterministic, in-memory MMU simulator. It has no physical or network output."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from faro.domain import ActionRequest
from faro.plan import DemoPlan


class SimStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class SimEvent:
    command_id: str
    status: SimStatus
    reason: str = ""


@dataclass
class _Pending:
    request: ActionRequest
    ticks_left: int
    started: bool = False
    cancellation_requested: bool = False
    elapsed_ticks: int = 0


@dataclass
class SimulatedMMU:
    plan: DemoPlan
    delay_ticks: int = 1
    fail_actions: frozenset[str] = frozenset()
    timeout_ticks: int | None = None
    _pending: _Pending | None = field(default=None, init=False, repr=False)
    _seen: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.delay_ticks) is not int or self.delay_ticks < 0:
            raise ValueError("delay_ticks must be a nonnegative integer")
        if self.timeout_ticks is not None and (type(self.timeout_ticks) is not int or self.timeout_ticks <= 0):
            raise ValueError("timeout_ticks must be a positive integer or None")

    @property
    def busy(self) -> bool:
        return self._pending is not None

    def submit(self, request: ActionRequest) -> SimEvent:
        """Accept a prevalidated fictional request without claiming completion."""
        if not isinstance(request, ActionRequest) or not request.command_id:
            raise ValueError("ActionRequest with command_id required")
        if request.command_id in self._seen:
            return SimEvent(request.command_id, SimStatus.REJECTED, "duplicate_command_id")
        self._seen.add(request.command_id)
        if not isinstance(request.action, str) or not isinstance(request.hole_id, str):
            return SimEvent(request.command_id, SimStatus.REJECTED, "invalid_request")
        if request.action == "cancel":
            if (self._pending is None or request.target_command_id is None
                    or self._pending.request.command_id != request.target_command_id
                    or self._pending.request.hole_id != request.hole_id
                    or self._pending.cancellation_requested):
                return SimEvent(request.command_id, SimStatus.REJECTED, "no_matching_action")
            self._pending.cancellation_requested = True
            return SimEvent(request.command_id, SimStatus.ACCEPTED, "cancel_requested")
        if self._pending is not None:
            return SimEvent(request.command_id, SimStatus.REJECTED, "simulator_busy")
        hole = next((h for h in self.plan.holes if h.id == request.hole_id), None)
        if hole is None or hole.blocked:
            return SimEvent(request.command_id, SimStatus.REJECTED, "invalid_hole")
        expected_method = "brazo" if request.action.endswith("brazo") else "manguera"
        if request.action in {"extender_brazo", "retraer_brazo", "extender_manguera", "retraer_manguera"}:
            if hole.delivery_method != expected_method:
                return SimEvent(request.command_id, SimStatus.REJECTED, "wrong_method")
        elif request.action == "iniciar_carga":
            if request.product != hole.product or request.planned_kg != hole.planned_kg:
                return SimEvent(request.command_id, SimStatus.REJECTED, "plan_mismatch")
        else:
            return SimEvent(request.command_id, SimStatus.REJECTED, "unknown_action")
        self._pending = _Pending(request, self.delay_ticks)
        return SimEvent(request.command_id, SimStatus.ACCEPTED)

    def tick(self) -> SimEvent | None:
        """Advance one deterministic injected-clock tick; no wall-clock or hardware use."""
        pending = self._pending
        if pending is None:
            return None
        if pending.cancellation_requested:
            self._pending = None
            return SimEvent(pending.request.command_id, SimStatus.CANCELLED)
        if not pending.started:
            pending.started = True
            return SimEvent(pending.request.command_id, SimStatus.IN_PROGRESS)
        pending.elapsed_ticks += 1
        if self.timeout_ticks is not None and pending.elapsed_ticks >= self.timeout_ticks:
            self._pending = None
            return SimEvent(pending.request.command_id, SimStatus.TIMEOUT, "simulator_timeout")
        if pending.ticks_left > 0:
            pending.ticks_left -= 1
            return None
        self._pending = None
        if pending.request.action in self.fail_actions:
            return SimEvent(pending.request.command_id, SimStatus.FAILED, "injected_failure")
        return SimEvent(pending.request.command_id, SimStatus.COMPLETED)
