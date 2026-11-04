"""Offline readiness check for a Faro demo laptop.

The diagnostic never downloads anything and exits non-zero when a required
local asset is missing. Audio hardware is reported as a warning so typed
commands remain usable without a microphone.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(root: Path) -> dict[str, object]:
    model = root / "models" / "vosk-model-small-es-0.42"
    fixture = root / "fixtures" / "malla_demo.json"
    required = {
        "python": sys.version.split()[0],
        "windows": platform.platform(),
        "plan": fixture.is_file(),
        "model": model.is_dir() and (model / "am" / "final.mdl").is_file(),
        "pyside6": importlib.util.find_spec("PySide6") is not None,
        "pytest": importlib.util.find_spec("pytest") is not None,
        "vosk": importlib.util.find_spec("vosk") is not None,
        "sounddevice": importlib.util.find_spec("sounddevice") is not None,
    }
    try:
        from faro.voice import VoiceRecognizer

        required["microphones"] = len(VoiceRecognizer.list_input_devices()) > 0
    except Exception as exc:
        required["microphones"] = False
        required["microphone_error"] = str(exc)
    required["required_ok"] = bool(required["plan"] and required["pyside6"])
    return required


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico local sin red para Faro.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = check(ROOT)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
        print("Nota: modelo, Vosk o micrófono faltantes desactivan solo voz; la entrada escrita sigue disponible.")
    return 0 if result["required_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
