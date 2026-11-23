// Contact: characters sit ON chairs and lie ON beds, never inside them.
//   import {sitOn, lieOn, settleOn, clearOf, sinkCheck} from './contact.js';
//   sitOn(haru, chair);                 // pose sitChair, face the chair's front, bottom on the seat, back in front of the backrest
//   lieOn(haru, bed);                   // on her back along the bed, head at the bed's head end, resting on the mattress
//   settleOn(gran, bed);                // any pose: move the character up or down until the lowest point touches the surface under it
//   clearOf(P, [chair, bed], dir)       // push the character along dir (world, horizontal) until nothing of it is inside the props
//   sinkCheck(P, props) -> {n, depth}   // how many of her vertices are inside the props, and how deep (0, 0 = clean)
// How: each prop's solid shape is measured once (rays straight down on a 2.5 cm grid, in the prop's own frame) as a column of
// slabs per cell; a point is inside the prop when it sits within a slab. The character's real skinned vertices are tested,
// so it works for any pose and any prop, and keeps working when a prop moves or turns.
import * as THREE from 'three';
import {pose} from './clay.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z), ray = new THREE.Raycaster();
export const CELL = .025;

// ---- the prop's solid: slabs [bottom, top] per grid cell, in the prop's local frame
export function solidOf(obj) {
  if (obj.userData.solid) return obj.userData.solid;
  obj.updateMatrixWorld(true);
  const inv = obj.matrixWorld.clone().invert(), meshes = [];
  obj.traverse(o => { if (o.isMesh && o.visible) meshes.push(o); });
  const box = new THREE.Box3(); meshes.forEach(m => box.expandByObject(m)); box.applyMatrix4(inv);   // local bounds
  const nx = Math.ceil((box.max.x - box.min.x) / CELL) + 1, nz = Math.ceil((box.max.z - box.min.z) / CELL) + 1;
  const sides = meshes.map(m => { const s = m.material.side; m.material.side = THREE.DoubleSide; return s; });
  const cells = new Array(nx * nz), down = V(0, -1, 0).transformDirection(obj.matrixWorld);
  for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) {
    const lp = V(box.min.x + i * CELL, box.max.y + .5, box.min.z + k * CELL), wp = lp.clone().applyMatrix4(obj.matrixWorld);
    ray.set(wp, down); ray.far = 100;
    const hits = ray.intersectObjects(meshes, false).map(h => h.point.applyMatrix4(inv).y);
    const ys = []; for (const y of hits) if (!ys.length || Math.abs(ys[ys.length - 1] - y) > .004) ys.push(y);   // drop double hits on a shared edge
    const slabs = []; for (let j = 0; j + 1 < ys.length; j += 2) slabs.push([ys[j + 1], ys[j]]);
    if (ys.length % 2) slabs.push([box.min.y, ys[ys.length - 1]]);                // an open shell: solid down to the bottom
    cells[i * nz + k] = slabs;
  }
  meshes.forEach((m, i) => { m.material.side = sides[i]; });
  // the seat or the mattress: the biggest flat area of tops; the back: cells reaching well above it
  const tops = []; cells.forEach(s => s.length && tops.push(s[0][1]));
  const hist = new Map(); tops.forEach(y => { const b = Math.round(y / .03); hist.set(b, (hist.get(b) || 0) + 1); });
  let best = 0, bestN = 0; for (const [b, n] of hist) if (b * .03 > .15 && n > bestN) { best = b; bestN = n; }
  const surfY = best * .03, seat = V(), back = V(); let ns = 0, nb = 0;
  for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) { const s = cells[i * nz + k]; if (!s.length) continue; const y = s[0][1], x = box.min.x + i * CELL, z = box.min.z + k * CELL;
    if (Math.abs(y - surfY) < .05) { seat.x += x; seat.z += z; ns++; } else if (y > surfY + .15) { back.x += x; back.z += z; nb++; } }
  seat.multiplyScalar(1 / Math.max(1, ns)); seat.y = surfY; back.multiplyScalar(1 / Math.max(1, nb));
  const front = nb ? V(seat.x - back.x, 0, seat.z - back.z).normalize() : V(0, 0, 1);
  // a bed's head end: along its long side, the end that rises higher (the pillow, the raised head section)
  const alongX = nx > nz, n = alongX ? nx : nz, band = Math.max(2, Math.round(n * .25)); let e0 = 0, e1 = 0, c0 = 0, c1 = 0;
  for (let i = 0; i < nx; i++) for (let k = 0; k < nz; k++) { const s = cells[i * nz + k]; if (!s.length || s[0][1] > surfY + .45) continue; const j = alongX ? i : k;
    if (j < band) { e0 += s[0][1]; c0++; } else if (j >= n - band) { e1 += s[0][1]; c1++; } }
  const sgn = e0 / Math.max(1, c0) > e1 / Math.max(1, c1) ? -1 : 1, head = alongX ? V(sgn, 0, 0) : V(0, 0, sgn);
  // the pillow's front edge: walking from the head end along the middle, where the top comes down to the mattress (local distance from the centre)
  const cx = (box.min.x + box.max.x) / 2, cz = (box.min.z + box.max.z) / 2; let edge = 0, inP = false;
  for (let d = (alongX ? box.max.x - cx : box.max.z - cz) - CELL; d > 0; d -= CELL) {
    const lp = V(cx + head.x * d, 0, cz + head.z * d), i = Math.round((lp.x - box.min.x) / CELL), k = Math.round((lp.z - box.min.z) / CELL), s = cells[i * nz + k];
    const y = s && s.length ? s[0][1] : -1; if (y > surfY + .1 && y < surfY + .45) inP = true; else if (inP && y < surfY + .04) { edge = d; break; } }
  const end = alongX ? box.max.x - cx : box.max.z - cz;
  return obj.userData.solid = {box, nx, nz, cells, surfY, seat, front, head, edge, end, centre: V(cx, surfY, cz), hasBack: nb > 4};
}
function slabsAt(S, lp) {
  const i = Math.round((lp.x - S.box.min.x) / CELL), k = Math.round((lp.z - S.box.min.z) / CELL);
  return i < 0 || k < 0 || i >= S.nx || k >= S.nz ? null : S.cells[i * S.nz + k];
}

