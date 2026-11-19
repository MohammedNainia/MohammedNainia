// Clay Haru v2, built to match YTB/channel_art/haru_turnaround_sheet.png and haru_expressions_sheet.png:
// big round head (about 4.5 heads tall), helmet hair with a swept fringe and long panels in front of the shoulders,
// oversized mustard hoodie (rolled hood, drawstrings, pocket, puffy sleeves, cuffs), straight grey trousers, white sneakers,
// and a clay face with interchangeable pieces (eyes, brows, mouths, tears, sweat).
import {THREE} from './lib.js';
import {clay, gloss, lump, add, S, Cp, G} from './clay.js';

const tube = (pts, r, seg = 24) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p))), seg, r, 8, false);
const capTube = (pts, r, mat, parent) => {           // a tube with rounded ends
  const g = G(parent); add(tube(pts, r), mat, g);
  for (const p of [pts[0], pts[pts.length - 1]]) add(new THREE.SphereGeometry(r, 10, 8), mat, g, p);
  return g;
};

export function makeHaru2(o = {}) {
  const M = {
    skin: clay(o.skin || 0xe39a72, {bumpScale: .25, roughness: .7, sheen: .5}),
    hood: clay(o.hood || 0xcf9132, {bumpScale: .9, roughness: .85}),
    hoodD: clay(0xc08a2c, {bumpScale: .6}),
    pants: clay(o.pants || 0x5c5b60, {bumpScale: .8}),
    shoe: clay(0xf2f0ec, {bumpScale: .3}), sole: clay(0xd8d6d0, {bumpScale: .2}),
    hair: clay(o.hair || 0x26262b, {bumpScale: .5, roughness: .6, sheen: .6}),
    eye: gloss(0x0a0a0c), white: gloss(0xf6f4ee), dark: clay(0x2a1a16, {bumpScale: 0}), nose: clay(0xd98a62, {bumpScale: .2}),
    mouthIn: clay(0x4a1418, {bumpScale: 0}), tongue: clay(0xd06a70, {bumpScale: .2}), teeth: gloss(0xfaf6ee),
    tear: new THREE.MeshPhysicalMaterial({color: 0xcfe8ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .75}),
    sweat: new THREE.MeshPhysicalMaterial({color: 0x9fd0ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .85}),
  };
  const root = new THREE.Group(); root.scale.setScalar(o.scale || 1);
  // ---- legs (straight trousers), shoes; hips at .64
  const hips = G(root, [0, .55, 0]);
  add(S(.15, 1.05, .45, .72, .003, 9), M.pants, hips, [0, .02, 0]);
  const legs = [-1, 1].map(sd => {
    const th = G(hips, [sd * .072, 0, 0]);
    add(Cp(.07, .17, .003, 10), M.pants, th, [0, -.12, 0]);
    const sh = G(th, [0, -.25, 0]);
    add(S(.069, 1, 1, 1, .002, 12), M.pants, sh);                                      // knee: same radius, no ring
    add(Cp(.069, .16, .003, 10), M.pants, sh, [0, -.11, 0]);
    add(lump(new THREE.CylinderGeometry(.073, .076, .045, 20), .002, 12), M.pants, sh, [0, -.215, 0]);   // hem
    const ft = G(sh, [0, -.235, 0]);
    add(S(.062, 1, .62, 1.75, .002, 12), M.shoe, ft, [0, -.012, .03]);
    add(lump(new THREE.CylinderGeometry(.064, .064, .016, 24).scale(1, 1, 1.75), .001, 14), M.sole, ft, [0, -.044, .03]);
    for (let i = 0; i < 3; i++) add(Cp(.004, .03, .0005, 30), M.sole, ft, [0, .012 - i * .002, .06 + i * .016], [0, 0, PI2]);
    return {th, sh, ft};
  });
  // ---- torso: oversized hoodie
  const chest = G(hips, [0, .04, 0]);
  add(Cp(.165, .22, .004, 9).scale(1.02, 1, .8), M.hood, chest, [0, .15, 0]);          // a little baggy
  add(lump(new THREE.TorusGeometry(.138, .03, 10, 32).scale(1.0, .8, 1).rotateX(PI2), .002, 12), M.hood, chest, [0, -.07, 0]);   // hem band, flush
  const pocket = G(chest, [0, .03, .124]);
  add(Cp(.05, .14, .002, 14).rotateZ(PI2).scale(1, 1, .3), M.hood, pocket);
  add(Cp(.004, .2, .0005, 30).rotateZ(PI2), M.hoodD, pocket, [0, .045, .014]);
  // the hood: a thick roll round the neck, a lump down the back, drawstrings
  add(lump(new THREE.TorusGeometry(.082, .046, 14, 30).rotateX(PI2), .003, 10), M.hood, chest, [0, .42, -.005]);
  add(S(.085, 1.1, .6, .45, .003, 10), M.hood, chest, [0, .33, -.1]);
  for (const x of [-.035, .035]) {
    capTube([[x, .4, .1], [x * 1.1, .33, .115], [x * 1.05, .27, .11]], .007, M.hood, chest);
  }
  const neck = G(chest, [0, .44, 0]);
  add(Cp(.045, .04, .002, 14), M.skin, neck, [0, .03, 0]);
  // ---- head
  const head = G(neck, [0, .19, 0]); head.scale.setScalar(1.16);
  add(S(.135, 1, 1.06, .96, .002, 10), M.skin, head);
  // hair: helmet, swept fringe, long panels in front of the shoulders, the back
  add(S(.152, 1.03, 1.05, 1.0, .003, 9), M.hair, head, [0, .028, -.036]);
  const fringe = add(S(.152, 1.03, .52, .97, .003, 9), M.hair, head, [-.006, .088, .014], [.4, 0, -.14]);
  for (const sd of [-1, 1]) {
    const p = G(head, [sd * .118, -.02, -.01]); p.rotation.z = sd * .06;
    add(Cp(.05, .3, .003, 10).scale(1, 1, .62), M.hair, p, [0, -.13, 0]);
  }
  const back = G(head, [0, -.02, -.07]);
  add(Cp(.13, .2, .003, 9).scale(1.25, 1, .52), M.hair, back, [0, -.13, -.012]);
  // ---- face pieces
  const face = G(head, [0, -.018, .117]);
  const eyes = [], whites = [], lids = [], squeeze = [], brows = [];
  for (const sd of [-1, 1]) {
    const x = sd * .05;
    whites.push(add(S(.026, 1, 1.08, .4, .0005, 30), M.white, face, [x, .004, -.004]));
    eyes.push(add(new THREE.SphereGeometry(.0165, 16, 12), M.eye, face, [x, .002, .004]));
    lids.push(capTube([[x - .02, .0, .004], [x, -.006, .008], [x + .02, .0, .004]], .0035, M.dark, face));
    squeeze.push(capTube([[x - sd * .02, .012, .004], [x + sd * .016, .0, .008], [x - sd * .02, -.012, .004]], .0038, M.dark, face));
    const b = G(face, [x, .042, .0]); capTube([[-.024, -.002, 0], [0, .004, .004], [.024, -.002, 0]], .0042, M.dark, b); brows.push(b);
  }
  add(S(.016, 1, .9, .8, .001, 20), M.nose, face, [0, -.03, .014]);
  // mouths
  const mouth = G(face, [0, -.068, .006]);
  const mLine = capTube([[-.016, 0, 0], [.016, 0, 0]], .0028, M.dark, mouth);
  const mSmile = capTube([[-.024, .006, 0], [-.012, -.004, .003], [0, -.007, .004], [.012, -.004, .003], [.024, .006, 0]], .003, M.dark, mouth);
  const mSad = capTube([[-.022, -.006, 0], [0, .004, .004], [.022, -.006, 0]], .003, M.dark, mouth);
  const mWobble = capTube([...Array(9)].map((_, i) => [-.022 + i * .0055, (i % 2 ? .004 : -.003), .003]), .0028, M.dark, mouth);
  const mO = G(mouth); add(S(.011, 1, 1.15, .4, .0005, 30), M.mouthIn, mO);
  const mOpen = G(mouth, [0, -.006, 0]);
  add(S(.034, 1.1, .8, .4, .001, 20), M.mouthIn, mOpen);
  add(S(.02, 1.2, .5, .4, .001, 20), M.tongue, mOpen, [0, -.014, .006]);
  add(new THREE.BoxGeometry(.04, .009, .006), M.teeth, mOpen, [0, .017, .008]);
  const mouths = {line: mLine, smile: mSmile, sad: mSad, wobble: mWobble, o: mO, open: mOpen};
  // tears and a sweat drop
  const tears = G(face);
  for (const sd of [-1, 1]) for (let i = 0; i < 3; i++) add(S(.0065 - i * .001, 1, 1.4, .6, .0003, 40), M.tear, tears, [sd * .052, -.024 - i * .018, .006]);
  const sweat = G(head, [.105, .07, .07]); add(S(.014, 1, 1.5, .7, .0005, 40), M.sweat, sweat);
  // ---- arms: puffy sleeves, cuffs, hands
  const arms = [-1, 1].map(sd => {
    const up = G(chest, [sd * .19, .34, 0]);
    add(S(.068, 1, 1, 1, .003, 10), M.hood, up);
    add(Cp(.064, .13, .003, 10), M.hood, up, [0, -.1, 0]);
    const fo = G(up, [0, -.19, 0]);
    add(S(.063, 1, 1, 1, .003, 10), M.hood, fo);
    add(Cp(.062, .12, .003, 10), M.hood, fo, [0, -.1, 0]);
    add(lump(new THREE.TorusGeometry(.05, .022, 10, 24).rotateX(PI2), .002, 14), M.hood, fo, [0, -.2, 0]);   // cuff
    const hand = G(fo, [0, -.225, 0]);
    add(S(.04, .78, 1.12, .55, .002, 16), M.skin, hand, [0, -.03, 0]);
    for (let k = 0; k < 4; k++) add(Cp(.009, .02, .0005, 30), M.skin, hand, [-.018 + k * .012, -.068, .002]);
    add(Cp(.011, .025, .001, 24), M.skin, hand, [-sd * .03, -.02, .014], [0, 0, sd * .6]);
    return {up, fo, hand};
  });

  const P = {root, hips, chest, neck, head, back, face, arms, legs, M, fringe};
  P.eyes = s => {                                  // open | wide | closed | squeeze
    const open = s === 'open' || s === 'wide';
    eyes.forEach(e => { e.visible = open; e.scale.setScalar(s === 'wide' ? .9 : 1); });
    whites.forEach(w => w.visible = s === 'wide');
    lids.forEach(l => l.visible = s === 'closed'); squeeze.forEach(l => l.visible = s === 'squeeze');
  };
  P.brows = (k, lift = 0) => brows.forEach((b, i) => { const sd = i ? 1 : -1; b.rotation.z = -sd * k * .45; b.position.y = .042 + lift * .01 + Math.abs(k) * .003; });
  P.mouth = s => { for (const [k, m] of Object.entries(mouths)) m.visible = k === s; };
  P.tears = on => tears.visible = on; P.sweat = on => sweat.visible = on;
  P.expr = name => {                                // the 8 faces from the expression sheet
    P.tears(false); P.sweat(false);
    const E = {neutral: ['open', 0, 0, 'line'], nervous: ['open', .5, .2, 'wobble'], curious: ['open', .25, .4, 'sad'],
      smile: ['open', -.1, .2, 'smile'], scared: ['wide', .5, 1, 'sad'], scream: ['squeeze', -.6, -.2, 'open'],
      cry: ['open', .8, .1, 'wobble'], whisper: ['open', .35, .3, 'o']}[name] || ['open', 0, 0, 'line'];
    P.eyes(E[0]); P.brows(E[1], E[2]); P.mouth(E[3]);
    if (name === 'nervous') P.sweat(true);
    if (name === 'cry') P.tears(true);
    if (name === 'curious') { brows[0].rotation.z = .1; brows[1].rotation.z = .45; brows[1].position.y += .008; }
  };
  P.expr('neutral');
  P.arms.forEach(({up}, i) => up.rotation.z = (i ? 1 : -1) * .1);
  return P;
}
const PI2 = Math.PI / 2;
