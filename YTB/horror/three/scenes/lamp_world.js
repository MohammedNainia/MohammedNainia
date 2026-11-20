// The world of "The Magic Lamp": the inside of the lamp, its brass people, the girl who climbs out, the old seller and his
// market stall. Built from the shared kit (characters.js, sets.js, motion.js) so every figure can be posed and animated.
//   import {lampInterior, brassify, coinMan, motherAndBaby, heldBoy, wallFigures, lampGirl, seller, marketStall} from './lamp_world.js';
import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {makeChar, SET_SCALE} from './characters.js';
import {clay3} from './haru3.js';
import {clayM, magicLamp} from './sets.js';
import {step12, ground} from './motion.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);
const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); if (parent) parent.add(g); return g; };
const mesh = (geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0]) => { const m = new THREE.Mesh(geo, mat); m.position.set(...pos); m.rotation.set(...rot); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; };
const rnd = (() => { let s = 77; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();

// ---- brass: a dull, tarnished, hand-made metal (clay finger marks, green in the hollows)
export const BRASS = 0xa88a48, TARNISH = 0x3e5a44;   // dark theme: older, greener brass
export const brassM = (c = BRASS, o = {}) => clay3(c, Object.assign({metalness: .65, roughness: .42, bumpScale: 1.3, sheen: 0}, o));

// turn a character into a brass figure (k = 1) or back to clay (k = 0): every clay material is blended towards brass;
// the pupils stay dark so the eyes can still follow you
export function brassify(P, k = 1, {tint = BRASS, tarnish = .35} = {}) {
  const target = new THREE.Color(tint).lerp(new THREE.Color(TARNISH), tarnish);
  for (const [name, m] of Object.entries(P.M)) {
    if (!m || !m.color || name === 'eye' || name === 'tear' || name === 'sweat') continue;
    m.userData.orig = m.userData.orig || {c: m.color.clone(), metal: m.metalness || 0, rough: m.roughness, sheen: m.sheen || 0};
    const o = m.userData.orig; m.color.copy(o.c).lerp(target, k);
    m.metalness = o.metal + (.65 - o.metal) * k; m.roughness = o.rough + (.42 - o.rough) * k; if ('sheen' in m) m.sheen = o.sheen * (1 - k);
  }
  P.brass = k;
}
// make a character look at a world point (head and neck share the turn); for the figures whose eyes follow Haru
export function lookAt(P, target, amount = 1) {
  P.root.updateMatrixWorld(true);
  const local = P.chest.worldToLocal(target.clone()), yaw = Math.atan2(local.x, local.z), pitch = -Math.atan2(local.y - .6, Math.hypot(local.x, local.z));
  P.neck.rotation.y = yaw * .4 * amount; P.head.rotation.y = yaw * .6 * amount; P.head.rotation.x = Math.max(-.5, Math.min(.5, pitch * .7)) * amount;
}

// ================================================================ the inside of the lamp
// A tall brass throat: wide and round at the bottom where Haru lands, narrowing up to the spout, with ridges like the inside
// of a throat, oil sweating down the walls, a floor that is soft (it dents round the feet) with hands coming out of it.
// The only light is the hole at the top (Haru's bedroom), plus the brass's own dull shine.
export function lampInterior({R = 2.3, H = 6} = {}) {
  const g = G(), radius = y => { const u = y / H; return R * (1 - .15 * u) * (u < .55 ? 1 : 1 - Math.pow((u - .55) / .45, 1.6) * .9) + .04 * Math.sin(y * 16) * (1 - u * .5); };
  // the wall: a lathe with ridges, its surface pushed in and out a little (hand-made), seen from inside
  const prof = []; for (let i = 0; i <= 120; i++) { const y = i / 120 * H; prof.push(new THREE.Vector2(radius(y), y)); }
  const wg = new THREE.LatheGeometry(prof, 96), p = wg.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), a = Math.atan2(x, z);
    const k = 1 + .025 * Math.sin(a * 5 + y * 3) + .018 * Math.sin(a * 13 - y * 7) + .012 * Math.sin(a * 29 + y * 11); p.setXYZ(i, x * k, y, z * k); }
  wg.computeVertexNormals();
  const wallM = brassM(0x3a2c16, {side: THREE.BackSide, roughness: .55});   // the walls stay dark; only light picks them out const wall = mesh(wg, wallM, g); wall.userData.noBoil = true;
  // the floor: a shallow bowl, soft-looking (darker, less shiny)
  const fg = new THREE.CircleGeometry(R * 1.02, 64); fg.rotateX(-Math.PI / 2); const fp = fg.attributes.position;
  for (let i = 0; i < fp.count; i++) { const x = fp.getX(i), z = fp.getZ(i), r = Math.hypot(x, z); fp.setY(i, Math.pow(r / R, 3) * .25 + .015 * Math.sin(x * 9) * Math.sin(z * 7)); }
  fg.computeVertexNormals(); mesh(fg, brassM(0x3a2a14, {roughness: .7, metalness: .4}), g).userData.noBoil = true;
  // oil sweating down the walls: small glossy drops, some with runs below them
  const oil = new THREE.MeshPhysicalMaterial({color: 0x2a1c08, roughness: .05, clearcoat: 1, metalness: .2});
  for (let i = 0; i < 70; i++) { const y = .4 + rnd() * H * .7, a = rnd() * Math.PI * 2, r = radius(y) * .985;
    const d = mesh(new THREE.SphereGeometry(.012 + rnd() * .012, 8, 6).scale(1, 1.5, .5), oil, g, [Math.sin(a) * r, y, Math.cos(a) * r]); d.lookAt(0, y, 0);
    if (rnd() < .5) { const run = mesh(new THREE.CylinderGeometry(.004, .007, .15 + rnd() * .3, 5), oil, g, [Math.sin(a) * r, y - .12, Math.cos(a) * r]); run.userData.noBoil = true; } }
  // the hole at the top (the spout opening): a disc of warm bedroom light, and the light that falls from it
  const hole = mesh(new THREE.CircleGeometry(radius(H) * 1.05, 32), new THREE.MeshStandardMaterial({color: 0x000000, emissive: 0xffe2b0, emissiveIntensity: 2.2}), g, [0, H - .02, 0], [Math.PI / 2, 0, 0]);
  const beam = new THREE.RectAreaLight(0xffd9a0, 90, radius(H) * 1.6, radius(H) * 1.6); beam.position.set(0, H - .05, 0); beam.lookAt(0, 0, 0); g.add(beam);
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(radius(H) * .9, R * .55, H, 32, 1, true), new THREE.MeshBasicMaterial({color: 0xffd9a0, transparent: true, opacity: .05, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending}));
  shaft.position.y = H / 2; g.add(shaft);
  // the light falling from the hole onto whoever stands in the middle
  const spot = new THREE.SpotLight(0xffd9a0, 10, H * 1.4, .2, .85, 1.5);   // a tight pool round Haru, darkness beyond spot.position.set(0, H - .1, 0); spot.target.position.set(0, 0, 0); spot.castShadow = true; g.add(spot, spot.target);
  return {group: g, R, H, radius, hole, beam, shaft, spot, wallPoint: (a, y, inset = 0) => { const r = radius(y) - inset; return V(Math.sin(a) * r, y, Math.cos(a) * r); }};
}

