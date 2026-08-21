#!/usr/bin/env bash
# Composite a recorded walkthrough into the iPhone frame as light + dark WebP.
# Usage: compose_demo.sh <video.webm> <output-basename>
# Needs frame.png and frame.env in the working directory (both written by
# make_frame.py), plus ffmpeg, python3, and img2webp. The two encodes run in
# parallel. Animated WebP is roughly a quarter the size of the GIF it replaced,
# and trim_holds.py drops the dead air so the loop stays under ~15 seconds.
set -euo pipefail
vid=$1
name=$2
here=$(cd "$(dirname "$0")" && pwd)
source frame.env # W H VX VY VW VH
for theme in ffffff:light 0d1117:dark; do
  (
    bg=${theme%%:*}
    suffix=${theme##*:}
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    ffmpeg -y -v error -i "$vid" -i frame.png -filter_complex \
      "color=c=0x${bg}:s=${W}x${H}:r=12[bg];[0:v]setpts=PTS/1.6,fps=12,scale=${VW}:${VH}:flags=lanczos[vid];[bg][vid]overlay=${VX}:${VY}:shortest=1[tmp];[tmp][1:v]overlay=0:0" \
      "${work}/full.mp4"
    python3 "${here}/trim_holds.py" "${work}/full.mp4" "${work}/frames"
    img2webp -loop 0 -d 83 -q 48 -m 6 -mixed "${work}"/frames/*.png -o "${name}-${suffix}.webp"
  ) &
done
wait
