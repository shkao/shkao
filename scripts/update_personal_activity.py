#!/usr/bin/env python3
"""Keep the profile contribution graph's rolling date range current."""

import re
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


START = "<!-- personal-activity starts -->"
END = "<!-- personal-activity ends -->"
README = Path("README.md")
USER = "shkao"


def date_range_title(as_of: date) -> tuple[date, str]:
    start = as_of - timedelta(days=30)
    if start.year == as_of.year:
        title = f"{start:%b} {start.day} – {as_of:%b} {as_of.day}, {as_of.year}"
    else:
        title = (
            f"{start:%b} {start.day}, {start.year} – "
            f"{as_of:%b} {as_of.day}, {as_of.year}"
        )
    return start, title


def graph_url(as_of: date, dark: bool) -> str:
    start, title = date_range_title(as_of)
    params = {
        "username": USER,
        "from": start.isoformat(),
        "to": as_of.isoformat(),
        "custom_title": title,
        "hide_border": "true",
        "area": "true",
    }
    if dark:
        params.update(
            {
                "bg_color": "0d1117",
                "color": "c9d1d9",
                "line": "ec4899",
                "point": "ec4899",
                "area_color": "ec4899",
            }
        )
    else:
        params.update(
            {
                "bg_color": "ffffff",
                "color": "24292f",
                "line": "ec4899",
                "point": "ec4899",
                "area_color": "ec4899",
            }
        )
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"https://github-readme-activity-graph.vercel.app/graph?{query}".replace(
        "&", "&amp;"
    )


def render_block(as_of: date) -> str:
    return "\n".join(
        [
            START,
            '<a href="https://github.com/shkao">',
            "  <picture>",
            '    <source media="(prefers-color-scheme: dark)" '
            f'srcset="{graph_url(as_of, dark=True)}">',
            f'    <img src="{graph_url(as_of, dark=False)}" '
            'alt="Shu-Min Kao\'s public GitHub contribution activity">',
            "  </picture>",
            "</a>",
            END,
        ]
    )


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    pattern = re.escape(START) + r".*?" + re.escape(END)
    if not re.search(pattern, readme, flags=re.S):
        raise RuntimeError("personal activity markers are missing from README.md")
    today = datetime.now(ZoneInfo("Europe/Brussels")).date()
    updated = re.sub(pattern, render_block(today), readme, flags=re.S)
    if updated != readme:
        README.write_text(updated, encoding="utf-8")
        print("updated personal activity range")
    else:
        print("personal activity range is current")


if __name__ == "__main__":
    main()
