// Motion for the clay characters (haru3.js / characters.js). Everything is a pure function of time t, so any frame can be
// rendered on its own (render.js renders frames out of order and in parallel): no state carried between frames.
//   import {walk, walkTo, poseBlend, face, sway, BONES} from './motion.js';
//   walkTo(P, t, {from: [x, z], to: [x, z], start: 2.0})      walks from A to B starting at t = 2, stops and stands at B
//   poseBlend(P, t, [[0, POSE_A], [1.5, POSE_B], [2.2, POSE_C]])   eased in-betweens from pose to pose (stop-motion stepped)
//   face(P, t, {expr: [[0, 'neutral'], [3.1, 'scared']], cues})  expressions with an in-between frame, blinks, lip sync
import * as THREE from 'three';

const TAU = Math.PI * 2;
export const step12 = t => Math.floor(t * 12 + 1e-6) / 12;                  // stop motion: poses change 12 times a second
export const ease = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
export const BONES = P => [P.hips, P.chest, P.neck, P.head, ...P.arms.flatMap(a => [a.up, a.fo, a.hand]), ...P.legs.flatMap(l => [l.th, l.sh, l.ft, l.toe])];

// ---------------------------------------------------------------- feet
// the points of a sole in world space: heel and ball on the foot bone, the toe tip on the toe bone (it bends)
export const solePoints = l => [l.ft.localToWorld(new THREE.Vector3(0, -.06, -.1)), l.ft.localToWorld(new THREE.Vector3(0, -.06, .0875)), l.toe.localToWorld(new THREE.Vector3(0, .001, .085))];
const smooth = (a, b, x) => { const k = Math.min(1, Math.max(0, (x - a) / (b - a))); return k * k * (3 - 2 * k); };

// ---------------------------------------------------------------- planted-foot gait (how animators do it)
// Each foot has a spot on the floor for each step. While it is on the ground it stays pinned there and rolls: heel strike
// (pivot on the heel, toes up) -> flat -> heel peels up (pivot on the ball, toes stay flat on the floor) -> push-off. In the air
// it travels in an arc to its next spot. The hips go as high as both legs can reach, and the legs find their angles by
// two-bone inverse kinematics. So nothing slides, skims or drags by construction.
const HEEL = new THREE.Vector3(0, -.06, -.1), BALL = new THREE.Vector3(0, -.061, .0875), ANKLE_Y = .061;   // in foot space
const Rx = (v, a) => new THREE.Vector3(v.x, v.y * Math.cos(a) - v.z * Math.sin(a), v.y * Math.sin(a) + v.z * Math.cos(a));
function gaitParams(P, {stride = 1, mood = 0, run = 0, cadence = .9} = {}) {
  const L1 = P.legs[0].sh.position.length(), L2 = P.legs[0].ft.position.length(), L = L1 + L2;
  const D = (1.6 + 1.5 * run) * L * stride * (1 - .35 * mood);          // ground covered per cycle (two steps), character units
  return {L1, L2, L, D, c: cadence, v: D * cadence, beta: .62 - .27 * run, h: .05 + .16 * run - .02 * mood, run, mood, stride};
}
// the foot's pitch over one stance (w 0..1) and one swing (w 0..1): + = toes down
function stanceRoll(w, run) { const strike = -.26 * (1 - .8 * run), off = .5 + .3 * run;
  return strike * (1 - smooth(0, .3, w)) + off * smooth(.45, 1, w); }
function swingRoll(w, run) { const strike = -.26 * (1 - .8 * run), off = .5 + .3 * run;
  return off + (.08 - off) * smooth(0, .35, w) + (strike - .08) * smooth(.55, 1, w); }
// ankle position (character space: forward = +z, floor y = 0) for a foot whose flat-ankle spot is z = Z, pitched by roll:
// heel down -> pivot on the heel, heel up -> pivot on the ball
function ankleAt(Z, roll) { const piv = roll < 0 ? HEEL : BALL;
  const p = new THREE.Vector3(0, ANKLE_Y + piv.y, Z + piv.z); return p.sub(Rx(piv, roll)); }
