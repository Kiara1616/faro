"""Short, explicit Spanish messages for the simulation console."""

from __future__ import annotations


STATE_LABELS = {
    "sin_seleccion": "Sin taladro seleccionado",
    "seleccionado": "Taladro seleccionado",
    "consultado": "Plan consultado",
    "preparado": "Plan verificado",
    "confirmacion_pendiente": "Confirmación pendiente",
    "movimiento_en_curso": "Movimiento en curso · simulación",
    "posicionado": "Brazo o manguera extendido · simulación",
    "carga_en_curso": "Carguío en curso · simulación",
    "cargado": "Carguío completado · simulación",
    "retraccion_en_curso": "Retiro en curso · simulación",
    "retraido": "Brazo o manguera retraído · simulación",
    "cerrado": "Taladro cerrado · simulación",
    "fallo": "Fallo simulado · requiere revisión",
    "resultado_desconocido": "Resultado desconocido · requiere revisión",
}


def state_label(state: str) -> str:
    """Return a readable label for a simulator state."""
    return STATE_LABELS.get(state, state.replace("_", " ").capitalize())


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
        "cancelled": "acción cancelada en la simulación",
        "timeout": "sin respuesta del simulador; requiere revisión",
        "unknown": "resultado desconocido; requiere revisión",
    }
    action_label = action.replace("_", " ") if action else "acción"
    return f"{hole}: {action_label} · {labels.get(stage, 'estado no disponible')}"


def confirmation_prompt(hole_id: str | None, action: str) -> str:
    hole = f"Taladro {hole_id}" if hole_id else "Taladro sin seleccionar"
    return f"{hole}: ¿confirmar {action.replace('_', ' ')}?"
