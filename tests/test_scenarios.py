from pathlib import Path

import pytest

from faro.plan import load_demo_plan
from faro.scenarios import build_simulator, load_scenarios
from faro.domain import ActionRequest
from faro.simulator import SimStatus


ROOT = Path(__file__).resolve().parents[1]


def test_scenarios_are_named_and_reproducible():
    scenarios = load_scenarios(ROOT / "fixtures" / "escenarios_demo.json")
    assert set(scenarios) == {"normal", "zona_ocupada", "fallo_brazo", "demora_timeout", "adaptador_lento"}
    plan = load_demo_plan(ROOT / "fixtures" / "malla_demo.json")
    a = build_simulator(plan, scenarios["demora_timeout"])
    b = build_simulator(plan, scenarios["demora_timeout"])
    assert (a.delay_ticks, a.timeout_ticks, a.fail_actions) == (b.delay_ticks, b.timeout_ticks, b.fail_actions)
    request = ActionRequest("cmd-1", "101", "extender_brazo")
    events = []
    for simulator in (a, b):
        assert simulator.submit(request).status is SimStatus.ACCEPTED
        sequence = []
        while simulator.busy:
            event = simulator.tick()
            if event is not None:
                sequence.append((event.status.value, event.reason))
        events.append(sequence)
    assert events[0] == events[1]


def test_scenario_loader_rejects_missing_normal(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text('{"schema_version": 1, "simulation_only": true, "scenarios": [{"name": "only_failure", "description": "x"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="normal"):
        load_scenarios(path)


def test_scenario_loader_rejects_nonfictional_header(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text('{"schema_version": 1, "simulation_only": false, "scenarios": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="fictional"):
        load_scenarios(path)
