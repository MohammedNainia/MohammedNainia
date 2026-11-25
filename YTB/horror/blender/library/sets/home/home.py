"""Haru's whole home (version 2): the four floors stacked into one building on the plan (plan.py).

  * as a set: `import home; home.build()` after kit.begin(); every object goes into a collection per floor
    (home_basement, home_ground, home_upstairs, home_attic) and camera marks are renamed cam_<floor>_<mark>.
    hide_wild(floor) hides the front walls of a floor for a shot that looks in from the front.
  * on its own: renders the doll's-house view of the whole house and one per floor.

    blender -b -P library/sets/home/home.py -- [--out DIR] [--res W H] [--samples N] [--marks a,b] [--blend F]
"""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import kit as K
import plan as PL
import basement, ground, upstairs, attic

FLOORS = [('basement', basement, PL.LEVEL['basement']), ('ground', ground, PL.LEVEL['ground']),
          ('upstairs', upstairs, PL.LEVEL['upstairs']), ('attic', attic, PL.LEVEL['attic'])]


def build():
    out = {}
    for name, mod, z in FLOORS:
        before = set(bpy.data.objects)
        mod.build(house=True)
        new = [o for o in bpy.data.objects if o not in before]
        coll = bpy.data.collections.new('home_' + name); bpy.context.scene.collection.children.link(coll)
        for o in new:
            if o.parent is None: o.location.z += z
            coll.objects.link(o)
            if o.name.startswith('cam_'): o.name = 'cam_' + name + '_' + o.name[4:].split('.')[0]
        out[name] = new
    x0, y0, x1, y1 = PL.FOOTPRINT
    K.mood('night', bounds=(x0 + 0.005, y0, PL.LEVEL['basement'], x1 - 0.005, y1 - 0.005, PL.LEVEL['attic']), haze_density=0.3)
    g = K.painted('night_ground', (0.03, 0.04, 0.03), rough=0.95)                 # the garden ground, round the house
    for (a, b, c, d) in ((x0 - 2, x1 + 2, y1, y1 + 2), (x0 - 2, x0, y0 - 2, y1), (x1, x1 + 2, y0 - 2, y1), (x0, x1, y0 - 2, y0 - 0.002)):
        gb = K.block('night_ground', a, b, c, d, -0.03, -0.012, g, bevel=0); gb.modifiers.clear()   # flat, not rounded
    return out


def hide_wild(floor_objs, hide=True):
    """hide (or show) the walls marked wild on a floor, with everything parented to them"""
    for o in floor_objs:
        if o.get('wild'):
            for c in [o] + list(o.children_recursive): c.hide_render = hide; c.hide_viewport = hide


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    def opt(name, n=1, default=None):
        if '--' + name not in argv: return default
        i = argv.index('--' + name); v = argv[i + 1:i + 1 + n]; return v if n > 1 else v[0]
    RES = tuple(int(v) for v in opt('res', 2, ('1080', '1920')))
    OUT = os.path.abspath(opt('out', 1, os.path.join(HERE, 'previews', 'home')))
    K.begin('home', res=RES, samples=int(opt('samples', 1, '64')))
    floors = build()
    for f in ('ground', 'upstairs', 'attic'): hide_wild(floors[f])
    f = K.area_light('front_fill', (0.5, -1.2, 0.5), (0.5, 0.4, 0.3), 3.0, 1.0, (0.5, 0.6, 0.9)); K._to(f, 'Lights')
    K.mark('house', (0.5, -2.4, 0.42), (0.5, 0.6, 0.4), lens=30)                 # the whole doll's house
    K.mark('house_ground', (0.5, -1.05, 0.13), (0.5, 0.4, 0.1), lens=24)
    K.mark('house_upstairs', (0.5, -1.05, 0.39), (0.5, 0.4, 0.36), lens=24)
    K.mark('house_attic', (0.5, -1.05, 0.68), (0.5, 0.4, 0.64), lens=24)
    if opt('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt('blend')))
    os.makedirs(OUT, exist_ok=True)
    for m in (opt('marks') or 'house,house_ground,house_upstairs,house_attic').split(','): K.shoot(m, OUT, fstop=float(opt('fstop', 1, '11')))
    print('DONE home', OUT)
