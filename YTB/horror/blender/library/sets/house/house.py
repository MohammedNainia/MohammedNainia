"""Haru's whole house as one doll's house: every room built on the plan (plan.py) at its level, doors lining up,
the stairs joining the upstairs hallway to the ground-floor hall, the attic on top, the front open.

Use it two ways:
  * as a set for a scene: `import house; house.build()` builds everything into the current scene (after kit.begin)
    and returns {room: [objects]}; camera marks are renamed cam_<room>_<mark>.
  * on its own, to look at it: renders the doll's-house view and a few cutaways, with two test Harus in it.

    blender -b -P library/sets/house/house.py -- [--blend OUT.blend] [--out DIR] [--res W H] [--samples N] [--no-haru]
"""
import bpy, os, sys, math
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import plan
import hallway, bathroom, bedroom, attic, kitchen, living_room, hall

ROOMS = [('living_room', living_room), ('kitchen', kitchen), ('hall', hall),
         ('bedroom', bedroom), ('bathroom', bathroom), ('hallway', hallway), ('attic', attic)]

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def opt(name, n=1, default=None):
    if '--' + name not in argv: return default
    i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]


def build():
    K.HOUSE = True
    out = {}
    for name, mod in ROOMS:
        before = set(bpy.data.objects)
        mod.build(house=True)
        new = [o for o in bpy.data.objects if o not in before]
        z = plan.LEVEL[name]
        coll = bpy.data.collections.new('room_' + name); bpy.context.scene.collection.children.link(coll)
        for o in new:
            if o.parent is None: o.location.z += z
            coll.objects.link(o)
            if o.name.startswith('cam_'): o.name = 'cam_' + name + '_' + o.name[4:].split('.')[0]
        out[name] = new
    K.HOUSE = False
    # one cold fill and one thin haze for the whole house; the night outside: dark ground all round
    x0, y0, x1, y1 = plan.FOOTPRINT
    f = K.area_light('house_fill', ((x0 + x1) / 2, -0.6, 0.35), ((x0 + x1) / 2, 0.3, 0.25), 2.0, 0.6, (0.5, 0.6, 0.9)); K._to(f, 'Lights')
    K.mood('night', bounds=(x0 + 0.005, y0, 0.0, x1 - 0.005, y1 - 0.005, plan.UP + K.H), haze_density=0.35)   # inside the walls only
    g = K.block('night_ground', x0 - 1.5, x1 + 1.5, y0 - 1.5, y1 + 1.5, -0.03, -0.012, K.painted('night_ground', (0.03, 0.04, 0.03), rough=0.95), bevel=0)
    return out


if __name__ == '__main__':
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'house')))
    K.begin('house', res=RES, samples=int(opt('samples', 1, '64')))
    build()
    if '--no-haru' not in argv:                                   # two test Harus: living room and her bedroom
        sys.path.insert(0, os.path.join(K.BL, 'puppets'))
        import haru_clay as HC
        h1 = HC.HaruClay(loc=(-0.1, 0.11, 0.0), yaw=math.radians(20), name='haru_lr'); h1.pose({}); h1.ground(floor=0.0)
        h2 = HC.HaruClay(loc=(-0.12, 0.08, plan.UP), yaw=math.radians(-15), name='haru_br'); h2.pose({}); h2.ground(floor=plan.UP)
        h1.expr('neutral'); h2.expr('worried')
    x0, y0, x1, y1 = plan.FOOTPRINT; cx = (x0 + x1) / 2
    K.mark('dollhouse', (cx, -1.25, 0.4), (cx, 0.3, 0.38), lens=42)                        # the whole house, front open
    K.mark('ground', (cx, -0.62, 0.12), (cx, 0.3, 0.1), lens=30)                           # the ground floor
    K.mark('upstairs', (cx, -0.62, plan.UP + 0.12), (cx, 0.3, plan.UP + 0.1), lens=30)     # the upstairs
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'dollhouse,ground,upstairs').split(','): K.shoot(m, OUT, fstop=float(opt('fstop', 1, '11')))
    print('DONE house', OUT)
