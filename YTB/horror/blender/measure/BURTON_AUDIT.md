# Audit: Blender Burton Haru vs the Artlist sheet (2026-11-24)

Reference: `YTB/channel_art/burton_turnaround.png`. Build: `puppets/haru_burton.py`.
Method: the sheet is split into parts by colour (`burton_measure.py`; hair, skin, hoodie, trousers, shoes); the
build is rendered with flat part colours, orthographic, front / side / back (`scenes/haru_sheet.py --mode id
--puppet burton`) and measured with the clay-character skill's `measure.py`. Landmarks are fractions of her height
from the top of the hair (0) to the soles (1). Silhouette overlays at equal height: `burton_overlay_{0,2,4}.png`.
Full numbers: `burton_audit_numbers.txt`.

## Front view, sheet vs build

| | sheet | first build | after the fixes |
|---|---|---|---|
| chin (where skin meets the hood) | 0.248 | 0.276 | **0.251** |
| hoodie hem | 0.637 | 0.654 | 0.659 (cuffs hang a little lower than the sheet's) |
| trouser hem | 0.912 | 0.921 | 0.922 |
| shoes top | 0.916 | 0.922 | 0.924 |
| hair width | 0.254 | 0.260 | 0.263 |
| face width (with ears) | 0.270 | 0.161 | **0.240** |
| hoodie width at the middle | 0.278 | 0.275 | 0.274 |
| hoodie width at the hem | 0.304 | 0.317 | 0.313 |
| trousers width | 0.142 | 0.133 | 0.131 |

Hands end at 0.71 on the sheet (read by eye; the script counts her bare ankles as skin) and 0.726 on the build.
Front hair ends at about 0.39 on both.

## What the audit found, and what was fixed

1. **Face too narrow, ears hidden.** The side hair sat over her cheeks. Fixed: wider head (x radius 0.128 -> 0.142),
   hair cap and side sheets set back and outside the cheeks, ears moved out so they peek through the hair.
2. **Tall bowl collar, long neck.** Fixed: the hood opening is a low, shallow V resting on the shoulders; shoulders
   filled up under it; head lengthened so the chin sits where the sheet's does (0.251 vs 0.248).
3. **Hoodie too flat from the side.** Fixed: about 6 cm deeper (in her 1.26 m units); side-view middle depth 0.124 -> 0.153 (sheet 0.170).
4. **Hands tiny and claw-like.** Fixed: bigger palms, long spindly fingers, turned in so the backs show from the front.
5. **Sneakers too short.** Fixed: about 35% longer.
6. **Faint eye rings, bead nose.** Fixed: darker, wider grey-purple rings; a small soft pointed nose.
7. **Short drawstrings, hem slightly low.** Fixed: drawstrings hang to the chest with knots; hem raised.
8. **Bald stripe at the crown** after the head was lengthened. Fixed: bigger hair cap.

## Deliberate differences

- **Eyes about 25% smaller than the sheet's**, at your request ("too big, looks like a cockroach").
- **Mechanical face**: eyelids and pupils act the expressions (sheet shows one neutral face).

## Still different (next pass if wanted)

- Hood shape: the sheet's hood is a draped fabric V with folds; ours is a smooth rolled collar.
- Sneakers: still soft rounded shapes, not crisp canvas sneakers with toe caps and stitched soles.
- Side view: the face shows a little less past the hair than on the sheet (face width 0.087 vs 0.129).
- Sleeve cuffs hang about 2% lower than the sheet's.
- A faint line where the crown hair meets the shoulder hair can show in some angles.
