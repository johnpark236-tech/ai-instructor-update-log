"""Offline analytics report contract tests; never fabricate real site traffic."""
import datetime as dt
import importlib.util
import pathlib
import unittest

MOD = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "analytics_daily.py"
spec = importlib.util.spec_from_file_location("stats", MOD)
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


class AnalyticsDailyTests(unittest.TestCase):
    def test_seoul_day_boundaries(self):
        start, end = stats.get_period(dt.date(2026, 10, 24))
        self.assertEqual(start, "2026-10-24T00:00:00+09:00")
        self.assertEqual(end, "2026-10-25T00:00:00+09:00")

    def test_news_visits_and_downloads_are_distinct(self):
        hits = [
            {"path": "/news/ai-auto-test", "title": "Example", "count": 8, "event": False},
            {"path": "download/news/guide.pdf", "title": "guide", "count": 4, "event": True},
            {"path": "/lesson/AI-2026-10-CAT09-008", "count": 22, "event": False},
            {"path": "/news/fake", "count": 90, "event": True},
        ]
        views, downloads = stats.summarize(hits, "news")
        self.assertEqual([(x["path"], x["count"]) for x in views], [("/news/ai-auto-test", 8)])
        self.assertEqual([x["count"] for x in downloads], [4])

    def test_lesson_download_clicks_not_misreported_as_people(self):
        hits = [
            {"path": "/lesson/AI-2026-10-CAT09-008", "count": 3, "event": False},
            {"path": "download/lesson/AI-2026-10-CAT09-008/learner", "count": 10, "event": True},
            {"path": "download/lesson/AI-2026-10-CAT09-008/instructor", "count": 5, "event": True},
            {"path": "download/lesson/AI-2026-10-CAT09-008/prompts", "count": 7, "event": True},
        ]
        views, downloads = stats.summarize(hits, "lesson")
        self.assertEqual(sum(x["count"] for x in views), 3)
        self.assertEqual(sum(x["count"] for x in downloads), 22)
        text = stats.markdown("lesson", dt.date(2026, 10, 24), views, downloads)
        self.assertIn("22회", text)
        self.assertIn("실제 개인의 신원", text)


if __name__ == "__main__":
    unittest.main()