// ---- the character's skinned vertices in world space (every step-th; the body and the drawn face)
const _v = V();
export function bodyPoints(P, step = 5) {
  P.root.updateMatrixWorld(true); const out = [];
  for (const m of [P.mesh, P.faceMesh]) { if (!m || !m.visible) continue; m.skeleton.update();
    const pos = m.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += step) { _v.fromBufferAttribute(pos, i); m.applyBoneTransform(i, _v); out.push(_v.clone().applyMatrix4(m.matrixWorld)); } }
  return out;
}
const local = (obj, pts) => { obj.updateMatrixWorld(true); const inv = obj.matrixWorld.clone().invert(); return pts.map(p => p.clone().applyMatrix4(inv)); };

// how many points are inside the props, and how deep (the vertical overlap)
export function sinkCheck(P, props, pts = bodyPoints(P)) {
  let n = 0, depth = 0;
  for (const o of props) { const S = solidOf(o);
    for (const lp of local(o, pts)) { const s = slabsAt(S, lp); if (!s) continue;
      for (const [b, t] of s) if (lp.y > b + .006 && lp.y < t - .006) { n++; depth = Math.max(depth, Math.min(t - lp.y, lp.y - b)); } } }
  return {n, depth};
}

// move the character up or down so her lowest point over the prop rests on its surface (gap above it).
// reach: how far a point may already be sunk in and still count as resting on that surface.
// Only the prop's main surface (the seat, the mattress, and what lies on it: a pillow, a folded blanket) holds her, not the rails or the backrest, unless all: true.
export function settleOn(P, obj, {gap = .006, reach = .3, all = false, soft = .2} = {}) {
  const S = solidOf(obj);
  for (let it = 0; it < 3; it++) {
    const L = local(obj, bodyPoints(P)); let lo = Infinity;
    for (const lp of L) { const s = slabsAt(S, lp); if (!s) continue;
      for (const [, t] of s) if ((all || (t > S.surfY - .07 && t < S.surfY + soft)) && t < lp.y + reach && t > lp.y - .6) lo = Math.min(lo, lp.y - t); }
    if (!isFinite(lo)) return 0;
    const dy = gap - lo; P.root.position.y += dy; if (Math.abs(dy) < .002) return dy;
  }
  return 0;
}

// push the character along dir until no point is inside the props (the chair's back, a bed rail); returns the distance moved
export function clearOf(P, props, dir, {max = .5, stepD = .01, allow = 2} = {}) {
  const d = dir.clone().setY(0).normalize(); let moved = 0;
  while (moved < max && sinkCheck(P, props, bodyPoints(P, 3)).n > allow) { P.root.position.addScaledVector(d, stepD); moved += stepD; }
  return moved;
}

