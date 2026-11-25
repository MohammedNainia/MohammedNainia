"""Walk a puppet along a route through a set (library/sets/house/nav.py), with motion capture and real feet.

    w = Walker(lib, route, t0=0.5)              # route from nav.route(); lib is a mocap.Library for the puppet
    floor = Floor()                             # every walkable surface (the Colliders collection) as one BVH
    for each frame:  W, xy, z, yaw = w.at(t); place the root; MC.apply(h, W, yaw); floor.stand(h, z)

Every leg plays the upright 'walk' clip at its own stride (no sliding); on the stairs it plays slower (careful
steps) and Floor.place() bends each leg with IK so the foot lands on the tread under it, so she stays upright instead
of using a crouching stairs clip. The yaw turns smoothly into each new leg,
clips cross-fade, and when the route ends she settles into a standing pose. Floor.stand() casts a ray down under
each shoe and lifts or lowers her so the foot she stands on rests on the floor, step or rug below it.
"""
import math
import bpy
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
import numpy as np
import mocap as MC

STAIR_RUN = 0.023          # horizontal depth of one stair (house kit)
CLIPS = {'walk': 'walk', 'stairs_down': 'walk', 'stairs_up': 'walk'}
STAIR_PACE = 0.7           # careful steps on the stairs: the walk played slower
IDLE = ('look_behind', 0.15)


def yaw_of(d):
    return math.atan2(d.x, -d.y)            # 0 faces -y, +90 deg faces +x (the puppets' convention)


def ang_lerp(a, b, u):
    d = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + d * u


class Walker:
    def __init__(self, lib, route, t0=0.0, turn=0.35, fade=0.3, pace=1.0):
        self.lib, self.turn, self.fade = lib, turn, fade
        K = lib.k
        H = lib.clips['walk'][1]; T = lib.length('walk')
        v_walk = K * float(np.linalg.norm((H[-1] - H[0])[:2])) / T * pace
        speed = {'walk': v_walk, 'stairs_down': v_walk * STAIR_PACE, 'stairs_up': v_walk * STAIR_PACE}
        self.rate = {'walk': 1.0, 'stairs_down': STAIR_PACE, 'stairs_up': STAIR_PACE}   # clip seconds per second
        self.legs = []; t = t0; prev_kind = None; phase = 0.0
        pts = [p for p, _ in route]
        for i in range(1, len(route)):
            a, (b, kind) = pts[i - 1], route[i]
            d = b - a; L = Vector((d.x, d.y)).length
            if L < 1e-6: continue
            dur = L / speed[kind]
            self.legs.append(dict(a=a, b=b, kind=kind, t0=t, t1=t + dur, yaw=yaw_of(d), phase0=phase))
            phase += dur * self.rate[kind]; t += dur; prev_kind = kind           # one continuous walk cycle
        self.t0, self.t_end = t0, t

    def _leg(self, t):
        for i, L in enumerate(self.legs):
            if t < L['t1']: return i, L
        return len(self.legs) - 1, self.legs[-1]

    def _pose(self, L, t):
        c = L['phase0'] + max(0.0, t - L['t0']) * self.rate[L['kind']]
        W, _ = self.lib.sample(CLIPS[L['kind']], c, loop=True)
        return W

    def at(self, t):
        """world rotations (with yaw), root xy, floor height under the path, yaw"""
        if t <= self.t0:
            L = self.legs[0]; W = self.lib.sample(*IDLE)[0]
            return MC.rotate(W, L['yaw']), Vector((L['a'].x, L['a'].y)), L['a'].z, L['yaw']
        i, L = self._leg(t)
        u = min(1.0, max(0.0, (t - L['t0']) / (L['t1'] - L['t0'])))
        p = L['a'].lerp(L['b'], u)
        yaw = L['yaw']; W = self._pose(L, min(t, L['t1']))
        if i > 0 and t - L['t0'] < self.turn:                            # turn into the new leg
            k = (t - L['t0']) / self.turn; k = k * k * (3 - 2 * k)
            yaw = ang_lerp(self.legs[i - 1]['yaw'], L['yaw'], 0.5 + 0.5 * k)
        elif i + 1 < len(self.legs) and L['t1'] - t < self.turn:          # ... starting just before the corner
            k = 1 - (L['t1'] - t) / self.turn; k = k * k * (3 - 2 * k)
            yaw = ang_lerp(L['yaw'], self.legs[i + 1]['yaw'], 0.5 * k)
        if i > 0 and self.legs[i - 1]['kind'] != L['kind'] and t - L['t0'] < self.fade:   # cross-fade clips
            Wp = self._pose(self.legs[i - 1], t)
            k = (t - L['t0']) / self.fade; W = MC.blend(Wp, W, k * k * (3 - 2 * k))
        if t > self.t_end:                                                # arrived: settle into standing
            k = min(1.0, (t - self.t_end) / 0.5)
            W = MC.blend(self._pose(L, self.t_end), self.lib.sample(*IDLE)[0], k * k * (3 - 2 * k))
        return MC.rotate(W, yaw), Vector((p.x, p.y)), p.z, yaw


