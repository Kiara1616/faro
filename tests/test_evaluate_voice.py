import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_voice import evaluate_cases, load_cases


class EvaluateVoiceTests(unittest.TestCase):
    def test_reports_false_accept_from_misrecognised_forbidden_phrase(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_path = root / "cases.csv"
            csv_path.write_text(
                "wav,expected_text,expected_accept,setup_commands\n"
                "a.wav,mostrar estado,true,\n"
                "b.wav,activar bomba,false,\n"
                "c.wav,activar bomba,false,\n",
                encoding="utf-8",
            )
            cases = load_cases(csv_path)
            transcripts = {
                "a.wav": "mostrar estado",
                "b.wav": "mostrar estado",  # Incorrect ASR becomes an allowed command.
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
            "expected_text": "consultar temperatura",
            "expected_accept": True,
            "setup_commands": ["iniciar revision auxiliar"],
        }]
        report = evaluate_cases(cases, lambda path: ("consultar temperatura", 5.0))
        self.assertEqual(report["summary"]["decision_accuracy"], 1.0)
        cases[0]["setup_commands"] = ["consultar temperatura"]
        with self.assertRaisesRegex(ValueError, "Preparación de caso rechazada"):
            evaluate_cases(cases, lambda path: ("consultar temperatura", 5.0))

    def test_bad_csv_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.csv"
            path.write_text("wav,expected_text,expected_accept\na.wav,mostrar estado,maybe\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_accept"):
                load_cases(path)


if __name__ == "__main__":
    unittest.main()
