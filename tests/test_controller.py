from pathlib import Path

from faro.controller import FaroController
from faro.domain import Mode, Source, State
from faro.plan import load_demo_plan


PLAN = load_demo_plan(Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json")


def complete(controller):
    while controller.simulator.busy:
        event = controller.tick()
        if event is not None and event.status.value in {"completed", "failed", "cancelled"}:
            return event


def test_controller_completes_two_holes_and_audits_events(tmp_path):
    controller = FaroController.create(PLAN, tmp_path / "audit.sqlite3")
    commands = ["seleccionar taladro 101", "consultar taladro 101", "preparar carga",
                "validar producto alfa, cien kilos"]
    for text in commands:
        assert controller.process(text).decision.accepted
    assert controller.process("extender brazo", zone_clear=True).decision.accepted
    complete(controller)
    assert controller.domain.state is State.POSICIONADO
    assert controller.process("iniciar carga").decision.accepted
    complete(controller)
    assert controller.process("retraer brazo").decision.accepted
    complete(controller)
    assert controller.process("cerrar taladro").decision.accepted
    assert controller.process("siguiente taladro").decision.accepted
    for text in ("seleccionar taladro 102", "consultar taladro 102", "preparar carga",
                 "validar producto beta, ciento veinte kilos"):
        assert controller.process(text).decision.accepted
    assert controller.process("extender manguera", zone_clear=True).decision.accepted
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
