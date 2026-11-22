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
// The clay shader. Two things the plain material can't do:
// 1. fingerprints and smudges placed by position on the piece (triplanar), not by its UVs: the same size everywhere, never stretched,
//    and they stay put on the puppet as it moves.  2. colour from the piece itself (attribute clayShade, made once in lump()):
//    a slight mottling, and darker clay pressed into the creases. Pieces without the attribute read 0 = unchanged.
// ?flat=1 on the page turns both off (to compare, or for a quick test render).
export const CLAY_FX = !/[?&]flat=1/.test(typeof location !== 'undefined' ? location.search : '');
const PRINT = 7.5;                                                                   // fingerprint marks per metre of clay
function clayShader(m) {
  if (!CLAY_FX) return m;
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float clayShade; varying float vClayShade; varying vec3 vClayPos; varying vec3 vClayNrm;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvClayPos = transformed; vClayNrm = objectNormal; vClayShade = clayShade;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vClayShade; varying vec3 vClayPos; varying vec3 vClayNrm;')
      .replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb *= 1.0 + vClayShade;')
      .replace('#include <bumpmap_pars_fragment>', THREE.ShaderChunk.bumpmap_pars_fragment.replace(/vec2 dHdxy_fwd\(\) \{[\s\S]*?return vec2\( dBx, dBy \);\s*\}/, `
        float clayH(vec3 p) { vec3 w = pow(abs(normalize(vClayNrm)), vec3(4.0)); w /= (w.x + w.y + w.z + 1e-5); p *= ${PRINT.toFixed(2)};
          return w.x * texture2D(bumpMap, p.yz).x + w.y * texture2D(bumpMap, p.zx + .37).x + w.z * texture2D(bumpMap, p.xy + .71).x; }
        vec2 dHdxy_fwd() { float H = 1.8 * bumpScale * clayH(vClayPos);
          return vec2(1.8 * bumpScale * clayH(vClayPos + dFdx(vClayPos)) - H, 1.8 * bumpScale * clayH(vClayPos + dFdy(vClayPos)) - H); }`));
  };
  m.customProgramCacheKey = () => 'clay-fx-1';
  return m;
}
export const clay = (c, o = {}) => clayShader(new THREE.MeshPhysicalMaterial(Object.assign({color: c, roughness: .9, metalness: 0, sheen: .35, sheenRoughness: .9,
  sheenColor: new THREE.Color(c).lerp(new THREE.Color(0xffffff), .35), bumpMap: bump, bumpScale: 1.0}, o)));
export const gloss = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, roughness: .25, clearcoat: .8, bumpMap: bump, bumpScale: .2}, o));

// ---------------------------------------------------------------- lumpy geometry + boil
const lumpy = [];
let pieceSeed = 1;
function shadePiece(geo) {                         // mottling + darker creases, once per piece (no cost per frame)
  const p = geo.attributes.position, n = geo.attributes.normal, N = p.count, cav = new Float32Array(N), cnt = new Float32Array(N), shade = new Float32Array(N);
  const idx = geo.index, sd = (pieceSeed = (pieceSeed * 16807) % 2147483647) % 1000;
  if (idx && n) { const a = idx.array;
    for (let t = 0; t < a.length; t += 3) for (let k = 0; k < 3; k++) { const i = a[t + k];
      for (const j of [a[t + (k + 1) % 3], a[t + (k + 2) % 3]]) { const dx = p.getX(j) - p.getX(i), dy = p.getY(j) - p.getY(i), dz = p.getZ(j) - p.getZ(i), L = Math.hypot(dx, dy, dz) || 1;
        cav[i] += (dx * n.getX(i) + dy * n.getY(i) + dz * n.getZ(i)) / L; cnt[i]++; } } }
  for (let i = 0; i < N; i++) { const c = cnt[i] ? cav[i] / cnt[i] : 0, x = p.getX(i) * 9, y = p.getY(i) * 9, z = p.getZ(i) * 9;
    shade[i] = -Math.min(.38, Math.max(0, c * 7)) + .09 * noise(x * .6, y * .6, z * .6, sd) + .035 * noise(x * 3, y * 3, z * 3, sd + 3); }
  geo.setAttribute('clayShade', new THREE.BufferAttribute(shade, 1));
}
export function lump(geo, amt = .004, freq = 10) { const e = {geo, base: null, nrm: null, amt, freq}; lumpy.push(e); if (CLAY_FX) shadePiece(geo); return geo; }
const noise = (x, y, z, sd) => Math.sin(x * 1.7 + sd) * Math.sin(y * 2.3 + sd * 1.3) * Math.sin(z * 1.9 + sd * .7)
  + .5 * Math.sin(x * 3.1 - sd * .9 + y * 1.2) * Math.sin(z * 2.7 + sd * 1.1);
let lastSeed = null;
export function boil(sd) {                       // shift every lump; only when the seed changes (every other stop-motion frame)
  if (SAMPLING || sd === lastSeed) return; lastSeed = sd;
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
let fs = 11; const frnd = () => (fs = (fs * 16807) % 2147483647) / 2147483647;
export const fold = (r, t, a = .002) => lump(new THREE.TorusGeometry(r, t * (.8 + .5 * frnd()), 8, 20, Math.PI * (1.15 + .6 * frnd())).rotateZ(frnd() * 6.28).scale(1, 1, .8 + .4 * frnd()), a, 16);   // bunched cloth: a broken, uneven ring
// a turned shape: a side profile [[radius, y], ...] spun round the y axis, smoothed through a curve: one continuous sculpted surface
export const turn = (pts, a = .006, f = 6, phiStart = Math.PI, phiLen = Math.PI * 2, seg = 36) => {   // a full turn closes at the back, never on the face
  if (pts[0][1] > pts[pts.length - 1][1]) pts = pts.slice().reverse();                 // bottom to top, so the surface faces out
  const c = new THREE.SplineCurve(pts.map(([r, y]) => new THREE.Vector2(r, y))).getPoints(pts.length * 6);
  const g = new THREE.LatheGeometry(c, seg, phiStart, phiLen), uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 4, uv.getY(i) * 3);   // smaller fingerprint marks
  return lump(g, a, f); };