// hands coming out of the floor (or a wall): a forearm and an open hand, brass
export function floorHand({grip = .3} = {}) {
  const g = G(), m = brassM(0x7a5c28);
  mesh(new THREE.CapsuleGeometry(.035, .16, 6, 12), m, g, [0, .06, 0]);
  const palm = G(g, [0, .17, 0]); mesh(new THREE.SphereGeometry(.045, 14, 10).scale(1, .9, .45), m, palm);
  for (let i = 0; i < 3; i++) { const f = G(palm, [(i - 1) * .025, .035, 0]); f.rotation.x = grip * (1 + i * .2);
    mesh(new THREE.CapsuleGeometry(.011, .05, 4, 8), m, f, [0, .03, 0]); }
  const th = G(palm, [.04, .0, .01]); th.rotation.z = -.8; mesh(new THREE.CapsuleGeometry(.012, .035, 4, 8), m, th, [0, .025, 0]);
  return g;
}

// ================================================================ the brass people
// the man who wanted to be rich: kneeling in a heap of coins to his waist, coughing up another one
export function coinMan() {
  const P = makeChar('grandpa', {glasses: false, hood: 0x6a5a3a, detail: 1}, true); brassify(P, 1, {tarnish: .25});
  const kneel = () => { P.rest(); for (const l of P.legs) { l.th.rotation.x = -.15; l.sh.rotation.x = 1.55; l.ft.rotation.x = .6; }
    P.chest.rotation.x = .45; P.neck.rotation.x = -.25; P.head.rotation.x = .25;
    P.arms.forEach(a => { a.up.rotation.set(-.6, 0, a.sd * .3); a.fo.rotation.set(-.6, 0, 0); a.hand.rotation.set(-.4, -a.sd * Math.PI / 2, 0); }); };
  kneel(); P.expr('effort'); P.mouth('vD'); ground(P);
  const coinM = brassM(0xc9a24a, {metalness: .8, roughness: .4, bumpScale: .4});
  const coinGeo = new THREE.CylinderGeometry(.03, .03, .006, 16);
  // the heap: a mound up to his waist (in his own units), its surface covered in coins lying every which way
  const heap = G(P.root), top = .55, rad = .62, hAt = r => top * Math.pow(Math.max(0, 1 - (r / rad) ** 2), .8);
  const mg = new THREE.SphereGeometry(1, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), mp = mg.attributes.position;
  for (let i = 0; i < mp.count; i++) { const x = mp.getX(i), y = mp.getY(i), z = mp.getZ(i), k = 1 + .035 * Math.sin(x * 9 + z * 7) * Math.sin(y * 8) + .02 * Math.sin(x * 17 - z * 13);
    mp.setXYZ(i, x * k, y * k, z * k); }
  mg.computeVertexNormals(); mg.scale(rad, top, rad * .9);
  mesh(mg, brassM(0x8a6a2a, {roughness: .55, metalness: .6}), heap, [0, 0, .05]);   // the mound is dark under the coins
  for (let i = 0; i < 1400; i++) { const r = Math.sqrt(rnd()) * rad, a = rnd() * Math.PI * 2, y = hAt(r);
    const c = mesh(coinGeo, coinM, heap, [Math.sin(a) * r, y + .004, Math.cos(a) * r * .9 + .05], [(rnd() - .5) * 1.2, rnd() * 6, (rnd() - .5) * 1.2]); c.castShadow = false; }
  const falling = mesh(coinGeo, coinM, P.root);                      // the coin coming out of his mouth
  return {P, heap, update(t) {
    const q = step12(t), cyc = (q % 1.6) / 1.6;                        // a cough every 1.6 s
    P.chest.rotation.x = .45 + (cyc < .15 ? Math.sin(cyc / .15 * Math.PI) * .18 : 0);
    P.root.updateMatrixWorld(true); const m = P.face.localToWorld(V(0, -.06, .03)); const loc = P.root.worldToLocal(m);
    const fall = Math.max(0, (cyc - .12) / .35); falling.visible = cyc > .1 && fall < 1;
    falling.position.set(loc.x, loc.y - fall * fall * (loc.y - .35), loc.z + fall * .05); falling.rotation.set(fall * 9, 0, fall * 4);
  }};
}

