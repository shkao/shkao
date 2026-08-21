#!/usr/bin/env python3
"""Drop the dead air out of a screen recording, then write the kept frames as PNGs.

A walkthrough spends most of its length holding still on one screen. Holds are
what makes the demo readable, so they stay, but anything past MAX_HOLD frames is
the viewer waiting for nothing and costs real bytes. Everything is normalised to
FPS first so frame numbers mean the same thing in both passes.

Usage: trim_holds.py <video> <output-directory>
"""

import subprocess
import sys
import tempfile
from pathlib import Path

FPS = 12
WIDTH = 320
MAX_HOLD = 12  # cap any still stretch at one second
STILL = 1.0  # mean per-pixel delta below which two frames count as identical
THUMB = (64, 132)  # analysis runs on a thumbnail; only large motion matters


def frame_deltas(video: str) -> list[float]:
    """Mean per-pixel difference between each frame and the one before it."""
    width, height = THUMB
    with tempfile.NamedTemporaryFile(suffix=".raw") as raw:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                video,
                "-vf",
                f"fps={FPS},scale={width}:{height},format=gray",
                "-f",
                "rawvideo",
                raw.name,
            ],
            check=True,
        )
        data = Path(raw.name).read_bytes()
    size = width * height
    frames = [data[i * size : (i + 1) * size] for i in range(len(data) // size)]
    return [999.0] + [
        sum(abs(a - b) for a, b in zip(frames[i], frames[i - 1])) / size
        for i in range(1, len(frames))
    ]


def keep_ranges(deltas: list[float]) -> list[tuple[int, int]]:
    kept, hold = [], 0
    for index, delta in enumerate(deltas):
        if delta < STILL:
            hold += 1
            if hold > MAX_HOLD:
                continue
        else:
            hold = 0
        kept.append(index)

    ranges, start = [], kept[0]
    for current, following in zip(kept, kept[1:] + [None]):
        if following != current + 1:
            ranges.append((start, current))
            start = following
    return ranges


def main() -> None:
    video, destination = sys.argv[1], Path(sys.argv[2])
    deltas = frame_deltas(video)
    ranges = keep_ranges(deltas)
    kept = sum(end - start + 1 for start, end in ranges)
    print(
        f"{len(deltas)} -> {kept} frames ({kept / FPS:.1f}s)",
        file=sys.stderr,
    )

    destination.mkdir(parents=True, exist_ok=True)
    for stale in destination.glob("*.png"):
        stale.unlink()
    select = "+".join(rf"between(n\,{start}\,{end})" for start, end in ranges)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            video,
            "-vf",
            f"fps={FPS},select='{select}',scale={WIDTH}:-2:flags=lanczos",
            "-fps_mode",
            "passthrough",
            str(destination / "f%04d.png"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
