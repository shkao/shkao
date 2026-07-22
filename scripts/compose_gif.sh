#!/usr/bin/env bash
# Composite a recorded walkthrough into the iPhone frame as light + dark GIFs.
# Usage: compose_gif.sh <video.webm> <output-basename>
# Needs frame.png and frame.env in the working directory (both written by
# make_frame.py), plus ffmpeg and gifsicle. The two encodes run in parallel.
set -euo pipefail
vid=$1
name=$2
source frame.env  # W H VX VY VW VH
for theme in ffffff:light 0d1117:dark; do
  (
    bg=${theme%%:*}
    suffix=${theme##*:}
    ffmpeg -y -v error -i "$vid" -i frame.png -filter_complex \
      "color=c=0x${bg}:s=${W}x${H}:r=15[bg];[0:v]setpts=PTS/1.6,fps=15,scale=${VW}:${VH}:flags=lanczos[vid];[bg][vid]overlay=${VX}:${VY}:shortest=1[tmp];[tmp][1:v]overlay=0:0,split[s0][s1];[s0]palettegen=max_colors=256:reserve_transparent=0[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
      "${name}-${suffix}.gif"
    gifsicle -O3 --lossy=30 "${name}-${suffix}.gif" -o "${name}-${suffix}.gif"
  ) &
done
wait
