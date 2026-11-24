"""Side by side: the Artlist concept (front turnaround + look-back pose) next to Blender Haru frames.
uv run --no-project --with pillow python compare_board.py OUT.png OURS1.png [OURS2.png ...]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / 'YTB' / 'channel_art'
H = 900


def fit(im, h=H):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def cell(sheet, cols, rows, c, r):
    w, h = sheet.width / cols, sheet.height / rows
    return sheet.crop((round(c * w), round(r * h), round((c + 1) * w), round((r + 1) * h)))


turn = Image.open(ART / 'haru_turnaround_sheet.png').convert('RGB')
poses = Image.open(ART / 'haru_poses_sheet.png').convert('RGB')
refs = [fit(cell(turn, 5, 1, 0, 0)), fit(cell(poses, 4, 2, 1, 1))]
ours = [fit(Image.open(p).convert('RGB')) for p in sys.argv[2:]]
gap = 16
W = sum(i.width for i in refs + ours) + gap * (len(refs + ours) + 2)
out = Image.new('RGB', (W, H + 60), (24, 24, 24))
d = ImageDraw.Draw(out); x = gap
d.text((x, 18), 'ARTLIST CONCEPT', fill=(230, 180, 60))
for im in refs: out.paste(im, (x, 50)); x += im.width + gap
x += gap
d.text((x, 18), 'BLENDER CLAY (v1)', fill=(230, 180, 60))
for im in ours: out.paste(im, (x, 50)); x += im.width + gap
out.save(sys.argv[1]); print(sys.argv[1], out.size)
