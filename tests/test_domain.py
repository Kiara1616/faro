from pathlib import Path

from faro.domain import Command, EventStatus, FaroDomain, Intent, State
from faro.plan import load_demo_plan


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json"


def engine():
    return FaroDomain(load_demo_plan(FIXTURE))


def send(domain, intent, **kwargs):
    return domain.handle(Command(intent, **kwargs))


def prepared(domain, hole="101", product="producto alfa", kg=100):
    assert send(domain, Intent.SELECCIONAR_TALADRO, hole_id=hole).accepted
    assert send(domain, Intent.CONSULTAR_TALADRO, hole_id=hole).accepted
    assert send(domain, Intent.PREPARAR_CARGA).accepted
    assert send(domain, Intent.DECLARAR_PLAN, product=product, kg=kg).accepted


def complete(domain, request):
    assert request is not None
    assert domain.apply_event(request.command_id, EventStatus.IN_PROGRESS)
    assert domain.apply_event(request.command_id, EventStatus.COMPLETED)


def test_complete_two_holes_with_correlated_events():
    domain = engine()
    prepared(domain)
    movement = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True)
    assert movement.state_before is State.PREPARADO
    assert movement.state_after is State.MOVIMIENTO_EN_CURSO
    assert movement.request.command_id == movement.command_id
    complete(domain, movement.request)
    assert domain.state is State.POSICIONADO
    load = send(domain, Intent.INICIAR_CARGA).request
    assert (load.product, load.planned_kg) == ("producto alfa", 100)
    complete(domain, load)
    complete(domain, send(domain, Intent.RETRAER_BRAZO).request)
    assert send(domain, Intent.CERRAR_TALADRO).accepted
    assert send(domain, Intent.SIGUIENTE_TALADRO).accepted
    assert domain.expected_next_hole_id == "102"
    prepared(domain, "102", "producto beta", 120)
    complete(domain, send(domain, Intent.EXTENDER_MANGUERA, zone_clear=True).request)
    complete(domain, send(domain, Intent.INICIAR_CARGA).request)
    complete(domain, send(domain, Intent.RETRAER_MANGUERA).request)
    assert send(domain, Intent.CERRAR_TALADRO).accepted
    assert domain.completed_holes == {"101", "102"}
    before = domain.snapshot()
    assert not send(domain, Intent.SIGUIENTE_TALADRO).accepted  # 103 is blocked.
    assert domain.snapshot() == before


def test_rejected_commands_do_not_mutate_operational_state():
    domain = engine()
    for command in (
        Command(Intent.PREPARAR_CARGA),
        Command(Intent.CONSULTAR_TALADRO, hole_id="101"),
        Command(Intent.SELECCIONAR_TALADRO, hole_id="999"),
    ):
        before = domain.snapshot()
        decision = domain.handle(command)
        assert not decision.accepted and domain.snapshot() == before
        assert decision.state_before is decision.state_after
    assert send(domain, Intent.SELECCIONAR_TALADRO, hole_id="101").accepted
    for command in (
        Command(Intent.SELECCIONAR_TALADRO, hole_id="102"),
        Command(Intent.CONSULTAR_TALADRO, hole_id="102"),
        Command(Intent.INICIAR_CARGA),
    ):
        before = domain.snapshot()
        decision = domain.handle(command)
        assert not decision.accepted and domain.snapshot() == before


def test_wrong_values_and_methods_cannot_start_action():
    domain = engine()
    assert send(domain, Intent.SELECCIONAR_TALADRO, hole_id="101").accepted
    assert send(domain, Intent.CONSULTAR_TALADRO, hole_id="101").accepted
    assert send(domain, Intent.PREPARAR_CARGA).accepted
    for values in ({"product": "producto beta", "kg": 100},
                   {"product": "producto alfa", "kg": 101},
                   {"product": "producto alfa", "kg": True}):
        before = domain.snapshot()
        assert not send(domain, Intent.DECLARAR_PLAN, **values).accepted
        assert domain.snapshot() == before
    assert not send(domain, Intent.EXTENDER_BRAZO).accepted
    assert send(domain, Intent.DECLARAR_PLAN, product="producto alfa", kg=100).accepted
    before = domain.snapshot()
    assert not send(domain, Intent.EXTENDER_BRAZO).accepted  # Missing fictional signal.
    assert domain.snapshot() == before
    for action in (Command(Intent.EXTENDER_MANGUERA),
                   Command(Intent.EXTENDER_BRAZO, zone_clear=False)):
        before = domain.snapshot()
        assert not domain.handle(action).accepted
        assert domain.snapshot() == before


