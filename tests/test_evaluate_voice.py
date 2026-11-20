import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_voice import evaluate_cases, evaluate_pipeline_cases, load_cases


class EvaluateVoiceTests(unittest.TestCase):
    def test_reports_false_accept_from_misrecognised_forbidden_phrase(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_path = root / "cases.csv"
            csv_path.write_text(
                "wav,expected_text,expected_accept,setup_commands\n"
                "a.wav,consultar estado,true,\n"
                "b.wav,activar bomba,false,\n"
                "c.wav,activar bomba,false,\n",
                encoding="utf-8",
            )
            cases = load_cases(csv_path)
            transcripts = {
                "a.wav": "consultar estado",
                "b.wav": "consultar estado",  # Incorrect ASR becomes an allowed command.
                "c.wav": "activar bomba",
            }
            report = evaluate_cases(cases, lambda path: (transcripts[path.name], 12.0))
            self.assertEqual(report["summary"]["cases"], 3)
            self.assertEqual(report["summary"]["exact_transcriptions"], 2)
            self.assertEqual(report["summary"]["false_accepts"], 1)
            self.assertEqual(report["summary"]["false_accept_rate"], 0.5)
            self.assertEqual(report["summary"]["decision_accuracy"], 0.6667)
            self.assertTrue(report["cases"][1]["false_accept"])

    def test_context_setup_rejects_wrong_sequence(self):
        cases = [{
            "wav": Path("case.wav"),
            "expected_text": "consultar taladro 101",
            "expected_accept": True,
            "setup_commands": ["seleccionar taladro 101"],
        }]
        report = evaluate_cases(cases, lambda path: ("consultar taladro 101", 5.0))
        self.assertEqual(report["summary"]["decision_accuracy"], 1.0)
        cases[0]["setup_commands"] = ["preparar carga"]
        with self.assertRaisesRegex(ValueError, "Preparación de caso rechazada"):
            evaluate_cases(cases, lambda path: ("consultar taladro 101", 5.0))

    def test_bad_csv_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.csv"
            path.write_text("wav,expected_text,expected_accept\na.wav,mostrar estado,maybe\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_accept"):
                load_cases(path)

    def test_pipeline_evaluator_reports_condition_and_false_acceptance(self):
        cases = [
            {"wav": Path("good.wav"), "expected_text": "consultar estado", "expected_accept": True,
             "setup_commands": [], "condition": "limpio", "speaker": "A", "noise": "none"},
            {"wav": Path("negative.wav"), "expected_text": "conversacion ajena", "expected_accept": False,
             "setup_commands": [], "condition": "ruido", "speaker": "B", "noise": "radio"},
        ]
        transcripts = {"good.wav": "consultar estado", "negative.wav": "consultar estado"}
        report = evaluate_pipeline_cases(cases, lambda path: (transcripts[path.name], 10.0))
        assert report["summary"]["false_accepts"] == 1
        assert report["summary"]["by_condition"]["ruido"]["false_accept_rate"] == 1.0
        assert report["summary"]["latency_p95_ms"] == 10.0


if __name__ == "__main__":
    unittest.main()
