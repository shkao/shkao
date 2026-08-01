#!/usr/bin/env python3
"""Generate a 12-month SVG activity rollup for Shu-Min's public projects."""

import html
import json
import math
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


OWNER = "shkao"
REPOSITORIES = ("shkao", "ration", "nami", "homebrew-tap")
METRICS = ("commits", "pull_requests", "issues", "releases")
LABELS = {
    "commits": "Commits",
    "pull_requests": "Pull requests",
    "issues": "Issues",
    "releases": "Releases",
}
COLORS = {
    "commits": "#599981",
    "pull_requests": "#9981E1",
    "issues": "#4A70C7",
    "releases": "#B78199",
}
API_ROOT = "https://api.github.com"
OUTPUT = Path("assets/public-project-activity.svg")


def month_keys(as_of: date, months: int) -> list[str]:
    """Return calendar-month keys ending with the month containing as_of."""
    end_index = as_of.year * 12 + as_of.month - 1
    keys = []
    for index in range(end_index - months + 1, end_index + 1):
        year, zero_based_month = divmod(index, 12)
        keys.append(f"{year:04d}-{zero_based_month + 1:02d}")
    return keys


def empty_counts(keys: list[str]) -> dict[str, dict[str, int]]:
    return {key: {metric: 0 for metric in METRICS} for key in keys}


def add_event(
    counts: dict[str, dict[str, int]], metric: str, timestamp: Optional[str]
) -> None:
    if timestamp and timestamp[:7] in counts:
        counts[timestamp[:7]][metric] += 1


def api_items(path: str, params: dict[str, str]) -> list[dict]:
    """Fetch all pages for one GitHub REST collection."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "shkao-profile-activity",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items = []
    page = 1
    while True:
        query = urllib.parse.urlencode({**params, "per_page": "100", "page": str(page)})
        request = urllib.request.Request(f"{API_ROOT}{path}?{query}", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                batch = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(
                f"GitHub API returned HTTP {error.code} for {path}"
            ) from error
        if not isinstance(batch, list):
            raise RuntimeError(f"GitHub API returned an unexpected response for {path}")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def collect_activity(
    counts: dict[str, dict[str, int]], start: datetime, end: datetime
) -> None:
    start_iso = start.isoformat().replace("+00:00", "Z")
    end_iso = end.isoformat().replace("+00:00", "Z")

    for repository in REPOSITORIES:
        prefix = f"/repos/{OWNER}/{repository}"

        commits = api_items(f"{prefix}/commits", {"since": start_iso, "until": end_iso})
        for commit in commits:
            add_event(counts, "commits", commit["commit"]["committer"]["date"])

        pulls = api_items(
            f"{prefix}/pulls",
            {"state": "all", "sort": "created", "direction": "desc"},
        )
        for pull in pulls:
            if pull["created_at"] < start_iso:
                break
            add_event(counts, "pull_requests", pull["created_at"])

        issues = api_items(
            f"{prefix}/issues",
            {
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "since": start_iso,
            },
        )
        for issue in issues:
            if issue["created_at"] < start_iso:
                break
            if "pull_request" not in issue:
                add_event(counts, "issues", issue["created_at"])

        releases = api_items(f"{prefix}/releases", {})
        for release in releases:
            add_event(counts, "releases", release.get("published_at"))


def render_svg(counts: dict[str, dict[str, int]], as_of: date) -> str:
    chart_left = 58
    chart_top = 86
    chart_width = 854
    chart_height = 244
    months = list(counts)
    totals = {
        metric: sum(month[metric] for month in counts.values()) for metric in METRICS
    }
    monthly_totals = [sum(counts[key].values()) for key in months]
    maximum = max(monthly_totals, default=0)
    axis_max = max(4, int(math.ceil(maximum / 5.0) * 5))

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="400" viewBox="0 0 960 400" role="img">',
        "<title>Public project activity for the latest 12 months</title>",
        "<desc>Monthly commits, opened pull requests, opened issues, and published releases across shkao, ration, nami, and homebrew-tap.</desc>",
        "<style>",
        ".background{fill:#ffffff;stroke:#d0d7de}.secondary{fill:#59636e}.grid{stroke:#d8dee4}.axis{fill:#59636e}",
        "@media (prefers-color-scheme:dark){.background{fill:#0d1117;stroke:#30363d}.secondary,.axis{fill:#8b949e}.grid{stroke:#30363d}}",
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}",
        "</style>",
        '<rect class="background" x="0.5" y="0.5" width="959" height="399" rx="10"/>',
        f'<text class="secondary" x="28" y="28" font-size="12">Latest 12 calendar months · updated {html.escape(as_of.isoformat())} UTC</text>',
    ]

    legend_x = 28
    for metric in METRICS:
        label = f"{LABELS[metric]} {totals[metric]}"
        lines.append(
            f'<rect x="{legend_x}" y="50" width="10" height="10" rx="2" fill="{COLORS[metric]}"/>'
        )
        lines.append(
            f'<text class="secondary" x="{legend_x + 16}" y="59" font-size="12">{html.escape(label)}</text>'
        )
        legend_x += 108 + len(label) * 3

    for tick in range(5):
        value = axis_max * tick / 4
        y = chart_top + chart_height - chart_height * tick / 4
        lines.append(
            f'<line class="grid" x1="{chart_left}" y1="{y:.1f}" x2="{chart_left + chart_width}" y2="{y:.1f}"/>'
        )
        lines.append(
            f'<text class="axis" x="{chart_left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="10">{value:.0f}</text>'
        )

    slot = chart_width / len(months)
    bar_width = min(40, slot * 0.58)
    for index, key in enumerate(months):
        x = chart_left + slot * index + (slot - bar_width) / 2
        y = chart_top + chart_height
        for metric in METRICS:
            value = counts[key][metric]
            segment_height = chart_height * value / axis_max
            y -= segment_height
            if segment_height:
                lines.append(
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{segment_height:.1f}" fill="{COLORS[metric]}"><title>{html.escape(key)} · {html.escape(LABELS[metric])}: {value}</title></rect>'
                )
        label_date = datetime.strptime(f"{key}-01", "%Y-%m-%d")
        label = label_date.strftime("%b")
        if index == 0 or label_date.month == 1:
            label += f" '{str(label_date.year)[2:]}"
        lines.append(
            f'<text class="axis" x="{x + bar_width / 2:.1f}" y="351" text-anchor="middle" font-size="10">{html.escape(label)}</text>'
        )

    repositories = " · ".join(REPOSITORIES)
    lines.append(
        f'<text class="secondary" x="480" y="380" text-anchor="middle" font-size="11">{html.escape(repositories)}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def write_output(svg: str) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=OUTPUT.parent, delete=False, encoding="utf-8"
    ) as temporary:
        temporary.write(svg)
        temporary_path = Path(temporary.name)
    temporary_path.chmod(0o644)
    temporary_path.replace(OUTPUT)


def main() -> None:
    now = datetime.now(timezone.utc)
    keys = month_keys(now.date(), 12)
    counts = empty_counts(keys)
    start = datetime.fromisoformat(f"{keys[0]}-01T00:00:00+00:00")
    collect_activity(counts, start, now)
    write_output(render_svg(counts, now.date()))
    print(f"updated {OUTPUT}")


if __name__ == "__main__":
    main()
