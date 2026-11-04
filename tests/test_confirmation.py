import pytest

from faro.confirmation import ConfirmationGate


def requested(gate, **overrides):
    values = dict(token="c1", session_id="s1", mode="manual", hole_id="101",
                  action="extender_brazo", product="producto alfa",
                  planned_kg=100, now=0.0)
    values.update(overrides)
    return gate.request(**values)


def test_confirmation_requires_same_context_and_is_single_use():
    gate = ConfirmationGate()
    requested(gate)
    assert gate.confirm(token="c1", session_id="s1", mode="manual", hole_id="102",
                       action="extender_brazo", product="producto alfa", planned_kg=100,
                       now=1.0) == (False, "confirmation_context_changed")
    assert gate.confirm(token="c1", session_id="s1", mode="manual", hole_id="101",
                       action="extender_brazo", product="producto alfa", planned_kg=100,
                       now=1.0) == (True, "confirmed")
    assert gate.pending is None


def test_confirmation_expires_and_duplicate_confirm_does_not_replay():
    gate = ConfirmationGate(ttl_seconds=2)
    requested(gate)
    args = dict(token="c1", session_id="s1", mode="manual", hole_id="101",
                action="extender_brazo", product="producto alfa", planned_kg=100)
    assert gate.confirm(**args, now=2.0) == (False, "confirmation_expired")
    assert gate.confirm(**args, now=2.1) == (False, "no_confirmation_pending")


def test_cancel_discards_confirmation_without_authorizing():
    gate = ConfirmationGate()
    requested(gate)
    assert gate.cancel() is True
    assert gate.cancel() is False


def test_invalid_ttl_is_rejected():
    with pytest.raises(ValueError):
        ConfirmationGate(ttl_seconds=0)
