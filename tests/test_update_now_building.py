import io
import json
import os
import runpy
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_now_building.py"
START = "<!-- now-building starts -->"
END = "<!-- now-building ends -->"


class NowBuildingSectionTests(unittest.TestCase):
    def test_backslashes_in_a_description_are_written_literally(self):
        description = r"C:\data \d+"
        repos = [
            {
                "name": "demo",
                "html_url": "https://github.com/shkao/demo",
                "description": description,
                "fork": False,
                "archived": False,
                "pushed_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
        response = io.BytesIO(json.dumps(repos).encode())
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(f"intro\n{START}\nold\n{END}\n")
            cwd = os.getcwd()
            os.chdir(directory)
            try:
                with mock.patch("urllib.request.urlopen", return_value=response):
                    with mock.patch("sys.stdout", io.StringIO()):
                        runpy.run_path(str(SCRIPT))
            finally:
                os.chdir(cwd)

            self.assertIn(f" · {description}\n{END}", readme.read_text())


if __name__ == "__main__":
    unittest.main()
