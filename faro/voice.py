"""Offline microphone recognition for the Faro simulator.

Callbacks run on a worker thread. A GUI must marshal them to its UI thread.
No audio is saved to disk or sent to a network service.
"""

from __future__ import annotations

import json
import queue
import threading
import time
from pathlib import Path
from typing import Callable


ResultCallback = Callable[[str], None]
ContextResultCallback = Callable[[str, int | None], None]
StatusCallback = Callable[[str, str], None]
ContextStatusCallback = Callable[[str, str, int | None], None]


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
        capture_generation: int | None = None,
        on_result_context: ContextResultCallback | None = None,
        on_status_context: ContextStatusCallback | None = None,
        audio_timeout_seconds: float = 5.0,
    ) -> None:
        if sample_rate <= 0 or block_size <= 0:
            raise ValueError("sample_rate and block_size must be positive")
        if audio_timeout_seconds <= 0:
            raise ValueError("audio_timeout_seconds must be positive")
        self.model_path = Path(model_path)
        self.on_result = on_result
        self.on_status = on_status
        self.device = device
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.grammar = grammar
        self.capture_generation = capture_generation
        self.on_result_context = on_result_context
        self.on_status_context = on_status_context
        self.audio_timeout_seconds = float(audio_timeout_seconds)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._capture_open_lock = threading.Lock()
        self._capture_state = "stopped"
        self._last_error: str | None = None

    @property
    def is_listening(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive() and not self._stop.is_set()

    @property
    def capture_state(self) -> str:
        """Actual worker state: stopped, starting, listening or error."""
        with self._lock:
            return self._capture_state

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def start(self) -> bool:
        """Start listening without blocking. Return False if already starting/listening."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._stop.clear()
            self._last_error = None
            self._capture_state = "starting"
            self._thread = threading.Thread(target=self._run, name="faro-voice", daemon=True)
            self._thread.start()
        return True

    def stop(self, timeout: float = 2.0) -> None:
        """Request microphone shutdown and optionally wait for the worker."""
        # Serialize the cancellation request with the tiny device-open
        # critical section so stop cannot race between the preflight check and
        # RawInputStream construction.
        deadline = time.monotonic() + max(0.0, timeout)
        self._stop.set()
        remaining = max(0.0, deadline - time.monotonic())
        acquired = self._capture_open_lock.acquire(timeout=remaining)
        if acquired:
            self._capture_open_lock.release()
        with self._lock:
            worker = self._thread
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=max(0.0, deadline - time.monotonic()))

    @staticmethod
    def list_input_devices() -> list[dict[str, object]]:
        """Return available input devices; raise ImportError if audio support is absent."""
        import sounddevice as sd

        devices: list[dict[str, object]] = []
        for index, device in enumerate(sd.query_devices()):
            if int(device["max_input_channels"]) > 0:
                devices.append({"index": index, "name": str(device["name"])})
        return devices

    def _emit_status(self, status: str, detail: str = "", generation: int | None = None) -> None:
        with self._lock:
            if status in {"starting", "listening", "stopped", "error"}:
                self._capture_state = status
            if status == "error":
                self._last_error = detail
        if self.on_status is not None or self.on_status_context is not None:
            try:
                if self.on_status_context is not None:
                    self.on_status_context(status, detail, generation)
                else:
                    self.on_status(status, detail)
            except Exception:
                pass  # A UI callback must not kill the audio worker.

    def _emit_result(self, text: str, generation: int | None = None) -> None:
        text = text.strip()
        if text:
            try:
                if self.on_result_context is not None:
                    self.on_result_context(text, generation)
                else:
                    self.on_result(text)
            except Exception:
                # A UI/application callback failure must fail closed: stop
                # consuming audio and let the worker close the stream.
                self._stop.set()
                self._emit_status("error", "Falló el procesamiento de la transcripción.", generation)

    def _run(self) -> None:
        capture_generation = self.capture_generation
        self._emit_status("starting", "Cargando reconocimiento de voz local.", capture_generation)
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

            # stop() may have been called while the local model was loading;
            # never open a capture device after cancellation was requested.
            if self._stop.is_set():
                return

            chunks: queue.Queue[bytes] = queue.Queue(maxsize=16)
            overflow_reported = False
            last_audio_at = time.monotonic()

            def audio_callback(indata: bytes, frames: int, time_info: object, status: object) -> None:
                nonlocal overflow_reported, last_audio_at
                if self._stop.is_set():
                    return
                last_audio_at = time.monotonic()
                if status and not overflow_reported:
                    overflow_reported = True
                    self._emit_status("warning", f"La captura de audio reportó: {status}", capture_generation)
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
                        self._emit_status("warning", "Se descartaron fragmentos de audio.", capture_generation)

            # Hold the open lock only across construction/enter and recheck
            # cancellation after entering. A stop requested during model load
            # therefore cannot produce a late "listening" state.
            with self._capture_open_lock:
                if self._stop.is_set():
                    return
                stream = sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.block_size,
                    device=self.device,
                    dtype="int16",
                    channels=1,
                    callback=audio_callback,
                )
                stream.__enter__()
                if self._stop.is_set():
                    stream.__exit__(None, None, None)
                    return
            try:
                self._emit_status("listening", "Micrófono activo; reconocimiento sin Internet.", capture_generation)
                while not self._stop.is_set():
                    try:
                        chunk = chunks.get(timeout=0.1)
                    except queue.Empty:
                        if time.monotonic() - last_audio_at >= self.audio_timeout_seconds:
                            raise RuntimeError("No se reciben datos del micrófono; revise el dispositivo.")
                        continue
                    if recognizer.AcceptWaveform(chunk):
                        result = json.loads(recognizer.Result())
                        self._emit_result(str(result.get("text", "")), capture_generation)
            finally:
                stream.__exit__(None, None, None)
        except ImportError as exc:
            self._emit_status("error", f"Falta una dependencia de voz: {exc}. Instale requirements-voice.txt.", capture_generation)
        except Exception as exc:
            self._emit_status("error", f"No se pudo iniciar o mantener el reconocimiento: {exc}", capture_generation)
        finally:
            self._stop.set()
            self._emit_status("stopped", "Micrófono desactivado.", capture_generation)
