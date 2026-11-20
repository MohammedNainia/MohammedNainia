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
export const BONES = P => [P.hips, P.chest, P.neck, P.head, ...P.arms.flatMap(a => [a.up, a.fo, a.hand]), ...P.legs.flatMap(l => [l.th, l.sh, l.ft])];

// ---------------------------------------------------------------- the walk cycle
// phase 0..1 = one full cycle (two steps). Each leg: thigh swings, knee bends while the leg swings forward, the foot stays
// flat on the ground in stance. Arms swing against the legs, the body bobs and twists a little. Values are in radians.
export const stanceLeg = ph => Math.cos(ph * TAU) < 0 ? 0 : 1;
// the foot's angle to the floor through one step (+ = toe down, radians). p: the leg's phase (90 deg = foot at the front).
// Walking: heel strike with the toes up -> flat -> heel peels up -> toe-off -> toes hang in the swing -> toes lift for the next
// strike. Running: lands flatter (on the ball of the foot) and pushes off harder.
export const SOLE = [new THREE.Vector3(0, -.058, -.08), new THREE.Vector3(0, -.058, .04), new THREE.Vector3(0, -.058, .16)];   // heel, middle, toe (foot space)
export const contact = pts => { let b = 0; for (let k = 1; k < pts.length; k++) if (pts[k].y < pts[b].y - 1e-4) b = k; return b; };
const smooth = (a, b, x) => { const k = Math.min(1, Math.max(0, (x - a) / (b - a))); return k * k * (3 - 2 * k); };
function footRoll(p, run = 0) {
  const u = ((p - Math.PI / 2) % TAU + TAU) % TAU / TAU;           // 0 = heel strike, .5 = toe-off, 1 = next strike
  const strike = -.32 * (1 - run * .8), off = .65 + .35 * run, hang = .3;
  if (u < .5) {                                                    // on the ground
    const flat = smooth(0, .12, u);                                // toes come down to flat
    const peel = smooth(.28, .5, u);                               // heel peels up towards toe-off
    return strike * (1 - flat) + off * peel;
  }
  const v = (u - .5) / .5;                                         // in the air
  return off + (hang - off) * smooth(0, .25, v) + (strike - hang) * smooth(.6, 1, v);
}
export function walkPose(P, ph, {stride = 1, mood = 0, run = 0} = {}) {   // mood: 0 normal, 1 scared (hunched, small steps, arms in); run: 0 walk .. 1 run
  const A = (.42 + .3 * run) * stride * (1 - .35 * mood);
  P.legs.forEach((l, i) => {
    const p = ph * TAU + (i ? Math.PI : 0), s = Math.sin(p);
    // swing = p from -90 to +90 deg: the knee bends most early in the swing and is straight exactly when the foot reaches
    // the front, so the foot lands and stops there (no skid). Running: the knee comes up high and the standing knee stays soft.
    const sw = ((p + Math.PI / 2) % TAU + TAU) % TAU, u = sw / Math.PI;
    const knee = (u < 1 ? Math.sin(Math.PI * Math.pow(u, .85 - .25 * run)) : 0) * (.55 + .3 * stride + 1.15 * run) + .05 + (u >= 1 ? .25 * run : 0);
    l.th.rotation.set(-A * s - .15 * run, 0, 0); l.sh.rotation.set(knee, 0, 0);
    l.ft.rotation.set(-(-A * s - .15 * run + knee) + footRoll(p, run) * stride, 0, 0);   // the foot's angle to the floor rolls through the step
  });
  P.arms.forEach((a, i) => {
    const s = Math.sin(ph * TAU + (i ? 0 : Math.PI));
    a.up.rotation.set(-(.32 + .45 * run) * s * stride * (1 - .6 * mood) - .1 * mood, 0, a.sd * (.24 - .1 * mood - .05 * run));
    a.fo.rotation.set(-.18 - Math.max(0, -s) * .35 * stride - .5 * mood - 1.15 * run, 0, 0);   // running: elbows bent about 90 degrees
    a.hand.rotation.set(-.12, -a.sd * Math.PI / 2, 0);
  });
  // the pelvis: twists with the leg that swings forward and drops a little on the swinging side; the chest twists back
  const tw = Math.sin(ph * TAU) * (.11 + .05 * run) * stride, drop = Math.cos(ph * TAU) * .045 * stride;
  P.hips.rotation.set(.1 * run, tw, drop);
  // the legs turn back at the hip joint by the same amount, so the hips twist over the feet without dragging them round
  P.legs.forEach(l => { l.th.rotation.order = 'YZX'; l.th.rotation.y = -tw; l.th.rotation.z = -drop; });
  P.chest.rotation.set(.04 + .25 * mood + .22 * run + (P.stoop || 0), -tw * 1.5, -drop * .8);
  P.neck.rotation.set(-.15 * mood - .18 * run - (P.stoop || 0) * .6, tw * .4, 0); P.head.rotation.set(0, 0, 0);
}
export const runPose = (P, ph, o = {}) => walkPose(P, ph, Object.assign({run: 1}, o));

