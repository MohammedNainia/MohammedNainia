"""Plasticine that reads as clay, not plastic (for pieces built in true metres on a ~12 cm puppet).

What makes clay look like plastic: one glossy layer with a crisp highlight, perfect surfaces, uniform colour.
Real modelling clay is MATTE and slightly translucent, with only a soft, diffused sheen from a thin oily film on top
(a layered BRDF: rough base + thin rough film; see the "creating a realistic clay shader for digital stop motion"
report, after Weidlich & Wilkie), and it is never smooth: folds, fingerprint indents, smears and bumps everywhere.

So: base roughness ~0.82, low specular, a weak coat with roughness ~0.45 as the oily film, a little subsurface;
colour mottling and kneading streaks; height = broad dents + small lumps + smears + modelling-tool creases + partial
fingerprint whorls (+ carved grooves for hair); handled (printed) spots a little shinier. All texture sizes are for
the puppet: a thumbprint ~8 mm across with ridges ~0.45 mm apart. Coordinates are Object space (rigid pieces), and a
'boil' Mapping node lets a scene nudge the marks a little per frame if wanted.

geometry(ob): matching shape imperfections as Displace modifiers (broad thumb dents, pressed pits, fine lumps).
"""
import bpy, math


def _lin(c):
    if isinstance(c, str):
        c = c.lstrip('#'); c = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)
    return tuple(c)


