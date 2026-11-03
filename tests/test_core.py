"""Meaningful state and rejection tests for the simulation-only engine."""

import sqlite3

from faro.core import FaroEngine


def test_complete_review_requires_inspection_at_each_step():
    engine = FaroEngine()
    assert engine.handle("iniciar revisión auxiliar").accepted
    assert not engine.handle("confirmar paso").accepted
    assert not engine.handle("consultar presión").accepted
    for name in ("temperatura", "presión", "batería"):
        decision = engine.handle(f"consultar {name}")
        assert decision.accepted
        assert "ficticio" in decision.message
        value, unit = {"temperatura": (42, "grados"), "presión": ("4,2", "bar"), "batería": (87, "por ciento")}[name]
        assert engine.handle(f"registrar {name} {value} {unit}").accepted
        assert engine.handle("confirmar paso").accepted
    snapshot = engine.snapshot()
    assert snapshot["workflow"]["completed"]
    assert not snapshot["workflow"]["active"]


def test_unsupported_and_ambiguous_commands_do_not_change_state():
    engine = FaroEngine()
    before = engine.snapshot()["workflow"]
    for phrase in ("", "activar bomba", "disparar", "mostrar", "consultar temperatura y presión"):
        result = engine.handle(phrase)
        assert not result.accepted
        assert engine.snapshot()["workflow"] == before
    assert len(engine.snapshot()["history"]) == 5


def test_spoken_invocation_keeps_command_validation_and_original_audit():
    engine = FaroEngine()
    accepted = engine.handle("Oye Faro, mostrar estado", source="voice")
    assert accepted.accepted
    assert accepted.transcript == "Oye Faro, mostrar estado"
    assert engine.history[-1]["source"] == "voice"
    assert engine.handle("Faro, iniciar revisión auxiliar").accepted
    assert not engine.handle("Oye Faro, activar bomba").accepted
    assert not engine.handle("Oye Faro").accepted


def test_stale_reading_blocks_confirmation_even_after_inspection():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    assert engine.handle("consultar temperatura").accepted
    assert engine.handle("registrar temperatura 42 grados").accepted
    engine.indicators["temperatura"]["status"] = "obsoleto"
    assert not engine.handle("confirmar paso").accepted
    assert engine.snapshot()["workflow"]["step"] == 1


def test_cancel_resets_workflow_without_clearing_audit_history():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    engine.handle("consultar temperatura")
    decision = engine.handle("cancelar revisión")
    assert decision.accepted
    assert not decision.snapshot["workflow"]["active"]
    assert decision.snapshot["view"] == "estado"
    assert len(decision.snapshot["history"]) == 3


def test_discrepancy_blocks_step_and_ambiguous_value_is_not_recorded():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    engine.handle("consultar temperatura")
    ambiguous = engine.handle("registrar temperatura 40 o 42 grados")
    assert not ambiguous.accepted
    assert not engine.snapshot()["workflow"]["recorded"]
    mismatch = engine.handle("registrar temperatura 55 grados")
    assert not mismatch.accepted
    assert "Discrepancia" in mismatch.message
    assert engine.snapshot()["workflow"]["requires_human"]
    assert not engine.handle("confirmar paso").accepted
    assert engine.snapshot()["workflow"]["step"] == 1


def test_optional_sqlite_audit_persists_decisions(tmp_path):
    database = tmp_path / "audit.sqlite3"
    engine = FaroEngine(db_path=database)
    engine.handle("iniciar revisión auxiliar")
    engine.handle("activar bomba")
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT transcript, accepted FROM decisions ORDER BY id").fetchall()
    assert rows == [("iniciar revisión auxiliar", 1), ("activar bomba", 0)]


def test_spoken_demo_numbers_equal_digit_forms_but_ambiguous_words_reject():
    pairs = (
        ("temperatura", "registrar temperatura 42 grados", "registrar temperatura cuarenta y dos grados"),
        ("presión", "registrar presión 4,2 bar", "registrar presión cuatro coma dos bar"),
        ("batería", "registrar batería 87 por ciento", "registrar batería ochenta y siete por ciento"),
    )
    for indicator, numeric, spoken in pairs:
        for phrase in (numeric, spoken):
            engine = FaroEngine()
            engine.handle("iniciar revisión auxiliar")
            for prior, prior_value in (("temperatura", "42 grados"), ("presión", "4,2 bar")):
                if prior == indicator:
                    break
                engine.handle(f"consultar {prior}")
                engine.handle(f"registrar {prior} {prior_value}")
                engine.handle("confirmar paso")
            engine.handle(f"consultar {indicator}")
            assert engine.handle(phrase).accepted
            assert engine.snapshot()["workflow"]["recorded"]

    engine = FaroEngine()
    engine.handle("iniciar revisión auxiliar")
    engine.handle("consultar temperatura")
    assert not engine.handle("registrar temperatura cuarenta y dos o tres grados").accepted
    assert not engine.snapshot()["workflow"]["recorded"]


def test_reference_change_after_consultation_requires_new_consultation():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    engine.handle("consultar temperatura")
    engine.indicators["temperatura"]["value"] = 43
    decision = engine.handle("registrar temperatura 43 grados")
    assert not decision.accepted
    assert "cambió" in decision.message
    assert not engine.snapshot()["workflow"]["inspected"]
    assert engine.handle("consultar temperatura").accepted
    assert engine.handle("registrar temperatura 43 grados").accepted
    engine.indicators["temperatura"]["updated_at"] = "nuevo dato"
    assert not engine.handle("confirmar paso").accepted
    assert not engine.snapshot()["workflow"]["recorded"]


def test_reconsultation_invalidates_previous_record():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    engine.handle("consultar temperatura")
    assert engine.handle("registrar temperatura 42 grados").accepted
    engine.indicators["temperatura"]["value"] = 50
    engine.indicators["temperatura"]["updated_at"] = "dato actualizado"
    assert engine.handle("consultar temperatura").accepted
    assert not engine.snapshot()["workflow"]["recorded"]
    assert not engine.handle("confirmar paso").accepted


def test_navigation_during_review_can_return_without_reset():
    engine = FaroEngine()
    engine.handle("iniciar revision auxiliar")
    engine.handle("consultar temperatura")
    engine.handle("mostrar indicadores")
    assert engine.snapshot()["view"] == "indicadores"
    decision = engine.handle("mostrar revision")
    assert decision.accepted
    assert decision.snapshot["view"] == "revision"
    assert decision.snapshot["workflow"]["inspected"]
    assert not engine.handle("iniciar revision auxiliar").accepted


def test_audit_step_and_source_persist_across_restart(tmp_path):
    database = tmp_path / "audit.sqlite3"
    engine = FaroEngine(db_path=database)
    engine.handle("iniciar revision auxiliar", source="voice")
    engine.handle("consultar temperatura", source="voice")
    engine.handle("registrar temperatura 42 grados", source="voice")
    engine.handle("confirmar paso", source="text")
    assert engine.history[-1]["step"] == 1
    assert engine.snapshot()["workflow"]["step"] == 2
    restarted = FaroEngine(db_path=database)
    assert len(restarted.history) == 4
    assert restarted.history[0]["source"] == "voice"
    assert restarted.history[-1]["source"] == "text"
    assert restarted.snapshot()["workflow"]["step"] == 0
