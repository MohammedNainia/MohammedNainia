"""Materials for Burton-style stop-motion puppets (pieces built in true metres, puppet ~12-13 cm tall).

Real Burton puppets (Corpse Bride, Nightmare) are silicone / foam latex over metal armatures, with real fabric
costumes, sculpted hair and glass eyes (research/BURTON.md). So:
  silicone(): smooth pale skin, soft translucency, faint sheen, micro texture; optional dark eye sockets
  fabric():   knit (hoodie) or weave (trousers, canvas): fibre heather, fine loops or threads, fuzzy sheen
  hair():     sculpted, glossy black with fine strand grooves running down from the crown
  glass_eye(): eyeball with iris, pupil and limbal ring in the shader, glassy coat; pupil size from the object's
              'pupil' custom property (keyable), so the eye can widen in fear. Eye objects must have their origin at
              the eyeball centre and look down their local -Y.
  lid():      darker grey-purple skin for the eyelids (Burton's tired, shadowed eyes)
Object coordinates throughout (rigid pieces: the texture stays on the puppet).
"""
import bpy, math


def _lin(c):
    if isinstance(c, str):
        c = c.lstrip('#'); c = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)
    return tuple(c)


class _G:
    """tiny node-graph helper"""
    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True; self.m = m; self.N, self.L = m.node_tree.nodes, m.node_tree.links; self.N.clear()
        self.out = self.N.new('ShaderNodeOutputMaterial'); self.b = self.N.new('ShaderNodeBsdfPrincipled')
        self.L.new(self.b.outputs['BSDF'], self.out.inputs['Surface'])
        self.tc = self.N.new('ShaderNodeTexCoord'); self.V = self.tc.outputs['Object']

    def map(self, scale=(1, 1, 1), vec=None):
        mp = self.N.new('ShaderNodeMapping'); self.L.new(vec or self.V, mp.inputs['Vector'])
        mp.inputs['Scale'].default_value = scale; return mp.outputs['Vector']

    def tex(self, kind, scale, vec=None, **kw):
        t = self.N.new(kind); self.L.new(vec or self.V, t.inputs['Vector']); t.inputs['Scale'].default_value = scale
        for k, v in kw.items():
            if k in t.inputs: t.inputs[k].default_value = v
            else: setattr(t, k, v)
        return t

    def op(self, kind, *ins, clamp=False):
        n = self.N.new('ShaderNodeMath'); n.operation = kind; n.use_clamp = clamp
        for i, x in enumerate(ins):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: self.L.new(x, n.inputs[i])
        return n.outputs[0]

    def vop(self, kind, a, b=None):
        n = self.N.new('ShaderNodeVectorMath'); n.operation = kind
        self.L.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list)): n.inputs[1].default_value = b
            else: self.L.new(b, n.inputs[1])
        return n

    def mix(self, fac, a, b, blend='MIX'):
        n = self.N.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend
        if isinstance(fac, (int, float)): n.inputs['Factor'].default_value = fac
        else: self.L.new(fac, n.inputs['Factor'])
        for sock, v in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, tuple): sock.default_value = (*v[:3], 1)
            else: self.L.new(v, sock)
        return n.outputs[2]

    def smooth(self, x, lo, hi):           # 0 below lo, 1 above hi
        n = self.N.new('ShaderNodeMapRange'); n.interpolation_type = 'SMOOTHSTEP'
        self.L.new(x, n.inputs['Value']); n.inputs['From Min'].default_value = lo; n.inputs['From Max'].default_value = hi
        return n.outputs['Result']

    def bump(self, h, strength, dist):
        bp = self.N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
        self.L.new(h, bp.inputs['Height']); self.L.new(bp.outputs['Normal'], self.b.inputs['Normal']); return bp


