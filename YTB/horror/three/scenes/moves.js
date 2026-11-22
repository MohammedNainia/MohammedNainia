// Movement for the library's characters (and any makePerson puppet): a relaxed default stance, idle, travelling walk / run along a path
// with feet that don't slide, turning on the spot with little steps, looking back over the shoulder.
//   import {relaxed, idle, stride, travel, turnOnSpot} from './moves.js';
//   reset(P); relaxed(P);                       // the default stance: weight on one leg, soft elbows, shoulders down, head a little tilted
//   idle(P, t);                                 // relaxed + breathing + a slow sway (call every frame instead of relaxed)
//   travel(P, t, path)                          // walk / run along a path of moves: see below
// Every function starts from the joints as reset() leaves them (all zero) and adds to them, so look(), expr() etc. still go on top.
import * as THREE from 'three';
import {walk as clayWalk, look, groundFeet} from './clay.js';

const sm = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
const lerp = (a, b, k) => a + (b - a) * k;

// relaxed(P, k, side): the stance a person falls into: weight on one leg (side = 1 her right, -1 her left), that hip up, the other knee
// soft and its foot turned out; shoulders let down; elbows soft, hands in a little towards the thighs; head tipped a touch.
export function relaxed(P, k = 1, side = 1) {
  const s = side;
  P.hips.rotation.z += .035 * s * k; P.hips.rotation.y += .05 * s * k;
  P.chest.rotation.z -= .045 * s * k; P.chest.rotation.x += .03 * k;           // the chest leans back over the standing leg
  P.neck.rotation.x += .05 * k; P.head.rotation.z += .04 * s * k; P.head.rotation.x -= .02 * k;
  P.legs.forEach(({th, sh, ft}, i) => { const stand = (i === 0) === (s > 0);
    if (stand) { th.rotation.z -= .02 * s * k; }
    else { th.rotation.x -= .07 * k; th.rotation.z += .04 * s * k; th.rotation.y += .15 * s * k; sh.rotation.x += .16 * k; ft.rotation.x -= .08 * k; } });
  P.arms.forEach(({up, fo, hand}, i) => { const m = i ? -1 : 1;
    up.rotation.z += .07 * m * k; up.rotation.x += .05 * k; up.rotation.y -= .1 * m * k;   // in towards the body, a little back, turned in
    fo.rotation.x -= .26 * k; fo.rotation.y -= .15 * m * k;                                 // soft elbow, the forearm turned so the palm faces the leg
    if (hand) { hand.rotation.x -= .12 * k; hand.rotation.z += .05 * m * k; } });
  groundFeet(P, k);
}
// idle(P, t): relaxed, breathing, a slow sway and a little drift of the head
export function idle(P, t, k = 1, seed = 0, side = 1) {
  relaxed(P, k, side);
  const b = Math.sin((t + seed) * Math.PI * 2 / 3.8) * k;
  P.chest.rotation.x -= b * .018; P.neck.rotation.x += b * .012; P.arms.forEach(({up}, i) => { up.rotation.z += b * .012 * (i ? -1 : 1); });
  P.hips.rotation.z += Math.sin((t + seed) * .7) * .008 * k; P.head.rotation.y += Math.sin((t + seed) * .43) * .03 * k;
}

// run(P, t, {amp, speed}): a sprint, not a fast walk: the body leans into it, the knees drive up in front, the back foot kicks up behind,
// the arms pump bent at 90 degrees, and both feet leave the ground between steps (the hips rise and drop twice a cycle).
export function run(P, t, {amp = 1, speed = 1} = {}) {
  const ph = t * Math.PI * 2 * 1.45 * speed, sw = Math.sin(ph), a = amp;
  const fl = Math.max(0, Math.sin(ph * 2 - .9));                              // flight: twice a cycle, just after each push off
  P.hips.position.y = .82 - .055 * a + fl * .045 * a;
  P.hips.rotation.x = .12 * a; P.hips.rotation.y = sw * .14 * a;
  P.chest.rotation.x = .2 * a; P.chest.rotation.y = -sw * .22 * a; P.neck.rotation.x = -.08 * a; P.head.rotation.x = -.2 * a;
  P.legs.forEach(({th, sh, ft}, i) => { const q = i ? -sw : sw, c = Math.cos(ph + (i ? Math.PI : 0));
    th.rotation.x = -(q * .62 + .12) * a;                                       // swing, a little forward overall
    sh.rotation.x = (.35 + Math.max(0, c) * 1.45 + Math.max(0, -q) * .25) * a;   // the kick behind and the bent leg coming through
    ft.rotation.x = (-.25 * Math.max(0, c) + q * .25) * a; });
  P.arms.forEach(({up, fo, hand}, i) => { const q = i ? sw : -sw;
    up.rotation.x = -q * .6 * a - Math.max(0, q) * .15 * a + .05; up.rotation.z -= (i ? -1 : 1) * .06; fo.rotation.x = -1.45 - Math.max(0, q) * .25; if (hand) hand.rotation.x = -.2; });
  if (P.clothes) P.clothes();
}
export const walk = clayWalk;
const gait = (P, t, o) => o.run ? run(P, t, o) : clayWalk(P, t, o);

// The length of one full walk cycle (two steps) for this puppet at amp a, measured from its own legs, so travelling speed = stride * cycles/s.
const STRIDE = new WeakMap();
export function stride(P, {run = false, amp = 1} = {}) {
  const key = (run ? 'r' : 'w') + amp, m = STRIDE.get(P) || {}; if (m[key]) return m[key];
  const v = new THREE.Vector3(), r0 = P.root.position.clone(), q0 = P.root.quaternion.clone(); let lo = Infinity, hi = -Infinity;
  P.root.position.set(0, 0, 0); P.root.quaternion.identity();
  for (let i = 0; i < 24; i++) { gait(P, i / (run ? 24 * 1.45 : 24), {run, amp}); P.root.updateMatrixWorld(true); P.legs[0].ft.getWorldPosition(v); lo = Math.min(lo, v.z); hi = Math.max(hi, v.z); }
  P.root.position.copy(r0); P.root.quaternion.copy(q0); m[key] = 2 * (hi - lo) * .92; STRIDE.set(P, m); return m[key];
}

