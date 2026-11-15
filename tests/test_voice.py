import threading
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

from faro.voice import VoiceRecognizer


class VoiceRecognizerTests(unittest.TestCase):
    def test_missing_model_reports_error_without_audio_dependencies(self):
        stopped = threading.Event()
        statuses = []

        def on_status(state, detail):
            statuses.append((state, detail))
            if state == "stopped":
                stopped.set()

        voice = VoiceRecognizer("missing-vosk-model", lambda text: None, on_status)
        self.assertTrue(voice.start())
        self.assertTrue(stopped.wait(timeout=3))
        self.assertTrue(any(state == "error" and "modelo Vosk" in detail for state, detail in statuses))
        voice.stop()
        self.assertFalse(voice.is_listening)
        self.assertEqual(voice.capture_state, "stopped")
        self.assertIn("modelo Vosk", voice.last_error or "")

    def test_failed_capture_can_be_retried_without_duplicate_worker(self):
        statuses = []
        voice = VoiceRecognizer("missing-vosk-model", lambda text: None,
                                lambda state, detail: statuses.append(state))
        self.assertTrue(voice.start())
        for _ in range(20):
            if voice.capture_state == "stopped":
                break
            threading.Event().wait(0.02)
        self.assertEqual(voice.capture_state, "stopped")
        self.assertTrue(voice.start())
        for _ in range(20):
            if voice.capture_state == "stopped" and statuses.count("stopped") >= 2:
                break
            threading.Event().wait(0.02)
        self.assertEqual(statuses.count("starting"), 2)
        self.assertEqual(statuses.count("stopped"), 2)
        self.assertFalse(voice.is_listening)

    def test_rejects_invalid_audio_configuration(self):
        with self.assertRaises(ValueError):
            VoiceRecognizer("model", lambda text: None, sample_rate=0)
        with self.assertRaises(ValueError):
            VoiceRecognizer("model", lambda text: None, audio_timeout_seconds=0)

    def test_result_callback_failure_stops_capture_fail_closed(self):
        statuses = []

        def broken_callback(text):
            raise RuntimeError("ui callback failed")

        voice = VoiceRecognizer("model", broken_callback,
                                lambda state, detail: statuses.append((state, detail)))
        voice._emit_result("consultar estado")
        self.assertTrue(voice._stop.is_set())
        self.assertEqual(voice.capture_state, "error")
        self.assertTrue(any(state == "error" for state, _ in statuses))

    def test_result_context_preserves_capture_generation(self):
        results = []
        voice = VoiceRecognizer("model", lambda text: None,
                                on_result_context=lambda text, generation: results.append((text, generation)))
        voice._emit_result("confirmar", 7)
        self.assertEqual(results, [("confirmar", 7)])

    def test_status_context_preserves_capture_generation(self):
        statuses = []
        voice = VoiceRecognizer("model", lambda text: None,
                                on_status_context=lambda state, detail, generation:
                                statuses.append((state, generation)))
        voice._emit_status("stopped", "done", 9)
        self.assertEqual(statuses, [("stopped", 9)])

    def test_silent_stream_triggers_watchdog_and_closes(self):
        class FakeStream:
            entered = False

            def __enter__(self):
                self.entered = True
                FakeStream.entered = True
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        fake_sounddevice = types.SimpleNamespace(
            RawInputStream=lambda **kwargs: FakeStream(),
        )
        fake_vosk = types.SimpleNamespace(
            Model=lambda path: object(),
            KaldiRecognizer=lambda model, rate, *args: types.SimpleNamespace(
                AcceptWaveform=lambda chunk: False,
            ),
        )
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(sys.modules, {"sounddevice": fake_sounddevice, "vosk": fake_vosk}):
                statuses = []
                voice = VoiceRecognizer(folder, lambda text: None,
                                        lambda state, detail: statuses.append((state, detail)),
                                        audio_timeout_seconds=0.05)
                self.assertTrue(voice.start())
                for _ in range(30):
                    if voice.capture_state == "stopped":
                        break
                    time.sleep(0.02)
                self.assertEqual(voice.capture_state, "stopped")
                self.assertTrue(FakeStream.entered)
                self.assertTrue(any(state == "error" and "No se reciben" in detail
                                    for state, detail in statuses))

    def test_stop_racing_device_open_never_emits_listening(self):
        constructor_entered = threading.Event()
        release_constructor = threading.Event()
        events = []

        class FakeStream:
            def __enter__(self):
                events.append("entered")
                return self

            def __exit__(self, exc_type, exc, tb):
                events.append("closed")

        def raw_stream(**kwargs):
            constructor_entered.set()
            release_constructor.wait(timeout=2)
            return FakeStream()

        fake_sounddevice = types.SimpleNamespace(RawInputStream=raw_stream)
        fake_vosk = types.SimpleNamespace(
            Model=lambda path: object(),
            KaldiRecognizer=lambda model, rate, *args: types.SimpleNamespace(
                AcceptWaveform=lambda chunk: False,
            ),
        )
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(sys.modules, {"sounddevice": fake_sounddevice, "vosk": fake_vosk}):
                statuses = []
                voice = VoiceRecognizer(folder, lambda text: None,
                                        lambda state, detail: statuses.append(state),
                                        audio_timeout_seconds=0.2)
                voice.start()
                self.assertTrue(constructor_entered.wait(timeout=2))
                stopper = threading.Thread(target=voice.stop)
                stopper.start()
                time.sleep(0.02)
                release_constructor.set()
                stopper.join(timeout=2)
                for _ in range(30):
                    if voice.capture_state == "stopped":
                        break
                    time.sleep(0.02)
                self.assertNotIn("listening", statuses)
                self.assertEqual(voice.capture_state, "stopped")


if __name__ == "__main__":
    unittest.main()