def clay(name, color, rough=0.82, sss=0.08, bump=0.6, prints=1.0, specks=1.0, grooves=0.0, film=0.15, gloss=False):
    """color: '#hex' (sRGB) or a linear RGB tuple. gloss=True gives a glossy bead (eyes)."""
    c = _lin(color)
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links; N.clear()
    out = N.new('ShaderNodeOutputMaterial'); b = N.new('ShaderNodeBsdfPrincipled')
    Lk.new(b.outputs['BSDF'], out.inputs['Surface'])
    if gloss:
        b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Roughness'].default_value = 0.18
        b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.05
        return m
    b.inputs['Specular IOR Level'].default_value = 0.22
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = (min(1, c[0] * 2 + 0.2), min(1, c[1] * 2 + 0.2), min(1, c[2] * 2 + 0.2))
    b.inputs['Subsurface Scale'].default_value = 0.0015
    b.inputs['Coat Weight'].default_value = film                  # the thin oily film: soft, diffused sheen
    b.inputs['Coat Roughness'].default_value = 0.45
    b.inputs['Coat IOR'].default_value = 1.4
    b.inputs['Sheen Weight'].default_value = 0.05; b.inputs['Sheen Roughness'].default_value = 0.6

    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping'); mp.name = mp.label = 'boil'
    mp.inputs['Scale'].default_value = (10.0, 10.0, 10.0)        # sizes below are per 0.1 m (puppet decimetre)
    Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
    V = mp.outputs['Vector']

    def tex(kind, scale, vec=None, **kw):
        t = N.new(kind); Lk.new(vec or V, t.inputs['Vector']); t.inputs['Scale'].default_value = scale
        for k, v in kw.items():
            if k in t.inputs: t.inputs[k].default_value = v
            else: setattr(t, k, v)
        return t

    def op(kind, *ins, clamp=False):
        n = N.new('ShaderNodeMath'); n.operation = kind; n.use_clamp = clamp
        for i, x in enumerate(ins):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: Lk.new(x, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, col, blend='MIX'):
        n = N.new('ShaderNodeMix'); n.data_type = 'RGBA'; n.blend_type = blend
        Lk.new(fac, n.inputs['Factor']); Lk.new(a, n.inputs[6]); n.inputs[7].default_value = col
        return n.outputs[2]

    # colour: mottling (+-10% value), kneading streaks, dust specks
    mot = tex('ShaderNodeTexNoise', 5, Detail=3, Distortion=0.5)
    ramp = N.new('ShaderNodeValToRGB'); e0, e1 = ramp.color_ramp.elements
    e0.position, e1.position = 0.3, 0.72
    e0.color = (*[v * 0.86 for v in c], 1); e1.color = (*[min(1, v * 1.08) for v in c], 1)
    Lk.new(mot.outputs['Fac'], ramp.inputs['Fac']); col = ramp.outputs['Color']
    marb = tex('ShaderNodeTexNoise', 2.5, Detail=2, Distortion=5)
    band = op('MULTIPLY', op('SUBTRACT', op('ABSOLUTE', op('SUBTRACT', marb.outputs['Fac'], 0.5)), 0.04), -12.0, clamp=True)
    col = mix(band, col, (0.88, 0.86, 0.84, 1), 'MULTIPLY')
    if specks:
        sp = tex('ShaderNodeTexVoronoi', 260)
        sc = N.new('ShaderNodeSeparateColor'); Lk.new(sp.outputs['Color'], sc.inputs[0])
        dot = op('MULTIPLY', op('LESS_THAN', sp.outputs['Distance'], 0.07), op('GREATER_THAN', sc.outputs[0], 0.82))
        col = mix(op('MULTIPLY', dot, 0.7 * specks), col, (*[v * 0.4 for v in c], 1))
    Lk.new(col, b.inputs['Base Color'])

    # height
    h = op('MULTIPLY', tex('ShaderNodeTexNoise', 6, Detail=2).outputs['Fac'], 1.0)                    # broad dents
    def acc(x, k): return op('MULTIPLY_ADD', x, k, h)
    h = acc(tex('ShaderNodeTexNoise', 25, Detail=1).outputs['Fac'], 0.3)                                # small lumps
    sm = N.new('ShaderNodeMapping'); Lk.new(V, sm.inputs['Vector']); sm.inputs['Scale'].default_value = (9, 9, 1.6)
    h = acc(tex('ShaderNodeTexNoise', 1.0, vec=sm.outputs['Vector'], Detail=1).outputs['Fac'], 0.35)   # smears
    tool = tex('ShaderNodeTexVoronoi', 9, feature='DISTANCE_TO_EDGE')
    h = acc(op('SMOOTH_MIN', tool.outputs['Distance'], 0.06, 0.04), 0.4)                                # tool creases
    shiny = None
    if prints:   # partial, oval, wobbly fingerprint whorls with a shallow pressed bowl
        st = N.new('ShaderNodeMapping'); Lk.new(V, st.inputs['Vector']); st.inputs['Scale'].default_value = (1.0, 1.0, 1.6)
        tp = tex('ShaderNodeTexVoronoi', 11, vec=st.outputs['Vector'], Randomness=1.0)
        warp = tex('ShaderNodeTexNoise', 22, Detail=2)
        d2 = op('MULTIPLY_ADD', warp.outputs['Fac'], 0.09, tp.outputs['Distance'])
        ridge = op('SINE', op('MULTIPLY', d2, 2 * math.pi * 26))
        rc = N.new('ShaderNodeSeparateColor'); Lk.new(tp.outputs['Color'], rc.inputs[0])
        cell = op('GREATER_THAN', rc.outputs[0], 0.4)
        fr = N.new('ShaderNodeMapRange'); fr.interpolation_type = 'SMOOTHSTEP'
        Lk.new(tp.outputs['Distance'], fr.inputs['Value'])
        fr.inputs['From Min'].default_value, fr.inputs['From Max'].default_value = 0.1, 0.36
        fr.inputs['To Min'].default_value, fr.inputs['To Max'].default_value = 1.0, 0.0
        part = op('MULTIPLY', op('SUBTRACT', tex('ShaderNodeTexNoise', 30, Detail=1).outputs['Fac'], 0.42), 4.0, clamp=True)
        mask = op('MULTIPLY', op('MULTIPLY', cell, fr.outputs['Result']), part)
        h = acc(op('MULTIPLY', ridge, mask), 0.16 * prints)
        h = acc(op('MULTIPLY', op('POWER', fr.outputs['Result'], 2.0), cell), -0.6 * prints)
        shiny = mask
    if grooves:  # tool-carved locks running down from the crown (angle around the vertical axis through x=y=0)
        gr = N.new('ShaderNodeTexGradient'); gr.gradient_type = 'RADIAL'; Lk.new(V, gr.inputs['Vector'])
        ang = op('MULTIPLY_ADD', tex('ShaderNodeTexNoise', 5, Detail=2).outputs['Fac'], 0.035, gr.outputs['Fac'])
        g = op('POWER', op('ABSOLUTE', op('SINE', op('MULTIPLY', ang, math.pi * 38))), 0.35)
        depth = op('MULTIPLY_ADD', tex('ShaderNodeTexNoise', 9, Detail=1).outputs['Fac'], 1.4, -0.2)
        h = acc(op('MULTIPLY', g, depth), grooves)
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0004
    Lk.new(h, bp.inputs['Height']); Lk.new(bp.outputs['Normal'], b.inputs['Normal'])
    Lk.new(bp.outputs['Normal'], b.inputs['Coat Normal'])
    # roughness: matte, uneven; handled spots a little shinier
    r = op('MULTIPLY_ADD', tex('ShaderNodeTexNoise', 4, Detail=1).outputs['Fac'], 0.12, rough - 0.06)
    if shiny is not None: r = op('MULTIPLY_ADD', shiny, -0.14, r)
    Lk.new(r, b.inputs['Roughness'])
    return m


def geometry(ob, dents=0.00035, pits=0.00018, lumps=0.00012):
    """shape imperfections for a piece in metres: broad thumb dents, pressed pits, fine lumps (Object coords)"""
    def disp(name, kind, size, strength, **kw):
        t = bpy.data.textures.get(name) or bpy.data.textures.new(name, kind)
        t.noise_scale = size
        for k, v in kw.items(): setattr(t, k, v)
        d = ob.modifiers.new(name, 'DISPLACE'); d.texture = t; d.strength = strength
        d.texture_coords = 'LOCAL'; d.mid_level = 0.5
    if dents: disp('clay_dents', 'CLOUDS', 0.0065, dents, noise_depth=0, noise_basis='ORIGINAL_PERLIN')   # broad, soft
    if pits: disp('clay_pits', 'VORONOI', 0.0032, -pits, distance_metric='DISTANCE', color_mode='INTENSITY', noise_intensity=1.0)
    if lumps: disp('clay_lumps_fine', 'CLOUDS', 0.0015, lumps, noise_depth=0)
    return ob
