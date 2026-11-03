"""List microphone inputs available to the Faro demo laptop."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faro.voice import VoiceRecognizer


for device in VoiceRecognizer.list_input_devices():
    print(f"{device['index']}: {device['name']}")