// the mother who wanted her baby never to grow up: sitting, rocking it, three hundred years; the baby's eyes are old
export function motherAndBaby() {
  const M = makeChar('mum', {top: 'cardigan', bottom: 'skirt', skirt: 0x6a5a3a, detail: 1}, true); brassify(M, 1, {tarnish: .45});
  const sit = () => { M.rest(); for (const l of M.legs) { l.th.rotation.x = -1.5; l.sh.rotation.x = 1.5; l.ft.rotation.x = 0; }
    M.chest.rotation.x = .3; M.head.rotation.x = .45; M.neck.rotation.x = .1;
    M.arms.forEach(a => { a.up.rotation.set(-.55, 0, a.sd * .25); a.fo.rotation.set(-1.7, 0, -a.sd * .9); a.hand.rotation.set(0, -a.sd * Math.PI / 2, 0); }); };
  sit(); M.expr('tired'); ground(M);
  // the baby: a tiny figure wrapped in a brass blanket, only the head out: an infant's head with an old face
  const B = makeChar('grandpa', {hairStyle: 'horseshoe', hair: 0x9a8a6a, glasses: false, age: 1, eyeSize: .9, head: 1.7, height: .4, legs: .152, detail: .8}, true);
  brassify(B, 1, {tarnish: .3}); B.expr('tired'); B.eyes('half');
  const bundle = G(B.root); mesh(new THREE.SphereGeometry(.42, 20, 14).scale(.9, 1.45, .8), brassM(0x7a6230), bundle, [0, .62, .0]);   // the swaddle (in the baby's own units)
  B.legs.forEach(l => l.th.visible = false);
  return {M, B, update(t, look) {
    const q = step12(t), rock = Math.sin(q * 2.2) * .12;               // slow rocking, forever
    M.root.rotation.z = rock * .3; M.chest.rotation.z = rock;
    M.root.updateMatrixWorld(true);
    const lap = M.chest.localToWorld(V(-.04, .02, .2)); B.root.position.copy(lap); B.root.position.y -= .12; B.root.rotation.set(-.15, M.root.rotation.y + .3, rock * 1.5);
    if (look) { B.root.updateMatrixWorld(true); lookAt(B, look, .7); }
  }};
}

