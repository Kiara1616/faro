from pathlib import Path

from faro.domain import Command, EventStatus, FaroDomain, Intent, Mode, Source, State
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


def test_session_requires_explicit_start_and_rejects_voice_in_manual():
    domain = engine()
    assert domain.session_snapshot()["active"] is False
    command = Command(Intent.CONSULTAR_ESTADO)
    denied = domain.handle_input(command, source=Source.VOICE, session_id="missing")
    assert not denied.accepted and denied.reason == "invalid_session"
    assert domain.begin_session("demo-1", "operador de prueba", Mode.MANUAL)
    view = domain.session_snapshot()
    assert view["active"] and view["simulation_only"] and view["mode"] == "manual"
    denied = domain.handle_input(command, source=Source.VOICE, session_id="demo-1")
    assert not denied.accepted and denied.reason == "voice_disabled_in_manual"
    assert domain.state is State.SIN_SELECCION


def test_voice_mode_requires_explicit_listening_and_current_generation():
    domain = engine()
    assert domain.begin_session("demo-1", "operador de prueba", Mode.VOZ)
    denied = domain.handle_input(Command(Intent.CONSULTAR_ESTADO), source=Source.VOICE, session_id="demo-1", generation=0)
    assert not denied.accepted and denied.reason == "listening_disabled"
    assert domain.set_listening("demo-1", True)
    generation = domain.session.generation
    stale = domain.handle_input(Command(Intent.CONSULTAR_ESTADO), source=Source.VOICE, session_id="demo-1", generation=generation - 1)
    assert not stale.accepted and stale.reason == "stale_listening_generation"
    accepted = domain.handle_input(Command(Intent.CONSULTAR_ESTADO), source=Source.VOICE, session_id="demo-1", generation=generation)
    assert accepted.accepted
    assert domain.set_mode("demo-1", Mode.MANUAL)
    assert domain.session.listening is False
    assert not domain.set_listening("demo-1", True)


def test_mode_transfer_is_blocked_during_action_and_audited_afterwards():
    domain = engine()
    assert domain.begin_session("demo-1", "operador de prueba", Mode.MANUAL)
    # Build the domain cycle through the same explicit text channel used by UI tests.
    for command in (Command(Intent.SELECCIONAR_TALADRO, hole_id="101"),
                    Command(Intent.CONSULTAR_TALADRO, hole_id="101"),
                    Command(Intent.PREPARAR_CARGA),
                    Command(Intent.DECLARAR_PLAN, product="producto alfa", kg=100),):
        assert domain.handle_input(command, source=Source.TEXT, session_id="demo-1").accepted
    action = domain.handle_input(Command(Intent.EXTENDER_BRAZO, zone_clear=True), source=Source.TEXT, session_id="demo-1")
    assert action.accepted
    assert not domain.set_mode("demo-1", Mode.VOZ)
    assert domain.session.mode is Mode.MANUAL
    domain.apply_event(action.command_id, EventStatus.COMPLETED)
    assert domain.set_mode("demo-1", Mode.VOZ)
    assert domain.session.listening is False
    assert domain.session.transfers[-1][:2] == (Mode.MANUAL, Mode.VOZ)


def test_id_and_blocked_hole_alerts_are_transient_and_correctable():
    domain = engine()
    operational = domain.snapshot()
    bad = send(domain, Intent.SELECCIONAR_TALADRO, hole_id="999")
    assert not bad.accepted and domain.snapshot() == operational
    assert bad.alert_after.received_hole_id == "999"
    assert not bad.alert_after.blocking
    blocked = send(domain, Intent.SELECCIONAR_TALADRO, hole_id="103")
    assert not blocked.accepted and domain.snapshot() == operational
    assert blocked.alert_after.reason == "hole_blocked"
    assert send(domain, Intent.SELECCIONAR_TALADRO, hole_id="101").accepted
    assert domain.alert is None
    wrong = send(domain, Intent.CONSULTAR_TALADRO, hole_id="102")
    assert not wrong.accepted and wrong.alert_after.expected_hole_id == "101"
    assert domain.state is State.SELECCIONADO
    corrected = send(domain, Intent.CONSULTAR_TALADRO, hole_id="101")
    assert corrected.accepted and corrected.alert_before.reason == "hole_mismatch"
    assert corrected.alert_after is None
    assert len(domain.alert_history) == 3


def test_missing_values_are_transient_but_plan_divergence_blocks_until_exact_retry():
    domain = engine()
    assert send(domain, Intent.SELECCIONAR_TALADRO, hole_id="101").accepted
    assert send(domain, Intent.CONSULTAR_TALADRO, hole_id="101").accepted
    assert send(domain, Intent.PREPARAR_CARGA).accepted
    operational = domain.snapshot()
    missing = send(domain, Intent.DECLARAR_PLAN, product="producto alfa")
    assert not missing.accepted and domain.snapshot() == operational
    assert missing.alert_after.reason == "invalid_plan_values"
    assert missing.alert_after.received_kg is None
    assert not missing.alert_after.blocking
    divergent = send(domain, Intent.DECLARAR_PLAN, product="producto beta", kg=101)
    assert not divergent.accepted and domain.snapshot() == operational
    alert = divergent.alert_after
    assert alert.blocking and not alert.requires_human
    assert (alert.expected_product, alert.expected_kg) == ("producto alfa", 100)
    assert (alert.received_product, alert.received_kg) == ("producto beta", 101)
    partial = send(domain, Intent.DECLARAR_PLAN, product="producto alfa")
    assert not partial.accepted and partial.alert_after == alert
    assert domain.alert.blocking
    denied = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True)
    assert not denied.accepted and denied.reason == "alert_pending"
    assert denied.request is None and domain.snapshot() == operational
    corrected = send(domain, Intent.DECLARAR_PLAN, product="producto alfa", kg=100)
    assert corrected.accepted and corrected.alert_before == alert
    assert corrected.alert_after is None and domain.pending is None
    assert domain.plan_validated
    assert send(domain, Intent.EXTENDER_BRAZO, zone_clear=True).request is not None


def test_method_mismatch_alert_does_not_authorize_movement_or_load():
    domain = engine()
    prepared(domain)
    before = domain.snapshot()
    wrong = send(domain, Intent.EXTENDER_MANGUERA, zone_clear=True)
    assert not wrong.accepted and domain.snapshot() == before
    assert wrong.alert_after.expected_method == "brazo"
    assert wrong.alert_after.received_method == "manguera"
    assert not wrong.alert_after.blocking
    assert not send(domain, Intent.INICIAR_CARGA).accepted
    right = send(domain, Intent.EXTENDER_BRAZO, zone_clear=True)
    assert right.accepted and right.alert_after is None
    complete(domain, right.request)
    complete(domain, send(domain, Intent.INICIAR_CARGA).request)
    before = domain.snapshot()
    wrong_retract = send(domain, Intent.RETRAER_MANGUERA)
    assert not wrong_retract.accepted and domain.snapshot() == before
    assert wrong_retract.alert_after.reason == "wrong_delivery_method"
    corrected_retract = send(domain, Intent.RETRAER_BRAZO)
    assert corrected_retract.request is not None
    assert corrected_retract.alert_after is None