def silicone(name, color, sockets=(), socket_color='#7a6a78', socket_r=0.0055):
    """pale silicone skin. sockets: eye centres (object coords, metres) to shade the dark rings around the eyes"""
    g = _G(name); b = g.b; c = _lin(color)
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.35
    b.inputs['Subsurface Weight'].default_value = 0.3
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.42, 0.28)
    b.inputs['Subsurface Scale'].default_value = 0.0018
    b.inputs['Coat Weight'].default_value = 0.06; b.inputs['Coat Roughness'].default_value = 0.3
    mot = g.tex('ShaderNodeTexNoise', 180, Detail=2)                        # very faint mottling
    col = g.mix(g.op('MULTIPLY', mot.outputs['Fac'], 0.25), (c[0] * 0.95, c[1] * 0.94, c[2] * 0.95), (c[0], c[1], c[2]))
    for sc in sockets:                                                        # dark rings around the eyes
        d = g.vop('DISTANCE', g.V, tuple(sc)).outputs['Value']
        ring = g.op('SUBTRACT', 1.0, g.smooth(d, socket_r * 0.55, socket_r * 1.35))
        col = g.mix(g.op('MULTIPLY', ring, 0.9), col, _lin(socket_color), 'MULTIPLY')
    g.L.new(col, b.inputs['Base Color'])
    h = g.op('MULTIPLY_ADD', g.tex('ShaderNodeTexNoise', 3500, Detail=1).outputs['Fac'], 0.5,
             g.tex('ShaderNodeTexNoise', 220, Detail=2).outputs['Fac'])     # micro texture + soft sculpt waviness
    g.bump(h, 0.05, 0.0003)
    return g.m


def lid(name, color='#9a8590'):
    return silicone(name, color)


def fabric(name, color, kind='knit', fuzz=0.85):
    """kind 'knit' (hoodie: fine loops, ribbing-friendly) or 'weave' (trousers, canvas: crossing threads)"""
    g = _G(name); b = g.b; c = _lin(color)
    b.inputs['Roughness'].default_value = 0.88
    b.inputs['Specular IOR Level'].default_value = 0.25
    b.inputs['Sheen Weight'].default_value = fuzz; b.inputs['Sheen Roughness'].default_value = 0.35
    b.inputs['Subsurface Weight'].default_value = 0.05; b.inputs['Subsurface Scale'].default_value = 0.0008
    heather = g.tex('ShaderNodeTexNoise', 900, Detail=2)                     # fibre colour variation
    blot = g.tex('ShaderNodeTexNoise', 40, Detail=2)                         # soft wear / dye patches
    base = g.mix(heather.outputs['Fac'], (c[0] * 0.8, c[1] * 0.8, c[2] * 0.8), (min(1, c[0] * 1.12), min(1, c[1] * 1.12), min(1, c[2] * 1.12)))
    base = g.mix(g.op('MULTIPLY', blot.outputs['Fac'], 0.3), base, (c[0] * 0.85, c[1] * 0.85, c[2] * 0.85))
    if kind == 'knit':   # stitch loops: stretched cells, ~0.45 mm on the puppet
        v = g.map((1.0, 1.0, 0.62))
        cell = g.tex('ShaderNodeTexVoronoi', 2300, vec=v, feature='DISTANCE_TO_EDGE')
        pat = g.smooth(cell.outputs['Distance'], 0.0, 0.18)
    else:                # crossing threads ~0.3 mm (twill-ish), in two directions
        w1 = g.tex('ShaderNodeTexWave', 700, bands_direction='X', Distortion=0.6)
        w2 = g.tex('ShaderNodeTexWave', 700, bands_direction='Z', Distortion=0.6)
        pat = g.op('MULTIPLY', w1.outputs['Fac'], w2.outputs['Fac'])
    col = g.mix(g.op('SUBTRACT', 1.0, pat), base, (c[0] * 0.55, c[1] * 0.55, c[2] * 0.55))   # dark between loops
    g.L.new(col, b.inputs['Base Color'])
    fz = g.tex('ShaderNodeTexNoise', 5000, Detail=1)
    h = g.op('MULTIPLY_ADD', fz.outputs['Fac'], 0.35, pat)
    h = g.op('MULTIPLY_ADD', blot.outputs['Fac'], 0.6, h)
    g.bump(h, 0.35, 0.00025)
    return g.m


