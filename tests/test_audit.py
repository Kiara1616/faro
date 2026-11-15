import sqlite3

import pytest

from faro.audit import AuditStore


def record(store, command_id="cmd-1"):
    return store.record_decision(
        command_id=command_id, session_id="session-1", operator_label="operador de prueba",
        source="voice", transcript="extender brazo", intent="extender_brazo", hole_id="101",
        state_before="preparado", state_after="movimiento_en_curso", accepted=True,
        decision="submitted", reason="submitted", timestamp="2026-11-04T10:00:00+00:00",
    )


def test_decision_and_event_survive_restart_without_audio(tmp_path):
    path = tmp_path / "audit.sqlite3"
    store = AuditStore(path)
    command_id = record(store)
    store.record_event(command_id, "in_progress")
    store.record_event(command_id, "completed", "simulator_completed")
    reopened = AuditStore(path)
    rows = reopened.list_records(command_id)
    assert len(rows) == 3
    row = rows[-1]
    assert row["session_id"] == "session-1"
    assert row["operator_label"] == "operador de prueba"
    assert row["event_status"] == "completed"
    assert "audio" not in row and "wav" not in row


def test_unknown_event_command_is_rejected(tmp_path):
    with pytest.raises(KeyError):
        AuditStore(tmp_path / "audit.sqlite3").record_event("missing", "completed")


def test_rejection_keeps_reason_and_state_transition(tmp_path):
    store = AuditStore(tmp_path / "audit.sqlite3")
    store.record_decision(
        command_id="reject-1", session_id="session-1", operator_label="operador de prueba",
        source="voice", transcript="iniciar carga", intent="iniciar_carga", hole_id="101",
        state_before="preparado", state_after="preparado", accepted=False,
        decision="rejected", reason="plan_mismatch",
    )
    row = store.list_records("reject-1")[0]
    assert row["accepted"] == 0
    assert row["state_before"] == row["state_after"] == "preparado"
    assert row["reason"] == "plan_mismatch"


def test_legacy_decisions_are_migrated_once(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE decisions (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, transcript TEXT NOT NULL, intent TEXT NOT NULL, accepted INTEGER NOT NULL, decision TEXT NOT NULL, step INTEGER NOT NULL, source TEXT NOT NULL DEFAULT 'text')")
        db.execute("INSERT INTO decisions(timestamp,transcript,intent,accepted,decision,step,source) VALUES(?,?,?,?,?,?,?)", ("2026-11-04T10:00:00+00:00", "mostrar estado", "mostrar_estado", 1, "ok", 0, "text"))
    store = AuditStore(path)
    assert len(store.list_records()) == 1
    AuditStore(path)
    assert len(store.list_records()) == 1
    assert store.list_records()[0]["command_id"].startswith("legacy-")