// sculptHead(geo, k): jaw tapering to a chin, cheekbones, eye sockets under a soft brow, a fuller back of the skull, a sloping forehead.
// k scales how strong (0 = the plain egg). Works on the head's own coordinates (about 0.2 m tall, face towards +z).
export function sculptHead(geo, k = 1) {
  const p = geo.attributes.position, sm = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const g = (x, y, z, cx, cy, cz, r) => Math.exp(-((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) / (r * r));
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i); const ax = Math.abs(x), sx = Math.sign(x) || 1;
    const low = sm(.0, -.1, y), front = Math.min(1, Math.max(0, z / .1));
    if (z > .035) z = .035 + (z - .035) * (1 - .3 * k);                             // a flatter face plane (a face is flatter than an egg)
    x *= 1 - .42 * k * low * (.3 + .7 * front);                                   // the lower face narrows into a V: jaw to chin
    z += .005 * k * low * low * front; y -= .006 * k * low * front;                   // the chin comes forward a little
    x += sx * .005 * k * g(ax, y, z, .075, -.06, .0, .03);                            // the corner of the jaw, below the ear
    if (z < 0) z -= .012 * k * Math.min(1, -z / .1) * sm(-.05, .05, y);               // the back of the skull, behind the neck
    if (y > .03 && z > 0) z -= .012 * k * sm(.03, .1, y) * front;                     // the forehead slopes back
    let d = .007 * g(ax, y, z, .062, -.016, .062, .026)                               // cheekbones
          - .0065 * g(ax, y, z, .034, -.012, .094, .017)                              // eye sockets
          + .0035 * g(ax, y, z, .036, .013, .09, .02)                                 // a soft brow ridge
          + .006 * g(ax, y, z, 0, -.1, .06, .022);                                    // the chin
    const L = Math.hypot(x, y, z) || 1; d *= k; p.setXYZ(i, x + x / L * d, y + y / L * d, z + z / L * d);
  }
  geo.computeVertexNormals(); return geo;
}
export const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); parent.add(g); return g; };