// One cycle sampled once per character + options: how far the body moves (so the standing foot does not slide) and how
// high the hips are (so the standing foot stays on the floor). Built by posing the character and measuring its feet.
const tables = new WeakMap();
function cycleTable(P, opt) {
  const key = JSON.stringify(opt); let T = tables.get(P); if (!T) tables.set(P, T = {}); if (T[key]) return T[key];
  const N = 96, saved = saveRot(P), root = P.root, rp = root.position.clone(), rq = root.quaternion.clone(), rs = root.scale.clone(), hy = P.hips.position.y;
  root.position.set(0, 0, 0); root.quaternion.identity(); root.scale.set(1, 1, 1); P.hips.position.y = P._hipY0;
  const feet = [], low = [];
  for (let i = 0; i <= N; i++) {
    walkPose(P, i / N, opt); root.updateMatrixWorld(true);
    feet.push(P.legs.map(l => SOLE.map(v => l.ft.localToWorld(v.clone()))));         // heel, middle and toe of each sole
    low.push(Math.min(...P.legs.flatMap(l => [l.ft.localToWorld(new THREE.Vector3(0, -.058, .16)).y, l.ft.localToWorld(new THREE.Vector3(0, -.058, -.08)).y])));   // toe and heel
  }
  P.legs.forEach(l => { l.th.rotation.set(0, 0, 0); l.sh.rotation.set(0, 0, 0); l.ft.rotation.set(0, 0, 0); }); P.hips.rotation.set(0, 0, 0);
  root.updateMatrixWorld(true); const restY = P.legs[0].ft.localToWorld(new THREE.Vector3(0, -.05, .03)).y, restLow = P.legs[0].ft.localToWorld(new THREE.Vector3(0, -.058, .16)).y;
  const dist = [0], lift = [];
  for (let i = 0; i <= N; i++) {
    const st = Math.cos((i / N) * TAU) < 0 ? 0 : 1;                                     // standing foot: the one moving back under the body
    lift.push(restLow - low[i]);                                                         // the lowest heel or toe touches the floor, none goes through it
    // the body moves forward exactly as far as the point of the standing foot that touches the floor (heel, sole or toe:
    // the lowest one) moves back, so that point stays put while the foot rolls over it
    const c = contact(feet[i][st]);
    if (i) dist.push(dist[i - 1] + (feet[i - 1][st][c].z - feet[i][st][c].z));
  }
  loadRot(P, saved); root.position.copy(rp); root.quaternion.copy(rq); root.scale.copy(rs); P.hips.position.y = hy; root.updateMatrixWorld(true);
  return T[key] = {N, dist, lift, D: dist[N]};
}
const lookup = (arr, N, f) => { const x = f * N, i = Math.min(N - 1, Math.floor(x)), k = x - i; return arr[i] + (arr[i + 1] - arr[i]) * k; };

