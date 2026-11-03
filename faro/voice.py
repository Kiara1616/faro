"""Offline microphone recognition for the Faro simulator.

Callbacks run on a worker thread. A GUI must marshal them to its UI thread.
No audio is saved to disk or sent to a network service.
"""

from __future__ import annotations

import json
import queue
import threading
from pathlib import Path
from typing import Callable


ResultCallback = Callable[[str], None]
StatusCallback = Callable[[str, str], None]


class VoiceRecognizer:
    """Listen explicitly, transcribe complete phrases locally with Vosk."""

    def __init__(
        self,
        model_path: str | Path,
        on_result: ResultCallback,
        on_status: StatusCallback | None = None,
        *,
        device: int | str | None = None,
        sample_rate: int = 16_000,
        block_size: int = 4_000,
        grammar: list[str] | None = None,
    ) -> None:
        if sample_rate <= 0 or block_size <= 0:
            raise ValueError("sample_rate and block_size must be positive")
        self.model_path = Path(model_path)
        self.on_result = on_result
        self.on_status = on_status
        self.device = device
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.grammar = grammar
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    @property
    def is_listening(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive() and not self._stop.is_set()

    def start(self) -> bool:
        """Start listening without blocking. Return False if already starting/listening."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="faro-voice", daemon=True)
            self._thread.start()
        return True

    def stop(self, timeout: float = 2.0) -> None:
        """Request microphone shutdown and optionally wait for the worker."""
        self._stop.set()
        with self._lock:
            worker = self._thread
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=timeout)

    @staticmethod
    def list_input_devices() -> list[dict[str, object]]:
        """Return available input devices; raise ImportError if audio support is absent."""
        import sounddevice as sd

        devices: list[dict[str, object]] = []
        for index, device in enumerate(sd.query_devices()):
            if int(device["max_input_channels"]) > 0:
                devices.append({"index": index, "name": str(device["name"])})
        return devices

    def _emit_status(self, status: str, detail: str = "") -> None:
        if self.on_status is not None:
            try:
                self.on_status(status, detail)
            except Exception:
                pass  # A UI callback must not kill the audio worker.

    def _emit_result(self, text: str) -> None:
        text = text.strip()
        if text:
            try:
                self.on_result(text)
            except Exception:
                self._emit_status("error", "Falló el procesamiento de la transcripción.")

    def _run(self) -> None:
        self._emit_status("starting", "Cargando reconocimiento de voz local.")
        try:
            if not self.model_path.is_dir():
                raise FileNotFoundError(f"No se encontró el modelo Vosk: {self.model_path}")

            import sounddevice as sd
            from vosk import KaldiRecognizer, Model

            model = Model(str(self.model_path))
            if self.grammar:
                vocabulary = [*self.grammar, "[unk]"]
                recognizer = KaldiRecognizer(model, self.sample_rate, json.dumps(vocabulary, ensure_ascii=False))
            else:
                recognizer = KaldiRecognizer(model, self.sample_rate)

            chunks: queue.Queue[bytes] = queue.Queue(maxsize=16)
            overflow_reported = False

            def audio_callback(indata: bytes, frames: int, time_info: object, status: object) -> None:
                nonlocal overflow_reported
                if self._stop.is_set():
                    return
                if status and not overflow_reported:
                    overflow_reported = True
                    self._emit_status("warning", f"La captura de audio reportó: {status}")
                try:
                    chunks.put_nowait(bytes(indata))
                except queue.Full:
                    # Keep the newest audio and report lost chunks; never block PortAudio.
                    try:
                        chunks.get_nowait()
                        chunks.put_nowait(bytes(indata))
                    except queue.Empty:
                        pass
                    if not overflow_reported:
                        overflow_reported = True
                        self._emit_status("warning", "Se descartaron fragmentos de audio.")

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                device=self.device,
                dtype="int16",
                channels=1,
                callback=audio_callback,
            ):
                self._emit_status("listening", "Micrófono activo; reconocimiento sin Internet.")
                while not self._stop.is_set():
                    try:
                        chunk = chunks.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    if recognizer.AcceptWaveform(chunk):
                        result = json.loads(recognizer.Result())
                        self._emit_result(str(result.get("text", "")))
        except ImportError as exc:
            self._emit_status("error", f"Falta una dependencia de voz: {exc}. Instale requirements-voice.txt.")
        except Exception as exc:
            self._emit_status("error", f"No se pudo iniciar o mantener el reconocimiento: {exc}")
        finally:
            self._stop.set()
            self._emit_status("stopped", "Micrófono desactivado.")
