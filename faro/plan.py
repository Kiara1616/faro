"""Versioned fictional blast-hole plan. No operational ORICA data."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Hole:
    id: str
    product: str
    planned_kg: int
    delivery_method: str
    blocked: bool
    scenario: str


@dataclass(frozen=True)
class DemoPlan:
    name: str
    holes: tuple[Hole, ...]


def load_demo_plan(path: str | Path) -> DemoPlan:
    """Reject malformed or non-fictional plans before any simulated operation."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "simulation_only", "name", "holes"}:
        raise ValueError("Invalid demo plan structure")
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise ValueError("Unsupported demo plan schema")
    if raw["simulation_only"] is not True:
        raise ValueError("Only fictional simulation plans are accepted")
    if not isinstance(raw["name"], str) or not raw["name"].strip():
        raise ValueError("Demo plan name is required")
    rows = raw["holes"]
    if not isinstance(rows, list) or len(rows) < 3:
        raise ValueError("Demo plan needs at least three holes")
    holes = []
    seen = set()
    required = {"id", "product", "planned_kg", "delivery_method", "blocked", "scenario"}
    for row in rows:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("Invalid hole structure")
        if not isinstance(row["id"], str) or not row["id"].isdigit() or row["id"] in seen:
            raise ValueError("Invalid or duplicate hole ID")
        seen.add(row["id"])
        if not isinstance(row["product"], str) or row["product"] not in {"producto alfa", "producto beta"}:
            raise ValueError("Unknown fictional product")
        if type(row["planned_kg"]) is not int or row["planned_kg"] <= 0:
            raise ValueError("Invalid planned kilograms")
        if not isinstance(row["delivery_method"], str) or row["delivery_method"] not in {"brazo", "manguera"}:
            raise ValueError("Invalid delivery method")
        if type(row["blocked"]) is not bool:
            raise ValueError("Invalid blocked flag")
        if not isinstance(row["scenario"], str) or not row["scenario"].strip():
            raise ValueError("Scenario is required")
        holes.append(Hole(**row))
    return DemoPlan(name=raw["name"].strip(), holes=tuple(holes))