// ---------------------------------------------------------------- a person (Haru or Mum): ~7 heads tall, joints, face controls
export function makePerson(o = {}) {
  const M = {skin: clay(o.skin || 0xefc09c, {bumpScale: .35}), top: clay(o.top || 0xe0a33a, {bumpScale: 1.2}), pants: clay(o.pants || 0x5a5862, {bumpScale: 1.2}),
    shoe: clay(o.shoe || 0xf2eee6), hair: clay(o.hair || 0x24222a, {bumpScale: .8}), eye: gloss(0x0c0c0e), white: gloss(0xf4f0e8),
    mouth: clay(0x2a0c10, {bumpScale: 0}), gum: clay(0xd86a78, {bumpScale: .2}), tooth: gloss(0xfaf6ee),
    blush: clay(0xd89080, {bumpScale: 0, transparent: true, opacity: .22}), sole: clay(0x3a3532, {bumpScale: .6}), lace: clay(0xd8d2c8, {bumpScale: 0}),
    shine: new THREE.MeshBasicMaterial({color: 0xffffff}), tear: gloss(0xa8d0f0, {transparent: true, opacity: .85}), lip: clay(new THREE.Color(o.skin || 0xefc09c).lerp(new THREE.Color(0xb86a5e), .45).getHex(), {bumpScale: .1})};
  M.crease = clay(new THREE.Color(o.skin || 0xefc09c).multiplyScalar(.66).getHex(), {bumpScale: .2});   // age lines: the skin pressed in
  const root = new THREE.Group(); root.scale.setScalar(o.scale || 1);
  const sec = {hair: null, hood: null, strings: []};                                          // the loose parts that swing behind the body (follow-through)
  // body build (child | woman | man | old) and outfit (hoodie | sweater | cardigan | shirt | coat | dress): every character, not only Haru
  const b = BUILDS[o.build || ((o.headScale || 1) >= 1.1 ? 'child' : 'woman')] || BUILDS.child;
  const outfit = o.outfit || (o.hood !== false ? 'hoodie' : 'sweater');
  const hips = G(root, [0, .82, 0]);
  add(S(.125 * b.hip, 1.05, .62, .72, .004), M.pants, hips, [0, .02, 0]);
  const chest = G(hips, [0, .06, 0]);
  const TORSO = {hoodie: [[0, -.105], [.11, -.1], [.146, -.088], [.152, -.066], [.147, -.048], [.157, -.02], [.16, .05], [.157, .15], [.156, .25], [.166, .34], [.168, .395], [.14, .44], [.09, .485], [.05, .515]],
    fitted: [[0, -.105], [.118, -.1], [.14, -.085], [.143, -.055], [.145, 0], [.148, .1], [.152, .25], [.155, .32], [.15, .37], [.13, .42], [.095, .462], [.06, .492], [.045, .505]]};   // sloping adult shoulders
  const torso = turn(outfit === 'hoodie' ? TORSO.hoodie : TORSO.fitted, .007, 5).scale(1.14 * b.sh, 1, .78 * b.chest);
  if (b.belly || b.bust) { const p = torso.attributes.position;                        // tummy and chest sculpted into the body itself (no stuck-on pieces)
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); if (z <= 0) continue; const f = Math.min(1, z / .1);
      const dz = b.belly * 1.6 * Math.exp(-(((y - .08) / .11) ** 2) - (x / .13) ** 2) + b.bust * .018 * Math.exp(-(((y - .3) / .06) ** 2)) * (Math.exp(-(((Math.abs(x) - .055) / .04) ** 2)));
      p.setZ(i, z + dz * f); }
    torso.computeVertexNormals(); }
  add(torso, M.top, chest);                                                                                                  // the top: one sculpted body
  const front = .16 * .78 * b.chest;                                                                                         // the front of the top
  if (outfit === 'hoodie' && o.pocket !== false) { add(S(.06, 1.75, .95, .3, .004, 8), M.top, chest, [0, .06, .118], [-.12, 0, 0]); add(Cp(.007, .17, .001, 20), M.top, chest, [0, .112, .128], [0, 0, Math.PI / 2]); }   // the kangaroo pouch and its opening
  if (outfit !== 'hoodie') {
    add(lump(new THREE.TorusGeometry(.13 * b.sh, .016, 8, 28), .002, 14).scale(1.12, .8 * b.chest / .78 * .78, 1), M.top, chest, [0, -.09, 0], [Math.PI / 2, 0, 0]);   // a ribbed hem band
    add(lump(new THREE.TorusGeometry(.048, .013, 8, 22), .002, 14), M.top, chest, [0, .5, 0], [Math.PI / 2, 0, 0]); }               // a round collar
  const dark = clay(new THREE.Color(o.top || 0xe0a33a).multiplyScalar(.6).getHex());
  if (outfit === 'cardigan' || outfit === 'shirt' || outfit === 'coat') {
    for (let k = 0; k < (outfit === 'coat' ? 4 : 5); k++) add(S(.008, 1, 1, .5, .0005, 24), outfit === 'shirt' ? M.lace : dark, chest, [outfit === 'shirt' ? 0 : .012, .1 + k * .07, front + .004]);   // buttons
    if (outfit === 'cardigan') { add(S(.026, 1, 3.2, .22, .001, 14), clay(o.under || 0xe8e2d6), chest, [0, .39, front - .002], [.12, 0, 0]);   // the blouse at the V of the neck
      for (const x of [-1, 1]) add(Cp(.009, .2, .001, 20), M.top, chest, [x * .022, .38, front + .002], [.1, 0, x * .2]); }   // the cardigan's front edges
    if (outfit === 'shirt' || outfit === 'coat') for (const x of [-1, 1]) add(S(.034, 1.1, .5, .3, .002, 12), outfit === 'coat' ? M.top : M.lace, chest, [x * .03, .47, .07], [-.5, x * .5, x * .5]);   // collar points / lapels
  }
  if (outfit === 'coat') add(turn([[.17 * b.hip, .02], [.19 * b.hip, -.12], [.215 * b.hip, -.42], [.205 * b.hip, -.46], [.18 * b.hip, -.45]], .007, 5).scale(1.05, 1, .8), M.top, hips);   // the coat's skirt, to the knee
  if (outfit === 'dress') add(turn([[.13 * b.hip, .06], [.15 * b.hip, -.06], [.22 * b.hip, -.4], [.235 * b.hip, -.47], [.2 * b.hip, -.46]], .007, 5).scale(1.05, 1, .85), M.top, hips);   // a dress, to below the knee                 // the kangaroo pocket: a flat panel                          // the kangaroo pocket
  if (o.hood !== false) { add(lump(new THREE.TorusGeometry(.074, .05, 12, 24).scale(1.18, 1, .95), .007, 6), M.top, chest, [0, .485, -.014], [Math.PI / 2 + .38, 0, 0]);   // the hood: soft, bunched, low at the front
    sec.hood = G(chest, [0, .49, -.07]); add(S(.095, 1.1, .7, .45, .008, 5), M.top, sec.hood, [0, -.065, -.025], [.5, 0, 0]);   // the hood hanging down the back (swings a little)
    for (const x of [-1, 1]) add(S(.04, 1.2, .8, .9, .005, 7), M.top, chest, [x * .062, .455, .045], [0, 0, x * .4]);       // loose folds either side of the opening
    for (const x of [-.028, .028]) { const g = G(chest, [x, .425, .128]); sec.strings.push(g);                              // drawstrings hang from the hood and swing
      add(Cp(.005, .09, .0008, 24), M.lace, g, [0, -.045, .002]); add(S(.008, 1, 1.4, 1, .0008, 24), M.lace, g, [0, -.1, .006]); } }
  const neck = G(chest, [0, .49, 0]);
  add(Cp(.038, .07, .002, 16), M.skin, neck, [0, .035, 0]);
  const head = G(neck, [0, o.neckLen ?? .155, 0]); head.scale.setScalar(o.headScale || 1);
  const skull = sculptHead(turn([[0, -.113], [.05, -.106], [.075, -.09], [.09, -.065], [.098, -.035], [.1, 0], [.098, .035], [.086, .07], [.052, .1], [0, .113]], .003, 12, Math.PI, Math.PI * 2, 48).scale(...(o.faceShape || [.92, 1.06, 1.05])), o.sculpt ?? 1); add(skull, M.skin, head);   // the head: one sculpted egg, full in the cheeks and jaw
  for (const x of [-.091, .091]) { add(S(.021, .5, 1, .78, .001, 20), M.skin, head, [x, -.022, -.012], [0, Math.sign(x) * .35, 0]);   // ears, eye-to-nose height
    add(lump(new THREE.TorusGeometry(.011, .003, 6, 14, Math.PI * 1.3), .0005, 30), M.crease, head, [x * 1.07, -.02, -.008], [0, Math.sign(x) * (Math.PI / 2 - .35), Math.PI * .3]); }
  // the hair cap: a slightly larger copy of the sculpted skull, cut along a hairline (swept to one side, like the sheet's fringe),
  // so it always sits snug on whatever head shape the sculpt makes
  { const cap = skull.clone(), p = cap.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i), front = Math.min(1, Math.max(0, z / .075));
      const h = z < -.01 ? 1 : y - ((o.hairline ?? .056) - .05 * (1 - front) + .016 * x / .09 - .01 * Math.max(0, -x / .09) * front);   // > 0 above the hairline
      const t = Math.min(1, Math.max(0, (h + .004) / .012)), k = .86 + .21 * t * t * (3 - 2 * t);                   // below it the hair thins into the skin: a smooth edge
      p.setXYZ(i, x * k, y * (k - .025 * t) + .002 * t, z * k - .002 * t); }
    cap.computeVertexNormals();
    const hm = M.hair.clone(); hm.side = THREE.DoubleSide; add(lump(cap, .004, 8), hm, head);
    if (o.hairTop) add(S(.107, 1.03, .52, 1.0, .004, 8), M.hair, head, [.012, .074, -.006], [.22, 0, -.22]); }   // the fringe swept across the forehead, lower on one side   // a fuller, rounded top (the sheet's hair volume)
  const back = G(head, [0, -.02, -.07]);
  if (o.longHair !== false) {
    sec.hair = G(head, [0, .06, -.012]);
    const curtain = add(turn([[.09, .09], [.11, .055], [.12, 0], [.124, -.08], [.133, -.16], [.152, -.225], [.16, -.26], [.148, -.29], [.124, -.288], [.11, -.2], [.1, -.08], [.096, .02], [.085, .07]],
      .004, 7, o.hairGap ?? 1.3, Math.PI * 2 - 2 * (o.hairGap ?? 1.3), 40), M.hair, sec.hair, [0, -.06, 0]); curtain.scale.set(o.hairThick || 1, 1, o.hairThick ? 1.04 : .95);           // rests on the shoulders, wider at the ends
    for (const a of [o.hairGap ?? 1.3, -(o.hairGap ?? 1.3)]) {                                                                                     // the two locks framing the face (they close the curtain's edges)
      const lock = G(sec.hair, [Math.sin(a) * .112 * (o.hairThick || 1), -.06, Math.cos(a) * .112 * .95]);
      add(turn([[0, .06], [.017, .04], [.022, -.02], [.024, -.11], [.024, -.17], [.016, -.205], [0, -.21]], .002, 10), M.hair, lock, [0, 0, 0], [0, a, -Math.sign(a) * .05]); }
  }
  if (o.bun) add(S(.055, 1, 1, 1, .003), M.hair, head, [0, .04, -.11]);
  // face
  const faceLight = new THREE.PointLight(o.faceColor || 0xffe6d0, o.faceLight ?? .35, .9, 1.6); faceLight.position.set(0, .03, .55); head.add(faceLight);
  const sk = o.sculpt ?? 1, fz = (o.faceShape || [.92, 1.06, 1.05])[2];
  const face = G(head, [0, -.012, .035 + (.1 * fz - .035) * (1 - .3 * sk) - .005 * sk]);   // the features sit on the sculpted face, however strong the sculpt
  const eyes = [], whites = [], lids = [], brows = [], caps = [];
  for (const x of [-.034, .034]) {
    const es = (o.eyeSize || .0098) / .0098;                                         // eye size relative to the default
    whites.push(add(S(.017 * es, 1.15, 1, .35, .001, 20), M.white, face, [x, 0, -.002]));
    const e = add(new THREE.SphereGeometry(.0098 * es, 14, 10), M.eye, face, [x, 0, .004 * es]); eyes.push(e);
    add(new THREE.SphereGeometry(.0028 * es, 8, 6), M.shine, e, [.0035 * es, .0042 * es, .0085 * es]).castShadow = false;                  // the catchlight: the eyes look wet and alive
    if (o.blush !== false) add(S(.012, 1.3, .75, .25, .0005, 20), M.blush, face, [x * 1.55, -.033, .003]).castShadow = false;
    lids.push(add(Cp(.0035, .022, .0005, 30), M.hair, face, [x, -.002, .006], [0, 0, Math.PI / 2]));
    const cap = add(new THREE.SphereGeometry(.0128 * es, 20, 10, 0, Math.PI * 2, 0, Math.PI * .5), M.skin, face, [x, .0005, .004 * es]); cap.castShadow = false; caps.push(cap);   // the upper eyelid
    if (o.eyeLines !== false) add(new THREE.TorusGeometry(.0125, .0016, 5, 14, Math.PI * .5), M.crease, face, [x, -.001, .0015], [0, 0, -Math.PI * .75]).castShadow = false;   // a soft line under the eye
    const br = new THREE.Group(); br.position.set(x, .031, .001); face.add(br);                                        // an arched brow, thick in the middle
    if (o.brow === 'dash') add(Cp(.0062, .016, .0006, 24), M.hair, br, [0, -.004, 0], [0, 0, Math.PI / 2 + (x > 0 ? -.28 : .28)]);   // a thick short dash, tilted worried
    else add(new THREE.TorusGeometry(.017, .0058, 6, 16, Math.PI * .5).scale(1, .75, 1), M.hair, br, [0, -.012, 0], [0, 0, Math.PI * .25]);
    brows.push(br);
    if ((o.age || 0) > .4) { add(new THREE.TorusGeometry(.015, .0018, 5, 14, Math.PI * .5), M.crease, face, [x, -.006, 0], [0, 0, -Math.PI * .75]);   // bags under the eyes
      add(Cp(.0016, .028, .0003, 30), M.crease, face, [x * 1.05, -.05, -.004], [0, 0, (x > 0 ? 1 : -1) * .55]); }            // the lines from nose to mouth
  }
  if (o.nose === 'button') add(S(.0092, 1.0, .95, .95, .001, 18), M.skin, face, [0, -.03, .006]);              // a small round button nose
  else { add(S(.0115, .95, .85, 1.15, .001, 18), M.skin, face, [0, -.033, .01]); add(Cp(.0058, .012, .0008, 24), M.skin, face, [0, -.02, .003], [-.35, 0, 0]); }   // nose: a rounded tip and a soft bridge
  if ((o.age || 0) > .6) for (const y of [.058, .07]) add(Cp(.0015, .045, .0003, 30), M.crease, face, [0, y, -.008], [0, 0, Math.PI / 2]);   // forehead lines
  const mouth = G(face, [0, -.06, -.003]);
  const mLine = add(new THREE.TorusGeometry(.013, .0034, 6, 18, Math.PI * .6).rotateZ(Math.PI * .2), M.mouth, mouth, [0, 0, .004]);   // the curve centred on its top, so it flattens evenly mLine.castShadow = false;   // the mouth: a curved line
  const lowLip = add(S(.0085, 1.45, .45, .35, .0008, 20), M.lip, mouth, [0, -.0075, 0]); lowLip.castShadow = false;                 // and a soft lower lip
  const mOpen = G(mouth);
  add(S(.016, 1.25, 1, .35, .001, 20), M.mouth, mOpen);
  const gums = [add(Cp(.004, .02, .0005, 30), M.gum, mOpen, [0, .012, .004], [0, 0, Math.PI / 2]), add(Cp(.004, .02, .0005, 30), M.gum, mOpen, [0, -.012, .004], [0, 0, Math.PI / 2])];
  const teeth = [add(new THREE.BoxGeometry(.026, .006, .004), M.tooth, mOpen, [0, .0075, .005]), add(new THREE.BoxGeometry(.022, .005, .004), M.tooth, mOpen, [0, -.008, .005])];
  // arms and legs
  const arms = [-1, 1].map(sd => {                     // fitted tops: the arm hangs from a lower, sloping shoulder
    const up = G(chest, outfit === 'hoodie' ? [sd * .175 * b.sh, .44, 0] : [sd * .165 * b.sh, .405, 0]); const pf = (o.puffy || (outfit === 'hoodie' ? 1.1 : 1)) * b.limb; add(turn([[0, .035], [.04, .028], [.06 * pf, 0], [.066 * pf, -.06], [.064 * pf, -.16], [.056 * pf, -.25], [.05, -.29]], .006, 6), M.top, up);
    const fo = G(up, [0, -.27, 0]); add(turn([[.05, .035], [.054 * pf, -.02], [.06 * pf, -.1], [.066 * pf, -.16], [.064 * pf, -.2], [.048, -.222], [.03, -.226], [0, -.227]], .006, 6), M.top, fo); add(fold(.046, .013), M.top, fo, [0, .012, 0], [Math.PI / 2 + .3, 0, 0]);
    add(fold(.047, .011), M.top, fo, [0, -.03, 0], [Math.PI / 2 - .25, 0, 0]);
    add(fold(.052, .013), M.top, fo, [0, -.215, 0], [Math.PI / 2, 0, 0]);              // sleeve cuff
    const hand = G(fo, [0, -.25, 0]); add(S(.027, .85, 1.0, .5, .002, 18), M.skin, hand, [0, -.022, 0]);
    for (const fx of [-.012, 0, .012]) add(Cp(.0078, .024 - Math.abs(fx) * .25, .0008, 22), M.skin, hand, [fx, -.056, .003], [.25, 0, 0]);
    add(Cp(.011, .03, .001, 20), M.skin, hand, [-sd * .022, -.015, .014], [0, 0, sd * .5]);
    return {up, fo, hand};
  });
  const legs = [-1, 1].map(sd => {
    const lb = b.limb, th = G(hips, [sd * .075 * b.hip, -.02, 0]); add(turn([[0, .04], [.05 * lb, .035], [.074 * lb, .005], [.076 * lb, -.08], [.069 * lb, -.25], [.062 * lb, -.36], [.06 * lb, -.4]], .006, 6), M.pants, th);
    const sh = G(th, [0, -.37, 0]); add(turn([[.06 * lb, .035], [.062 * lb, -.04], [.059 * lb, -.15], [.061 * lb, -.26], [.065 * lb, -.31], [.058 * lb, -.335]], .006, 6), M.pants, sh); if (outfit !== 'dress') add(fold(.058, .012), M.pants, sh, [0, -.02, .005], [Math.PI / 2 - .3, 0, 0]);
    const trousers = outfit !== 'dress';
    if (trousers) add(S(.034, 1.1, .9, .55, .003, 10), M.pants, sh, [0, -.015, .045]);             // the knee, showing through the trousers
    if (trousers) { add(fold(.06, .011), M.pants, sh, [0, -.27, 0], [Math.PI / 2 + .15, 0, 0]);
    add(fold(.06, .013), M.pants, sh, [0, -.315, 0], [Math.PI / 2, 0, 0]); }          // trouser hem
    const ft = G(sh, [0, -.37, 0]); add(S(.058, 1, .66, 2.2, .003), M.shoe, ft, [0, -.01, .05]);
    add(S(.061, 1.02, .22, 2.25, .002), M.sole, ft, [0, -.042, .05]);
    for (let k = 0; k < 3; k++) add(Cp(.0035, .05, .0005, 30), M.lace, ft, [0, .025, .06 + k * .022], [0, 0, Math.PI / 2]);
    return {th, sh, ft};
  });
  const P = {root, hips, chest, neck, head, back, face, arms, legs, M, faceLight, sec, neckLen: o.neckLen ?? .155, s0: o.scale || 1};   // s0: the character's size (scenes reset to it)
  const eyeBase = eyes.map(e => e.position.clone());
  const tears = [-1, 1].map(x => { const t = add(S(.0055, 1, 1.6, .8, .0005, 20), M.tear, face, [x * .038, -.024, .004]); t.visible = false; return t; });
  P.eyes = s => {                 // 'open' | 'closed' | 'wide' | 'squeeze'
    const open = s === 'open' || s === 'wide';
    eyes.forEach((e, i) => { e.visible = open; e.scale.setScalar(s === 'wide' ? 1.15 : 1); e.position.copy(eyeBase[i]); }); tears.forEach(t => t.visible = false);
    whites.forEach(w => { w.visible = s === 'wide'; });
    lids.forEach((l, i) => { l.visible = !open; l.scale.set(1, s === 'squeeze' ? 1.25 : 1, 1); l.rotation.z = Math.PI / 2 + (s === 'squeeze' ? (i ? -.25 : .25) : 0); });
    caps.forEach(c => { c.visible = open && o.lids !== false; c.rotation.x = s === 'wide' ? -1.15 : -.62; });   // the lid only over the top of the eye
  };
  P.brows = k => brows.forEach((b, i) => { b.rotation.z = (i ? -1 : 1) * k * .45; b.position.y = .031 + Math.abs(k) * .005; });  // k>0 worried, k<0 cross
  P.mouth = (s, amt = 1) => {     // 'closed' | 'pressed' | 'smile' | 'frown' | 'open' | 'gums' | 'o' | 'grimace' | 'scream'   (amt: how much)
    const shut = s === 'closed' || s === 'pressed' || s === 'smile' || s === 'frown'; mLine.visible = lowLip.visible = shut;
    const up = s === 'smile', cy = s === 'pressed' ? .22 : up ? .45 + .35 * amt : s === 'frown' ? .9 : .45;   // a smile curves up; the rest gently down
    mLine.rotation.z = up ? Math.PI : 0;
    mLine.scale.set(s === 'pressed' ? .85 : up ? 1 + .15 * amt : 1, cy, 1);
    mLine.position.y = up ? .013 * cy - .004 : -.013 * cy; lowLip.scale.setScalar(s === 'pressed' ? .8 : 1);
    const sc = {open: [1, .35 + .65 * amt], gums: [1, .35 + .65 * amt], o: [.55, .7 + .3 * amt], grimace: [1.5, .4 + .15 * amt], scream: [1.05, 1.1 + .6 * amt]}[s];
    mOpen.visible = !!sc; if (sc) mOpen.scale.set(sc[0], sc[1], 1);
    teeth[0].visible = s === 'open' || s === 'grimace' || s === 'scream'; teeth[1].visible = s === 'open' || s === 'grimace'; gums.forEach(g => g.visible = s === 'gums');
  };
  // ---- expressions: continuous controls, then named looks built from them (P.expr('scared'))
  P.lid = v => {                  // upper lid: 0 wide open .. 1 shut
    if (v >= .9) { P.eyes('closed'); return; }
    eyes.forEach(e => e.visible = true); lids.forEach(l => l.visible = false); caps.forEach(c => { c.visible = o.lids !== false || v > .3; c.rotation.x = -1.2 + v * 1.85; });
  };
  P.pupils = k => eyes.forEach(e => e.scale.setScalar(k));                   // small pupils = fear
  P.look = (x = 0, y = 0) => eyes.forEach((e, i) => e.position.set(eyeBase[i].x + x * .005, eyeBase[i].y + y * .004, eyeBase[i].z));   // -1..1
  P.browPair = (r, l, up = 0) => brows.forEach((b, i) => { const k = i ? l : r; b.rotation.z = (i ? -1 : 1) * k * .8; b.position.y = .031 + up + Math.max(0, k) * .006 - Math.max(0, -k) * .004; b.position.x = (i ? 1 : -1) * (.034 - Math.max(0, -k) * .004); });
  P.tears = on => tears.forEach(t => t.visible = on);
  P.expr = name => { const e = EXPR[name] || EXPR.neutral;
    whites.forEach(w => w.visible = !!e.wide); P.lid(e.lid); if (e.lid < .9) { P.pupils(e.pupils ?? 1); P.look(...(e.look || [0, 0])); }
    P.browPair(e.brows[0], e.brows[1], e.brows[2] || 0); P.mouth(e.mouth, e.open ?? 1); P.tears(!!e.tears); };
  P.rest = (k = 1) => {
    if (b.stoop) { chest.rotation.x += b.stoop * .45 * k; neck.rotation.x += b.stoop * .25 * k; head.rotation.x -= b.stoop * .5 * k; }   // an old back bends forward; the eyes stay up
    hips.rotation.z += .035 * k; hips.position.x += .008 * k; chest.rotation.z -= .05 * k; chest.rotation.x += .03 * k; neck.rotation.z += .03 * k; head.rotation.z += .04 * k;
    arms[0].up.rotation.z -= .06 * k; arms[0].up.rotation.x += .06 * k; arms[0].fo.rotation.x -= .14 * k;
    arms[1].up.rotation.z += .1 * k; arms[1].up.rotation.x -= .05 * k; arms[1].fo.rotation.x -= .3 * k; arms[1].hand.rotation.y = .4 * k;
    legs[0].th.rotation.z -= .03 * k; legs[1].th.rotation.z += .05 * k; legs[1].th.rotation.x -= .08 * k; legs[1].sh.rotation.x += .14 * k; legs[1].ft.rotation.x -= .05 * k;
  };
  P.eyes('open'); P.brows(0); P.mouth('closed');
  return P;
}
// ---------------------------------------------------------------- expressions (P.expr(name)): lid 0 open..1 shut, brows [right, left, raise] (+ worried, - cross)
export const EXPR = {
  neutral: {lid: .25, brows: [0, 0], mouth: 'closed'},            worried: {lid: .2, brows: [.6, .6], mouth: 'closed'},
  scared: {lid: .05, brows: [.9, .9, .004], mouth: 'o', open: .4, pupils: .85},
  terrified: {lid: 0, brows: [1, 1, .006], mouth: 'scream', open: .7, pupils: .6, wide: true},
  sad: {lid: .45, brows: [.8, .8], mouth: 'frown', look: [0, -.6]}, crying: {lid: .6, brows: [1, 1], mouth: 'frown', tears: true, look: [0, -.4]},
  angry: {lid: .4, brows: [-.8, -.8, -.002], mouth: 'pressed'},   smile: {lid: .3, brows: [.1, .1], mouth: 'smile', open: .6},
  creepySmile: {lid: .55, brows: [-.3, -.3], mouth: 'smile', open: 1, pupils: .75},
  surprised: {lid: 0, brows: [.4, .4, .008], mouth: 'o', open: .8, wide: true},
  shock: {lid: 0, brows: [.7, .7, .008], mouth: 'scream', open: 1, pupils: .65, wide: true},
  sleepy: {lid: .75, brows: [.2, .2], mouth: 'closed'},         suspicious: {lid: .55, brows: [-.5, .4], mouth: 'pressed', look: [.7, 0]},
  relieved: {lid: .6, brows: [.5, .5], mouth: 'smile', open: .4}, disgusted: {lid: .5, brows: [-.6, .2], mouth: 'grimace', open: .3},
  determined: {lid: .35, brows: [-.5, -.5], mouth: 'pressed'},
};

