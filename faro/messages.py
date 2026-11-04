"""Short, explicit Spanish messages for the simulation console."""

from __future__ import annotations


def execution_message(hole_id: str | None, action: str, stage: str) -> str:
    """Render a message that never calls recognition itself completion."""
    hole = f"Taladro {hole_id}" if hole_id else "Taladro sin seleccionar"
    labels = {
        "heard": "orden escuchada",
        "interpreted": "orden interpretada",
        "accepted": "orden aceptada; esperando simulador",
        "in_progress": "acción en curso en la simulación",
        "completed": "acción completada en la simulación",
        "rejected": "orden rechazada",
        "failed": "acción fallida; revisar estado",
        "unknown": "resultado desconocido; requiere revisión",
    }
    action_label = action.replace("_", " ") if action else "acción"
    return f"{hole}: {action_label} · {labels.get(stage, 'estado no disponible')}"


def confirmation_prompt(hole_id: str | None, action: str) -> str:
    hole = f"Taladro {hole_id}" if hole_id else "Taladro sin seleccionar"
    return f"{hole}: ¿confirmar {action.replace('_', ' ')}?"
