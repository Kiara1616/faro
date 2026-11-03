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

    def test_rejects_invalid_audio_configuration(self):
        with self.assertRaises(ValueError):
            VoiceRecognizer("model", lambda text: None, sample_rate=0)


if __name__ == "__main__":
    unittest.main()