// ---------------------------------------------------------------- poses (pose(P, name, k)): on top of a reset pose, k blends 0..1
// arms[0] is the character's right arm, arms[1] the left. up/fo x < 0 raises forward / bends the elbow; for the right arm z < 0 is out.
// Each entry: joint: [x, y, z] rotations; the left arm mirrors y and z of 'arm' entries automatically; 'drop' lowers the hips.
const A = (up, fo) => ({up, fo});
export const POSES = {
  stand: {},
  scared: {chest: [.25, 0, 0], neck: [.1, 0, 0], head: [-.18, 0, 0], arms: A([-.55, .55, -.1], [-1.5, 0, 0]), legs: {th: [-.15, 0, 0], sh: [.3, 0, 0]}, drop: .03},
  cower: {chest: [.65, 0, 0], head: [.25, 0, 0], arms: A([-2.5, .4, -.35], [-1.3, 0, 0]), legs: {th: [-1.95, 0, .12], sh: [2.25, 0, 0]}, drop: .44},
  handsMouth: {arms: A([-1.2, .8, 0], [-2.3, 0, 0]), chest: [.08, 0, 0], head: [.1, 0, 0]},   // both hands over the mouth, eyes free
  cry: {chest: [.4, 0, 0], neck: [.2, 0, 0], head: [.35, 0, 0], arms: A([-1.3, .7, 0], [-2.35, 0, 0])},   // face buried in her hands
  point: {armR: A([-1.45, 0, -.05], [-.1, 0, 0]), head: [0, -.2, 0]},
  reach: {arms: A([-1.3, .15, 0], [-.25, 0, 0]), chest: [.15, 0, 0]},
  armsCrossed: {arms: A([-.5, 1.1, .1], [-1.75, 0, 0]), chest: [-.05, 0, 0]},
  shrug: {arms: A([-.2, 0, -.45], [-1.3, 0, 0]), neck: [0, 0, .12]},
  think: {armR: A([-.4, .6, 0], [-1.6, 0, 0]), armL: A([-.6, -.4, .1], [-2.4, 0, 0]), head: [.1, 0, .1]},
  flashlight: {armR: A([-1.2, .15, -.05], [-.35, 0, 0]), chest: [.1, 0, 0], head: [.05, 0, 0]},
  wave: {armL: A([0, 0, 2.5], [-.6, 0, 0])},
  armsUp: {arms: A([-2.9, 0, -.15], [-.2, 0, 0]), head: [-.2, 0, 0]},
  hug: {arms: A([-1.2, .9, 0], [-1.25, 0, 0]), chest: [.1, 0, 0]},
  sitFloor: {legs: {th: [-1.35, 0, .1], sh: [2.3, 0, 0]}, arms: A([-.95, .55, 0], [-.85, 0, 0]), chest: [.3, 0, 0], drop: .62},
  sitChair: {legs: {th: [-1.5, 0, 0], sh: [1.5, 0, 0]}, arms: A([-.4, 0, 0], [-.7, 0, 0])},
  kneel: {legs: {th: [.05, 0, 0], sh: [1.6, 0, 0]}, chest: [.1, 0, 0], drop: .38},
  peek: {hips: [0, 0, .12], chest: [0, 0, .3], head: [0, 0, .2], armR: A([-.4, 0, -.2], [-1.2, 0, 0])},
  sneak: {chest: [.3, 0, 0], head: [-.25, 0, 0], arms: A([-.6, 0, -.3], [-1.1, 0, 0]), legs: {th: [-.35, 0, 0], sh: [.6, 0, 0]}, drop: .07},
};
const lerpRot = (o, v, k) => { o.rotation.x += (v[0] - o.rotation.x) * k; o.rotation.y += (v[1] - o.rotation.y) * k; o.rotation.z += (v[2] - o.rotation.z) * k; };
export function pose(P, name, k = 1) {
  const p = POSES[name]; if (!p) return;
  for (const j of ['hips', 'chest', 'neck', 'head']) if (p[j]) lerpRot(P[j], p[j], k);
  const arm = (a, d, m) => { if (!d) return; lerpRot(a.up, [d.up[0], m * d.up[1], m * d.up[2]], k); lerpRot(a.fo, [d.fo[0], m * d.fo[1], m * d.fo[2]], k); };
  if (p.arms) { arm(P.arms[0], p.arms, 1); arm(P.arms[1], p.arms, -1); }
  arm(P.arms[0], p.armR, 1); arm(P.arms[1], p.armL, 1);
  if (p.legs) P.legs.forEach((l, i) => { for (const j of ['th', 'sh', 'ft']) if (p.legs[j]) lerpRot(l[j], [p.legs[j][0], (i ? -1 : 1) * p.legs[j][1], (i ? -1 : 1) * p.legs[j][2]], k); });
  if (p.drop) P.hips.position.y -= p.drop * k;
}