// the boy who wanted never to be alone: arms grow out of the wall and hold him, wrists, hair, mouth
export function heldBoy(world, angle, y = .05) {
  const P = makeChar('leo', {stripes: 0, detail: 1}, true); brassify(P, 1, {tarnish: .3});
  const g = G(world.group), at = world.wallPoint(angle, y, .55); P.root.position.copy(at); P.root.rotation.y = angle + Math.PI; g.add(P.root);
  P.rest(); P.arms.forEach(a => { a.up.rotation.set(-.2, 0, a.sd * .9); a.fo.rotation.set(-.2, 0, 0); });
  P.expr('afraid');
  P.root.updateMatrixWorld(true);
  // targets on the boy, and an arm from the wall to each one (a curved brass tube, a hand at the end)
  const targets = [...P.arms.map(a => a.hand.localToWorld(V(0, -.04, 0))), P.head.localToWorld(V(0, .12, -.02)), P.head.localToWorld(V(.08, .05, .06)),
    P.head.localToWorld(V(-.07, .02, .07)), P.face.localToWorld(V(0, -.06, .03)), P.chest.localToWorld(V(.1, .3, .1)), P.chest.localToWorld(V(-.12, .2, .1)),
    P.chest.localToWorld(V(0, .1, -.12)), P.legs[0].sh.localToWorld(V(0, -.1, .05)), P.legs[1].sh.localToWorld(V(0, -.1, .05)), P.hips.localToWorld(V(.12, -.05, 0))];
  const armM = brassM(0x8a6a30);
  // each arm: from a ring of melted brass in the wall, an upper arm to an elbow (bent outwards and up), a forearm thinning to
  // a wrist, and a hand with three fingers closed round the spot it holds
  const limb = (a, b, r1, r2) => { const d = b.clone().sub(a), m = mesh(new THREE.CapsuleGeometry(1, 1, 6, 12), armM, g);
    m.position.copy(a).add(b).multiplyScalar(.5); m.scale.set(1, 1, 1); m.geometry = new THREE.CylinderGeometry(r2, r1, d.length(), 12);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), d.normalize()); mesh(new THREE.SphereGeometry(Math.max(r1, r2) * 1.05, 10, 8), armM, g, b.toArray()); return m; };
  targets.forEach((tp, i) => {
    const a0 = angle + (rnd() - .5) * 1.0, y0 = Math.max(.25, tp.y + (rnd() - .2) * .6), w0 = world.wallPoint(a0, y0, .02);
    const elbow = w0.clone().lerp(tp, .5).add(V(0, .14 + rnd() * .12, 0)).add(w0.clone().sub(tp).cross(V(0, 1, 0)).normalize().multiplyScalar((rnd() - .5) * .2));
    const wrist = tp.clone().lerp(elbow, .18);
    mesh(new THREE.TorusGeometry(.05, .02, 8, 16), armM, g, w0.toArray()).lookAt(0, w0.y, 0);
    // one continuous arm, thick at the wall, thinning to the wrist, bending at the elbow (a smooth clay roll, not two poles)
    const cv = new THREE.CatmullRomCurve3([w0, w0.clone().lerp(elbow, .55), elbow, elbow.clone().lerp(wrist, .5), wrist]);
    const tg = new THREE.TubeGeometry(cv, 32, 1, 10, false), tp2 = tg.attributes.position, cen = new THREE.Vector3();
    for (let k = 0; k < tp2.count; k++) { const seg = Math.floor(k / 11), u = seg / 32; cv.getPoint(u, cen);
      const r = .038 - .016 * u + .006 * Math.exp(-(((u - .5) / .06) ** 2));                 // tapers; a slight bulge at the elbow
      const v = new THREE.Vector3(tp2.getX(k), tp2.getY(k), tp2.getZ(k)).sub(cen); const L = v.length() || 1; v.multiplyScalar(r / L * L).add(cen); tp2.setXYZ(k, v.x, v.y, v.z); }
    tg.computeVertexNormals(); mesh(tg, armM, g);
    const hand = G(g); hand.position.copy(wrist); hand.lookAt(tp);
    mesh(new THREE.SphereGeometry(.035, 12, 8).scale(1, .55, 1.2), armM, hand, [0, 0, .03]);
    for (let k = 0; k < 3; k++) { const f = G(hand, [(k - 1) * .022, .0, .06]); f.rotation.x = 1.2;
      mesh(new THREE.CapsuleGeometry(.009, .04, 4, 8), armM, f, [0, .025, 0]); }
  });
  return {P, group: g};
}