// the seat in world space: its centre, its height, and the way a sitter faces
export function seatOf(obj) {
  const S = solidOf(obj); obj.updateMatrixWorld(true);
  return {at: S.seat.clone().applyMatrix4(obj.matrixWorld), front: S.front.clone().transformDirection(obj.matrixWorld).setY(0).normalize(),
    head: S.head.clone().transformDirection(obj.matrixWorld).setY(0).normalize(), centre: S.centre.clone().applyMatrix4(obj.matrixWorld), edge: S.edge, end: S.end};
}
// turn a prop (about y) so its front looks at a world point (a chair toward a bed)
export function turnToward(obj, target) {
  const S = solidOf(obj), f0 = Math.atan2(S.front.x, S.front.z), p = obj.getWorldPosition(V());
  obj.rotation.y = Math.atan2(target.x - p.x, target.z - p.z) - f0; obj.updateMatrixWorld(true);
}

// sit on a chair: sitChair pose, facing the chair's front, bottom on the seat, nothing through the back or the seat
// (a still pose: the fit is kept per chair placement and key, so later frames cost nothing; add idle() after it)
export function sitOn(P, chair, {forward = .02, fix, key = ''} = {}) {
  const {at, front} = seatOf(chair), k = chair.uuid + '|' + key + '|' + chair.position.toArray() + chair.rotation.y;
  P.root.visible = true; P.skirtMode?.('sit'); P.root.rotation.set(0, Math.atan2(front.x, front.z), 0); pose(P, 'sitChair'); if (fix) fix(P);
  const c = P.root.userData.sit; if (c && c.k === k) { P.root.position.copy(c.p); return; }
  P.root.position.set(0, 0, 0); P.root.updateMatrixWorld(true);
  const hip = P.hips.getWorldPosition(V());                                     // the pelvis over the seat's middle, a little forward
  P.root.position.x += at.x - hip.x + front.x * forward; P.root.position.z += at.z - hip.z + front.z * forward;
  settleOn(P, chair); clearOf(P, [chair], front); settleOn(P, chair);
  P.root.userData.sit = {k, p: P.root.position.clone()};
}
// lie on a bed on her back: along the bed, her head on the pillow at the head end (along: metres further toward the foot),
// the body tilted up as much as the pillow needs so nothing sinks in. A still pose: the result is kept, so later frames cost nothing.
export function lieOn(P, bed, {along = 0, fix, key = ''} = {}) {
  const {at, head} = seatOf(bed), k = bed.uuid + '|' + along + '|' + key + '|' + bed.position.toArray() + bed.rotation.y;
  P.root.visible = true; P.root.rotation.order = 'YXZ'; if (fix) fix(P);
  const c = P.root.userData.lie; if (c && c.k === k) { P.root.position.copy(c.p); P.root.rotation.copy(c.r); return; }
  const {centre, end} = seatOf(bed), yaw = Math.atan2(-head.x, -head.z); let best = null;
  for (let a = 0; a <= .5; a += .05) {                                           // tilt the head up, a little at a time; keep the lowest-lying fit
    P.root.rotation.set(-Math.PI / 2 + a, yaw, 0); P.root.position.set(0, at.y + .4, 0); P.root.updateMatrixWorld(true);
    const top = P.head.localToWorld(V(0, P.J ? P.J.headTop.y - P.J.headBase.y : .25, 0)), want = centre.clone().addScaledVector(head, end - .17 - along);   // the top of her head just short of the head end
    P.root.position.x += want.x - top.x; P.root.position.z += want.z - top.z;
    settleOn(P, bed, {reach: .6, soft: .35}); P.root.updateMatrixWorld(true); const hy = P.hips.getWorldPosition(V()).y;
    if (!best || hy < best.hy - .004) best = {hy, p: P.root.position.clone(), r: P.root.rotation.clone()};
  }
  P.root.position.copy(best.p); P.root.rotation.copy(best.r);
  clearOf(P, [bed], head.clone().negate(), {max: .3, allow: 0}); best.p.copy(P.root.position);   // nothing through the headboard
  P.root.userData.lie = {k, p: best.p.clone(), r: best.r.clone()};
}
// sit up in a bed: back to the head end, facing the foot, on the mattress, nothing through the head section or the rails
export function sitUpIn(P, bed, {from = .12, poseName = 'sitBed', fix, key = ''} = {}) {
  const {head, centre, edge} = seatOf(bed), k = bed.uuid + '|' + from + poseName + '|' + key + '|' + bed.position.toArray() + bed.rotation.y;
  P.root.visible = true; P.skirtMode?.('sit'); P.root.rotation.set(0, Math.atan2(-head.x, -head.z), 0); pose(P, poseName); if (fix) fix(P);
  const c = P.root.userData.up; if (c && c.k === k) { P.root.position.copy(c.p); return; }
  P.root.position.set(0, 0, 0); P.root.updateMatrixWorld(true);
  const hip = P.hips.getWorldPosition(V()), want = centre.clone().addScaledVector(head, edge - from);   // her bottom just in front of the raised head section
  P.root.position.x += want.x - hip.x; P.root.position.z += want.z - hip.z; P.root.position.y = centre.y + .5 - hip.y;
  settleOn(P, bed, {reach: .5}); clearOf(P, [bed], head.clone().negate(), {max: .5, allow: 0}); settleOn(P, bed, {reach: .5});
  P.root.userData.up = {k, p: P.root.position.clone()};
}