// ---------------------------------------------------------------- the neck: head looks and gestures (call after reset / pose, before the face)
// look(P, {turn, tilt, nod, jut}): turn > 0 to her left, tilt > 0 ear towards her right shoulder, nod > 0 chin down, jut > 0 chin forward (metres).
// The bend is shared: the neck takes 40 %, the head 60 %, so it reads as a neck bending, not a ball turning on a stick.
export function look(P, {turn = 0, tilt = 0, nod = 0, jut = 0} = {}) {
  P.neck.rotation.y += turn * .4; P.head.rotation.y += turn * .6;
  P.neck.rotation.z -= tilt * .45; P.head.rotation.z -= tilt * .55;
  P.neck.rotation.x += nod * .4; P.head.rotation.x += nod * .6;
  P.head.position.set(0, (P.neckLen || .155) - Math.abs(jut) * .3, jut);
  if (P.sec && P.sec.hair) { P.sec.hair.rotation.y = -turn * .3; P.sec.hair.rotation.z = tilt * .35; }   // the hair hangs and stays over the shoulders (followFrame refines it)
}
export const LOOKS = {                                 // ready-made head looks; 'expr' is the face that usually goes with it
  straight: {}, wtf: {turn: .15, tilt: .38, nod: -.14, jut: -.016, expr: 'suspicious'}, curious: {tilt: .28, nod: -.06, jut: .01, expr: 'surprised'},
  tiltL: {tilt: -.32}, tiltR: {tilt: .32}, turnL: {turn: .95}, turnR: {turn: -.95}, glanceL: {turn: .45, expr: 'suspicious'}, glanceR: {turn: -.45, expr: 'suspicious'},
  lookUp: {nod: -.55, expr: 'scared'}, lookDown: {nod: .5, expr: 'sad'}, peer: {jut: .028, nod: .12, expr: 'suspicious'}, recoil: {jut: -.022, nod: -.22, tilt: -.1, expr: 'shock'},
  overShoulderL: {turn: 1.35, nod: -.05, expr: 'scared'}, overShoulderR: {turn: -1.35, nod: -.05, expr: 'scared'},
};
export function headLook(P, name, k = 1) { const l = LOOKS[name] || {}; look(P, {turn: (l.turn || 0) * k, tilt: (l.tilt || 0) * k, nod: (l.nod || 0) * k, jut: (l.jut || 0) * k}); if (l.expr && k > .5 && P.expr) P.expr(l.expr); }
// gesture(P, name, u): an animated head move, u = 0..1 through it. 'doubleTake' | 'nod' | 'shake' | 'wtf' (snaps into it, holds) | 'flinch'
export function gesture(P, name, u) {
  const e = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
  if (name === 'doubleTake') { const t1 = e(u / .14) - e((u - .16) / .14), t2 = e((u - .5) / .08);   // a glance, back, a beat, then snap round and hold
    look(P, {turn: .55 * t1 + 1.0 * t2, nod: -.08 * t2, jut: -.012 * t2}); if (P.expr) P.expr(t2 > .5 ? 'shock' : 'neutral'); }
  else if (name === 'nod') look(P, {nod: Math.sin(u * Math.PI * 4) * .22 * (1 - u * .5)});
  else if (name === 'shake') look(P, {turn: Math.sin(u * Math.PI * 6) * .42 * (1 - u * .6)});
  else if (name === 'wtf') headLook(P, 'wtf', e(u / .25));
  else if (name === 'flinch') { const k = e(u / .1) * (1 - e((u - .35) / .5)); look(P, {jut: -.025 * k, nod: -.15 * k, turn: -.3 * k, tilt: -.15 * k}); if (P.expr) P.expr(k > .3 ? 'shock' : 'scared'); }
}

