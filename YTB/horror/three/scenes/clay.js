// Clay (stop-motion) kit: clay materials with fingerprint bumps, lumpy shapes that "boil" between frames,
// and the puppets: Haru (human anatomy, face controls), Mum, and the Tooth Fairy.
import {THREE} from './lib.js';

// ---------------------------------------------------------------- materials
const bc = document.createElement('canvas'); bc.width = bc.height = 512; { const g = bc.getContext('2d');
  g.fillStyle = '#808080'; g.fillRect(0, 0, 512, 512);
  let s = 3; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let k = 0; k < 40; k++) { const cx = r() * 512, cy = r() * 512, n = 6 + r() * 8;
    for (let i = 0; i < n; i++) { const v = r() < .5 ? 60 : 200; g.strokeStyle = `rgba(${v},${v},${v},.35)`; g.lineWidth = 1.6;
      g.beginPath(); g.ellipse(cx, cy, 4 + i * 3, 3 + i * 2.2, r() * 3, 0, 6.3); g.stroke(); } }
  for (let k = 0; k < 900; k++) { const v = r() < .5 ? 40 : 220; g.fillStyle = `rgba(${v},${v},${v},.12)`; g.beginPath(); g.arc(r() * 512, r() * 512, 1 + r() * 3, 0, 6.3); g.fill(); } }
export const bump = new THREE.CanvasTexture(bc); bump.wrapS = bump.wrapT = THREE.RepeatWrapping; bump.repeat.set(2, 2);
export const clay = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, roughness: .9, metalness: 0, sheen: .35, sheenRoughness: .9,
  sheenColor: new THREE.Color(c).lerp(new THREE.Color(0xffffff), .35), bumpMap: bump, bumpScale: 1.0}, o));
export const gloss = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, roughness: .25, clearcoat: .8, bumpMap: bump, bumpScale: .2}, o));

// ---------------------------------------------------------------- lumpy geometry + boil
const lumpy = [];
export function lump(geo, amt = .004, freq = 10) { const e = {geo, base: null, nrm: null, amt, freq}; lumpy.push(e); return geo; }
const noise = (x, y, z, sd) => Math.sin(x * 1.7 + sd) * Math.sin(y * 2.3 + sd * 1.3) * Math.sin(z * 1.9 + sd * .7)
  + .5 * Math.sin(x * 3.1 - sd * .9 + y * 1.2) * Math.sin(z * 2.7 + sd * 1.1);
let lastSeed = null;
export function boil(sd) {                       // shift every lump; only when the seed changes (every other stop-motion frame)
  if (sd === lastSeed) return; lastSeed = sd;
  for (const e of lumpy) {
    const {geo, amt, freq} = e;
    if (!e.base) { geo.computeVertexNormals(); e.base = geo.attributes.position.array.slice(); e.nrm = geo.attributes.normal.array.slice();
      const b = e.base, n = e.nrm, acc = new Map();
      for (let i = 0; i < b.length; i += 3) { const k = Math.round(b[i] * 1e4) + ',' + Math.round(b[i + 1] * 1e4) + ',' + Math.round(b[i + 2] * 1e4);
        const a = acc.get(k) || [0, 0, 0, []]; a[0] += n[i]; a[1] += n[i + 1]; a[2] += n[i + 2]; a[3].push(i); acc.set(k, a); }
      for (const [x, y, z, ids] of acc.values()) { if (ids.length < 2) continue; const l = Math.hypot(x, y, z) || 1; for (const i of ids) { n[i] = x / l; n[i + 1] = y / l; n[i + 2] = z / l; } } }
    const p = geo.attributes.position.array, b = e.base, n = e.nrm;
    for (let i = 0; i < p.length; i += 3) { const d = noise(b[i] * freq, b[i + 1] * freq, b[i + 2] * freq, sd) * amt;
      p[i] = b[i] + n[i] * d; p[i + 1] = b[i + 1] + n[i + 1] * d; p[i + 2] = b[i + 2] + n[i + 2] * d; }
    geo.attributes.position.needsUpdate = true; geo.computeVertexNormals();
  }
}
export function add(geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0]) {
  const m = new THREE.Mesh(geo, mat); m.position.set(...pos); m.rotation.set(...rot); m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
export const S = (r, sx = 1, sy = 1, sz = 1, a = .003, f = 12) => lump(new THREE.SphereGeometry(r, 36, 26).scale(sx, sy, sz), a, f);
export const Cp = (r, l, a = .003, f = 12) => lump(new THREE.CapsuleGeometry(r, l, 8, 20), a, f);
export const tube = (r0, r1, l, a = .006, f = 7) => lump(new THREE.CylinderGeometry(r0, r1, l, 20, 8, false), a, f);   // a cloth tube: r0 top, r1 bottom
export const fold = (r, t, a = .002) => lump(new THREE.TorusGeometry(r, t, 8, 20), a, 16);                                 // bunched cloth ring
export const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); parent.add(g); return g; };

