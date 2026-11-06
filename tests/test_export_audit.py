import json

from faro.audit import AuditStore
from scripts.export_audit import export_audit


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
