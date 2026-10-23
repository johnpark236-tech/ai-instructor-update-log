"""Fast regression tests for fail-closed hourly publishing without credentials or network."""
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hourly_publish", HERE / "hourly_publish.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)


class HourlyPublisherRegressionTests(unittest.TestCase):
    def test_stdout_from_validator_is_not_discarded(self):
        failed = subprocess.CompletedProcess(["python"], 1, stdout="FIELD ERROR: missing outcome", stderr="")
        with patch.object(engine.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "missing outcome"):
                engine.run(["python", "validator.py"], pathlib.Path("."))

    def test_error_output_hides_credentials(self):
        message = "prefix sk-" + "a" * 32 + " and Bearer " + "b" * 40
        cleaned = engine.safe_detail(message)
        self.assertNotIn("a" * 32, cleaned)
        self.assertNotIn("b" * 40, cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_after_rejection_noop_is_not_misreported_as_clean_skip(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp)
            with (patch.object(engine, "HOME", p),
                  patch.object(engine.shutil, "which", return_value="codex"),
                  patch.object(engine, "preflight"),
                  patch.object(engine, "codex"),
                  patch.object(engine, "permitted"),
                  patch.object(engine, "changed_files", side_effect=[
                      ["public/data/ai-news.json"], [], ["public/data/ai-news.json"]]),
                  patch.object(engine, "validate_news", side_effect=RuntimeError("Schema field invalid"))):
                with self.assertRaisesRegex(RuntimeError, "Schema field invalid"):
                    engine.execute("news", p, no_push=True)

    def test_first_attempt_no_new_information_is_normal_skip(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp)
            with (patch.object(engine, "HOME", p),
                  patch.object(engine.shutil, "which", return_value="codex"),
                  patch.object(engine, "preflight"),
                  patch.object(engine, "codex"),
                  patch.object(engine, "changed_files", return_value=[])):
                result = engine.execute("news", p, no_push=True)
                self.assertEqual(result["status"], "SKIPPED")


if __name__ == "__main__":
    unittest.main()