// two-bone IK in the leg's plane: hip joint (y, z) to ankle (y, z) -> thigh and knee angles (our rotation conventions)
function legIK(L1, L2, hy, hz, ay, az) {
  const dy = ay - hy, dz = az - hz; let d = Math.hypot(dy, dz); d = Math.min(d, (L1 + L2) * .9995);
  const a = Math.atan2(dz, -dy), b = Math.acos(Math.min(1, Math.max(-1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))));
  const g = Math.acos(Math.min(1, Math.max(-1, (L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2))));
  return {th: -(a + b), knee: Math.PI - g};
}
// where everything is at gait time tau (seconds since the walk started), in character space
function gaitState(P, G, tau) {
  const {L1, L2, L, D, c, v, beta, h, run} = G, hipZ = v * tau, feet = [];
  const flatZ = (i, n) => v * (n - .5 * i + beta / 2) / c;                 // foot i's spot for step n: under the hips at mid-stance
  for (let i = 0; i < 2; i++) {
    const x = tau * c + .5 * i, n = Math.floor(x), ph = x - n;
    if (ph < beta) { const w = ph / beta, roll = stanceRoll(w, run); feet.push({stance: true, w, roll, A: ankleAt(flatZ(i, n), roll)}); }
    else { const w = (ph - beta) / (1 - beta), A0 = ankleAt(flatZ(i, n), stanceRoll(1, run)), A1 = ankleAt(flatZ(i, n + 1), stanceRoll(0, run));
      const k = ease(w), A = new THREE.Vector3(0, A0.y + (A1.y - A0.y) * w + h * Math.pow(Math.sin(Math.PI * w), .8), A0.z + (A1.z - A0.z) * k);
      feet.push({stance: false, w, roll: swingRoll(w, run), A, A0, A1, n, i}); }
  }
  // hip height: as high as the planted legs reach (a little bent), easing in/out as a foot lands or lifts
  const top = (L1 + L2) * .985 + ANKLE_Y, reach = (A, z) => { const dz = Math.abs(A.z - z); return dz < L * .995 ? A.y + Math.sqrt((L * .995) ** 2 - dz * dz) : A.y; };
  let H = top;
  for (const f of feet) {
    if (f.stance) H = Math.min(H, reach(f.A, hipZ));
    else { if (f.w > .75) H = Math.min(H, top + (reach(f.A1, hipZ) - top) * smooth(.75, 1, f.w));
      if (f.w < .25) { const tOff = (f.n - .5 * f.i + beta) / c; H = Math.min(H, reach(f.A0, v * tOff) + (top - reach(f.A0, v * tOff)) * smooth(0, .25, f.w)); } }
  }
  if (run && !feet.some(f => f.stance)) H += run * .03 * Math.sin(Math.PI * Math.min(1, Math.max(0, ((tau * c) % .5 - beta) / (.5 - beta))));   // airborne between running strides
  return {hipZ, H, feet};
}
export function gaitPose(P, G, tau) {
  const S = gaitState(P, G, tau), ph = tau * G.c, {run, mood, stride} = G;
  // upper body: arms swing against the legs, pelvis twists and drops, chest counter-twists (phase: left foot lands at ph = 0)
  const up = ph - .25, tw = Math.sin(up * TAU) * (.11 + .05 * run) * stride, drop = Math.cos(up * TAU) * .045 * stride;
  P.hips.position.y = S.H; P.hips.rotation.set(0, tw, drop);
  // upright: a frightened walk only draws the shoulders in a little; running leans into the run
  P.chest.rotation.set(.07 * mood + .18 * run + (P.stoop || 0), -tw * 1.5, -drop * .8);
  P.neck.rotation.set(-.05 * mood - .14 * run - (P.stoop || 0) * .6, tw * .4, 0); P.head.rotation.set(0, 0, 0);
  // arms swing from the shoulder against the opposite leg; the elbow bends more as the arm comes forward. Scared: a tighter,
  // stiffer swing with the arms held in, plus a tremble
  P.arms.forEach((a, i) => { const s = Math.sin(up * TAU + (i ? Math.PI : 0)), amp = (.48 + .4 * run) * stride * (1 - .45 * mood);
    a.up.rotation.set(-amp * s - .12 * mood, 0, a.sd * (.24 - .08 * mood - .05 * run));
    a.fo.rotation.set(-.22 - Math.max(0, -s) * (.45 + .2 * run) * stride - .45 * mood - 1.1 * run, 0, 0);
    a.hand.rotation.set(-.12 - Math.max(0, -s) * .2, -a.sd * Math.PI / 2, 0); });
  if (mood > 0) tremble(P, tau, mood);
  // legs: inverse kinematics to the ankles; the thighs undo the pelvis twist so the knees point forward
  P.legs.forEach((l, i) => { const f = S.feet[i], hx = l.th.position.x;
    const hy = S.H + hx * Math.sin(drop), hz = S.hipZ - hx * Math.sin(tw);
    const k = legIK(G.L1, G.L2, hy, hz, f.A.y, f.A.z);
    l.th.rotation.order = 'YZX'; l.th.rotation.set(k.th, -tw, -drop); l.sh.rotation.set(k.knee, 0, 0);
    l.ft.rotation.set(-(k.th + k.knee) + f.roll, 0, 0);
    l.toe.rotation.set(-Math.max(0, f.roll) * (f.stance ? 1 : 1 - .2 * smooth(.3, .7, f.w)), 0, 0); });   // toes flat on the floor at push-off, level just after
  sway(P, Math.cos(ph * TAU * 2) * (.025 + .04 * run) * stride - .06 * run, Math.sin(up * TAU) * .02 * stride);
  return S;
}
// walk along a straight line, in stop-motion steps; returns how far (world units) the body has gone
export function walk(P, t, {from = [0, 0], dir = 0, start = 0, cadence = .9, stride = 1, mood = 0, run = 0} = {}) {
  const G = gaitParams(P, {stride, mood, run, cadence}), tau = step12(Math.max(0, t - start)), S = P.root.scale.x;
  const st = gaitPose(P, G, tau), d = st.hipZ * S;
  P.root.rotation.set(0, dir, 0);
  P.root.position.set(from[0] + Math.sin(dir) * d, P.root.position.y, from[1] + Math.cos(dir) * d);
  return d;
}
// walk from A to B and stop there (the last step eases into the standing pose)
export function walkTo(P, t, {from, to, start = 0, cadence = .9, stride = 1, mood = 0, run = 0}) {
  const dx = to[0] - from[0], dz = to[1] - from[1], L = Math.hypot(dx, dz), dir = Math.atan2(dx, dz);
  const dur = walkDuration(P, from, to, {cadence, stride, mood, run});
  if (t < start) { standAt(P, from, dir); return 0; }
  if (t - start >= dur) { standAt(P, to, dir); return 1; }
  walk(P, t, {from, dir, start, cadence, stride, mood, run});
  return (t - start) / dur;
}
function standAt(P, at, dir) { P.rest(); P.hips.position.y = P._hipY0; P.root.rotation.set(0, dir, 0); P.root.position.set(at[0], P.root.position.y, at[1]); sway(P, 0, 0); }
export const walkDuration = (P, from, to, o = {}) => Math.hypot(to[0] - from[0], to[1] - from[1]) / (gaitParams(P, o).v * P.root.scale.x);