// ---------------------------------------------------------------- a person (Haru or Mum): ~7 heads tall, joints, face controls
export function makePerson(o = {}) {
  const M = {skin: clay(o.skin || 0xf0c9a8, {bumpScale: .35}), top: clay(o.top || 0xe0a33a, {bumpScale: 1.2}), pants: clay(o.pants || 0x5a5862, {bumpScale: 1.2}),
    shoe: clay(o.shoe || 0xf2eee6), hair: clay(o.hair || 0x24222a, {bumpScale: .8}), eye: gloss(0x0c0c0e), white: gloss(0xf4f0e8),
    mouth: clay(0x2a0c10, {bumpScale: 0}), gum: clay(0xd86a78, {bumpScale: .2}), tooth: gloss(0xfaf6ee),
    blush: clay(0xd89080, {bumpScale: 0, transparent: true, opacity: .22}), sole: clay(0x3a3532, {bumpScale: .6}), lace: clay(0xd8d2c8, {bumpScale: 0}),
    shine: new THREE.MeshBasicMaterial({color: 0xffffff})};
  const root = new THREE.Group(); root.scale.setScalar(o.scale || 1);
  const hips = G(root, [0, .82, 0]);
  add(S(.125, 1.05, .62, .72, .004), M.pants, hips, [0, .02, 0]);
  const chest = G(hips, [0, .06, 0]);
  add(Cp(.135, .26, .008, 6).scale(1.1, 1, .78), M.top, chest, [0, .23, 0]);
  for (const x of [-1, 1]) add(S(.075, 1.25, .62, .9, .006, 7), M.top, chest, [x * .135, .425, 0], [0, 0, -x * .45]);   // sloped shoulders
  add(Cp(.13, .05, .006, 7).scale(1.18, 1, .82), M.top, chest, [0, -.01, 0]);
  add(fold(.13, .022, .003).scale(1.18, .82, 1), M.top, chest, [0, -.045, 0], [Math.PI / 2, 0, 0]);                     // the hem band
  if (o.pocket !== false) add(S(.07, 1.5, .42, .28, .003, 14), M.top, chest, [0, .08, .095]);
  if (o.hood !== false) { add(lump(new THREE.TorusGeometry(.075, .035, 12, 24), .003, 14), M.top, chest, [0, .47, -.03], [Math.PI / 2 + .35, 0, 0]);
    for (const x of [-.028, .028]) { add(Cp(.005, .085, .0008, 24), M.lace, chest, [x, .37, .1], [.12, 0, x * 2]); add(S(.008, 1, 1.4, 1, .0008, 24), M.lace, chest, [x * 1.15, .315, .107]); } }
  const neck = G(chest, [0, .49, 0]);
  add(Cp(.042, .045, .002, 16), M.skin, neck, [0, .02, 0]);
  const head = G(neck, [0, .14, 0]);
  add(S(.1, .94, 1.12, 1.02, .003, 14), M.skin, head);
  add(S(.03, 1, .8, .6, .002, 16), M.skin, head, [0, -.075, .055]);
  for (const x of [-.093, .093]) add(S(.019, .55, 1, .75, .001, 20), M.skin, head, [x, -.012, -.004]);            // ears (long hair hides them)
  add(S(.109, 1.02, 1.1, 1.0, .004), M.hair, head, [0, .02, -.02]);
  const fringe = new THREE.Mesh(lump(new THREE.SphereGeometry(.112, 32, 14, 0, Math.PI * 2, 0, .9).scale(1.0, 1.08, 1.0), .002, 14), M.hair.clone());
  fringe.material.side = THREE.DoubleSide; fringe.position.set(0, .022, .004); fringe.rotation.x = .35; fringe.castShadow = true; head.add(fringe);
  const back = G(head, [0, -.02, -.07]);
  if (o.longHair !== false) {
    add(Cp(.085, .3, .004, 10).scale(1.25, 1, .42), M.hair, back, [0, -.2, 0]);
    for (const x of [-.092, .092]) add(Cp(.024, .22, .002, 14), M.hair, head, [x, -.14, .005]);
    for (let i = 0; i < 5; i++) add(Cp(.016, .26, .002, 14), M.hair, back, [(i - 2) * .036, -.2 - (i % 2) * .02, -.028], [0, 0, (i - 2) * .05]);   // strands
  }
  if (o.bun) add(S(.055, 1, 1, 1, .003), M.hair, head, [0, .04, -.11]);
  // face
  const face = G(head, [0, -.012, .096]);
  const eyes = [], whites = [], lids = [], brows = [];
  for (const x of [-.034, .034]) {
    whites.push(add(S(.017, 1.15, 1, .35, .001, 20), M.white, face, [x, 0, -.002]));
    const e = add(new THREE.SphereGeometry(.011, 14, 10), M.eye, face, [x, 0, .004]); eyes.push(e);
    add(new THREE.SphereGeometry(.0028, 8, 6), M.shine, e, [.0035, .0042, .0085]).castShadow = false;                  // the catchlight: the eyes look wet and alive
    add(S(.012, 1.3, .75, .25, .0005, 20), M.blush, face, [x * 1.55, -.035, -.007]).castShadow = false;
    lids.push(add(Cp(.0035, .022, .0005, 30), M.hair, face, [x, -.002, .006], [0, 0, Math.PI / 2]));
    brows.push(add(Cp(.004, .022, .0005, 30), M.hair, face, [x, .034, .002], [0, 0, Math.PI / 2]));
  }
  add(S(.01, .9, 1, .8, .001, 18), M.skin, face, [0, -.03, .01]);                  // nose
  const mouth = G(face, [0, -.058, .002]);
  const mLine = add(Cp(.0035, .016, .0005, 30), M.mouth, mouth, [0, 0, .003], [0, 0, Math.PI / 2]);
  const mOpen = G(mouth);
  add(S(.016, 1.25, 1, .35, .001, 20), M.mouth, mOpen);
  const gums = [add(Cp(.004, .02, .0005, 30), M.gum, mOpen, [0, .012, .004], [0, 0, Math.PI / 2]), add(Cp(.004, .02, .0005, 30), M.gum, mOpen, [0, -.012, .004], [0, 0, Math.PI / 2])];
  const teeth = [add(new THREE.BoxGeometry(.026, .006, .004), M.tooth, mOpen, [0, .0075, .005]), add(new THREE.BoxGeometry(.022, .005, .004), M.tooth, mOpen, [0, -.008, .005])];
  // arms and legs
  const arms = [-1, 1].map(sd => {
    const up = G(chest, [sd * .175, .44, 0]); add(S(.052, 1, 1.1, 1, .005, 8), M.top, up, [0, -.025, 0]); add(tube(.053, .05, .26), M.top, up, [0, -.14, 0]);
    const fo = G(up, [0, -.27, 0]); add(S(.05, 1, 1, 1, .004, 8), M.top, fo); add(fold(.046, .013), M.top, fo, [0, .012, 0], [Math.PI / 2 + .3, 0, 0]);
    add(fold(.047, .011), M.top, fo, [0, -.03, 0], [Math.PI / 2 - .25, 0, 0]); add(tube(.048, .056, .2), M.top, fo, [0, -.115, 0]);
    add(fold(.052, .013), M.top, fo, [0, -.215, 0], [Math.PI / 2, 0, 0]);              // sleeve cuff
    const hand = G(fo, [0, -.25, 0]); add(S(.027, .85, 1.0, .5, .002, 18), M.skin, hand, [0, -.022, 0]);
    for (const fx of [-.012, 0, .012]) add(Cp(.0078, .024 - Math.abs(fx) * .25, .0008, 22), M.skin, hand, [fx, -.056, .003], [.25, 0, 0]);
    add(Cp(.011, .03, .001, 20), M.skin, hand, [-sd * .022, -.015, .014], [0, 0, sd * .5]);
    return {up, fo, hand};
  });
  const legs = [-1, 1].map(sd => {
    const th = G(hips, [sd * .075, -.02, 0]); add(tube(.072, .062, .36), M.pants, th, [0, -.18, 0]); add(S(.07, 1, .7, 1, .004, 8), M.pants, th, [0, -.01, 0]);
    const sh = G(th, [0, -.37, 0]); add(S(.06, 1, 1, 1, .004, 8), M.pants, sh); add(fold(.058, .012), M.pants, sh, [0, -.02, .005], [Math.PI / 2 - .3, 0, 0]);
    add(tube(.057, .061, .3), M.pants, sh, [0, -.165, 0]); add(fold(.06, .011), M.pants, sh, [0, -.27, 0], [Math.PI / 2 + .15, 0, 0]);
    add(fold(.06, .013), M.pants, sh, [0, -.315, 0], [Math.PI / 2, 0, 0]);           // trouser hem
    const ft = G(sh, [0, -.37, 0]); add(S(.058, 1, .66, 2.2, .003), M.shoe, ft, [0, -.01, .05]);
    add(S(.061, 1.02, .22, 2.25, .002), M.sole, ft, [0, -.042, .05]);
    for (let k = 0; k < 3; k++) add(Cp(.0035, .05, .0005, 30), M.lace, ft, [0, .025, .06 + k * .022], [0, 0, Math.PI / 2]);
    return {th, sh, ft};
  });
  const P = {root, hips, chest, neck, head, back, face, arms, legs, M};
  P.eyes = s => {                 // 'open' | 'closed' | 'wide' | 'squeeze'
    const open = s === 'open' || s === 'wide';
    eyes.forEach(e => { e.visible = open; e.scale.setScalar(s === 'wide' ? 1.15 : 1); });
    whites.forEach(w => { w.visible = s === 'wide'; });
    lids.forEach((l, i) => { l.visible = !open; l.scale.set(1, s === 'squeeze' ? 1.25 : 1, 1); l.rotation.z = Math.PI / 2 + (s === 'squeeze' ? (i ? -.25 : .25) : 0); });
  };
  P.brows = k => brows.forEach((b, i) => { b.rotation.z = Math.PI / 2 + (i ? -1 : 1) * k * .5; b.position.y = .034 + Math.abs(k) * .006; });  // k>0 worried
  P.mouth = (s, amt = 1) => {     // 'closed' | 'pressed' | 'open' | 'gums' | 'smile'
    mLine.visible = s === 'closed' || s === 'pressed' || s === 'smile';
    mLine.scale.set(1, s === 'pressed' ? 1.4 : s === 'smile' ? 1.3 : 1, s === 'pressed' ? .7 : 1);
    mLine.rotation.x = 0; mLine.position.y = s === 'smile' ? -.002 : 0;
    mOpen.visible = s === 'open' || s === 'gums'; mOpen.scale.set(1, .35 + .65 * amt, 1);
    teeth.forEach(t => t.visible = s === 'open'); gums.forEach(g => g.visible = s === 'gums');
  };
  P.eyes('open'); P.brows(0); P.mouth('closed');
  return P;
}
export const haruOpts = {};
export const mumOpts = {top: 0x3e3040, pants: 0x26252c, shoe: 0x2a2424, longHair: false, bun: true, pocket: false, hood: false, scale: 1.07, hair: 0x2c2420};