// ---------------------------------------------------------------- movement (shared by every scene and every character)
// walk(P, t, {speed, amp, run, sneak}): legs, arms opposite the legs, a hip/chest counter-twist, the head kept level.
export function walk(P, t, {speed = 1, amp = 1, run = false, sneak = false} = {}) {
  if (run) { speed *= 1.7; amp *= 1.5; } if (sneak) { speed *= .55; amp *= .6; }
  const ph = t * Math.PI * 2 * speed, sw = Math.sin(ph);
  P.hips.position.y = .82 - (1 - Math.cos(.42 * amp * sw)) * .74 + Math.abs(Math.cos(ph)) * (run ? .03 : .012) * amp - (sneak ? .07 : 0);
  P.hips.rotation.y = sw * .1 * amp; P.chest.rotation.y = -sw * .16 * amp; P.neck.rotation.y = sw * .06 * amp;
  P.chest.rotation.x = run ? .22 : sneak ? .3 : .04; P.head.rotation.x = run ? -.15 : sneak ? -.25 : 0;
  P.legs.forEach(({th, sh, ft}, i) => { const q = i ? -sw : sw, kn = Math.max(0, Math.sin(ph + (i ? Math.PI : 0) - .6)) * (.9 + .5 * (amp - 1)) + (sneak ? .5 : 0);
    th.rotation.x = -q * .42 * amp - (sneak ? .3 : 0); sh.rotation.x = kn; ft.rotation.x = -kn * .5 + q * .2; });
  P.arms.forEach(({up, fo}, i) => { const q = i ? sw : -sw; up.rotation.x = -q * .4 * amp - (sneak ? .5 : 0); fo.rotation.x = run ? -1.4 : sneak ? -1.1 : -.2 - Math.max(0, q) * .4 * amp; });
}
// tremble(P, t, k): a fearful shake in the shoulders, hands and head (stop-motion: it changes every pose)
export function tremble(P, t, k = 1) {
  const n = i => Math.sin(Math.floor(t * 12) * 12.9898 + i * 78.233) * .5;
  P.chest.rotation.z += n(1) * .03 * k; P.head.rotation.z += n(2) * .04 * k; P.head.rotation.x += n(3) * .03 * k;
  P.arms.forEach(({up, fo}, i) => { up.rotation.x += n(4 + i) * .06 * k; fo.rotation.x += n(6 + i) * .08 * k; });
}
export function breathe(P, t, k = 1) { const b = Math.sin(t * Math.PI * 2 / 3.6) * k; P.chest.rotation.x -= b * .02; P.neck.rotation.x += b * .015; }
// autoBlink(P, t, seed): a blink every ~4 s (one or two stop-motion poses with the eyes shut); returns true while blinking
export function autoBlink(P, t, seed = 0) { const c = (t + seed * 1.37) % 4.1; if (c < .14) { P.eyes('closed'); return true; } return false; }

