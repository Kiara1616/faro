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

from faro.core import FaroEngine
from faro.ui import FaroWindow
from faro.voice import VoiceRecognizer


ROOT = Path(__file__).resolve().parent


class VoiceEvents(QObject):
    """Move worker-thread voice callbacks onto Qt's GUI thread."""

    result = Signal(str)
    status = Signal(str, str)


def main() -> int:
    app = QApplication(sys.argv)
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    engine = FaroEngine(db_path=data_dir / "decisions.sqlite3")
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
    }
    if engine.history:
        last_event = engine.history[-1]
        ui_state["transcript"] = last_event["transcript"]
        ui_state["decision"] = last_event["decision"]

    def render() -> None:
        window.render_state({**engine.snapshot(), **ui_state})

    def handle_command(text: str, source: str = "text") -> None:
        decision = engine.handle(text, source=source)
        ui_state["transcript"] = decision.transcript
        ui_state["decision"] = decision.message
        render()

    def handle_voice_status(status: str, detail: str) -> None:
        if status == "listening":
            ui_state["listening"] = True
        elif status in {"stopped", "error"}:
            ui_state["listening"] = False
        if status != "stopped" or not str(ui_state["voice_status"]).startswith("No se pudo"):
            ui_state["voice_status"] = detail or status
        render()

    def toggle_voice(activate: bool) -> None:
        if activate:
            if voice.start():
                ui_state["voice_status"] = "Iniciando micrófono…"
            else:
                ui_state["voice_status"] = "El micrófono ya está iniciándose."
        else:
            voice.stop(timeout=0.5)
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
