import threading
import unittest

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


if __name__ == "__main__":
    unittest.main()
