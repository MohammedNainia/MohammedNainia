"""The lights kit: the real light sources in a room (practicals), each one switchable and able to flicker, so a scene
can stage the classic light scares in a line or two (1:10 scale, metres). Looks follow refs/props/lamps_set.jpg.

    import practicals as PL
    lamp = PL.Lamp(x, y, z=0.045, yaw=0)            # table / bedside lamp: fabric shade that glows, pool of light
    bulb = PL.Bulb(x, y, ceiling=K.H, drop=0.06)     # bare bulb on a cord; bulb.sway(f0, f1, deg)
    cnd  = PL.Candle(x, y, z)                        # cnd.burn(f0, f1): the flame moves on its own
    ph   = PL.Phone(x, y, z, yaw, tilt=90)           # screen light; parent ph.h to a hand to hold it
    tv   = PL.TV(x, y, yaw, static=True)             # CRT: blue glow, or snow when static=True
    ceil = PL.CeilingLight(x, y, ceiling=K.H)
    sw   = PL.switch(holder_or_None, x, y, z, yaw)   # a light switch plate (the click before the dark)

Every light has the same controls (each keys the frame it gets; f=None just sets it):
    L.level(f, 0..1)            0 off, 1 its normal brightness (in between for dimmed or dying)
    L.on(f) / L.off(f)
    L.flicker(f0, f1, kind)     'dying' (mostly on, sudden drops and outs), 'candle' (soft, never out),
                                'tv' (restless), 'buzz' (fast small shakes); seed= for a different pattern
    L.fade(f0, f1, a, b)        a slow fade from a to b
    L.src()                     where the light is (world), to aim the clay key: rake.aim(f, head, cam, L.src(), on)
"""
import bpy, math, random
from mathutils import Vector
import kit as K
import burton_materials as BM
from claylib import sphere, cylinder, empty, point_light, area_light


