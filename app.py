"""Run the Faro desktop simulator.

All commands affect only an in-process, fictional workflow. This application has
no industrial connectors, network control endpoints, or physical outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication

from faro.controller import FaroController
from faro.domain import Mode, Source
from faro.plan import load_demo_plan
from faro.presentation import build_snapshot
from faro.scenarios import load_scenarios
from faro.ui import FaroWindow
from faro.voice import VoiceRecognizer
from faro.wake_word import WakeCommandGate


ROOT = Path(__file__).resolve().parent


class VoiceEvents(QObject):
    """Move worker-thread voice callbacks onto Qt's GUI thread."""

    result = Signal(str, object)
    status = Signal(str, str, object)


def main() -> int:
    app = QApplication(sys.argv)
    plan = load_demo_plan(ROOT / "fixtures" / "malla_demo.json")
    scenarios = load_scenarios(ROOT / "fixtures" / "escenarios_demo.json")
    scenario_name = os.environ.get("FARO_SCENARIO", "normal")
    selected_scenario = scenarios.get(scenario_name, scenarios["normal"])
    audit_path = ROOT / "data" / "faro-audit.sqlite3"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    controller = FaroController.create(plan, audit_path, scenario=selected_scenario)
    domain = controller.domain
    session_id = "demo-session"
    window = FaroWindow()
    events = VoiceEvents()

    model_path = Path(os.environ.get("FARO_VOSK_MODEL", str(ROOT / "models" / "vosk-model-small-es-0.42")))
    raw_device = os.environ.get("FARO_AUDIO_DEVICE")
    audio_device = int(raw_device) if raw_device and raw_device.isdecimal() else raw_device
    voice = VoiceRecognizer(model_path, lambda text: None, lambda state, detail: None,
                            device=audio_device, on_result_context=events.result.emit,
                            on_status_context=events.status.emit)
    ui_state = {
        "listening": False,
        "transcript": "",
        "decision": "Esperando una solicitud",
        "voice_status": "Micrófono inactivo",
        "command_status": "en espera",
        "history": [],
        "zone_clear": False,
    }
    wake_gate = WakeCommandGate(command_window_seconds=6.0)
    voice_error_detail: str | None = None

    def render() -> None:
        window.render_state({**ui_state, **build_snapshot(controller, ui_state)})

    def expire_wake_window() -> None:
        if wake_gate.expire():
            ui_state["voice_status"] = "Micrófono activo; espera «Oye Faro»."
            ui_state["command_status"] = "en espera de frase de activación"
            render()

    def handle_command(text: str, source: str = "text", generation: int | None = None) -> None:
        input_source = Source.VOICE if source == "voice" else Source.TEXT
        if input_source is Source.VOICE:
            wake = wake_gate.consume(text)
            if wake.status == "ignored":
                return
            if wake.status == "activated":
                ui_state["voice_status"] = "Faro activado. Di una orden en los próximos 6 segundos."
                ui_state["command_status"] = "esperando orden por voz"
                render()
                QTimer.singleShot(6_100, expire_wake_window)
                return
            text = wake.command or ""
            ui_state["voice_status"] = "Micrófono activo; di «Oye Faro» para otra orden."
        if input_source is Source.VOICE and generation is None:
            generation = domain.session.generation if domain.session else None
        result = controller.process(text, source=input_source, generation=generation,
                                    zone_clear=ui_state["zone_clear"])
        ui_state["transcript"] = text
        if result.decision is None:
            accepted, intent, reason = False, result.parsed.intent or "desconocido", result.parsed.reason
            ui_state["command_status"] = "rechazado / no interpretado"
        else:
            accepted, intent, reason = result.decision.accepted, result.parsed.intent or "desconocido", result.decision.reason
            ui_state["command_status"] = "interpretado / aceptado" if accepted else "rechazado"
        ui_state["decision"] = reason
        if (result.decision is not None and result.decision.accepted
                and result.parsed.intent in {"consultar_plan", "consultar_taladro"}
                and domain.selected_hole is not None):
            hole = domain.selected_hole
            ui_state["decision"] = (
                f"Plan ficticio del taladro {hole.id}: {hole.product}, "
                f"{hole.planned_kg} kg, entrega por {hole.delivery_method}."
            )
        ui_state["history"].append({"transcript": text, "intent": intent,
                                    "accepted": accepted, "decision": ui_state["decision"],
                                    "state": domain.state.value,
                                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        render()

    def handle_zone_clear(enabled: bool) -> None:
        ui_state["zone_clear"] = bool(enabled) and controller.zone_clear_available
        ui_state["decision"] = (
            "Zona marcada como despejada para esta simulación. No proviene de un sensor."
            if ui_state["zone_clear"] else
            "La zona simulada permanece ocupada; los movimientos serán rechazados."
        )
        ui_state["command_status"] = "condición ficticia de demostración"
        render()

    def handle_voice_status(status: str, detail: str, generation: int | None = None) -> None:
        nonlocal voice_error_detail
        if (generation is not None and domain.session is not None
                and generation != domain.session.generation):
            return
        if status == "listening":
            voice_error_detail = None
            ui_state["listening"] = True
            if domain.session is None or not domain.session.listening:
                domain.set_listening(session_id, True)
        elif status == "error":
            wake_gate.reset()
            voice_error_detail = detail or "Micrófono no disponible."
            ui_state["listening"] = False
            domain.set_listening(session_id, False)
            if domain.pending is None:
                domain.set_mode(session_id, Mode.MANUAL)
        elif status == "stopped":
            wake_gate.reset()
            ui_state["listening"] = False
            domain.set_listening(session_id, False)
        if status == "listening":
            ui_state["voice_status"] = "Micrófono activo; espera «Oye Faro»."
        else:
            ui_state["voice_status"] = (voice_error_detail if status == "stopped" and voice_error_detail
                                         else detail or status)
        render()

    def toggle_voice(activate: bool) -> None:
        if activate:
            wake_gate.reset()
            if not domain.set_mode(session_id, Mode.VOZ) or not domain.set_listening(session_id, True):
                ui_state["voice_status"] = "No se puede activar voz durante una acción o sesión inválida."
            else:
                voice.capture_generation = domain.session.generation if domain.session else None
                if voice.start():
                    ui_state["voice_status"] = "Iniciando micrófono…"
                else:
                    domain.set_listening(session_id, False)
                    domain.set_mode(session_id, Mode.MANUAL)
                    ui_state["voice_status"] = "El micrófono ya está iniciándose."
        else:
            wake_gate.reset()
            voice.stop(timeout=0.5)
            domain.set_listening(session_id, False)
            domain.set_mode(session_id, Mode.MANUAL)
            ui_state["listening"] = False
            ui_state["voice_status"] = "Micrófono desactivado."
        render()

    def recover_unknown() -> None:
        if controller.recover_unknown("revisión manual en consola"):
            ui_state["command_status"] = "recuperado manualmente; requiere nueva orden"
            ui_state["decision"] = "Resultado desconocido revisado; no se reintentó automáticamente."
            render()

    window.command_submitted.connect(handle_command)
    window.listening_toggled.connect(toggle_voice)
    window.recovery_requested.connect(recover_unknown)
    window.zone_clear_toggled.connect(handle_zone_clear)
    events.result.connect(lambda text, generation: handle_command(
        text, source="voice", generation=generation))
    events.status.connect(handle_voice_status)
    simulator_timer = QTimer(window)
    simulator_timer.setInterval(100)

    def advance_simulator() -> None:
        event = controller.tick()
        if event is not None:
            ui_state["command_status"] = f"ejecución: {event.status.value}"
            ui_state["decision"] = event.reason or event.status.value
            render()

    simulator_timer.timeout.connect(advance_simulator)
    simulator_timer.start()
    app.aboutToQuit.connect(voice.stop)
    render()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