// ---------------------------------------------------------------- the Tooth Fairy
export function makeFairy(opt = {}) {
  const ash = clay(opt.skin || 0x8f8c84), ashD = clay(opt.skinD || 0x5e5a54), gum = clay(0x6a1e22), mouthIn = clay(0x1a0608, {bumpScale: 0}), nail = clay(0x2e2a26);
  const T = [gloss(0xf4efe2), gloss(0xe8dfc4), gloss(0xd8cba0), gloss(0xfaf6ee)];
  const wingMat = new THREE.MeshPhysicalMaterial({color: 0xa89e8a, roughness: .55, transmission: .3, thickness: .02, side: THREE.DoubleSide,
    transparent: true, opacity: .8, bumpMap: bump, bumpScale: 1.5});
  const eyeMat = gloss(0xd8dccc);
  let rs = 11; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
  const root = new THREE.Group();
  const pelvis = G(root, [0, .95, 0]); add(S(.11, 1.1, .7, .8, .006, 9), ash, pelvis);
  const legs = [-1, 1].map(sd => {
    const th = G(pelvis, [sd * .09, -.02, 0]); add(Cp(.045, .4, .005, 9), ash, th, [0, -.24, 0]);
    const sh = G(th, [0, -.48, 0]); add(S(.05, 1, 1, 1, .004, 10), ash, sh); add(Cp(.035, .42, .004, 10), ash, sh, [0, -.24, 0]);
    const ft = G(sh, [0, -.47, 0]); add(S(.05, .9, .5, 2.4, .004, 10), ash, ft, [0, 0, .08]);
    for (const k of [-1, 0, 1]) add(new THREE.ConeGeometry(.012, .08, 8).rotateX(Math.PI / 2), nail, ft, [k * .025, -.01, .21]);
    return {th, sh, ft};
  });
  const spine = G(pelvis, [0, .05, 0]);
  add(Cp(.1, .42, .006, 9).scale(1.05, 1, .7), ash, spine, [0, .28, 0]);
  for (let i = 0; i < 6; i++) add(lump(new THREE.TorusGeometry(.098 - i * .003, .006, 8, 30, Math.PI * .9).rotateX(Math.PI / 2).rotateZ(Math.PI * .05), .002, 14).scale(1.08, 1, .74), ashD, spine, [0, .3 + i * .045, .012]);
  for (let i = 0; i < 7; i++) add(S(.02, 1, .8, 1, .002, 14), ashD, spine, [0, .12 + i * .07, -.075]);
  add(S(.05, 1.2, .9, 1, .004, 10), ash, spine, [0, .52, 0]);
  add(S(.035, 1, 1.2, .8, .004, 10), clay(0x4a3a2a), pelvis, [.12, -.06, .05]);                 // coin pouch
  const neck = G(spine, [0, .62, 0]); add(Cp(.035, .16, .004, 10), ash, neck, [0, .1, 0]);
  const head = G(neck, [0, .22, .03]);
  add(S(.12, .92, 1.25, 1.0, .006, 9), ash, head, [0, .02, 0]);
  for (const x of [-.045, .045]) { add(S(.028, 1.2, .8, .5, .003, 12), ashD, head, [x, .07, .1]); add(new THREE.SphereGeometry(.009, 10, 8), eyeMat, head, [x, .07, .112]); }
  const mouth = G(head, [0, -.05, .085]); mouth.scale.setScalar(1.25);
  add(S(.1, 1, .42, .35, .003, 12), mouthIn, mouth, [0, 0, .005]);
  add(lump(new THREE.TorusGeometry(.1, .016, 10, 40), .003, 12).scale(1, .45, 1), gum, mouth, [0, 0, .012]);
  for (const row of [1, -1]) for (let i = 0; i < 17; i++) {
    const a = (i / 16 - .5) * 2.5, x = Math.sin(a) * .095, z = Math.cos(a) * .03 - .01, h = .014 + rnd() * .014, w = .009 + rnd() * .006;
    const tg = new THREE.BoxGeometry(w, h, .008, 2, 3, 1); tg.translate(0, -row * h / 2, 0);
    add(tg, T[Math.floor(rnd() * 4)], mouth, [x, row * .03 + (rnd() - .5) * .004, z + .014], [(rnd() - .5) * .3, -a * .9, (rnd() - .5) * .35]);
  }
  if (opt.crown !== false) for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2;
    add(new THREE.ConeGeometry(.012, .04 + rnd() * .02, 6), T[i % 4], head, [Math.sin(a) * .085, .16, Math.cos(a) * .075 - .01], [Math.cos(a) * .3, 0, -Math.sin(a) * .3]); }
  const arms = [-1, 1].map(sd => { const up = G(spine, [sd * .12, .5, 0]); return Object.assign(fairyArm(up, ash, nail), {sd}); });
  function wing(sd) {
    const sh = new THREE.Shape(); sh.moveTo(0, 0); const pts = [];
    for (let i = 0; i <= 14; i++) { const a = i / 14 * Math.PI * .95, r = (.75 + rnd() * .15) * (1 - .35 * Math.sin(a * 2));
      pts.push([Math.sin(a) * r * .9 + (rnd() - .5) * .05, Math.cos(a) * r * .8 - .25 + (rnd() - .5) * .05]);
      if (i % 3 === 1) pts.push([Math.sin(a) * r * .62, Math.cos(a) * r * .55 - .25]); }
    for (const [x, y] of pts) sh.lineTo(x, y); sh.lineTo(0, 0);
    for (let h = 0; h < 4; h++) { const hole = new THREE.Path(), rr = .03 + rnd() * .05; hole.absellipse(.2 + rnd() * .35, -.3 + rnd() * .4, rr, rr * .7, 0, Math.PI * 2, false, rnd()); sh.holes.push(hole); }
    const g = new THREE.ShapeGeometry(sh, 24), pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) pos.setZ(i, Math.sin(pos.getX(i) * 7) * .03 + Math.sin(pos.getY(i) * 9) * .02 - pos.getX(i) * pos.getX(i) * .25);
    g.computeVertexNormals(); g.scale(sd, 1, 1);
    const m = new THREE.Mesh(g, wingMat); m.castShadow = true; return m;
  }
  const wings = opt.wings === false ? [] : [-1, 1].map(sd => { const w = G(spine, [sd * .06, .5, -.08]); w.rotation.set(-.2, sd * .6, sd * -.35); w.scale.setScalar(.6); w.add(wing(sd)); return w; });
  return {root, pelvis, spine, neck, head, mouth, arms, legs, wings};
}
export function fairyArm(up, ash, nail) {             // shoulder group in; long arm, hand, four fingers with four joints each
  add(S(.045, 1, 1, 1, .004, 10), ash, up); add(Cp(.03, .36, .004, 10), ash, up, [0, -.2, 0]);
  const fo = G(up, [0, -.4, 0]); add(S(.035, 1, 1, 1, .003), ash, fo); add(Cp(.026, .36, .004, 10), ash, fo, [0, -.2, 0]);
  const hd = G(fo, [0, -.4, 0]); add(S(.035, 1.1, .9, .5, .003), ash, hd, [0, -.02, 0]);
  const fingers = [];
  for (let k = 0; k < 4; k++) {
    let p = G(hd, [(k - 1.5) * .018, -.045, 0]); p.rotation.z = (k - 1.5) * .12; const chain = [p];
    for (let j = 0; j < 4; j++) { add(Cp(.007, .055, .001, 20), ash, p, [0, -.035, 0]); p = G(p, [0, -.07, 0]); chain.push(p); }
    add(new THREE.ConeGeometry(.007, .035, 6).rotateX(Math.PI), nail, p, [0, -.012, 0]);
    fingers.push(chain);
  }
  return {up, fo, hd, fingers};
}
export const curl = (arm, k, wave = 0, t = 0) => arm.fingers.forEach((ch, i) => ch.forEach((q, j) => { if (j) q.rotation.x = k + wave * Math.sin(t * 4 + i * .7 + j * .4); }));
