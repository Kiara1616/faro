import copy
import json
from pathlib import Path

import pytest

from faro.plan import load_demo_plan


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json"


def test_demo_plan_is_reproducible_and_fictional():
    first = load_demo_plan(FIXTURE)
    assert first == load_demo_plan(FIXTURE)
    assert [hole.id for hole in first.holes] == ["101", "102", "103"]
    assert first.holes[1].delivery_method == "manguera"
    assert first.holes[2].blocked is True


@pytest.mark.parametrize(
    "change",
    [
        lambda data: data["holes"][1].update(id="101"),
        lambda data: data["holes"][0].pop("planned_kg"),
        lambda data: data["holes"][0].update(planned_kg=-1),
        lambda data: data["holes"][0].update(planned_kg=True),
        lambda data: data["holes"][0].update(delivery_method="radio"),
        lambda data: data["holes"][0].update(product=["producto alfa"]),
        lambda data: data["holes"][0].update(delivery_method=["brazo"]),
        lambda data: data.update(simulation_only=False),
    ],
)
def test_malformed_plan_is_rejected_before_use(tmp_path, change):
    data = copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
    change(data)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_demo_plan(path)


def test_plan_requires_normal_discrepancy_and_blocked_cases(tmp_path):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["holes"][1]["scenario"] = "normal"
    path = tmp_path / "missing-discrepancy.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="discrepancy"):
        load_demo_plan(path)

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for hole in data["holes"]:
        hole["blocked"] = False
    path = tmp_path / "missing-blocked.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="blocked"):
        load_demo_plan(path)