// travel(P, t, moves): play a list of moves from t = 0, each one starting where the last ended. Returns {pos, heading, move}.
//   {walk: [x, z]}          walk to the point (heading turns smoothly into the direction)       options: speed (cycles/s, 1), amp
//   {run: [x, z]}           run there
//   {turn: angle, dur}      turn on the spot to face a heading (radians; 0 = facing +z, PI/2 = facing +x) with small steps
//   {idle: seconds}         stand relaxed
//   {look: 'L'|'R', dur}    stop and look back over a shoulder (the body turns a little with the head)
// Start: {from: [x, z], heading} as the first item.
export function travel(P, t, moves) {
  const start = moves[0]; let pos = new THREE.Vector2(...start.from), head = start.heading || 0, T = 0, phase = 0;
  for (let i = 1; i < moves.length; i++) {
    const mv = moves[i], kind = Object.keys(mv).find(k => ['walk', 'run', 'turn', 'idle', 'look'].includes(k));
    let dur, apply;
    if (kind === 'walk' || kind === 'run') {
      const run = kind === 'run', to = new THREE.Vector2(...mv[kind]), d = to.clone().sub(pos), L = d.length(), cps = (mv.speed || 1) * (run ? 1.45 : 1);
      const amp = mv.amp || 1, sp = stride(P, {run, amp}) * cps;                                   // metres per second
      const ramp = .35;                                     // seconds to get going and to stop (the stride grows and shrinks)
      dur = L / sp + ramp; const h1 = Math.atan2(d.x, d.y), p0 = pos.clone(), h0 = head, ph0 = phase;
      apply = u => { const tt = u * dur, k = sm(tt / ramp) * sm((dur - tt) / ramp);       // u: 0..1 through this move
        const along = Math.min(1, Math.max(0, (tt - ramp / 2) / (dur - ramp))), dh = Math.atan2(Math.sin(h1 - h0), Math.cos(h1 - h0));
        const hd = h0 + dh * sm(tt / .45);
        gait(P, ph0 + tt * (mv.speed || 1), {run, amp: amp * (.25 + .75 * k)}); P.root.rotation.y = hd;
        return {pos: p0.clone().lerp(to, along), heading: hd, phase: ph0 + tt * (mv.speed || 1)}; };
      head = h1; pos = to.clone(); phase += dur * (mv.speed || 1);
    } else if (kind === 'turn') {
      dur = mv.dur || .9; const h0 = head, dh = Math.atan2(Math.sin(mv.turn - h0), Math.cos(mv.turn - h0)), p0 = pos.clone();
      apply = u => { const k = sm(u), steps = Math.max(2, Math.round(Math.abs(dh) / 1.2) * 2);
        relaxed(P, .5);
        P.legs.forEach(({th, sh}, i) => { const lift = Math.max(0, Math.sin((u * steps + i) * Math.PI)) * Math.sin(u * Math.PI); th.rotation.x -= lift * .25; sh.rotation.x += lift * .45; });
        look(P, {turn: dh * .35 * (sm(u / .3) - sm((u - .5) / .5)), nod: 0});                 // the head leads, the body catches up
        P.chest.rotation.y += dh * .15 * Math.sin(u * Math.PI); P.root.rotation.y = h0 + dh * k; return {pos: p0, heading: h0 + dh * k}; };
      head = mv.turn;
    } else if (kind === 'idle') {
      dur = mv.idle; const p0 = pos.clone(), h0 = head, T0 = T; apply = u => { idle(P, T0 + u * dur); P.root.rotation.y = h0; return {pos: p0, heading: h0}; };
    } else if (kind === 'look') {
      dur = mv.dur || 1.6; const p0 = pos.clone(), h0 = head, s = mv.look === 'L' ? 1 : -1;
      apply = u => { const k = sm(u / .2) * (1 - sm((u - .75) / .25));
        relaxed(P, 1 - .6 * k); look(P, {turn: 1.25 * s * k, nod: -.05 * k}); P.chest.rotation.y += .35 * s * k; P.hips.rotation.y += .15 * s * k;
        P.arms.forEach(({up}) => { up.rotation.x -= .1 * k; }); if (P.expr) P.expr(k > .5 ? 'scared' : 'neutral');
        P.root.rotation.y = h0; return {pos: p0, heading: h0}; };
    }
    if (t < T + dur || i === moves.length - 1) { const r = apply(Math.min(1, Math.max(0, (t - T) / dur))); P.root.position.x = r.pos.x; P.root.position.z = r.pos.y; return {...r, move: kind, index: i}; }
    T += dur;
  }
}
// how long a travel() list takes
export function travelTime(P, moves) { let T = 0, pos = new THREE.Vector2(...moves[0].from), head = moves[0].heading || 0;
  for (const mv of moves.slice(1)) {
    if (mv.walk || mv.run) { const run = !!mv.run, to = new THREE.Vector2(...(mv.walk || mv.run)), cps = (mv.speed || 1) * (run ? 1.45 : 1); T += to.distanceTo(pos) / (stride(P, {run, amp: mv.amp || 1}) * cps) + .35; pos = to; }
    else if (mv.turn !== undefined) T += mv.dur || .9; else if (mv.idle) T += mv.idle; else if (mv.look) T += mv.dur || 1.6; }
  return T; }
