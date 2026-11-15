"""Run Faro's deterministic normal and injected-failure demo scenarios offline."""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from faro.controller import FaroController
from faro.domain import State
from faro.plan import load_demo_plan
from faro.scenarios import load_scenarios


def _accept(controller: FaroController, text: str, **kwargs):
    result = controller.process(text, **kwargs)
    if result.decision is None or not result.decision.accepted:
        raise AssertionError(f"Rejected demo command: {text}: {result.decision}")
    return result


def _confirm(controller: FaroController) -> None:
    _accept(controller, "confirmar")


def _drain(controller: FaroController) -> None:
    guard = 20
    while controller.simulator.busy and guard:
        controller.tick()
        guard -= 1
    if controller.simulator.busy:
        raise AssertionError("Simulator did not reach a terminal event")


def _prepare(controller: FaroController, hole: str, validation: str) -> None:
    _accept(controller, f"seleccionar taladro {hole}")
    _accept(controller, f"consultar taladro {hole}")
    _accept(controller, "preparar carga")
    _accept(controller, validation)


def _run_normal(plan, scenarios) -> dict:
    with tempfile.TemporaryDirectory(prefix="faro-normal-") as folder:
        controller = FaroController.create(plan, Path(folder) / "audit.sqlite3",
                                           scenario=scenarios["normal"])
        _prepare(controller, "101", "validar producto alfa, cien kilos")
        _accept(controller, "extender brazo", zone_clear=True)
        _confirm(controller); _drain(controller)
        _accept(controller, "iniciar carga"); _confirm(controller); _drain(controller)
        _accept(controller, "retraer brazo"); _confirm(controller); _drain(controller)
        _accept(controller, "cerrar taladro"); _accept(controller, "siguiente taladro")
        _prepare(controller, "102", "validar producto beta, ciento veinte kilos")
        _accept(controller, "extender manguera", zone_clear=True)
        _confirm(controller); _drain(controller)
        _accept(controller, "iniciar carga"); _confirm(controller); _drain(controller)
        _accept(controller, "retraer manguera"); _confirm(controller); _drain(controller)
        _accept(controller, "cerrar taladro")
        rows = controller.audit.list_records()
        report = {"scenario": "normal", "state": controller.domain.state.value,
                "completed_holes": sorted(controller.domain.completed_holes),
                "event_count": len(rows),
                "terminal_events": [row["event_status"] for row in rows
                                     if row["event_status"] in {"completed", "failed", "timeout"}]}
        del controller
        gc.collect()
        return report


def _run_failure(plan, scenarios) -> dict:
    with tempfile.TemporaryDirectory(prefix="faro-failure-") as folder:
        controller = FaroController.create(plan, Path(folder) / "audit.sqlite3",
                                           scenario=scenarios["fallo_brazo"])
        _prepare(controller, "101", "validar producto alfa, cien kilos")
        _accept(controller, "extender brazo", zone_clear=True)
        _confirm(controller); _drain(controller)
        rows = controller.audit.list_records()
        report = {"scenario": "fallo_brazo", "state": controller.domain.state.value,
                "completed_holes": sorted(controller.domain.completed_holes),
                "failed": controller.domain.state is State.FALLO,
                "terminal_events": [row["event_status"] for row in rows
                                     if row["event_status"] in {"completed", "failed", "timeout"}]}
        del controller
        gc.collect()
        return report


def verify(root: Path = ROOT) -> dict:
    plan = load_demo_plan(root / "fixtures" / "malla_demo.json")
    scenarios = load_scenarios(root / "fixtures" / "escenarios_demo.json")
    normal = _run_normal(plan, scenarios)
    failure = _run_failure(plan, scenarios)
    if normal["state"] != "cerrado" or normal["completed_holes"] != ["101", "102"]:
        raise AssertionError(f"Unexpected normal result: {normal}")
    if normal["terminal_events"] != ["completed"] * 6:
        raise AssertionError(f"Normal scenario did not complete six expected actions: {normal}")
    if not failure["failed"]:
        raise AssertionError(f"Unexpected failure result: {failure}")
    if failure["terminal_events"] != ["failed"]:
        raise AssertionError(f"Failure scenario did not produce one failed terminal event: {failure}")
    return {"simulation_only": True, "normal": normal, "failure": failure}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica escenarios Faro sin red ni hardware.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = verify()
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else
          "Escenarios Faro OK: normal=2 taladros, fallo=fallo controlado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