class Floor:
    """every surface in the Colliders collection (floors, stair treads, rugs, beds, seats) as one BVH, world space"""
    def __init__(self, coll='Colliders'):
        dg = bpy.context.evaluated_depsgraph_get(); verts, polys = [], []
        for ob in bpy.data.collections[coll].objects:
            if ob.type != 'MESH': continue
            ev = ob.evaluated_get(dg); me = ev.to_mesh(); M = ev.matrix_world
            base = len(verts)
            verts += [M @ v.co for v in me.vertices]
            polys += [[base + i for i in p.vertices] for p in me.polygons]
            ev.to_mesh_clear()
        self.bvh = BVHTree.FromPolygons(verts, polys)

    def below(self, x, y, z_from, reach=0.2):
        """height of the first upward-facing surface under (x, y), looking down from z_from"""
        o = Vector((x, y, z_from))
        for _ in range(4):
            hit = self.bvh.ray_cast(o, Vector((0, 0, -1)), reach)
            if hit[0] is None: return None
            if hit[1].z > 0.2: return hit[0].z                           # a floor, a tread, a rug
            o = hit[0] - Vector((0, 0, 0.0005))                           # the underside of something: look on below it
        return None

    def stand(self, h, z_hint, sink=0.0006):
        """put the root at the height where the lowest shoe rests on whatever is under it"""
        h.root.location.z = z_hint
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        best = None
        for ob in h.meshes:
            if 'sole' not in ob.name: continue
            ev = ob.evaluated_get(dg); me = ev.to_mesh()
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
            Mw = np.array(ev.matrix_world); W = co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]; ev.to_mesh_clear()
            zlo = float(W[:, 2].min()); flat = W[W[:, 2] < zlo + 0.0025]                 # the sole's bottom
            pick = flat[np.linspace(0, len(flat) - 1, min(12, len(flat))).astype(int)]
            gs = [self.below(float(p[0]), float(p[1]), z_hint + 0.07) for p in pick]
            gs = [g for g in gs if g is not None]
            if not gs: continue
            d = max(gs) - zlo - sink                                       # it rests on the highest thing under it
            best = d if best is None else max(best, d)
        if best is not None: h.root.location.z = z_hint + best
        return h.root.location.z

    def place(self, h, W, yaw, z_path, lift=0.35):
        """Put her on the floor or the stairs with both feet: find the surface under each shoe, set the root between
        the two (closer to the lower one), then bend each leg with two-bone IK so its ankle sits on its own surface
        at the height the walk clip lifts it. Returns the root height."""
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        ank = h.rest['foot.L'].z
        sides = {}
        for s in ('L', 'R'):
            sole = next(o for o in h.meshes if o.name.startswith('sole.' + s))
            ev = sole.evaluated_get(dg); me = ev.to_mesh()
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
            Mw = np.array(ev.matrix_world); P_ = co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]; ev.to_mesh_clear()
            zlo = float(P_[:, 2].min()); flat = P_[P_[:, 2] < zlo + 0.0025]
            pick = flat[np.linspace(0, len(flat) - 1, min(10, len(flat))).astype(int)]
            gs = [self.below(float(p[0]), float(p[1]), z_path + 0.07) for p in pick]
            gs = [g for g in gs if g is not None]
            A = h.P['foot.' + s].matrix_world.translation.copy()
            sides[s] = dict(g=max(gs) if gs else z_path, A=A, hc=max(0.0, zlo - z_path),
                            H=h.P['thigh.' + s].matrix_world.translation.copy(), K=h.P['shin.' + s].matrix_world.translation.copy())
        g0, g1 = sorted(v['g'] for v in sides.values())
        r = g0 + lift * (g1 - g0)
        d = r - z_path; h.root.location.z = r
        W = dict(W); changed = False
        for s, v in sides.items():
            H, K_, A = v['H'] + Vector((0, 0, d)), v['K'] + Vector((0, 0, d)), v['A'] + Vector((0, 0, d))
            T = Vector((A.x, A.y, v['g'] + (A.z - r)))                     # the clip's ankle height, over this foot's own surface
            if abs(T.z - A.z) < 1e-4: continue
            a, b = (K_ - H).length, (A - K_).length
            ST = T - H; dl = min(ST.length, (a + b) * 0.999); u = ST.normalized()
            pole = (K_ - H) - u * (K_ - H).dot(u)
            pole = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
            ca = max(-1.0, min(1.0, (a * a + dl * dl - b * b) / (2 * a * dl)))
            E = H + (u * ca + pole * math.sqrt(1 - ca * ca)) * a; T2 = H + u * dl
            R1 = (K_ - H).rotation_difference(E - H)
            v1 = R1 @ (A - K_); R2 = v1.rotation_difference(T2 - E)
            W['thigh.' + s] = R1 @ W['thigh.' + s]
            W['shin.' + s] = R2 @ R1 @ W['shin.' + s]
            changed = True
        if changed: MC.apply(h, W, yaw)
        # last: the walk clip never puts a foot quite to zero, so lower her until the planted shoe touches
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); gaps = []
        for s in ('L', 'R'):
            sole = next(o for o in h.meshes if o.name.startswith('sole.' + s))
            ev = sole.evaluated_get(dg); me = ev.to_mesh()
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co)
            Mw = np.array(ev.matrix_world); P_ = co.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]; ev.to_mesh_clear()
            zlo = float(P_[:, 2].min()); flat = P_[P_[:, 2] < zlo + 0.0025]
            gs = [self.below(float(p[0]), float(p[1]), zlo + 0.03) for p in flat[::max(1, len(flat) // 10)]]
            gs = [g for g in gs if g is not None]
            if gs: gaps.append(zlo - max(gs))
        if gaps: h.root.location.z -= min(gaps) + 0.0006
        return h.root.location.z
