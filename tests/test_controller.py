from pathlib import Path
import time

from faro.controller import FaroController
from faro.domain import Mode, Source, State
from faro.plan import load_demo_plan
from faro.scenarios import load_scenarios


PLAN = load_demo_plan(Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json")


def complete(controller):
    while controller.simulator.busy:
        event = controller.tick()
        if event is not None and event.status.value in {"completed", "failed", "cancelled"}:
            return event


def confirm(controller):
    result = controller.process("confirmar")
    assert result.decision is not None and result.decision.accepted
    assert result.decision.state_after is controller.domain.state
    return result


def test_controller_completes_two_holes_and_audits_events(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    commands = ["seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                "validar producto alfa, cien kilos"]
    for text in commands:
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    confirm(controller)
    complete(controller)
    assert controller.domain.state is State.POSICIONADO
    assert controller.process("iniciar carga").decision.accepted
    confirm(controller)
    complete(controller)
    assert controller.process("retraer brazo").decision.accepted
    confirm(controller)
    complete(controller)
    assert controller.process("cerrar taladro").decision.accepted
    assert controller.process("siguiente taladro").decision.accepted
    for text in ("seleccionar taladro 102", "consultar taladro 102", "preparar carga",
                 "validar producto beta, ciento veinte kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender manguera", zone_clear=True).decision.accepted
    confirm(controller)
    complete(controller)
    rows = controller.audit.list_records()
    assert any(row["event_status"] == "completed" for row in rows)
    assert all(row["session_id"] == "demo-session" for row in rows)


def test_rejected_order_never_reaches_simulator_or_marks_success(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    result = controller.process("iniciar carga")
    assert result.decision is not None and not result.decision.accepted
    assert not controller.simulator.busy
    assert controller.domain.state is State.SIN_SELECCION
    row = controller.audit.list_records()[-1]
    assert row["accepted"] == 0 and row["event_status"] is None


def test_voice_controller_uses_same_rules(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    assert controller.domain.set_mode(controller.session_id, Mode.VOZ)
    assert controller.domain.set_listening(controller.session_id, True)
    generation = controller.domain.session.generation
    result = controller.process("Oye Faro, consultar estado", source=Source.VOICE, generation=generation)
    assert result.decision.accepted


def test_controller_timeout_is_audited_and_never_replayed(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    controller.simulator.timeout_ticks = 1
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    confirm(controller)
    assert controller.tick().status.value == "in_progress"
    timeout = controller.tick()
    assert timeout.status.value == "timeout"
    assert controller.domain.state is State.RESULTADO_DESCONOCIDO
    assert controller.tick() is None
    assert any(row["event_status"] == "timeout" for row in controller.audit.list_records())


def test_restart_after_timeout_does_not_replay_or_infer_success(tmp_path):
    audit_path = tmp_path / "audit.sqlite3"
    controller = FaroController.create(PLAN, audit_path)
    controller.simulator.timeout_ticks = 1
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    confirm(controller)
    assert controller.tick().status.value == "in_progress"
    assert controller.tick().status.value == "timeout"
    restarted = FaroController.create(PLAN, audit_path)
    assert restarted.simulator.busy is False
    assert restarted.domain.state is State.SIN_SELECCION
    assert restarted.tick() is None


def test_unknown_result_requires_explicit_manual_recovery(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    controller.simulator.timeout_ticks = 1
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    confirm(controller)
    controller.tick()
    assert controller.tick().status.value == "timeout"
    assert controller.recover_unknown("operator_review")
    assert controller.domain.state is State.FALLO
    assert controller.recover_unknown() is False
    assert any(row["event_status"] == "recovered" for row in controller.audit.list_records())


def test_controller_scenario_is_visible_and_isolated(tmp_path):
    scenarios = load_scenarios(Path(__file__).resolve().parents[1] / "fixtures" / "escenarios_demo.json")
    failed = FaroController.create(PLAN, tmp_path / "failed.sqlite3", scenario=scenarios["fallo_brazo"])
    normal = FaroController.create(PLAN, tmp_path / "normal.sqlite3", scenario=scenarios["normal"])
    assert failed.scenario_name == "fallo_brazo"
    assert normal.scenario_name == "normal"
    assert failed.simulator.fail_actions != normal.simulator.fail_actions
    assert normal.simulator.busy is False


def test_critical_action_waits_for_confirmation_and_cancel_never_submits(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "confirmation.sqlite3")
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    result = controller.process("extender brazo", zone_clear=True)
    assert result.decision.accepted
    assert controller.domain.state is State.CONFIRMACION_PENDIENTE
    assert result.decision.state_after is State.CONFIRMACION_PENDIENTE
    assert controller.confirmation_pending
    assert controller.simulator.busy is False
    cancelled = controller.process("cancelar")
    assert cancelled.decision.accepted
    assert not controller.confirmation_pending
    assert controller.simulator.busy is False
    assert any(row["event_status"] == "confirmation_cancelled"
               for row in controller.audit.list_records())


def test_confirmation_expires_without_execution(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "expiry.sqlite3")
    controller.confirmation_ttl = 0.001
    controller.confirmation_gate.ttl_seconds = 0.001
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    time.sleep(0.05)
    expired = controller.process("confirmar")
    assert expired.decision is not None and not expired.decision.accepted
    assert expired.decision.reason == "confirmation_expired"
    assert controller.simulator.busy is False


def test_duplicate_confirmation_is_single_use_and_audited(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "duplicate.sqlite3")
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    result = controller.process("extender brazo", zone_clear=True)
    command_id = result.decision.command_id
    confirm(controller)
    duplicate = controller.process("confirmar")
    assert duplicate.decision is not None and not duplicate.decision.accepted
    assert duplicate.decision.reason == "no_confirmation_pending"
    events = [row["event_status"] for row in controller.audit.list_records(command_id)]
    assert events.count("confirmation_pending") == 1
    assert events.count("confirmation_accepted") == 1


def test_live_context_change_rejects_confirmation(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "context.sqlite3")
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    result = controller.process("extender brazo", zone_clear=True)
    command_id = result.decision.command_id
    controller.domain.selected_hole_id = "102"  # hostile/stale context simulation
    rejected = controller.process("confirmar")
    assert rejected.decision is not None and not rejected.decision.accepted
    assert rejected.decision.reason == "confirmation_context_changed"
    assert controller.simulator.busy is False
    assert any(row["event_status"] == "confirmation_context_changed"
               for row in controller.audit.list_records(command_id))


def test_authorization_failure_fails_closed(tmp_path, monkeypatch):
    controller = FaroController.create(PLAN, tmp_path / "authorize.sqlite3")
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    result = controller.process("extender brazo", zone_clear=True)
    monkeypatch.setattr(controller.domain, "authorize_pending_action", lambda _: False)
    rejected = controller.process("confirmar")
    assert rejected.decision is not None and not rejected.decision.accepted
    assert rejected.decision.reason == "confirmation_authorization_failed"
    assert controller.simulator.busy is False


def test_pause_during_confirmation_cancels_pending_without_simulator_request(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "pause-confirmation.sqlite3")
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    pending = controller.process("extender brazo", zone_clear=True)
    command_id = pending.decision.command_id
    paused = controller.process("pausar")
    assert paused.decision is not None and paused.decision.accepted
    assert paused.decision.reason == "confirmation_cancelled_by_pause"
    assert controller.domain.state is State.PREPARADO
    assert controller.domain.pending is None
    assert controller.confirmation_pending is False
    assert controller.simulator.busy is False
    events = [row["event_status"] for row in controller.audit.list_records(command_id)]
    assert "confirmation_cancelled" in events


def test_stale_voice_control_cannot_confirm_pending_action(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "stale-control.sqlite3")
    assert controller.domain.set_mode(controller.session_id, Mode.VOZ)
    assert controller.domain.set_listening(controller.session_id, True)
    generation = controller.domain.session.generation
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text, source=Source.VOICE, generation=generation).decision.accepted
    pending = controller.process("extender brazo", source=Source.VOICE,
                                  generation=generation, zone_clear=True)
    assert pending.decision.accepted
    assert controller.domain.set_listening(controller.session_id, False)
    assert controller.domain.set_listening(controller.session_id, True)
    stale = controller.process("confirmar", source=Source.VOICE, generation=generation)
    assert stale.decision is not None and not stale.decision.accepted
    assert stale.decision.reason == "stale_listening_generation"
    assert controller.confirmation_pending
    assert controller.simulator.busy is False


def test_controller_audit_includes_selected_scenario(tmp_path):
    scenarios = load_scenarios(Path(__file__).resolve().parents[1] / "fixtures" / "escenarios_demo.json")
    controller = FaroController.create(PLAN, tmp_path / "scenario.sqlite3", scenario=scenarios["fallo_brazo"])
    for text in ("seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                 "validar producto alfa, cien kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    confirm(controller)
    for _ in range(4):
        controller.tick()
    rows = controller.audit.list_records()
    assert any(row["event_status"] == "failed" and "scenario=fallo_brazo" in row["reason"] for row in rows)
