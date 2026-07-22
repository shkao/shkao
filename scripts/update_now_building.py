#!/usr/bin/env python3
"""Rewrite the now-building section of README.md from recent public repo activity.

Runs unauthenticated, so only public repos appear. Repos with no push in the
last 60 days are skipped; if nothing qualifies, a fallback line is written.
"""

import json
import re
import urllib.request
from datetime import datetime, timezone

USER = "shkao"
EXCLUDE = {USER, "homebrew-tap"}
MAX_ITEMS = 3
MAX_AGE_DAYS = 60
START = "<!-- now-building starts -->"
END = "<!-- now-building ends -->"

req = urllib.request.Request(
    f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30",
    headers={"Accept": "application/vnd.github+json"},
)
repos = json.load(urllib.request.urlopen(req))
now = datetime.now(timezone.utc)


def days_since(iso: str) -> int:
    return (now - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days


lines = []
for r in repos:
    if r["fork"] or r["archived"] or r["name"] in EXCLUDE:
        continue
    days = days_since(r["pushed_at"])
    if days > MAX_AGE_DAYS:
        continue
    desc = f" · {r['description']}" if r["description"] else ""
    lines.append(f"- [{r['name']}]({r['html_url']}){desc}")
    if len(lines) == MAX_ITEMS:
        break

if not lines:
    lines = ["- Heads-down in private repos right now."]

block = "\n".join([START, *lines, END])
readme = open("README.md").read()
updated = re.sub(re.escape(START) + r".*?" + re.escape(END), block, readme, flags=re.S)
if updated != readme:
    open("README.md", "w").write(updated)
    print("updated")
else:
    print("no change")
