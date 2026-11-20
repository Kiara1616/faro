"""Build UI snapshots from the active simulator without depending on Qt."""

from __future__ import annotations

from typing import Any, Mapping

from faro.controller import FaroController
from faro.messages import state_label


def build_snapshot(controller: FaroController, ui_state: Mapping[str, Any]) -> dict[str, Any]:
    """Describe the current fictional operation for the desktop console."""
    domain = controller.domain
    hole = domain.selected_hole
    plan_rows = []
    for item in controller.plan.holes:
        if item.blocked:
            status = "bloqueado"
        elif item.id in domain.completed_holes:
            status = "completado"
        elif item.id == domain.selected_hole_id:
            status = "activo"
        else:
            status = "pendiente"
        plan_rows.append({
            "id": item.id, "product": item.product,
            "planned_kg": item.planned_kg,
            "delivery_method": item.delivery_method,
            "status": status, "scenario": item.scenario,
        })

    if hole is None:
        detail = "Seleccione un taladro de la malla ficticia para comenzar."
    else:
        detail = (f"Plan ficticio · {hole.product} · {hole.planned_kg} kg · "
                  f"entrega por {hole.delivery_method}.")
    if domain.alert is not None:
        detail = f"Revisión requerida · {domain.alert.reason}"

    state = domain.state.value
    return {
        "operation": {
            "hole_id": hole.id if hole else None,
            "product": hole.product if hole else None,
            "planned_kg": hole.planned_kg if hole else None,
            "delivery_method": hole.delivery_method if hole else None,
            "plan_validated": domain.plan_validated,
            "scenario": controller.scenario_name,
            "state": state,
        },
        "plan": plan_rows,
        "plan_name": controller.plan.name,
        "zone_clear": bool(ui_state["zone_clear"]) and controller.zone_clear_available,
        "zone_clear_enabled": (controller.zone_clear_available
                               and not controller.confirmation_pending
                               and domain.pending is None),
        "zone_clear_note": (
            "Escenario con zona ocupada: movimiento bloqueado."
            if not controller.zone_clear_available else
            "Condición ficticia, sin sensor conectado."
        ),
        "session": domain.session_snapshot(),
        "workflow": {
            "active": hole is not None and state not in {"cerrado", "fallo"},
            "status": state_label(state),
            "label": f"Taladro {hole.id}" if hole else "Malla ficticia",
            "total": len(controller.plan.holes),
            "step": len(domain.completed_holes) + 1,
            "detail": detail,
            "scenario": controller.scenario_name,
        },
        "confirmation": controller.confirmation_snapshot(),
        "history": ui_state["history"],
        "alert": vars(domain.alert) if domain.alert else None,
    }