// ---------------------------------------------------------------- pose to pose
const saveRot = P => ({q: BONES(P).map(b => b.quaternion.clone()), hy: P.hips.position.y, rq: P.root.quaternion.clone()});
const loadRot = (P, s) => { BONES(P).forEach((b, i) => b.quaternion.copy(s.q[i])); P.hips.position.y = s.hy; P.root.quaternion.copy(s.rq); };
export const snapshot = saveRot;
// keys: [[time, poseFn(P)], ...]; the pose functions set bone rotations (like POSES[i].fn). Between two keys the pose is
// eased (slow out, slow in) and stepped at 12 a second. Poses are captured once and cached on the character.
// put the lowest sole on the floor (y = floor, world), by moving the hips; air: lift above the floor (jumps)
export function ground(P, floor = 0, air = 0) {
  P.root.updateMatrixWorld(true);
  const lo = Math.min(...P.legs.flatMap(l => solePoints(l).map(p => p.y)));
  P.hips.position.y += (floor + air - lo) / P.root.scale.y; P.root.updateMatrixWorld(true);
}
// keys: [[time, poseFn, air?], ...]   air = height of the feet above the floor for that pose (a jump), eased like the rest
// keepFacing: ignore the direction a pose turns the whole body (perform() decides where the character faces)
export function poseBlend(P, t, keys, {hold = 0, floor = 0, keepFacing = false} = {}) {
  const face0 = P.root.quaternion.clone();
  P._poseCache = P._poseCache || new Map();
  const snap = fn => { if (!P._poseCache.has(fn)) { const s0 = saveRot(P); P.rest(); P.hips.position.y = P._hipY0; fn(P, THREE); P._poseCache.set(fn, saveRot(P)); loadRot(P, s0); } return P._poseCache.get(fn); };
  const q = step12(t);
  let i = 0; while (i < keys.length - 1 && q >= keys[i + 1][0]) i++;
  const A = snap(keys[i][1]);
  if (i === keys.length - 1 || q < keys[0][0]) { const K = i === keys.length - 1 ? keys[i] : keys[0]; loadRot(P, snap(K[1])); if (keepFacing) P.root.quaternion.copy(face0); ground(P, floor, K[2] || 0); return; }
  const B = snap(keys[i + 1][1]), t0 = keys[i][0] + hold, k = ease((q - t0) / (keys[i + 1][0] - t0));
  BONES(P).forEach((b, j) => b.quaternion.copy(A.q[j]).slerp(B.q[j], k));
  P.hips.position.y = A.hy + (B.hy - A.hy) * k; P.root.quaternion.copy(A.rq).slerp(B.rq, k); if (keepFacing) P.root.quaternion.copy(face0);
  ground(P, floor, (keys[i][2] || 0) + ((keys[i + 1][2] || 0) - (keys[i][2] || 0)) * k);
}