// figures fused into the wall, all round: only their fronts come out of the brass; their eyes follow Haru, their lips move
export function wallFigures(world, n = 9, {skip = []} = {}) {
  const kinds = ['grandpa', 'mum', 'grandma', 'mina', 'leo', 'haru'], out = [];
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2 + .2; if (skip.some(s => Math.abs(((a - s + Math.PI) % (2 * Math.PI)) - Math.PI) < .45)) continue;
    const y = .25 + (i % 3) * .5 + rnd() * .2, P = makeChar(kinds[i % kinds.length], {detail: .8}, true);
    brassify(P, 1, {tarnish: .5 + rnd() * .3});
    P.root.position.copy(world.wallPoint(a, y, .03)); P.root.rotation.y = a + Math.PI;    // facing the middle, back half sunk in the wall
    // the brass pooled round them where they meet the wall: a flat, lumpy disc in the wall's own colour
    const pool = new THREE.Mesh(new THREE.TorusGeometry(1, .16, 10, 40).scale(.36, .8, .45), brassM(0x5e4620, {roughness: .5}));   // a ring of melted brass round them
    pool.position.copy(world.wallPoint(a, y + .62, .0)); pool.rotation.y = a + Math.PI; pool.castShadow = pool.receiveShadow = true; world.group.add(pool);
    P.rest(); P.arms.forEach(arm => { arm.up.rotation.set(-.3 - rnd() * .5, 0, arm.sd * (.2 + rnd() * .6)); arm.fo.rotation.set(-rnd() * 1.2, 0, 0); });
    P.expr(['afraid', 'tired', 'worried', 'suspicious'][i % 4]);
    world.group.add(P.root); out.push(P);
  }
  return {figures: out, update(t, look, whisper = false) {
    out.forEach((P, i) => { if (look) lookAt(P, look, .8);
      if (whisper) { const q = Math.floor(t * 12 + i * 5); P.mouth(['vU', 'vO', 'vM', 'vU'][q % 4]); } });
  }};
}

