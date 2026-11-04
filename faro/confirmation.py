"""Deterministic confirmation gate for the Faro simulator.

This module is deliberately independent from Qt, ASR and industrial I/O. It
binds a confirmation to the session, mode, hole and plan fingerprint so a late
or duplicated confirmation cannot authorize a different action.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Confirmation:
    token: str
    session_id: str
    mode: str
    hole_id: str
    action: str
    product: str | None
    planned_kg: int | None
    expires_at: float


class ConfirmationGate:
    def __init__(self, *, ttl_seconds: float = 10.0) -> None:
        if type(ttl_seconds) not in (int, float) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = float(ttl_seconds)
        self.pending: Confirmation | None = None

    def request(self, *, token: str, session_id: str, mode: str, hole_id: str,
                action: str, product: str | None = None,
                planned_kg: int | None = None, now: float) -> Confirmation:
        if not all(isinstance(value, str) and value.strip() for value in
                   (token, session_id, mode, hole_id, action)):
            raise ValueError("confirmation identity fields are required")
        self.pending = Confirmation(token, session_id, mode, hole_id, action,
                                    product, planned_kg, now + self.ttl_seconds)
        return self.pending

    def cancel(self) -> bool:
        existed = self.pending is not None
        self.pending = None
        return existed

    def confirm(self, *, token: str, session_id: str, mode: str, hole_id: str,
                action: str, product: str | None = None,
                planned_kg: int | None = None, now: float) -> tuple[bool, str]:
        pending = self.pending
        if pending is None:
            return False, "no_confirmation_pending"
        if now >= pending.expires_at:
            self.pending = None
            return False, "confirmation_expired"
        if (token, session_id, mode, hole_id, action, product, planned_kg) != (
                pending.token, pending.session_id, pending.mode, pending.hole_id,
                pending.action, pending.product, pending.planned_kg):
            return False, "confirmation_context_changed"
        self.pending = None
        return True, "confirmed"