// ---------------------------------------------------------------- face: expressions, blinks, lip sync
// expr: [[time, name], ...]. On the frame an expression changes, one in-between frame is shown (eyes shut, brows half way),
// the way stop-motion animators hide a replacement-face swap. cues: Rhubarb cues for this character (mouths.json); words:
// word timings (fallback). Blinks run on their own rhythm unless the character is talking with eyes shut.
// breathe: [[from, to, per second], ...] times when the character is out of breath: the mouth opens a little on each breath
export function face(P, t, {expr = [[0, 'neutral']], cues = null, words = null, breathe = []} = {}) {
  const q = step12(t); let i = 0; while (i < expr.length - 1 && q >= expr[i + 1][0]) i++;
  P.expr(expr[i][1]);
  const changedAt = expr[i][0], inBetween = i > 0 && q - changedAt < 1 / 12 - 1e-6;
  if (inBetween) { P.eyes('closed'); }
  const talking = cues ? P.talkCues(cues, t) : words ? P.talk(words, t) : false;
  if (!talking) for (const [a, b, rate] of breathe) if (q >= a && q < b && Math.sin((q - a) * rate * Math.PI * 2) > 0) { P.mouth('vU'); break; }
  if (!inBetween) P.blink(t);
  return talking;
}

// ---------------------------------------------------------------- secondary motion
// hair: a small tilt of the hair pieces round the head (forward/back, side to side). Callers give it from the motion
// (walk does), so it stays a function of time.
export function sway(P, fwd, side) { for (const h of P.hair || []) h.rotation.set(fwd, 0, side); }
// a frightened jolt: the body squashes down and springs back over ~0.4 s (stop-motion stepped)
export function jolt(P, t, at, amount = 1) {
  const q = step12(t) - at; if (q < 0 || q > .5) return;
  const k = Math.exp(-q * 9) * Math.cos(q * 26) * amount;
  P.root.scale.y = P.root.scale.x * (1 - .06 * k); P.chest.rotation.x -= .12 * k; sway(P, -.08 * k, 0);
}


