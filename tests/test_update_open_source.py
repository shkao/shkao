import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_open_source.py"
SPEC = importlib.util.spec_from_file_location("update_open_source", SCRIPT)
open_source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(open_source)


class OpenSourceSectionTests(unittest.TestCase):
    def test_star_counts_are_abbreviated(self):
        self.assertEqual(open_source.format_stars(8), "8")
        self.assertEqual(open_source.format_stars(999), "999")
        self.assertEqual(open_source.format_stars(8527), "8.5k")
        self.assertEqual(open_source.format_stars(14762), "14.8k")
        self.assertEqual(open_source.format_stars(12000), "12k")

    def test_rendered_block_round_trips_through_previous_badges(self):
        block = open_source.render_block(
            open_source.CONTRIBUTIONS,
            {"feynman": "8.5k", "awesome-claude-skills": "15k"},
        )

        self.assertTrue(block.startswith(open_source.START))
        self.assertTrue(block.endswith(open_source.END))
        self.assertEqual(
            open_source.previous_badges(block),
            {"feynman": "8.5k", "awesome-claude-skills": "15k"},
        )

    def test_offline_run_keeps_the_badges_already_in_the_readme(self):
        readme = Path(__file__).parents[1] / "README.md"
        badges = open_source.previous_badges(readme.read_text())

        for item in open_source.CONTRIBUTIONS:
            self.assertIn(item["name"], badges)

    def test_every_contribution_links_somewhere(self):
        for item in open_source.CONTRIBUTIONS:
            self.assertTrue(item["links"], item["name"])
            for text, url in item["links"]:
                self.assertTrue(text)
                self.assertTrue(url.startswith("https://github.com/"), url)


if __name__ == "__main__":
    unittest.main()
