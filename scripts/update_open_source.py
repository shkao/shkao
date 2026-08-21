#!/usr/bin/env python3
"""Rewrite the open-source section of README.md with live star counts.

The contributions themselves are curated in CONTRIBUTIONS below; only the star
count is fetched, so a rate-limited or offline run reuses the count already in
the README rather than dropping the section.
"""

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

README = Path("README.md")
START = "<!-- open-source starts -->"
END = "<!-- open-source ends -->"

CONTRIBUTIONS = [
    {
        "repo": "companion-inc/feynman",
        "name": "feynman",
        "what": "AI research agent for scientists",
        "summary": (
            "Concurrent PubMed lookups were tripping NCBI's E-utilities rate limit "
            "mid-search. Diagnosed it, then routed every caller through a shared "
            "pacing queue with a regression test and a burst-check script."
        ),
        "links": [
            ("issue #237", "https://github.com/companion-inc/feynman/issues/237"),
            (
                "3 commits",
                "https://github.com/companion-inc/feynman/commits?author=shkao",
            ),
            ("merged in #239", "https://github.com/companion-inc/feynman/pull/239"),
        ],
    },
]


def fetch_stars(repo: str) -> Optional[int]:
    """Return the repo's star count, or None when GitHub is unreachable."""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)["stargazers_count"]
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
        return None


def format_stars(count: int) -> str:
    if count < 1000:
        return str(count)
    return f"{count / 1000:.1f}k".replace(".0k", "k")


def previous_badges(readme: str) -> dict[str, str]:
    """Star badges already in the README, keyed by repo name."""
    return dict(re.findall(r">([\w.-]+)</a></b> · ★ ([\d.k]+)", readme))


def render_block(contributions: list[dict], badges: dict[str, str]) -> str:
    rows = []
    for item in contributions:
        badge = badges.get(item["name"], "")
        links = " · ".join(f'<a href="{url}">{text}</a>' for text, url in item["links"])
        rows.append(
            "<tr>\n"
            f'<td valign="top" width="230"><b><a href="https://github.com/{item["repo"]}">'
            f"{item['name']}</a></b> · ★ {badge}<br><sub>{item['what']}</sub></td>\n"
            f'<td valign="top">{item["summary"]}<br><sub>{links}</sub></td>\n'
            "</tr>"
        )
    return "\n".join([START, "<table>", *rows, "</table>", END])


def main() -> None:
    readme = README.read_text()
    badges = previous_badges(readme)
    for item in CONTRIBUTIONS:
        count = fetch_stars(item["repo"])
        if count is not None:
            badges[item["name"]] = format_stars(count)

    block = render_block(CONTRIBUTIONS, badges)
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END), block, readme, flags=re.S
    )
    if updated != readme:
        README.write_text(updated)
        print("updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