def _emit_mat(name, color, strength, base=None, mix=1.0):
    """an emissive surface whose glow can be keyed (base: a diffuse colour it shows when off)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
    pb = N['Principled BSDF']; pb.inputs['Base Color'].default_value = (*(base or color), 1); pb.inputs['Roughness'].default_value = 0.85
    pb.inputs['Emission Color'].default_value = (*color, 1); pb.inputs['Emission Strength'].default_value = strength
    return m, pb.inputs['Emission Strength']


class Practical:
    def __init__(self, name, x, y, z=0.0, yaw=0.0):
        self.h = empty(name, (x, y, z)); K._to(self.h); self.h.rotation_euler = (0, 0, math.radians(yaw))
        self.lights = []; self.glows = []; self.cur = 1.0

    def _light(self, ob, energy):
        K._to(ob, 'Lights'); self.lights.append((ob, energy))
        ob.visible_camera = False                                           # the glowing surfaces are what the camera sees
        return ob

    def _glow(self, sock, strength):
        self.glows.append((sock, strength))

    def _part(self, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0008, par=None):
        return K.attach(K.block(name, x0, x1, y0, y1, z0, z1, mat, bevel=bevel), par or self.h)

    def _put(self, ob, loc, par=None):
        K._to(ob); K.attach(ob, par or self.h); ob.location = loc; return ob

    def level(self, f, v):
        self.cur = v
        for ob, e in self.lights:
            ob.data.energy = e * v
            if f is not None: ob.data.keyframe_insert('energy', frame=f)
        for s, g in self.glows:
            s.default_value = g * v
            if f is not None: s.keyframe_insert('default_value', frame=f)

    def on(self, f=None): self.level(f, 1.0)
    def off(self, f=None): self.level(f, 0.0)

    def fade(self, f0, f1, a, b):
        for f in range(f0, f1 + 1):
            t = (f - f0) / max(1, f1 - f0); t = t * t * (3 - 2 * t); self.level(f, a + (b - a) * t)

    def flicker(self, f0, f1, kind='dying', seed=1, base=1.0):
        r = random.Random(seed); out = 0
        for f in range(f0, f1 + 1):
            if kind == 'dying':
                if out > 0: v = 0.0; out -= 1
                elif r.random() < 0.08: out = r.randint(1, 4); v = 0.0              # drops out for a few frames
                elif r.random() < 0.2: v = r.uniform(0.25, 0.7)                     # a weak stutter
                else: v = r.uniform(0.92, 1.05)
            elif kind == 'candle': v = r.uniform(0.75, 1.1)
            elif kind == 'tv': v = r.uniform(0.55, 1.2) if r.random() < 0.6 else r.uniform(0.9, 1.0)
            else: v = r.uniform(0.85, 1.0)                                          # buzz
            self.level(f, v * base)
        self.level(f1 + 1, base)

    def src(self):
        bpy.context.view_layer.update()
        ob = self.lights[0][0] if self.lights else self.h
        return ob.matrix_world.translation.copy()


# ------------------------------------------------------------------ the lights
class Lamp(Practical):
    """table or bedside lamp: a turned base, a fabric shade that glows when on, the bulb inside. The shade blocks the
    sideways light, so it throws a warm pool down on the table and a ring up the wall, like a real lamp."""
    def __init__(self, x, y, z=0.0, yaw=0.0, energy=0.6, color=(1.0, 0.66, 0.35), shade='#d8c49a', size=1.0):
        Practical.__init__(self, 'lamp', x, y, z, yaw); k = size
        base = cylinder('lamp_base', 0.0055 * k, 0.004 * k, (0, 0, 0), verts=32, mat=K.M['wood']); self._put(base, (0, 0, 0.002 * k))
        body = sphere('lamp_body', 0.0055 * k, (0, 0, 0), scale=(1, 1, 1.25), mat=K.M['wood']); self._put(body, (0, 0, 0.0095 * k))
        stem = cylinder('lamp_stem', 0.0009 * k, 0.012 * k, (0, 0, 0), verts=12, mat=K.M['brass']); self._put(stem, (0, 0, 0.02 * k))
        bm, glow = _emit_mat('lamp_shade', (1.0, 0.7, 0.4), 3.0, base=tuple(v / 255 for v in bytes.fromhex(shade.lstrip('#'))))
        self._glow(glow, 3.0)
        bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.011 * k, radius2=0.0065 * k, depth=0.012 * k, end_fill_type='NOTHING')
        sh = bpy.context.object; sh.name = 'lamp_shade'; sh.data.materials.append(bm)
        sol = sh.modifiers.new('cloth', 'SOLIDIFY'); sol.thickness = 0.0004
        for p in sh.data.polygons: p.use_smooth = True
        self._put(sh, (0, 0, 0.028 * k)); K.add_lumps(sh, 0.00015, size=0.006)
        bb, bglow = _emit_mat('lamp_bulb', (1.0, 0.8, 0.55), 25.0); self._glow(bglow, 25.0)
        bu = sphere('lamp_bulb', 0.0024 * k, (0, 0, 0), mat=bb); self._put(bu, (0, 0, 0.026 * k)); bu.visible_shadow = False
        lt = point_light('lamp_light', (0, 0, 0), energy, radius=0.002 * k, color=color); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, 0, 0.026 * k)


class Bulb(Practical):
    """a bare bulb hanging on a cord from the ceiling (hallways, basements, attics); it can sway"""
    def __init__(self, x, y, ceiling=K.H, drop=0.06, energy=0.9, color=(1.0, 0.72, 0.42)):
        Practical.__init__(self, 'bulb', x, y, ceiling, 0.0)
        self.pv = empty('bulb_pivot', (0, 0, 0)); K._to(self.pv); K.attach(self.pv, self.h)
        rose = cylinder('ceiling_rose', 0.004, 0.002, (0, 0, 0), verts=24, mat=K.M['trim']); self._put(rose, (0, 0, -0.001))
        cord = cylinder('bulb_cord', 0.0004, drop, (0, 0, 0), verts=8, mat=K.M['wood']); self._put(cord, (0, 0, -drop / 2), self.pv)
        sock = cylinder('bulb_socket', 0.0016, 0.004, (0, 0, 0), verts=16, mat=K.M['wood']); self._put(sock, (0, 0, -drop - 0.002), self.pv)
        gm, glow = _emit_mat('bare_bulb', (1.0, 0.82, 0.55), 40.0, base=(0.6, 0.6, 0.55)); self._glow(glow, 40.0)
        bu = sphere('bare_bulb', 0.0032, (0, 0, 0), scale=(1, 1, 1.3), mat=gm); self._put(bu, (0, 0, -drop - 0.0075), self.pv)
        bu.visible_shadow = False
        lt = point_light('bulb_light', (0, 0, 0), energy, radius=0.002, color=color); self._light(lt, energy)
        K.attach(lt, self.pv); lt.location = (0, 0, -drop - 0.0075)

    def sway(self, f0, f1, deg=6.0, period=36, axis=(1, 0.3)):
        """swinging after a bump (it dies away), deg at the start, period in frames"""
        for f in range(f0, f1 + 1):
            t = f - f0; a = math.radians(deg) * math.exp(-t / max(1.0, (f1 - f0) / 2.5)) * math.sin(2 * math.pi * t / period)
            self.pv.rotation_euler = (a * axis[1], a * axis[0], 0); self.pv.keyframe_insert('rotation_euler', frame=f)


class Candle(Practical):
    """a candle on a saucer: drippy wax, a wick, a flame that never sits still, warm small light"""
    def __init__(self, x, y, z=0.0, height=0.016, energy=0.12, color=(1.0, 0.6, 0.3)):
        Practical.__init__(self, 'candle', x, y, z, 0.0); hgt = self.hgt = height
        dish = cylinder('candle_dish', 0.0065, 0.0012, (0, 0, 0), verts=32, mat=K.M['brass']); self._put(dish, (0, 0, 0.0006))
        wax_m = K.painted('candle_wax', (0.82, 0.78, 0.66), rough=0.5)
        wax = cylinder('candle_wax', 0.0028, hgt, (0, 0, 0), verts=32, mat=wax_m); self._put(wax, (0, 0, 0.0012 + hgt / 2))
        K.add_lumps(wax, 0.00018, size=0.004)
        for a in (0.4, 2.1, 4.0):                                                       # drips down the side
            d = sphere('candle_drip', 0.0007, (0, 0, 0), scale=(1, 1, 3.2), mat=wax_m)
            self._put(d, (0.0027 * math.cos(a), 0.0027 * math.sin(a), 0.0012 + hgt * 0.78))
        wick = cylinder('candle_wick', 0.00025, 0.0016, (0, 0, 0), verts=8, mat=K.M['void']); self._put(wick, (0, 0, 0.0012 + hgt + 0.0007))
        fm, glow = _emit_mat('candle_flame', (1.0, 0.62, 0.22), 30.0); self._glow(glow, 30.0)
        self.flame = sphere('candle_flame', 0.0009, (0, 0, 0), scale=(1, 1, 2.4), mat=fm)
        self._put(self.flame, (0, 0, 0.0012 + hgt + 0.0024)); self.flame.visible_shadow = False
        lt = point_light('candle_light', (0, 0, 0), energy, radius=0.0015, color=color); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, 0, 0.0012 + hgt + 0.0035)

    def burn(self, f0, f1, seed=3):
        """the flame leans and stretches every frame and the light breathes with it"""
        r = random.Random(seed); z0 = 0.0012 + self.hgt + 0.0024
        for f in range(f0, f1 + 1):
            s = r.uniform(0.85, 1.15)
            self.flame.scale = (1, 1, 2.4 * s); self.flame.location = (r.uniform(-0.0003, 0.0003), r.uniform(-0.0003, 0.0003), z0 + 0.0003 * (s - 1))
            self.flame.keyframe_insert('scale', frame=f); self.flame.keyframe_insert('location', frame=f)
        self.flicker(f0, f1, 'candle', seed=seed)


class Phone(Practical):
    """a phone (1:10, 1.5 x 0.7 cm): dark body, the screen glows and lights whatever is in front of it (her face from
    below). tilt 0 = lying face up, 90 = standing up facing -y. Parent phone.h to a hand empty to hold it."""
    def __init__(self, x, y, z=0.0, yaw=0.0, tilt=0.0, energy=0.004, color=(0.75, 0.85, 1.0)):
        Practical.__init__(self, 'phone', x, y, z, yaw)
        self.h.rotation_euler = (math.radians(tilt), 0, math.radians(yaw))
        self._part('phone_body', -0.0035, 0.0035, -0.0075, 0.0075, 0.0, 0.0008, K.painted('phone_black', (0.02, 0.02, 0.025), rough=0.25), bevel=0.0006)
        sm, glow = _emit_mat('phone_screen', color, 2.5, base=(0.01, 0.01, 0.012)); self._glow(glow, 2.5)
        self._part('phone_screen', -0.0031, 0.0031, -0.0068, 0.0068, 0.0008, 0.00095, sm, bevel=0)
        lt = area_light('phone_light', (0, 0, 0), (0, 0, 1), energy, 0.01, color); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, 0, 0.0012)
        lt.rotation_euler = (math.pi, 0, 0)                                  # area lights shine down -z: turn it out of the screen


class TV(Practical):
    """an old CRT on a low cabinet. static=False: a soft blue glow; True: snow (moving noise) and a restless light"""
    def __init__(self, x, y, yaw=0.0, z=0.0, energy=0.4, static=False, cabinet=True):
        Practical.__init__(self, 'tv', x, y, z, yaw); self.static = static
        z0 = 0.03 if cabinet else 0.0
        if cabinet: self._part('tv_cabinet', -0.032, 0.032, 0.0, 0.034, 0.0, 0.03, K.M['wood'], bevel=0.0015)
        shell = K.painted('tv_shell', (0.06, 0.055, 0.05), rough=0.5)
        self._part('tv_body', -0.026, 0.026, 0.004, 0.034, z0, z0 + 0.044, shell, bevel=0.006)
        for sd in (1, -1):                                                              # rabbit-ear aerial
            ant = cylinder('tv_aerial', 0.0004, 0.03, (0, 0, 0), verts=8, mat=K.M['metal'])
            self._put(ant, (sd * 0.005, 0.02, z0 + 0.044 + 0.013)); ant.rotation_euler = (0, sd * 0.5, 0)
        m = bpy.data.materials.new('tv_screen_live'); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links
        pb = N['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.02, 0.025, 0.03, 1); pb.inputs['Roughness'].default_value = 0.15
        if static:
            nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 45.0
            nz.inputs['Detail'].default_value = 0.0; self.noise_w = nz.inputs['W']
            ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.4; ramp.color_ramp.elements[1].position = 0.6
            L.new(nz.outputs['Fac'], ramp.inputs[0]); L.new(ramp.outputs[0], pb.inputs['Emission Color'])
        else:
            pb.inputs['Emission Color'].default_value = (0.5, 0.65, 1.0, 1)
        g = 0.7 if static else 2.0
        pb.inputs['Emission Strength'].default_value = g; self._glow(pb.inputs['Emission Strength'], g)
        self._part('tv_screen', -0.02, 0.016, 0.003, 0.005, z0 + 0.007, z0 + 0.038, m, bevel=0.003)
        for kx in (0.0205, 0.0205):
            kn = cylinder('tv_knob', 0.0018, 0.002, (0, 0, 0), verts=16, mat=K.M['metal'], rot=(math.pi / 2, 0, 0)); self._put(kn, (kx, 0.003, z0 + 0.03))
        col = (0.85, 0.9, 1.0) if static else (0.55, 0.7, 1.0)
        gl = area_light('tv_glow', (0, 0, 0), (0, -1, 0), energy, 0.035, col); self._light(gl, energy)
        K.attach(gl, self.h); gl.location = (0, -0.003, z0 + 0.022); gl.rotation_euler = (math.radians(90), 0, 0)
        gl.visible_glossy = False                                           # or it shows as a white disc in the glass

    def snow(self, f0, f1):
        """the static moves every frame (and the light jumps with it)"""
        if not self.static: return
        for f in range(f0, f1 + 1):
            self.noise_w.default_value = f * 1.37; self.noise_w.keyframe_insert('default_value', frame=f)
        self.flicker(f0, f1, 'tv')


class CeilingLight(Practical):
    """a frosted glass dome on the ceiling: the room's main light (the one the switch turns off)"""
    def __init__(self, x, y, ceiling=K.H, energy=2.5, color=(1.0, 0.78, 0.55)):
        Practical.__init__(self, 'ceiling_light', x, y, ceiling, 0.0)
        gm, glow = _emit_mat('ceiling_dome', (1.0, 0.85, 0.62), 6.0, base=(0.75, 0.73, 0.68)); self._glow(glow, 6.0)
        d = sphere('ceiling_dome', 0.012, (0, 0, 0), scale=(1, 1, 0.45), mat=gm); self._put(d, (0, 0, -0.002)); d.visible_shadow = False
        rim = cylinder('ceiling_rim', 0.0125, 0.0015, (0, 0, 0), verts=40, mat=K.M['brass']); self._put(rim, (0, 0, -0.0008))
        lt = point_light('ceiling_light', (0, 0, 0), energy, radius=0.008, color=color); self._light(lt, energy)
        K.attach(lt, self.h); lt.location = (0, 0, -0.009)


def switch(x, y, z=0.12, yaw=0.0, holder=None):
    """a light switch plate on a wall, facing -y in its own frame (yaw turns it); returns the toggle (key its rotation
    to show the click: rotation_euler.x = +-0.35)"""
    h = empty('light_switch', (x, y, z)); K._to(h); h.rotation_euler = (0, 0, math.radians(yaw))
    if holder: K.attach(h, holder); h.location = (x, y, z)
    K.attach(K.block('switch_plate', -0.004, 0.004, -0.0008, 0.0, -0.006, 0.006, K.M['trim'], bevel=0.0005), h)
    tg = empty('switch_toggle', (0, 0, 0)); K._to(tg); K.attach(tg, h); tg.location = (0, -0.0008, 0)
    K.attach(K.block('switch_rocker', -0.0016, 0.0016, -0.0012, 0.0, -0.0026, 0.0026, K.M['trim'], bevel=0.0004), tg)
    tg.rotation_euler = (0.3, 0, 0)
    return tg
