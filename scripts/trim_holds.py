#!/usr/bin/env python3
"""Drop the dead air out of a screen recording, then write the kept frames as PNGs.

Two kinds of wasted time get cut. A leading splash screen, if the recording
opens on one, is dropped entirely so the loop starts on real content instead of
an empty phone. After that, holds are what makes a walkthrough readable so they
stay, but anything past MAX_HOLD frames is the viewer waiting for nothing and
costs real bytes.

Everything is normalised to FPS first so frame numbers mean the same thing in
both the analysis pass and the export pass.

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
FLIP = 64  # per-pixel delta counted as a full-range flip
WIPE = 0.5  # fraction of flipped pixels that marks a splash cut
THUMB = (64, 132)  # analysis runs on a thumbnail; only large motion matters


def thumbnails(video: str) -> list[bytes]:
    """Every frame at FPS, as a small grayscale bitmap."""
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
    return [data[i * size : (i + 1) * size] for i in range(len(data) // size)]


def frame_deltas(frames: list[bytes]) -> list[float]:
    """Mean per-pixel difference between each frame and the one before it."""
    size = len(frames[0])
    return [999.0] + [
        sum(abs(a - b) for a, b in zip(frames[i], frames[i - 1])) / size
        for i in range(1, len(frames))
    ]


def splash_end(frames: list[bytes]) -> int:
    """Index of the first real frame, skipping an opening splash screen.

    A splash-to-content cut repaints most of the screen at once. Ordinary
    transitions inside a walkthrough - a scroll, a tab switch - move well under
    half the pixels, so WIPE separates the two cleanly. Only the opening second
    is considered, so a genuine first interaction is never mistaken for one.
    """
    size = len(frames[0])
    for index in range(1, min(FPS, len(frames))):
        flipped = sum(
            1 for a, b in zip(frames[index], frames[index - 1]) if abs(a - b) > FLIP
        )
        if flipped / size > WIPE:
            return index
    return 0


def keep_ranges(deltas: list[float], start: int) -> list[tuple[int, int]]:
    kept, hold = [], 0
    for index in range(start, len(deltas)):
        if deltas[index] < STILL and index != start:
            hold += 1
            if hold > MAX_HOLD:
                continue
        else:
            hold = 0
        kept.append(index)

    ranges, first = [], kept[0]
    for current, following in zip(kept, kept[1:] + [None]):
        if following != current + 1:
            ranges.append((first, current))
            first = following
    return ranges


def main() -> None:
    video, destination = sys.argv[1], Path(sys.argv[2])
    frames = thumbnails(video)
    start = splash_end(frames)
    ranges = keep_ranges(frame_deltas(frames), start)
    kept = sum(end - begin + 1 for begin, end in ranges)
    print(
        f"{len(frames)} -> {kept} frames ({kept / FPS:.1f}s), splash cut at {start}",
        file=sys.stderr,
    )

    destination.mkdir(parents=True, exist_ok=True)
    for stale in destination.glob("*.png"):
        stale.unlink()
    select = "+".join(rf"between(n\,{begin}\,{end})" for begin, end in ranges)
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