// walk along a straight line, in stop-motion steps. cadence: cycles per second (2 steps each); returns metres walked.
export function walk(P, t, {from = [0, 0], dir = 0, start = 0, cadence = .9, stride = 1, mood = 0, run = 0, scale = null} = {}) {
  const opt = {stride, mood, run}, T = cycleTable(P, opt), q = step12(Math.max(0, t - start)), c = q * cadence, ph = c - Math.floor(c);
  const S = scale !== null ? scale : P.root.scale.x;
  const d = (Math.floor(c) * T.D + lookup(T.dist, T.N, ph)) * S;
  walkPose(P, ph, opt);
  P.hips.position.y = P._hipY0 + lookup(T.lift, T.N, ph);
  P.root.rotation.set(0, dir, 0);
  P.root.position.set(from[0] + Math.sin(dir) * d, P.root.position.y, from[1] + Math.cos(dir) * d);
  sway(P, Math.cos(ph * TAU * 2) * (.025 + .04 * run) * stride - .06 * run, Math.sin(ph * TAU) * .02 * stride);   // the hair bounces with every step (and flies back running)
  return d;
}
// walk from A to B and stop there (the last step eases into the standing pose)
export function walkTo(P, t, {from, to, start = 0, cadence = .9, stride = 1, mood = 0, run = 0}) {
  const opt = {stride, mood, run}, T = cycleTable(P, opt), S = P.root.scale.x;
  const dx = to[0] - from[0], dz = to[1] - from[1], L = Math.hypot(dx, dz), dir = Math.atan2(dx, dz);
  const cycles = L / (T.D * S), dur = cycles / cadence;                              // how long it takes
  if (t < start) { standAt(P, from, dir); return 0; }
  if (t - start >= dur) { standAt(P, to, dir); return 1; }
  walk(P, t, {from, dir, start, cadence, stride, mood, run});
  return (t - start) / dur;
}
function standAt(P, at, dir) { P.rest(); P.hips.position.y = P._hipY0; P.root.rotation.set(0, dir, 0); P.root.position.set(at[0], P.root.position.y, at[1]); sway(P, 0, 0); }
export const walkDuration = (P, from, to, {cadence = .9, stride = 1, mood = 0, run = 0} = {}) =>
  Math.hypot(to[0] - from[0], to[1] - from[1]) / (cycleTable(P, {stride, mood, run}).D * P.root.scale.x) / cadence;

// ---------------------------------------------------------------- pose to pose
const saveRot = P => ({q: BONES(P).map(b => b.quaternion.clone()), hy: P.hips.position.y, rq: P.root.quaternion.clone()});
const loadRot = (P, s) => { BONES(P).forEach((b, i) => b.quaternion.copy(s.q[i])); P.hips.position.y = s.hy; P.root.quaternion.copy(s.rq); };
export const snapshot = saveRot;
// keys: [[time, poseFn(P)], ...]; the pose functions set bone rotations (like POSES[i].fn). Between two keys the pose is
// eased (slow out, slow in) and stepped at 12 a second. Poses are captured once and cached on the character.
// put the lowest sole on the floor (y = floor, world), by moving the hips; air: lift above the floor (jumps)
export function ground(P, floor = 0, air = 0) {
  P.root.updateMatrixWorld(true);
  const lo = Math.min(...P.legs.map(l => Math.min(l.ft.localToWorld(new THREE.Vector3(0, -.058, .16)).y, l.ft.localToWorld(new THREE.Vector3(0, -.058, -.08)).y)));
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
  const evalPart = (p, tt) => {
    sway(P, 0, 0); P.hips.rotation.set(0, 0, 0);
    if (p.pose) { P.root.position.set(p._from[0], floor, p._from[1]); P.rest(); P.hips.position.y = P._hipY0; P.root.rotation.set(0, p._dir, 0);
      poseBlend(P, tt, p.pose, {floor, keepFacing: true}); }
    else if (p.walk) { P.root.position.y = floor; walkTo(P, tt, Object.assign({from: p._from, start: p.start}, p.walk)); }
    else { P.rest(); P.hips.position.y = P._hipY0; P.root.position.set(p._from[0], floor, p._from[1]); P.root.rotation.set(0, p._dir, 0); }
  };
  const q = step12(t); let i = 0; while (i < track.length - 1 && q >= track[i + 1].start) i++;
  evalPart(track[i], q);
  const k = i > 0 ? ease((q - track[i].start) / fade) : 1;
  if (k < 1) {                                                        // cross-fade from the previous part
    const B = saveRot(P), bp = P.root.position.clone(), bh = P.hair.map(h => h.rotation.clone());
    evalPart(track[i - 1], q); const A = saveRot(P), ap = P.root.position.clone();
    BONES(P).forEach((b, j) => b.quaternion.copy(A.q[j]).slerp(B.q[j], k));
    P.hips.position.y = A.hy + (B.hy - A.hy) * k; P.root.quaternion.copy(A.rq).slerp(B.rq, k); P.root.position.lerpVectors(ap, bp, k);
    P.hair.forEach((h, j) => h.rotation.set(h.rotation.x * (1 - k) + bh[j].x * k, 0, h.rotation.z * (1 - k) + bh[j].z * k));
    ground(P, floor);
  }
  return {part: i, position: P.root.position};
}
