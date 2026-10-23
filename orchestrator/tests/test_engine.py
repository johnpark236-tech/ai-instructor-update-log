import unittest
from orchestrator.quota import exceeded
from orchestrator.validator import scope
from orchestrator.dashboard import markdown
class EngineTest(unittest.TestCase):
    def test_quota(self):
        self.assertTrue(exceeded("usage limit reached"))
        self.assertFalse(exceeded("completed successfully"))
    def test_protected(self):
        self.assertFalse(scope([".github/workflows/pages.yml"])[0])
        self.assertFalse(scope(["orchestrator/master.py"])[0])
        self.assertTrue(scope(["lessons/AI-2026-10-CAT01-001.json"])[0])
    def test_status(self):
        self.assertIn("QUOTA_WAIT",markdown({"status":"QUOTA_WAIT"}))
if __name__=="__main__": unittest.main()