// ================================================================ the girl who comes out
// three hundred years in the wall: an old dress, brass all over; as she climbs into the light she warms into clay and her face
// becomes Haru's. warm(k): 0 brass .. 1 Haru
export function lampGirl() {
  const P = makeChar('haru', {top: 'sweater', hood: 0x4a3a46, bottom: 'gown', skirt: 0x3e3038, lace: 0xd8ccb0, pants: 0x8a7a6a, shoe: 0x2e2622, detail: 1}, true);
  brassify(P, 1, {tarnish: .55});
  return {P, warm(k) { brassify(P, 1 - k, {tarnish: .55}); }};
}

// ================================================================ the old seller and his stall
export function seller() {
  const P = makeChar('grandpa', {top: 'cardigan', hood: 0x3e5a3a, button: 0xb89a5a, hairStyle: 'horseshoe', glasses: false, age: 1, belly: .2}, true);
  // the giveaway: his fingertips are brass
  P.root.traverse(o => { if (o.isMesh && o.material === P.M.skin && o.parent && P.arms.some(a => a.hand === o.parent)) o.material = brassM(); });
  return P;
}
export function marketStall() {
  const g = G(), wood = 0x7a5a3e, cloth = 0x8a3a3a;
  mesh(new RoundedBoxGeometry(1.4, .06, .7, 2, .02), clayM(wood, 1.4), g, [0, .74, 0]);
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) mesh(new RoundedBoxGeometry(.06, .74, .06, 1, .01), clayM(wood, .7), g, [x * .64, .37, z * .3]);
  mesh(new RoundedBoxGeometry(1.5, .02, .8, 2, .01), clayM(cloth, 1.5), g, [0, .78, 0]);
  mesh(new THREE.BoxGeometry(1.5, .25, .01), clayM(cloth, 1.5), g, [0, .66, .4]);                       // cloth hanging at the front
  for (const sx of [-1, 1]) mesh(new THREE.CylinderGeometry(.02, .02, 1.3, 8), clayM(wood, 1.3), g, [sx * .7, 1.4, -.35]);
  const awn = mesh(new THREE.PlaneGeometry(1.6, .9), Object.assign(clayM(0xd9c48a, 1.6), {side: THREE.DoubleSide}), g, [0, 2.0, 0], [-1.25, 0, 0]);
  for (let i = 0; i < 6; i++) mesh(new THREE.PlaneGeometry(.12, .9), Object.assign(clayM(0xb8452e, 1), {side: THREE.DoubleSide}), g, [-.65 + i * .26, 2.002, .002], [-1.25, 0, 0]);
  // trinkets on the cloth: jars, a candlestick, beads, and the lamp in front
  for (let i = 0; i < 5; i++) mesh(new THREE.CylinderGeometry(.04, .045, .1 + rnd() * .08, 12), clayM([0x5a7a6a, 0x9a6a3a, 0x6a5a8a][i % 3], .2), g, [-.55 + i * .12, .84, -.2]);
  const lamp = magicLamp(); lamp.position.set(.15, .79, .12); lamp.rotation.y = -.6; g.add(lamp);
  return {group: g, lamp};
}
// the rest of the market: stalls either side and behind, bunting, crates, a cobbled ground, and shoppers
export function marketStreet({people = true} = {}) {
  const g = G(), cols = [[0xd9c48a, 0x4a7a5a], [0xd9c48a, 0x3a5a8a], [0xe0d0a0, 0x8a3a5a], [0xd9c48a, 0xb87a2e]];
  const stall = (x, z, ry, k) => { const s = G(g, [x, 0, z]); s.rotation.y = ry;
    mesh(new RoundedBoxGeometry(1.3, .7, .6, 2, .03), clayM(0x6e5038, 1.3), s, [0, .35, 0]);
    for (let i = 0; i < 7; i++) mesh(new THREE.SphereGeometry(.06 + rnd() * .03, 10, 8), clayM([0xc9502e, 0xe0b040, 0x6a9a3a, 0x9a3a5a][i % 4], .2), s, [-.5 + i * .16, .76, (rnd() - .5) * .3]);
    for (const sx of [-1, 1]) mesh(new THREE.CylinderGeometry(.02, .02, 1.6, 8), clayM(0x6e5038, 1.6), s, [sx * .62, .8, -.28]);
    for (let i = 0; i < 6; i++) mesh(new THREE.PlaneGeometry(.22, .8), Object.assign(clayM(cols[k % 4][i % 2], 1), {side: THREE.DoubleSide}), s, [-.55 + i * .22, 1.75, .05], [-1.2, 0, 0]);
    return s; };
  [[-2.0, -.4, .3, 0], [2.0, -.4, -.3, 1], [-1.1, -2.6, 0, 2], [1.2, -2.8, 0, 3], [-3.0, -1.8, .7, 1], [3.1, -2.0, -.6, 2]].forEach(([x, z, r, k]) => stall(x, z, r, k));
  for (let i = 0; i < 6; i++) mesh(new RoundedBoxGeometry(.4, .3, .3, 1, .02), clayM(0x8a6a44, .4), g, [-2.6 + rnd() * 5.2, .15, .9 + rnd() * .6], [0, rnd() * 3, 0]);
  // bunting: little triangle flags on a line across the street
  const line = new THREE.CatmullRomCurve3([V(-3.2, 2.6, -1.2), V(0, 2.25, -1.0), V(3.2, 2.6, -1.2)]);
  mesh(new THREE.TubeGeometry(line, 30, .006, 4), clayM(0x3a3a3a, .5), g);
  for (let i = 1; i < 24; i++) { const p = line.getPoint(i / 24), f = mesh(new THREE.ConeGeometry(.07, .16, 3), clayM([0xc9502e, 0xe0b040, 0x3a7a9a, 0xe8e0cc][i % 4], .2), g, [p.x, p.y - .08, p.z]); f.rotation.z = Math.PI; }
  // cobbles
  const cob = clayM(0x8a7e6a, .3);
  for (let i = 0; i < 380; i++) { const c = mesh(new THREE.SphereGeometry(.09 + rnd() * .04, 8, 5).scale(1, .25, .8), cob, g, [-4 + rnd() * 8, .0, -3.5 + rnd() * 6]); c.castShadow = false; }
  const out = {group: g, people: []};
  if (people) [['mum', -1.3, -1.6, .6], ['grandma', 2.3, -1.4, -.8], ['leo', -2.4, .6, 1.2], ['mina', 1.6, -3.2, .2]].forEach(([n, x, z, r]) => {
    const P = makeChar(n, {detail: .7}, true); P.root.position.set(x, 0, z); P.root.rotation.y = r; P.expr('neutral'); g.add(P.root); out.people.push(P); });
  return out;
}

