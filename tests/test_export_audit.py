import json

from faro.audit import AuditStore
from scripts.export_audit import export_audit
from scripts.clean_evidence import clean_evidence


def test_export_contains_decisions_but_no_audio(tmp_path):
    database = tmp_path / "audit.sqlite3"
    store = AuditStore(database)
    store.record_decision(command_id="c1", session_id="s1", operator_label="demo",
                          source="text", transcript="consultar estado", intent="consultar_estado",
                          hole_id=None, state_before="sin_seleccion", state_after="sin_seleccion",
                          accepted=True, decision="accepted", reason="read_only")
    output = tmp_path / "report.json"
    assert export_audit(database, output) == 1
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["simulation_only"] is True
    assert report["audio_included"] is False
    assert "audio" not in report["records"][0]


def test_export_redacts_operator_and_transcript(tmp_path):
    database = tmp_path / "audit.sqlite3"
    store = AuditStore(database)
    store.record_decision(command_id="c1", session_id="s1", operator_label="Ana",
                          source="text", transcript="frase privada", intent="x",
                          hole_id=None, state_before="a", state_after="a", accepted=False,
                          decision="rejected", reason="unknown")
    output = tmp_path / "redacted.json"
    export_audit(database, output, redact=True)
    record = json.loads(output.read_text(encoding="utf-8"))["records"][0]
    assert record["operator_label"] == "<operator-redacted>"
    assert record["transcript"] == "<transcript-redacted>"


def test_clean_evidence_removes_only_allowed_artifacts(tmp_path):
    for name in ("voice.wav", "audit.sqlite3", "run.log", "keep.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert set(clean_evidence(tmp_path)) == {"voice.wav", "audit.sqlite3", "run.log"}
    assert (tmp_path / "keep.txt").exists()
