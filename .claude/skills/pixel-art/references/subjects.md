# Subjects: proportions and build recipes (in head-units; h = head height in px)

## Humans
- Chibi: 2 to 3 heads. Game standard: 4 to 5. Heroic/realistic (detailed sprites, 96 px+): 7 to 8.
- Recipe (realistic, total height T, head h = T/7.5):
  head `ellipsoid` (rx=.42h, ry=.5h); neck capsule; torso capsule shoulders->hips (r .9h -> .7h); upper/lower arms and legs
  as tapered capsules (upper arm r .32h, forearm .26h, thigh .45h, shin .32h); hands/feet small ellipsoids;
  clothing = poly panels with bevel on top (cloaks, robes, tabards) with z0 slightly above the body.
- Faces at small sizes: 1 to 2 px eyes, a nose shadow pixel, no mouth unless needed. Expression comes from the brows (1 px).

## Animals
- Quadruped: body ellipsoid (long), chest ellipsoid in front, head ellipsoid + muzzle capsule, four tapered leg capsules
  (far legs z0 lower and one shade darker via contour), tail capsule.
- Birds: body ellipsoid, wing poly with bevel (feather steps via `pattern()` stripes), beak `cone()`.

## Monsters
- Start from an animal or human base and break one rule: extra limbs, a mouth too big, wrong joints, a missing face.
- Size contrast sells scale: put a tiny human next to it.

## Architecture
- Walls: `box` with bevel 1; masonry/tiles with `pattern()`; arches with `arch(kind=...)`; roofs as `poly` with `tilt`.
- Perspective: keep to front view or simple 3/4; parallax by layering (far = lower contrast, cooler, smaller).