// metal needs something to reflect, or it looks like cardboard: a dim, warm environment for the inside of the lamp
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
export function brassEnvironment(renderer, scene, strength = .45) {
  const pm = new THREE.PMREMGenerator(renderer), env = pm.fromScene(new RoomEnvironment(renderer), .04).texture;
  scene.environment = env; scene.traverse(o => { if (o.isMesh && o.material && 'envMapIntensity' in o.material) o.material.envMapIntensity = strength; });
  return env;
}
// a camera that looks at a character's face: dist in front of where they face, up/side offsets, world units
export function faceCam(P, dist = 1.2, up = .05, side = .2) {
  P.root.updateMatrixWorld(true); const h = P.head.getWorldPosition(new THREE.Vector3()), ry = P.root.rotation.y;
  const fwd = new THREE.Vector3(Math.sin(ry), 0, Math.cos(ry)), right = new THREE.Vector3(Math.cos(ry), 0, -Math.sin(ry));
  return {pos: h.clone().add(fwd.multiplyScalar(dist)).add(new THREE.Vector3(0, up, 0)).add(right.multiplyScalar(side)), at: h};
}

// a soft light that only follows one character (attached in front, slightly above): they stay readable in the dark while the
// walls behind them do not light up. Warm like the light from the hole. Returns the light (set .intensity to taste).
export function keyOn(P, {color = 0xffd8a8, power = 1.6, dist = .5, height = .5, side = .75} = {}) {   // from the side: faces half in shadow
  const l = new THREE.PointLight(color, power, 2.2, 2); l.position.set(side, (P.hips.position.y + .7) + height, dist); P.root.add(l);
  return l;
}
