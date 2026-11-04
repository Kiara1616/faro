"""Named, reproducible simulator scenarios for QA and demonstrations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from faro.plan import DemoPlan
from faro.simulator import SimulatedMMU


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    delay_ticks: int = 1
    timeout_ticks: int | None = None
    fail_actions: frozenset[str] = frozenset()


def load_scenarios(path: str | Path) -> dict[str, Scenario]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios: dict[str, Scenario] = {}
    for item in raw.get("scenarios", []):
        scenario = Scenario(
            name=item["name"], description=item["description"],
            delay_ticks=item.get("delay_ticks", 1),
            timeout_ticks=item.get("timeout_ticks"),
            fail_actions=frozenset(item.get("fail_actions", [])),
        )
        if scenario.name in scenarios:
            raise ValueError(f"duplicate scenario: {scenario.name}")
        scenarios[scenario.name] = scenario
    if "normal" not in scenarios:
        raise ValueError("scenario set must include normal")
    return scenarios


def build_simulator(plan: DemoPlan, scenario: Scenario) -> SimulatedMMU:
    return SimulatedMMU(plan, delay_ticks=scenario.delay_ticks,
                        timeout_ticks=scenario.timeout_ticks,
                        fail_actions=scenario.fail_actions)
