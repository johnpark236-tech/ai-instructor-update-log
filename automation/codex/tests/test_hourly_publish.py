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


    def test_reject_new_lesson_pricing_links_as_strings(self):
        lesson_id = "AI-2026-10-CAT09-009"
        old = {"lessons": [], "count": 0}
        new = {"lessons": [{"id": lesson_id}], "count": 1}
        data = {"id": lesson_id, "wrap": {"quiz": [{}, {}, {}]},
                "verification": [], "pricing": {"sources": ["https://example.com"]}}
        def original(_repo, p):
            return old if p == "lessons.json" else {"items": []}
        def current(_repo, p):
            return new if p == "lessons.json" else data
        with (patch.object(engine, "orig_json", side_effect=original),
              patch.object(engine, "current_json", side_effect=current),
              patch.object(engine, "git", side_effect=RuntimeError("not in HEAD"))):
            with self.assertRaisesRegex(RuntimeError, "pricing.sources must be"):
                engine.validate_lesson(pathlib.Path("."), [
                    "lessons.json", f"lessons/{lesson_id}.json", "releases.json"])

    def test_discard_only_unpublished_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            candidate = root / "lessons" / "AI-2026-10-CAT09-009.json"
            candidate.parent.mkdir()
            candidate.write_text("{}", encoding="utf-8")
            files = ["lessons.json", candidate.relative_to(root).as_posix(), "releases.json"]
            commands = []
            def fake_git(_repo, *args, **kwargs):
                commands.append(args)
                if args[0] == "cat-file":
                    raise RuntimeError("new file")
                return ""
            with (patch.object(engine, "git", side_effect=fake_git),
                  patch.object(engine, "changed_files", return_value=[])):
                engine.discard_unverifiable_lesson(root, files, candidate.stem)
            self.assertFalse(candidate.exists())
            self.assertTrue(any(c[0] == "restore" for c in commands))



if __name__ == "__main__":
    unittest.main()
