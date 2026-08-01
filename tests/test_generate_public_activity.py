import importlib.util
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_public_activity.py"
SPEC = importlib.util.spec_from_file_location("generate_public_activity", SCRIPT)
activity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activity)


class ActivityChartTests(unittest.TestCase):
    def test_month_keys_cover_latest_twelve_calendar_months(self):
        keys = activity.month_keys(date(2026, 8, 2), 12)

        self.assertEqual(keys[0], "2025-09")
        self.assertEqual(keys[-1], "2026-08")
        self.assertEqual(len(keys), 12)

    def test_events_are_bucketed_and_rendered(self):
        counts = activity.empty_counts(activity.month_keys(date(2026, 8, 2), 12))
        activity.add_event(counts, "commits", "2026-07-03T10:00:00Z")
        activity.add_event(counts, "pull_requests", "2026-07-04T10:00:00Z")
        activity.add_event(counts, "issues", "2026-08-01T10:00:00Z")
        activity.add_event(counts, "releases", "2025-08-31T23:59:59Z")

        svg = activity.render_svg(counts, date(2026, 8, 2))

        self.assertEqual(counts["2026-07"]["commits"], 1)
        self.assertEqual(counts["2026-07"]["pull_requests"], 1)
        self.assertEqual(counts["2026-08"]["issues"], 1)
        self.assertNotIn("2025-08", counts)
        self.assertIn("Public project activity", svg)
        self.assertIn("Commits 1", svg)
        self.assertIn("Pull requests 1", svg)
        self.assertIn("Issues 1", svg)
        self.assertIn("Releases 0", svg)


if __name__ == "__main__":
    unittest.main()
