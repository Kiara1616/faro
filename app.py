"""Run the Faro desktop simulator.

All commands affect only an in-process, fictional workflow. This application has
no industrial connectors, network control endpoints, or physical outputs.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from faro.domain import FaroDomain, Mode, Source
from faro.plan import load_demo_plan
from faro.ui import FaroWindow
from faro.voice import VoiceRecognizer
from faro.voice_pipeline import VoicePipeline


ROOT = Path(__file__).resolve().parent


class VoiceEvents(QObject):
    """Move worker-thread voice callbacks onto Qt's GUI thread."""

    result = Signal(str)
    status = Signal(str, str)


def main() -> int:
    app = QApplication(sys.argv)
    plan = load_demo_plan(ROOT / "fixtures" / "malla_demo.json")
    domain = FaroDomain(plan)
    session_id = "demo-session"
    domain.begin_session(session_id, "Operador de prueba", Mode.MANUAL)
    pipeline = VoicePipeline(plan, domain)
    window = FaroWindow()
    events = VoiceEvents()

    model_path = Path(os.environ.get("FARO_VOSK_MODEL", str(ROOT / "models" / "vosk-model-small-es-0.42")))
    raw_device = os.environ.get("FARO_AUDIO_DEVICE")
    audio_device = int(raw_device) if raw_device and raw_device.isdecimal() else raw_device
    voice = VoiceRecognizer(model_path, events.result.emit, events.status.emit, device=audio_device)
    ui_state = {
        "listening": False,
        "transcript": "",
        "decision": "Esperando una solicitud",
        "voice_status": "Micrófono inactivo",
        "history": [],
    }

    def snapshot() -> dict:
        hole = domain.selected_hole
        return {"operation": {"hole_id": hole.id if hole else None,
                               "product": hole.product if hole else None,
                               "planned_kg": hole.planned_kg if hole else None,
                               "delivery_method": hole.delivery_method if hole else None,
                               "state": domain.state.value},
                "session": domain.session_snapshot(),
                "workflow": {"active": domain.state.value not in {"sin_seleccion", "cerrado"},
                             "status": domain.state.value, "label": domain.state.value,
                             "total": len(plan.holes), "step": len(domain.completed_holes) + 1},
                "history": ui_state["history"]}

    def render() -> None:
        window.render_state({**snapshot(), **ui_state})

    def handle_command(text: str, source: str = "text") -> None:
        input_source = Source.VOICE if source == "voice" else Source.TEXT
        generation = domain.session.generation if input_source is Source.VOICE else None
        result = pipeline.process(text, source=input_source, session_id=session_id,
                                  generation=generation, zone_clear=False)
        ui_state["transcript"] = text
        if result.decision is None:
            accepted, intent, reason = False, result.parsed.intent or "desconocido", result.parsed.reason
        else:
            accepted, intent, reason = result.decision.accepted, result.parsed.intent or "desconocido", result.decision.reason
        ui_state["decision"] = reason
        ui_state["history"].append({"transcript": text, "intent": intent,
                                    "accepted": accepted, "decision": reason,
                                    "state": domain.state.value})
        render()

    def handle_voice_status(status: str, detail: str) -> None:
        if status == "listening":
            ui_state["listening"] = True
            domain.set_listening(session_id, True)
        elif status in {"stopped", "error"}:
            ui_state["listening"] = False
            domain.set_listening(session_id, False)
            if status == "error" and domain.pending is None:
                domain.set_mode(session_id, Mode.MANUAL)
        ui_state["voice_status"] = detail or status
        render()

    def toggle_voice(activate: bool) -> None:
        if activate:
            if not domain.set_mode(session_id, Mode.VOZ) or not domain.set_listening(session_id, True):
                ui_state["voice_status"] = "No se puede activar voz durante una acción o sesión inválida."
            elif voice.start():
                ui_state["voice_status"] = "Iniciando micrófono…"
            else:
                domain.set_listening(session_id, False)
                domain.set_mode(session_id, Mode.MANUAL)
                ui_state["voice_status"] = "El micrófono ya está iniciándose."
        else:
            voice.stop(timeout=0.5)
            domain.set_listening(session_id, False)
            domain.set_mode(session_id, Mode.MANUAL)
            ui_state["listening"] = False
            ui_state["voice_status"] = "Micrófono desactivado."
        render()

    window.command_submitted.connect(handle_command)
    window.listening_toggled.connect(toggle_voice)
    events.result.connect(lambda text: handle_command(text, source="voice"))
    events.status.connect(handle_voice_status)
    app.aboutToQuit.connect(voice.stop)
    render()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
