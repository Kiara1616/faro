"""Evaluate Faro's offline speech recognition and command safety on WAV cases.

CSV columns: wav, expected_text, expected_accept, setup_commands (optional).
Paths are relative to the CSV. setup_commands uses | to separate known commands
needed to put a fresh simulator in context before the WAV is processed.
No microphone, internet connection, or audio recording is used.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import unicodedata
import wave
from collections import defaultdict
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from faro.core import FaroEngine
from faro.domain import FaroDomain, Mode, Source
from faro.plan import load_demo_plan
from faro.voice_pipeline import VoicePipeline


Transcriber = Callable[[Path], tuple[str, float]]
REQUIRED_COLUMNS = {"wav", "expected_text", "expected_accept"}


def _normalize(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(ch for ch in plain if not unicodedata.combining(ch)).split())


def _parse_bool(value: str) -> bool:
    lowered = value.strip().casefold()
    if lowered in {"1", "true", "yes", "si", "sí"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    raise ValueError(f"expected_accept debe ser true/false o 1/0: {value!r}")


def load_cases(csv_path: Path) -> list[dict]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"El CSV necesita columnas: {', '.join(sorted(REQUIRED_COLUMNS))}")
        cases = []
        for line, row in enumerate(reader, start=2):
            wav_name = (row.get("wav") or "").strip()
            expected_text = (row.get("expected_text") or "").strip()
            if not wav_name or not expected_text:
                raise ValueError(f"Fila {line}: wav y expected_text son obligatorios.")
            cases.append({
                "wav": (csv_path.parent / wav_name).resolve(),
                "expected_text": expected_text,
                "expected_accept": _parse_bool(row.get("expected_accept") or ""),
                "setup_commands": [part.strip() for part in (row.get("setup_commands") or "").split("|") if part.strip()],
                "condition": (row.get("condition") or "unspecified").strip() or "unspecified",
                "speaker": (row.get("speaker") or "unspecified").strip() or "unspecified",
                "noise": (row.get("noise") or "unspecified").strip() or "unspecified",
            })
    if not cases:
        raise ValueError("El CSV no contiene casos.")
    return cases


def make_vosk_transcriber(model_path: Path) -> Transcriber:
    if not model_path.is_dir():
        raise FileNotFoundError(f"No existe el modelo Vosk: {model_path}")
    from vosk import KaldiRecognizer, Model

    model = Model(str(model_path))

    def transcribe(wav_path: Path) -> tuple[str, float]:
        if not wav_path.is_file():
            raise FileNotFoundError(f"No existe el WAV: {wav_path}")
        with wave.open(str(wav_path), "rb") as stream:
            if (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()) != (1, 2, 16_000):
                raise ValueError(f"WAV debe ser PCM mono, 16 bits y 16 kHz: {wav_path}")
            recognizer = KaldiRecognizer(model, 16_000)
            segments = []
            start = time.perf_counter()
            while chunk := stream.readframes(4_000):
                if recognizer.AcceptWaveform(chunk):
                    segments.append(json.loads(recognizer.Result()).get("text", ""))
            segments.append(json.loads(recognizer.FinalResult()).get("text", ""))
            latency_ms = (time.perf_counter() - start) * 1_000
        return " ".join(segment for segment in segments if segment).strip(), round(latency_ms, 1)

    return transcribe


def evaluate_cases(cases: list[dict], transcribe: Transcriber) -> dict:
    rows = []
    for case in cases:
        engine = FaroEngine()
        for command in case["setup_commands"]:
            decision = engine.handle(command)
            if not decision.accepted:
                raise ValueError(f"Preparación de caso rechazada ({case['wav']}): {command}: {decision.message}")

        transcript, latency_ms = transcribe(case["wav"])
        decision = engine.handle(transcript)
        transcript_correct = _normalize(transcript) == _normalize(case["expected_text"])
        expected_accept = case["expected_accept"]
        rows.append({
            "wav": str(case["wav"]),
            "expected_text": case["expected_text"],
            "transcript": transcript,
            "transcript_correct": transcript_correct,
            "expected_accept": expected_accept,
            "accepted": decision.accepted,
            "false_accept": not expected_accept and decision.accepted,
            "intent": decision.intent,
            "reason": decision.message,
            "recognition_latency_ms": latency_ms,
        })

    negatives = sum(not row["expected_accept"] for row in rows)
    false_accepts = sum(row["false_accept"] for row in rows)
    total = len(rows)
    summary = {
        "cases": total,
        "exact_transcriptions": sum(row["transcript_correct"] for row in rows),
        "exact_transcription_rate": round(sum(row["transcript_correct"] for row in rows) / total, 4),
        "decision_accuracy": round(sum(row["accepted"] == row["expected_accept"] for row in rows) / total, 4),
        "forbidden_cases": negatives,
        "false_accepts": false_accepts,
        "false_accept_rate": round(false_accepts / negatives, 4) if negatives else None,
        "mean_recognition_latency_ms": round(sum(row["recognition_latency_ms"] for row in rows) / total, 1),
    }
    return {"summary": summary, "cases": rows}


def evaluate_pipeline_cases(cases: list[dict], transcribe: Transcriber, plan_path: Path | None = None) -> dict:
    """Evaluate the current parser/domain boundary with a local transcriber.

    This keeps the legacy evaluator available while ensuring F-11 measures the
    same session-protected path used by Faro v1. Audio is read only by the
    injected transcriber; this function never saves or uploads it.
    """
    plan = load_demo_plan(plan_path or PROJECT_ROOT / "fixtures" / "malla_demo.json")
    rows = []
    for index, case in enumerate(cases, start=1):
        domain = FaroDomain(plan)
        domain.begin_session(f"eval-{index}", case.get("speaker", "test"), Mode.VOZ)
        domain.set_listening(f"eval-{index}", True)
        generation = domain.session.generation
        pipeline = VoicePipeline(plan, domain)
        for command_text in case["setup_commands"]:
            setup = pipeline.process(command_text, source=Source.TEXT, session_id=f"eval-{index}")
            if setup.decision is None or not setup.decision.accepted:
                raise ValueError(f"Preparación de caso rechazada ({case['wav']}): {command_text}")
        transcript, latency_ms = transcribe(case["wav"])
        result = pipeline.process(transcript, source=Source.VOICE,
                                  session_id=f"eval-{index}", generation=generation,
                                  zone_clear=case.get("zone_clear", False))
        decision = result.decision
        accepted = bool(decision and decision.accepted)
        rows.append({
            "wav": str(case["wav"]), "condition": case["condition"],
            "speaker": case["speaker"], "noise": case["noise"],
            "expected_text": case["expected_text"], "transcript": transcript,
            "transcript_correct": _normalize(transcript) == _normalize(case["expected_text"]),
            "expected_accept": case["expected_accept"], "accepted": accepted,
            "false_accept": not case["expected_accept"] and accepted,
            "intent": result.parsed.intent, "reason": (decision.reason if decision else result.parsed.reason),
            "recognition_latency_ms": latency_ms,
        })
    latencies = sorted(row["recognition_latency_ms"] for row in rows)
    negatives = sum(not row["expected_accept"] for row in rows)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row["condition"]].append(row)
    by_condition = {}
    for condition, items in groups.items():
        forbidden = sum(not item["expected_accept"] for item in items)
        false = sum(item["false_accept"] for item in items)
        by_condition[condition] = {"cases": len(items), "false_accepts": false,
                                   "forbidden_cases": forbidden,
                                   "false_accept_rate": round(false / forbidden, 4) if forbidden else None}
    summary = {
        "cases": len(rows), "exact_transcriptions": sum(row["transcript_correct"] for row in rows),
        "exact_transcription_rate": round(sum(row["transcript_correct"] for row in rows) / len(rows), 4),
        "decision_accuracy": round(sum(row["accepted"] == row["expected_accept"] for row in rows) / len(rows), 4),
        "forbidden_cases": negatives, "false_accepts": sum(row["false_accept"] for row in rows),
        "false_accept_rate": round(sum(row["false_accept"] for row in rows) / negatives, 4) if negatives else None,
        "latency_p50_ms": latencies[(len(latencies) - 1) // 2],
        "latency_p95_ms": latencies[min(len(latencies) - 1, max(0, int(len(latencies) * 0.95) - 1))],
        "by_condition": by_condition,
    }
    return {"summary": summary, "cases": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa WAV etiquetados con Vosk y Faro sin conexión.")
    parser.add_argument("csv", type=Path, help="CSV con wav, expected_text, expected_accept y setup_commands opcional.")
    parser.add_argument("--model", type=Path, default=Path(__file__).resolve().parents[1] / "models" / "vosk-model-small-es-0.42")
    parser.add_argument("--output", type=Path, help="JSON de resultados; por defecto se imprime por pantalla.")
    args = parser.parse_args()
    try:
        report = evaluate_cases(load_cases(args.csv), make_vosk_transcriber(args.model))
    except (OSError, ValueError, ImportError, wave.Error) as exc:
        print(f"No se pudo evaluar la voz: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Reporte: {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
