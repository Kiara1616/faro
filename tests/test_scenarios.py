from pathlib import Path

import pytest

from faro.plan import load_demo_plan
from faro.scenarios import build_simulator, load_scenarios
from faro.simulator import SimStatus


ROOT = Path(__file__).resolve().parents[1]


def test_scenarios_are_named_and_reproducible():
    scenarios = load_scenarios(ROOT / "fixtures" / "escenarios_demo.json")
    assert set(scenarios) == {"normal", "zona_ocupada", "fallo_brazo", "demora_timeout", "adaptador_lento"}
    plan = load_demo_plan(ROOT / "fixtures" / "malla_demo.json")
    a = build_simulator(plan, scenarios["demora_timeout"])
    b = build_simulator(plan, scenarios["demora_timeout"])
    assert (a.delay_ticks, a.timeout_ticks, a.fail_actions) == (b.delay_ticks, b.timeout_ticks, b.fail_actions)


def test_scenario_loader_rejects_missing_normal(tmp_path):
    path = tmp_path / "scenarios.json"
    path.write_text('{"scenarios": [{"name": "only_failure", "description": "x"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="normal"):
        load_scenarios(path)
