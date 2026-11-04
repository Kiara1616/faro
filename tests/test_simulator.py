from pathlib import Path

from faro.domain import ActionRequest, Command, EventStatus, FaroDomain, Intent, State
from faro.plan import load_demo_plan
from faro.simulator import SimStatus, SimulatedMMU


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json"


def ready():
    plan = load_demo_plan(FIXTURE)
    domain = FaroDomain(plan)
    for command in (
        Command(Intent.SELECCIONAR_TALADRO, hole_id="101"),
        Command(Intent.CONSULTAR_TALADRO, hole_id="101"),
        Command(Intent.PREPARAR_CARGA),
        Command(Intent.DECLARAR_PLAN, product="producto alfa", kg=100),
    ):
        assert domain.handle(command).accepted
    return domain, SimulatedMMU(plan, delay_ticks=2)


def test_acceptance_progress_and_completion_are_distinct():
    domain, simulator = ready()
    decision = domain.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True))
    assert simulator.submit(decision.request).status is SimStatus.ACCEPTED
    assert domain.state is State.MOVIMIENTO_EN_CURSO
    progress = simulator.tick()
    assert progress.status is SimStatus.IN_PROGRESS
    assert domain.apply_event(progress.command_id, EventStatus.IN_PROGRESS)
    assert simulator.tick() is None
    assert simulator.tick() is None
    assert domain.state is State.MOVIMIENTO_EN_CURSO
    final = simulator.tick()
    assert final.status is SimStatus.COMPLETED
    assert domain.apply_event(final.command_id, EventStatus.COMPLETED)
    assert domain.state is State.POSICIONADO
    assert simulator.tick() is None


def test_duplicate_wrong_id_and_busy_requests_do_not_complete():
    domain, simulator = ready()
    request = domain.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True)).request
    assert simulator.submit(request).status is SimStatus.ACCEPTED
    assert simulator.submit(request).status is SimStatus.REJECTED
    other = ActionRequest("unrelated", "102", "extender_manguera")
    assert simulator.submit(other).status is SimStatus.REJECTED
    assert not domain.apply_event("unrelated", EventStatus.COMPLETED)
    assert domain.state is State.MOVIMIENTO_EN_CURSO


def test_injected_failure_and_cancellation():
    domain, simulator = ready()
    simulator.fail_actions = frozenset({"extender_brazo"})
    request = domain.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True)).request
    assert simulator.submit(request).status is SimStatus.ACCEPTED
    assert simulator.tick().status is SimStatus.IN_PROGRESS
    assert simulator.tick() is None
    assert simulator.tick() is None
    failed = simulator.tick()
    assert failed.status is SimStatus.FAILED
    assert domain.apply_event(failed.command_id, EventStatus.FAILED)
    assert domain.state is State.FALLO

    other, second_simulator = ready()
    active = other.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True)).request
    assert second_simulator.submit(active).status is SimStatus.ACCEPTED
    wrong_hole_cancel = ActionRequest("wrong-hole-cancel", "102", "cancel", target_command_id=active.command_id)
    assert second_simulator.submit(wrong_hole_cancel).status is SimStatus.REJECTED
    assert second_simulator.busy
    pause = other.handle(Command(Intent.PAUSAR)).request
    assert second_simulator.submit(pause).status is SimStatus.ACCEPTED
    cancelled = second_simulator.tick()
    assert cancelled.status is SimStatus.CANCELLED
    assert other.apply_event(cancelled.command_id, EventStatus.CANCELLED)
    assert other.state is State.FALLO


def test_simulator_rejects_invalid_load_plan():
    _, simulator = ready()
    invalid = ActionRequest("load-1", "101", "iniciar_carga", product="producto beta", planned_kg=100)
    assert simulator.submit(invalid).status is SimStatus.REJECTED
    assert not simulator.busy
    malformed = ActionRequest("bad-action", "101", None)
    assert simulator.submit(malformed).status is SimStatus.REJECTED
    blocked = ActionRequest("blocked", "103", "extender_brazo")
    assert simulator.submit(blocked).status is SimStatus.REJECTED


def test_rejected_submission_reconciles_domain_without_false_completion():
    domain, simulator = ready()
    occupying = ActionRequest("other-active", "102", "extender_manguera")
    assert simulator.submit(occupying).status is SimStatus.ACCEPTED
    decision = domain.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True))
    assert decision.state_after is State.MOVIMIENTO_EN_CURSO
    rejected = simulator.submit(decision.request)
    assert rejected.status is SimStatus.REJECTED
    assert domain.reject_submission(rejected.command_id, rejected.reason)
    assert domain.state is State.FALLO
    assert domain.pending is None
    assert not domain.apply_event(rejected.command_id, EventStatus.COMPLETED)


def test_rejected_cancellation_keeps_result_unknown():
    domain, simulator = ready()
    action = domain.handle(Command(Intent.EXTENDER_BRAZO, zone_clear=True)).request
    # Simulate a lost initial request: the adapter cannot find it to cancel.
    pause = domain.handle(Command(Intent.PAUSAR)).request
    rejected = simulator.submit(pause)
    assert rejected.status is SimStatus.REJECTED
    assert domain.reject_cancellation(action.command_id, rejected.reason)
    assert domain.state is State.RESULTADO_DESCONOCIDO
    assert domain.pending is None
    assert not domain.apply_event(action.command_id, EventStatus.COMPLETED)
