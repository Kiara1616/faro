from faro.domain import State
from faro.web import WebConsole


def prepare_hole_101(console: WebConsole) -> None:
    for command in (
        "seleccionar taladro 101",
        "consultar taladro 101",
        "preparar carga",
        "validar producto alfa 100 kilos",
    ):
        result = console.execute_command(command)
        assert result["operation"]["state"] == console.controller.domain.state.value


def test_tablet_console_guides_and_confirms_simulated_movement(tmp_path):
    console = WebConsole.create(audit_path=tmp_path / "tablet.sqlite3")
    initial = console.snapshot()
    assert initial["suggestion"]["command"] == "seleccionar taladro 101"
    assert initial["operation"]["hole_id"] is None

    prepare_hole_101(console)
    assert console.snapshot()["suggestion"]["command"] == "extender brazo"
    assert console.snapshot()["scenario"]["zone_clear"] is False
    console.set_zone_clear(True)
    pending = console.execute_command("extender brazo")
    assert pending["confirmation"]["hole_id"] == "101"
    assert console.controller.simulator.busy is False

    running = console.execute_command("confirmar")
    assert running["operation"]["state"] == State.MOVIMIENTO_EN_CURSO.value
    assert console.controller.simulator.busy is True
    for _ in range(4):
        console.last_tick_at -= 1
        console.advance_if_due(interval=0.1)
        if not console.controller.simulator.busy:
            break
    assert console.controller.domain.state is State.POSICIONADO
    assert console.snapshot()["history"][-1]["title"] == "Acción completada"


def test_zone_occupied_scenario_cannot_be_overridden_from_tablet(tmp_path):
    console = WebConsole.create(
        audit_path=tmp_path / "occupied.sqlite3",
        scenario_name="zona_ocupada",
    )
    prepare_hole_101(console)
    zone = console.set_zone_clear(True)
    assert zone["scenario"]["zone_clear_available"] is False
    assert zone["scenario"]["zone_clear"] is False

    rejected = console.execute_command("extender brazo")
    assert rejected["operation"]["state"] == State.PREPARADO.value
    assert rejected["history"][-1]["accepted"] is False
    assert console.controller.simulator.busy is False