def hair(name, color='#141517', grooves=110):
    """sculpted, glossy hair: fine wavy strand grooves running down from the crown (angle round the z axis)"""
    g = _G(name); b = g.b; c = _lin(color)
    b.inputs['Base Color'].default_value = (*c, 1)
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Specular IOR Level'].default_value = 0.2
    b.inputs['Coat Weight'].default_value = 0.12; b.inputs['Coat Roughness'].default_value = 0.3
    gr = g.N.new('ShaderNodeTexGradient'); gr.gradient_type = 'RADIAL'; g.L.new(g.V, gr.inputs['Vector'])
    warp = g.tex('ShaderNodeTexNoise', 35, Detail=2)
    ang = g.op('MULTIPLY_ADD', warp.outputs['Fac'], 0.012, gr.outputs['Fac'])
    gv = g.op('POWER', g.op('ABSOLUTE', g.op('SINE', g.op('MULTIPLY', ang, math.pi * grooves))), 0.4)
    depth = g.op('MULTIPLY_ADD', g.tex('ShaderNodeTexNoise', 60, Detail=1).outputs['Fac'], 1.2, -0.1)
    h = g.op('MULTIPLY', gv, depth)
    g.bump(h, 0.55, 0.0003)
    # strand-wise sheen breakup
    r = g.op('MULTIPLY_ADD', gv, 0.15, 0.5); g.L.new(r, b.inputs['Roughness'])
    return g.m


def glass_eye(name, iris='#4a2a17', sclera='#ece6df', iris_deg=27.0, pupil_deg=11.0):
    """eyeball shader: object-space angle from the local -Y axis gives iris and pupil; 'pupil' object property
    scales the pupil (1 = normal, 0.5 = pinprick, 1.3 = wide)"""
    g = _G(name); b = g.b
    b.inputs['Roughness'].default_value = 0.25; b.inputs['Specular IOR Level'].default_value = 0.5
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02; b.inputs['Coat IOR'].default_value = 1.45
    b.inputs['Subsurface Weight'].default_value = 0.1; b.inputs['Subsurface Scale'].default_value = 0.0006
    n = g.vop('NORMALIZE', g.V).outputs[0]
    sep = g.N.new('ShaderNodeSeparateXYZ'); g.L.new(n, sep.inputs[0])
    ang = g.op('DEGREES', g.op('ARCCOSINE', g.op('MULTIPLY', sep.outputs['Y'], -1.0)))       # 0 at the front pole
    pa = g.N.new('ShaderNodeAttribute'); pa.attribute_type = 'OBJECT'; pa.attribute_name = 'pupil'
    pup = g.op('MULTIPLY', g.op('MAXIMUM', pa.outputs['Fac'], 0.3), pupil_deg)
    irism = g.op('SUBTRACT', 1.0, g.smooth(ang, iris_deg - 1.2, iris_deg + 0.4))
    # pupil edge: soft step from pupil size (deg) to +0.8 deg; Map Range takes sockets for its range
    pr = g.N.new('ShaderNodeMapRange'); pr.interpolation_type = 'SMOOTHSTEP'
    g.L.new(ang, pr.inputs['Value']); g.L.new(pup, pr.inputs['From Min']); g.L.new(g.op('ADD', pup, 0.8), pr.inputs['From Max'])
    pupm = g.op('SUBTRACT', 1.0, pr.outputs['Result'])
    limb = g.smooth(ang, iris_deg - 5.0, iris_deg)                                         # darker rim of the iris
    azi = g.op('ARCTAN2', sep.outputs['X'], sep.outputs['Z'])                              # radial streaks round the pupil
    st_val = g.op('ABSOLUTE', g.op('SINE', g.op('MULTIPLY', azi, 23.0)))
    ic = _lin(iris)
    icol = g.mix(g.op('MULTIPLY', st_val, 0.5), (ic[0] * 0.7, ic[1] * 0.7, ic[2] * 0.7), (min(1, ic[0] * 1.6), min(1, ic[1] * 1.5), min(1, ic[2] * 1.3)))
    icol = g.mix(g.op('MULTIPLY', limb, 0.8), icol, (0.02, 0.015, 0.012))
    sc = _lin(sclera)
    edge = g.smooth(ang, 55.0, 85.0)                                                       # faint pink toward the sides
    scol = g.mix(g.op('MULTIPLY', edge, 0.4), (*sc,), (sc[0], sc[1] * 0.86, sc[2] * 0.84))
    col = g.mix(irism, scol, icol)
    col = g.mix(pupm, col, (0.005, 0.005, 0.006))
    g.L.new(col, b.inputs['Base Color'])
    return g.m