def test_pending_action_rejects_duplicate_change_and_unrelated_event():
    domain = engine()
    prepared(domain)
    request = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request
    assert request is not None
    for command in (Command(Intent.EXTENDER_BRAZO),
                    Command(Intent.SELECCIONAR_TALADRO, hole_id="102"),
                    Command(Intent.INICIAR_CARGA)):
        before = domain.snapshot()
        decision = domain.handle(command)
        assert not decision.accepted and domain.snapshot() == before
    assert not domain.apply_event("another-command", EventStatus.COMPLETED)
    assert domain.state is State.MOVIMIENTO_EN_CURSO
    complete(domain, request)
    assert not domain.apply_event(request.command_id, EventStatus.COMPLETED)
    assert domain.state is State.POSICIONADO


def test_failed_or_cancelled_action_never_completes():
    domain = engine()
    prepared(domain)
    first = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request
    assert domain.apply_event(first.command_id, EventStatus.FAILED)
    assert domain.state is State.FALLO
    assert not send(domain, Intent.INICIAR_CARGA).accepted
    other = engine()
    prepared(other)
    second = send(other, Intent.EXTENDER_BRAZO, zone_clear=True).request
    pause = send(other, Intent.PAUSAR)
    assert pause.accepted and pause.request.target_command_id == second.command_id
    assert other.state is State.MOVIMIENTO_EN_CURSO
    assert other.apply_event(second.command_id, EventStatus.CANCELLED)
    assert other.state is State.FALLO
    assert not send(other, Intent.CERRAR_TALADRO).accepted


def test_completion_racing_with_pause_requires_reconciliation():
    domain = engine()
    prepared(domain)
    action = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request
    assert send(domain, Intent.PAUSAR).accepted
    assert domain.apply_event(action.command_id, EventStatus.COMPLETED)
    assert domain.state is State.RESULTADO_DESCONOCIDO
    assert not send(domain, Intent.INICIAR_CARGA).accepted


def test_simulator_submission_refusal_reconciles_only_matching_pending():
    domain = engine()
    prepared(domain)
    request = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request
    before = domain.snapshot()
    assert not domain.reject_submission("another-command", "simulator_busy")
    assert not domain.reject_submission(request.command_id, "")
    assert domain.snapshot() == before
    assert domain.reject_submission(request.command_id, "simulator_busy")
    assert domain.state is State.FALLO
    assert domain.last_failure_reason == "simulator_busy"
    assert domain.pending is None
    assert not domain.apply_event(request.command_id, EventStatus.COMPLETED)


def test_cancel_refusal_requires_reconciliation_and_ignores_late_completion():
    domain = engine()
    prepared(domain)
    request = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request
    assert send(domain, Intent.PAUSAR).accepted
    before = domain.snapshot()
    assert not domain.reject_cancellation("other-command", "no_matching_action")
    assert not domain.reject_cancellation(request.command_id, "")
    assert domain.snapshot() == before
    assert domain.reject_cancellation(request.command_id, "no_matching_action")
    assert domain.state is State.RESULTADO_DESCONOCIDO
    assert domain.last_failure_reason == "no_matching_action"
    assert domain.pending is None
    assert not domain.apply_event(request.command_id, EventStatus.COMPLETED)


def test_blocked_hole_and_skipping_next_hole_are_rejected():
    domain = engine()
    before = domain.snapshot()
    assert not send(domain, Intent.SELECCIONAR_TALADRO, hole_id="103").accepted
    assert domain.snapshot() == before

    ordered = engine()
    prepared(ordered)
    complete(ordered, send(ordered, Intent.EXTENDER_BRAZO, zone_clear=True).request)
    complete(ordered, send(ordered, Intent.INICIAR_CARGA).request)
    complete(ordered, send(ordered, Intent.RETRAER_BRAZO).request)
    assert send(ordered, Intent.CERRAR_TALADRO).accepted
    assert send(ordered, Intent.SIGUIENTE_TALADRO).accepted
    before = ordered.snapshot()
    assert not send(ordered, Intent.SELECCIONAR_TALADRO, hole_id="103").accepted
    assert ordered.snapshot() == before
