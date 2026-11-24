#!/usr/bin/env bash
# Measure Blender Haru's ID renders (YTB/horror/blender/measure/id_view{0,2,4}.png) against the Artlist turnaround sheet.
# Run build_haru.py's id_renders() in Blender first. Needs uv (or a python with pillow + numpy as PY).
set -e
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
S="$ROOT/.claude/skills/clay-character/scripts"; W="$ROOT/YTB/horror/blender/measure"
SHEET="$ROOT/YTB/channel_art/haru_turnaround_sheet.png"
PY="${PY:-${UV:-uv} run --quiet --no-project --with pillow --with numpy python}"
for v in 0 2 4; do
  [ -s "$W/ref_view$v.json" ] || $PY "$S/measure.py" sheet "$SHEET" --view $v > "$W/ref_view$v.json"
  $PY "$S/measure.py" ids "$W/id_view$v.png" --view 0 > "$W/ours_view$v.json"
  echo "--- view $v"; $PY "$S/compare.py" "$W/ref_view$v.json" "$W/ours_view$v.json"
done
(cd "$S" && $PY overlay.py "$SHEET" "$W/id_view0.png" "$W/overlay0.png")
