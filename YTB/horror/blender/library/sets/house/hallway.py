"""Haru's house, upstairs: the hallway and landing (built with the room kit, library/sets/kit.py).

Floor plan (metres at 1:10; +y runs away from the camera, the near end is open for filming):
    the corridor is 13 cm wide (x -0.065..0.065) and 60 cm long (y 0..0.6), ceiling 25 cm;
    left wall: Haru's bedroom door (ajar, her lamp spilling out) and the bathroom door (shut);
    right wall: the stairwell (stairs going down toward the camera, banister along the corridor) and the linen
    cupboard; far wall: a window with the moon, a radiator under it.
Dressing: a long runner rug, crooked family photos, a wall lamp between the doors.

    blender -b -P library/sets/house/hallway.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--marks a,b]
renders a still from each camera mark (wide, low, stairs, door) unless --marks narrows it.
"""
import bpy, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, n=1, default=None):
    if '--' + name not in argv: return default
    i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'hallway')))
MARKS = (opt('marks') or 'wide,low,stairs,door').split(',')

K.begin('hallway', res=RES, samples=int(opt('samples', 1, '64')))
X0, X1, XS, Y1 = -0.065, 0.065, 0.165, 0.6          # corridor sides, stairwell outer side, far end
SW = (X1, 0.15, XS, 0.45)                            # stairwell hole (x0, y0, x1, y1)

K.floor((X0, 0.0, XS, Y1), holes=[SW])
K.ceiling((X0, 0.0, XS, Y1))
K.wall((X0, 0.0), (X0, Y1), inward=-1, openings=[
    K.door(0.06, 0.14, angle=28, hinge='start', spill=(0.35, (1.0, 0.66, 0.35))),     # Haru's bedroom, ajar
    K.door(0.38, 0.46, angle=0, hinge='end')])                                         # bathroom, shut
K.wall((X1, 0.0), (X1, SW[1]), inward=1)
K.wall((X1, SW[3]), (X1, Y1), inward=1, openings=[K.door(0.05, 0.11, h=0.19, angle=0, hinge='end')])   # linen cupboard
K.wall((X0, Y1), (X1, Y1), inward=-1, openings=[K.window(0.035, 0.095, 0.08, 0.19, moon=True)])
# the stairwell: walls going down below the floor, stairs coming down toward the camera, a landing at the bottom
for (a, b, c, d, z0) in ((XS, SW[1] - 0.12, XS + K.WT, SW[3], -0.24), (X1, SW[3], XS + K.WT, SW[3] + K.WT, -0.24),
                         (X1, SW[1] - K.WT, XS + K.WT, SW[1], -0.012)):          # the near end only above the floor:
    K.block('stairwell_wall', a, c, b, d, z0, K.H, K.M['wall'], bevel=0.0004)     # the flight runs on under it
K.stairs_down(X1 + 0.004, XS - 0.004, SW[3], -1, n=12)
K.block('lower_landing', X1, XS, SW[1] - 0.1, SW[3] - 0.3, -0.226, -0.216, K.M['floor'], bevel=0.0004, coll=True)
K.banister(X1 + 0.003, SW[1], SW[3])

K.runner(-0.03, 0.03, 0.03, 0.56)
K.picture((X0 + K.WT / 2 + 0.001, 0.24, 0.135), (0.028, 0.036), normal=(1, 0, 0))
K.picture((X0 + K.WT / 2 + 0.001, 0.31, 0.15), (0.022, 0.028), normal=(1, 0, 0))
K.picture((X0 + K.WT / 2 + 0.001, 0.205, 0.165), (0.018, 0.022), normal=(1, 0, 0))
K.picture((X1 - K.WT / 2 - 0.001, 0.08, 0.14), (0.032, 0.024), normal=(-1, 0, 0))
K.picture((X1 - K.WT / 2 - 0.001, 0.52, 0.215), (0.02, 0.02), normal=(-1, 0, 0), crooked=9)
K.radiator((0.0, Y1 - K.WT / 2 - 0.001, 0.0), width=0.06, normal=(0, -1, 0))
K.sconce((X0 + K.WT / 2 + 0.001, 0.27, 0.165), normal=(1, 0, 0), energy=0.6)
low = K.point_light('downstairs_glow', (0.115, 0.09, -0.17), 0.25, radius=0.03, color=(1.0, 0.72, 0.45)); K._to(low, 'Lights')   # a lamp left on downstairs

K.mood('night', moon_from=(0.02, 0.95, 0.32), moon_to=(0.0, 0.35, 0.0), bounds=(X0, 0.0, -0.25, XS, Y1, K.H))

K.mark('wide', (0.0, 0.005, 0.1), (0.0, 0.5, 0.075), lens=20)                 # down the corridor from the near end
K.mark('low', (0.035, 0.02, 0.018), (-0.015, 0.5, 0.06), lens=20)             # Haru's eye level, low
K.mark('stairs', (0.115, 0.44, 0.16), (0.115, 0.2, -0.14), lens=18)          # from the top, straight down the flight
K.mark('door', (0.04, 0.22, 0.075), (X0, 0.1, 0.08), lens=26)                 # at her bedroom door

if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
os.makedirs(OUT, exist_ok=True)
for m in MARKS: K.shoot(m, OUT, fstop=float(opt('fstop', 1, '5.6')))
print('DONE hallway', OUT)