// a sheet or blanket draped over someone in a bed: a soft cloth surface shaped to her body (the highest clay under each spot, smoothed),
// lying on the mattress elsewhere and hanging over its sides. from: 'neck' (to her chin) or 'hips' (a lap blanket, legs only).
// Returns a mesh (add it to the scene once; call again each frame: it is only rebuilt when she or the bed moves).
export function drape(P, bed, {from = 'neck', back = .06, mat, mesh} = {}) {
  const S = solidOf(bed), {head, centre, at, end} = seatOf(bed), across = V(head.z, 0, -head.x);
  const key = P.root.position.toArray().join() + P.root.rotation.x + from + bed.position.toArray();
  if (mesh && mesh.userData.key === key) { mesh.visible = true; return mesh; }
  const half = (S.nx > S.nz ? S.box.max.z - S.box.min.z : S.box.max.x - S.box.min.x) / 2 - .1, base = at.y + .012;
  const ref = (from === 'neck' ? P.neck : P.hips).getWorldPosition(V()), A = ref.clone().sub(centre).dot(head) - back, B = -end + .06;
  const D = .025, nu = Math.max(2, Math.round((A - B) / D)), nv = Math.round((half + .14) * 2 / D);
  const H = new Float32Array((nu + 1) * (nv + 1)).fill(-1);
  for (const p of bodyPoints(P, 4)) {                                              // the highest clay over each spot
    const d = p.clone().sub(centre), u = d.dot(head), v = d.dot(across); if (u > A + .02 || (from === 'hips' && p.y > ref.y - .02)) continue;
    const i = Math.round((u - B) / D), j = Math.round((v + half + .14) / D); if (i < 0 || j < 0 || i > nu || j > nv) continue;
    H[i * (nv + 1) + j] = Math.max(H[i * (nv + 1) + j], p.y);
  }
  // grow and soften: cloth bridges the gaps between limbs and falls off the body's sides instead of hugging it
  let G = Float32Array.from(H, h => Math.max(h + .02, base));
  for (let it = 0; it < 3; it++) { const N = G.slice(); for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) { let m = G[i * (nv + 1) + j];
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) { const ii = i + a, jj = j + b; if (ii >= 0 && jj >= 0 && ii <= nu && jj <= nv) m = Math.max(m, G[ii * (nv + 1) + jj] - .012); } N[i * (nv + 1) + j] = m; } G = N; }
  for (let it = 0; it < 4; it++) { const N = G.slice(); for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) { let s = 0, c = 0;
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) { const ii = i + a, jj = j + b; if (ii >= 0 && jj >= 0 && ii <= nu && jj <= nv) { s += G[ii * (nv + 1) + jj]; c++; } } N[i * (nv + 1) + j] = Math.max(s / c, base); } G = N; }
  const pos = [], idx = [];
  for (let i = 0; i <= nu; i++) for (let j = 0; j <= nv; j++) {
    const u = B + i * D, v = -half - .14 + j * D, over = Math.max(0, Math.abs(v) - half);
    let y = G[i * (nv + 1) + j]; if (over > 0) y = Math.min(y, base) - over * 1.6;      // hanging over the mattress's sides
    const w = centre.clone().addScaledVector(head, u).addScaledVector(across, Math.sign(v) * Math.min(Math.abs(v), half + over * .3)); pos.push(w.x, y, w.z);
    if (i < nu && j < nv) { const a = i * (nv + 1) + j; idx.push(a, a + nv + 1, a + 1, a + 1, a + nv + 1, a + nv + 2); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  if (!mesh) { mesh = new THREE.Mesh(g, mat); mesh.castShadow = mesh.receiveShadow = true; } else { mesh.geometry.dispose(); mesh.geometry = g; }
  if (mesh.material) mesh.material.side = THREE.DoubleSide;
  mesh.userData.key = key; mesh.visible = true; return mesh;
}
