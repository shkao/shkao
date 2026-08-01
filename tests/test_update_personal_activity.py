import importlib.util
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_personal_activity.py"
SPEC = importlib.util.spec_from_file_location("update_personal_activity", SCRIPT)
activity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activity)


class PersonalActivityTests(unittest.TestCase):
    def test_block_names_the_rolling_month_and_day_range(self):
        block = activity.render_block(date(2026, 8, 2))

        self.assertIn("Jul%203%20%E2%80%93%20Aug%202%2C%202026", block)
        self.assertIn("from=2026-07-03", block)
        self.assertIn("to=2026-08-02", block)
        self.assertIn(activity.START, block)
        self.assertIn(activity.END, block)

    def test_graph_uses_repobeats_contribution_pink_in_both_themes(self):
        light = activity.graph_url(date(2026, 8, 2), dark=False)
        dark = activity.graph_url(date(2026, 8, 2), dark=True)

        self.assertIn("line=ec4899", light)
        self.assertIn("point=ec4899", light)
        self.assertIn("area_color=ec4899", light)
        self.assertIn("bg_color=0d1117", dark)
        self.assertIn("line=ec4899", dark)
        self.assertNotIn("theme=github-compact", dark)


if __name__ == "__main__":
    unittest.main()
