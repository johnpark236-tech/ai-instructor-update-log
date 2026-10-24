"""Fast regression tests for fail-closed hourly publishing without credentials or network."""
import importlib.util
import json
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
                  patch.object(engine, "generation_result", side_effect=[{"status":"GENERATED","reason":"ok"},{"status":"SKIPPED_NO_NEWS","reason":"none"}]),
                  patch.object(engine, "permitted"),
                  patch.object(engine, "changed_files", side_effect=[
                      ["public/data/ai-news.json"], [], ["public/data/ai-news.json"]]),
                  patch.object(engine, "validate_news", side_effect=RuntimeError("Schema field invalid"))):
                result = engine.execute("news", p, no_push=True)
                self.assertEqual(result["status"], "REJECTED_SCHEMA")
                self.assertIn("Schema field invalid", result["reason"])

    def test_no_file_changes_without_report_is_generation_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp)
            with (patch.object(engine, "HOME", p),
                  patch.object(engine.shutil, "which", return_value="codex"),
                  patch.object(engine, "preflight"),
                  patch.object(engine, "codex"),
                  patch.object(engine, "changed_files", return_value=[])):
                result = engine.execute("news", p, no_push=True)
                self.assertEqual(result["status"], "FAILED_GENERATION")


    def test_reject_new_lesson_pricing_links_as_strings(self):
        lesson_id = "AI-2026-10-CAT09-009"
        old = {"lessons": [], "count": 0}
        new = {"lessons": [{"id": lesson_id}], "count": 1}
        data = {"id": lesson_id, "wrap": {"quiz": [{"options":["a","b","c","d"],"answer":0,"explain":"why"}]*3},
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



    def test_quota_detection_specific_not_generic_limit(self):
        for message in [
            "You've hit your ChatGPT usage limit. Try again later.",
            "usage_limit_reached: resets at 07:00",
            "Rate limit exceeded for Codex",
            "ChatGPT 사용량 한도 초과",
            "quota exceeded",
        ]:
            self.assertTrue(engine.is_codex_quota_error(message), message)
        for message in [
            "Limit 3 questions per lesson",
            "A news rate limit policy has changed",
            "Missing pricing.sources schema",
            "You've hit a user interface bug",
        ]:
            self.assertFalse(engine.is_codex_quota_error(message), message)

    def test_codex_return_code_quota_raises_distinct_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            result = subprocess.CompletedProcess(
                ["codex"], 1, stdout="", stderr="You've hit your ChatGPT usage limit.")
            with patch.object(engine.subprocess, "run", return_value=result):
                with self.assertRaises(engine.CodexQuotaExceeded):
                    engine.codex("codex", root, "prompt", root / "out.txt")

    def test_codex_zero_exit_quota_notice_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            output = root / "out.txt"
            output.write_text("usage_limit_reached", encoding="utf-8")
            with patch.object(engine.subprocess, "run", return_value=subprocess.CompletedProcess(["codex"], 0, stdout="", stderr="")):
                with self.assertRaises(engine.CodexQuotaExceeded):
                    engine.codex("codex", root, "prompt", output)

    def test_quota_ends_execution_without_commit_or_three_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with (patch.object(engine, "HOME", root),
                  patch.object(engine.shutil, "which", return_value="codex"),
                  patch.object(engine, "preflight"),
                  patch.object(engine, "codex", side_effect=engine.CodexQuotaExceeded("quota")),
                  patch.object(engine, "git") as git_mock,
                  patch.object(engine, "changed_files") as changed_mock):
                result = engine.execute("news", root, no_push=True)
                self.assertEqual(result["status"], "RATE_LIMITED")
                self.assertTrue(result["draft_discarded"])
                git_mock.assert_not_called()
                changed_mock.assert_not_called()

    def test_quota_during_review_never_publishes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            with (patch.object(engine, "HOME", root),
                  patch.object(engine.shutil, "which", return_value="codex"),
                  patch.object(engine, "preflight"),
                  patch.object(engine, "codex", side_effect=[None, engine.CodexQuotaExceeded("quota")]),
                  patch.object(engine, "changed_files", return_value=["public/data/ai-news.json"]),
                  patch.object(engine, "permitted"),
                  patch.object(engine, "validate_news", return_value="ai-auto-test"),
                  patch.object(engine, "generation_result", return_value={"status":"GENERATED","reason":"ok"}),
                  patch.object(engine.hashlib, "sha256"),
                  patch.object(pathlib.Path, "read_bytes", return_value=b"test"),
                  patch.object(engine, "git") as git_mock):
                result = engine.execute("news", root, no_push=True)
                self.assertEqual(result["status"], "RATE_LIMITED")
                git_mock.assert_not_called()



    def test_generation_reports_distinguish_no_news_search_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            p = pathlib.Path(directory)/"report.json"
            for status in ["SKIPPED_NO_NEWS", "SKIPPED_DUPLICATE", "FAILED_SEARCH", "REJECTED_AVAILABILITY"]:
                p.write_text(json.dumps({"status":status,"reason":"checked official source","sources":["https://openai.com/news/"]}))
                self.assertEqual(engine.generation_result(p, [])["status"],status)
            p.write_text(json.dumps({"status":"SKIPPED_NO_NEWS","reason":"none","sources":[]}))
            self.assertEqual(engine.generation_result(p, [])["status"], "FAILED_SEARCH")
            p.write_text(json.dumps({"status":"GENERATED","reason":"done","sources":[]}))
            self.assertEqual(engine.generation_result(p, [])["status"], "FAILED_GENERATION")

    def test_authentication_distinct_from_quota(self):
        self.assertEqual(engine.failure_status(RuntimeError("401 unauthorized")), "AUTH_FAILED")
        self.assertEqual(engine.failure_status(engine.CodexQuotaExceeded()), "RATE_LIMITED")


if __name__ == "__main__":
    unittest.main()