// ---------------------------------------------------------------- a performance: poses, walks and runs in one list
// perform(P, t, track) plays a list of parts, each starting at its own time, and cross-fades from one into the next (fade s),
// so a crouch rises into a stand, the stand eases into a slow walk, the walk speeds into a run. Works for every character
// (they share one skeleton). Parts:
//   {start, pose: [[time, poseFn, air?], ...], at: [x, z], dir}        poses (absolute times), standing at `at`
//   {start, walk: {to: [x, z], cadence, mood, stride, run}}            walks (or runs, run: 1) from where the last part ended
//   {start, stand: {dir}}                                            just stand (rest pose) where the last part ended
// Returns {part index, position}. Everything is a function of t (any frame alone).
export function perform(P, t, track, {fade = .3, floor = 0} = {}) {
  // where each part starts from: the end of the one before
  if (!track._resolved) { let at = track[0].at || [0, 0], dir = track[0].dir || 0;
    for (const p of track) { p._from = at; p._dir = dir;
      if (p.pose) { at = p.at || at; dir = p.dir !== undefined ? p.dir : dir; p._from = at; p._dir = dir; }
      if (p.walk) { p._end = p.start + walkDuration(P, at, p.walk.to, p.walk); dir = Math.atan2(p.walk.to[0] - at[0], p.walk.to[1] - at[1]); at = p.walk.to; }
      if (p.stand && p.stand.dir !== undefined) { dir = p.stand.dir; p._dir = dir; } }
    track._resolved = true; }
  const evalPart = (p, tt, cont = false) => {
    sway(P, 0, 0); P.hips.rotation.set(0, 0, 0);
    if (p.pose) { P.root.position.set(p._from[0], floor, p._from[1]); P.rest(); P.hips.position.y = P._hipY0; P.root.rotation.set(0, p._dir, 0);
      poseBlend(P, tt, p.pose, {floor, keepFacing: true}); }
    else if (p.walk && cont) {                                       // blending out of a walk: it keeps walking underneath (no stop)
      P.root.position.y = floor; const dir = Math.atan2(p.walk.to[0] - p._from[0], p.walk.to[1] - p._from[1]);
      walk(P, tt, Object.assign({}, p.walk, {from: p._from, dir, start: p.start})); }
    else if (p.walk) { P.root.position.y = floor; walkTo(P, tt, Object.assign({from: p._from, start: p.start}, p.walk)); }
    else { P.rest(); P.hips.position.y = P._hipY0; P.root.position.set(p._from[0], floor, p._from[1]); P.root.rotation.set(0, p._dir, 0); }
  };
  const q = step12(t); let i = 0; while (i < track.length - 1 && q >= track[i + 1].start) i++;
  evalPart(track[i], q);
  if (track[i].tremble) tremble(P, q, track[i].tremble);
  const k = i > 0 ? ease((q - track[i].start) / fade) : 1;
  if (k < 1) {                                                        // cross-fade from the previous part
    const B = saveRot(P), bp = P.root.position.clone(), bh = P.hair.map(h => h.rotation.clone());
    evalPart(track[i - 1], q, !!track[i].walk); const A = saveRot(P), ap = P.root.position.clone();   // walk into walk/run: no stop in between
    BONES(P).forEach((b, j) => b.quaternion.copy(A.q[j]).slerp(B.q[j], k));
    P.hips.position.y = A.hy + (B.hy - A.hy) * k; P.root.quaternion.copy(A.rq).slerp(B.rq, k); P.root.position.lerpVectors(ap, bp, k);
    P.hair.forEach((h, j) => h.rotation.set(h.rotation.x * (1 - k) + bh[j].x * k, 0, h.rotation.z * (1 - k) + bh[j].z * k));
    ground(P, floor);
  }
  return {part: i, position: P.root.position};
}

// trembling with fear: small quick shakes of the hands, forearms and head, different every stop-motion frame (a function of t).
// amount 0..1. Call after the pose is set (it adds to it).
export function tremble(P, t, amount = 1) {
  const q = Math.floor(t * 12 + 1e-6), n = (k, j) => Math.sin((q * 12.9898 + k * 78.233 + j * 37.719) * 43758.5453 % 6.2831);
  P.arms.forEach((a, i) => { a.fo.rotation.x += n(i, 1) * .06 * amount; a.fo.rotation.z += n(i, 2) * .05 * amount;
    a.hand.rotation.x += n(i, 3) * .12 * amount; a.hand.rotation.z += n(i, 4) * .1 * amount; a.up.rotation.z += n(i, 5) * .02 * amount; });
  P.head.rotation.z += n(5, 6) * .015 * amount; P.chest.rotation.x += n(6, 7) * .008 * amount;
}