// ---------------------------------------------------------------- follow-through: hair, hood and drawstrings swing behind the body and settle
// The scene's frame(t) is run again at a few earlier poses (with the clay boil paused) to see how each character moved, so every frame
// can be rendered on its own, in any order.   const frameFX = followFrame(frame, () => [haru, mum]);  then call frameFX(t) instead of frame(t).
let SAMPLING = false;
export const sampling = () => SAMPLING;
const _v = new THREE.Vector3(), _q = new THREE.Quaternion(), _q2 = new THREE.Quaternion(), _e = new THREE.Euler(0, 0, 0, 'YXZ');
function shown(o) { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; }
function capture(P) {
  if (!P.root.parent || !shown(P.root)) return null; P.root.updateMatrixWorld(true);
  return {head: P.head.getWorldPosition(new THREE.Vector3()), chest: P.chest.getWorldPosition(new THREE.Vector3()),
          hq: P.head.getWorldQuaternion(new THREE.Quaternion()), cq: P.chest.getWorldQuaternion(new THREE.Quaternion())};
}
const W0 = 2 * Math.PI * 2.0, ZETA = .32, WD = W0 * Math.sqrt(1 - ZETA * ZETA);
const impulse = tau => Math.exp(-ZETA * W0 * tau) * Math.sin(WD * tau) / WD;   // a damped spring's answer to a push
function lag(hist, key, dt) {                        // how far a hanging part trails behind (world metres), from the recent accelerations
  const d = new THREE.Vector3(), n = hist.length;
  for (let j = 2; j < n; j++) {
    const a = hist[j][key].clone().sub(hist[j - 1][key]).sub(hist[j - 1][key]).add(hist[j - 2][key]).divideScalar(dt * dt);
    d.addScaledVector(a, -impulse((n - j) * dt + dt * .5) * dt);
  }
  return d;
}
function swing(g, worldLag, parentQ, L, hang, lim) {   // turn a pivot so its tip trails by worldLag and hangs towards the ground
  if (!g) return; _q.copy(parentQ).invert();
  const d = worldLag.clone().applyQuaternion(_q), down = _v.set(0, -1, 0).applyQuaternion(_q);
  const cl = (x, a, b) => Math.max(a, Math.min(b, x));
  g.rotation.x = cl(-Math.asin(cl(d.z / L, -1, 1)) - hang * Math.asin(cl(down.z, -1, 1)), lim[0], lim[1]);
  g.rotation.z = cl(Math.asin(cl(d.x / L, -1, 1)) + hang * Math.asin(cl(down.x, -1, 1)), -lim[2], lim[2]);
}
export function followFrame(frame, people, {samples = 5, dt = 1 / 12} = {}) {
  return t => {
    const ps = people(), hist = ps.map(() => []);
    SAMPLING = true;
    for (let k = samples; k >= 1; k--) { frame(t - k * dt); ps.forEach((P, i) => hist[i].push(capture(P))); }
    SAMPLING = false; frame(t);
    ps.forEach((P, i) => { let h = hist[i]; h.push(capture(P)); const now = h[h.length - 1]; if (!now || !P.sec) return;
      for (let j = h.length - 1; j > 0; j--) {          // a cut (or a hidden character): only the poses since the last jump count
        if (!h[j - 1] || h[j - 1].chest.distanceTo(h[j].chest) > .4 || h[j - 1].hq.angleTo(h[j].hq) > 1.2) { h = h.slice(j); break; } }
      const full = h.length >= 3, Z = new THREE.Vector3();
      const hl = full ? lag(h, 'head', dt) : Z, cl = full ? lag(h, 'chest', dt) : Z;
      if (h.length >= 2) { const k = h.length - 1;                                     // air drag: moving fast, loose parts stream back
        hl.addScaledVector(h[k].head.clone().sub(h[k - 1].head), -.05 / dt); cl.addScaledVector(h[k].chest.clone().sub(h[k - 1].chest), -.05 / dt); }
      swing(P.sec.hair, hl.multiplyScalar(1.1), now.hq, .3, .75, [-.06, .7, .16]);   // free to swing back; the face, chest and shoulders stop it going forward or sideways
      if (P.sec.hair) { _q2.copy(now.cq).invert().multiply(now.hq); _e.setFromQuaternion(_q2); P.sec.hair.rotation.y = -_e.y * .3; }   // the hair stays over the shoulders when she turns her head
      for (const s of P.sec.strings) swing(s, cl.clone().multiplyScalar(2.2), now.cq, .1, 1, [-1, 1, .9]);
      swing(P.sec.hood, cl.clone().multiplyScalar(.35), now.cq, .14, .3, [-.2, .2, .15]);
    });
  };
}
export const BUILDS = {                     // sh shoulders, hip, chest depth, limb thickness, belly, bust, stoop
  child: {sh: 1, hip: 1, chest: 1, limb: 1, belly: 0, bust: 0, stoop: 0},
  woman: {sh: .98, hip: 1.1, chest: .95, limb: .92, belly: 0, bust: 1, stoop: 0},
  man:   {sh: 1.16, hip: .96, chest: 1.08, limb: 1.08, belly: .015, bust: 0, stoop: 0},
  old:   {sh: .94, hip: 1.06, chest: 1, limb: .9, belly: .025, bust: 0, stoop: .3},
};
export const haruOpts = {scale: .71, headScale: 1.24, sculpt: .35, faceShape: [.95, 1.04, 1.05], eyeSize: .0072, lids: false, brow: 'dash', blush: false, eyeLines: false, nose: 'button',
  puffy: 1.22, hairThick: 1.22, hairGap: 1.12, hairTop: true, hairline: .066, neckLen: .195,
  skin: 0xe8a27c, top: 0xc8963c, pants: 0x55555c, shoe: 0xe8e6e0, hair: 0x26262c};       // matched to the Artlist sheets
export const mumOpts = {build: 'woman', outfit: 'sweater', headScale: 1.05, top: 0x3e3040, pants: 0x26252c, shoe: 0x2a2424, longHair: false, bun: true, pocket: false, hood: false, scale: 1.07, hair: 0x2c2420};

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
