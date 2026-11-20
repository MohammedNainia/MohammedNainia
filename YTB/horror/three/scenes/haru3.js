// Clay Haru v3: every garment is ONE piece of clay. Each part is described as soft shapes that melt into each other
// (smooth union of signed distance fields), turned into a single mesh (marching cubes), roughened with small lumps,
// given fingerprints / tool marks / colour mottling, and skinned to a skeleton so it still bends.
// Matches YTB/channel_art/haru_turnaround_sheet.png and haru_expressions_sheet.png.
import {THREE} from './lib.js';
import {MarchingCubes} from 'three/addons/objects/MarchingCubes.js';
import {gloss} from './clay.js';

// ---------------------------------------------------------------- SDF toolkit
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const smin = (a, b, k) => { const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k * .25; };
const smax = (a, b, k) => -smin(-a, -b, k);
function sdCapsule(px, py, pz, a, b, r) {
  const bax = b.x - a.x, bay = b.y - a.y, baz = b.z - a.z, pax = px - a.x, pay = py - a.y, paz = pz - a.z;
  const h = Math.min(1, Math.max(0, (pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz)));
  const dx = pax - bax * h, dy = pay - bay * h, dz = paz - baz * h; return Math.sqrt(dx * dx + dy * dy + dz * dz) - r;
}
function sdRoundCone(px, py, pz, a, b, r1, r2) {      // a capsule whose radius goes from r1 (at a) to r2 (at b)
  const bax = b.x - a.x, bay = b.y - a.y, baz = b.z - a.z, pax = px - a.x, pay = py - a.y, paz = pz - a.z;
  const h = Math.min(1, Math.max(0, (pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz)));
  const dx = pax - bax * h, dy = pay - bay * h, dz = paz - baz * h; return Math.sqrt(dx * dx + dy * dy + dz * dz) - (r1 + (r2 - r1) * h);
}
function sdEll(px, py, pz, c, r) {                       // ellipsoid (approximate distance)
  const x = (px - c.x) / r.x, y = (py - c.y) / r.y, z = (pz - c.z) / r.z;
  const k0 = Math.sqrt(x * x + y * y + z * z), k1 = Math.sqrt(x * x / (r.x * r.x) + y * y / (r.y * r.y) + z * z / (r.z * r.z));
  return k1 === 0 ? -Math.min(r.x, r.y, r.z) : k0 * (k0 - 1) / k1;
}
function sdTorusY(px, py, pz, c, R, r, sx = 1, sz = 1) { // a ring lying flat (around y)
  const x = (px - c.x) / sx, z = (pz - c.z) / sz, q = Math.sqrt(x * x + z * z) - R, y = py - c.y; return Math.sqrt(q * q + y * y) - r;
}
function sdTorusAxis(px, py, pz, c, axis, R, r) {        // a ring around any axis (sleeve cuffs)
  const dx = px - c.x, dy = py - c.y, dz = pz - c.z, h = dx * axis.x + dy * axis.y + dz * axis.z;
  const qx = dx - axis.x * h, qy = dy - axis.y * h, qz = dz - axis.z * h, q = Math.sqrt(qx * qx + qy * qy + qz * qz) - R;
  return Math.sqrt(q * q + h * h) - r;
}
function sdRoundBox(px, py, pz, c, b, r) {
  const qx = Math.abs(px - c.x) - b.x, qy = Math.abs(py - c.y) - b.y, qz = Math.abs(pz - c.z) - b.z;
  const ox = Math.max(qx, 0), oy = Math.max(qy, 0), oz = Math.max(qz, 0);
  return Math.sqrt(ox * ox + oy * oy + oz * oz) + Math.min(Math.max(qx, qy, qz), 0) - r;
}
const sdPlane = (x, y, z, p, n) => (x - p.x) * n.x + (y - p.y) * n.y + (z - p.z) * n.z;   // > 0 on the side n points to
// value noise for the hand-made lumps
const P = new Uint8Array(512); { let s = 7; const p = [...Array(256).keys()]; for (let i = 255; i > 0; i--) { s = (s * 16807) % 2147483647; const j = s % (i + 1); [p[i], p[j]] = [p[j], p[i]]; } for (let i = 0; i < 512; i++) P[i] = p[i & 255]; }
const fade = t => t * t * (3 - 2 * t);
function vnoise(x, y, z) {
  const X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z), fx = fade(x - X), fy = fade(y - Y), fz = fade(z - Z);
  const h = (i, j, k) => P[P[P[(X + i) & 255] + ((Y + j) & 255)] + ((Z + k) & 255)] / 127.5 - 1;
  const l = (a, b, t) => a + (b - a) * t;
  return l(l(l(h(0, 0, 0), h(1, 0, 0), fx), l(h(0, 1, 0), h(1, 1, 0), fx), fy), l(l(h(0, 0, 1), h(1, 0, 1), fx), l(h(0, 1, 1), h(1, 1, 1), fx), fy), fz);
}
const lumps = (x, y, z, a = 1) => a * (.0024 * vnoise(x * 26, y * 26, z * 26) + .0011 * vnoise(x * 70 + 3, y * 70, z * 70));

// SDF -> one mesh. center/half: the cube to sample; res: samples per side.
// Speed: the surface only needs exact values near it. A coarse pass (every B-th sample) finds blocks that are clearly
// inside or outside (further from the surface than the block's own size + a safety margin) and fills them without
// evaluating the shape; only the blocks near the surface are sampled at full resolution (about 5-10x fewer evaluations).
let DETAIL = 1;                    // mesh detail for the next makeHaru3 (o.detail): lower = fewer triangles, faster path tracing
let GEO_CACHE = null, GEO_KEY = '', GEO_N = 0;   // reuse of identical meshes between copies of the same character
const CACHE = new Map();
export const MESH_OPTS = {band: true};          // band: false = sample every grid point (slow; only to verify the fast path)
function meshSDF(sdf, center, half, res) {
  res = Math.max(28, Math.round(res * DETAIL));
  const ck = GEO_CACHE ? GEO_KEY + '#' + (GEO_N++) + '@' + res : null;
  if (ck && CACHE.has(ck)) return CACHE.get(ck);                    // shared geometry (skin weights included)
  const mc = new MarchingCubes(res, new THREE.MeshBasicMaterial(), false, false, 220000);
  const f = mc.field, h = res / 2, K = 4000, step = half / h, B = 4;
  const P = i => (i - h) * step;                                    // grid index -> offset from the centre
  const blockR = Math.sqrt(3) * (B / 2) * step, margin = 1.5 * blockR + 3 * step + .006;   // generous: shapes are not exact distances
  for (let bz = 0; bz < res; bz += B) for (let by = 0; by < res; by += B) for (let bx = 0; bx < res; bx += B) {
    const cx = Math.min(bx + B / 2, res - 1), cy = Math.min(by + B / 2, res - 1), cz = Math.min(bz + B / 2, res - 1);
    const dc = sdf(center.x + P(cx), center.y + P(cy), center.z + P(cz));
    const x1 = Math.min(bx + B, res), y1 = Math.min(by + B, res), z1 = Math.min(bz + B, res);
    if (MESH_OPTS.band && Math.abs(dc) > margin) {                                     // clearly inside or outside: one value for the block
      const v = 80 - dc * K;
      for (let z = bz; z < z1; z++) for (let y = by; y < y1; y++) { const o = y * res + z * res * res; f.fill(v, o + bx, o + x1); }
    } else {
      for (let z = bz; z < z1; z++) for (let y = by; y < y1; y++) for (let x = bx; x < x1; x++)
        f[x + y * res + z * res * res] = 80 - sdf(center.x + P(x), center.y + P(y), center.z + P(z)) * K;
    }
  }
  mc.update();
  const n = mc.count, pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2);
  for (let i = 0; i < n; i++) {
    const px = center.x + mc.positionArray[i * 3] * half, py = center.y + mc.positionArray[i * 3 + 1] * half, pz = center.z + mc.positionArray[i * 3 + 2] * half;
    pos[i * 3] = px; pos[i * 3 + 1] = py; pos[i * 3 + 2] = pz;
    let nx = mc.normalArray[i * 3], ny = mc.normalArray[i * 3 + 1], nz = mc.normalArray[i * 3 + 2]; const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l; ny /= l; nz /= l; nor[i * 3] = nx; nor[i * 3 + 1] = ny; nor[i * 3 + 2] = nz;
    // texture wrapped round the shape like a label on a can (around the vertical axis): continuous all round, so no seams on the
    // forehead or down striped sleeves; the only join is at the back (angle +-180 degrees), hidden by hair or the body
    const s = 5, dx = px - center.x, dz = pz - center.z, r = Math.max(.02, Math.hypot(dx, dz));
    uv[i * 2] = Math.atan2(dx, dz) * r * s; uv[i * 2 + 1] = py * s;
  }
  mc.geometry.dispose();
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  if (ck) CACHE.set(ck, g);
  return g;
}

// ---------------------------------------------------------------- clay surface: fingerprints, tool marks, pits, mottling
function canvas(n, draw) { const c = document.createElement('canvas'); c.width = c.height = n; draw(c.getContext('2d'), n); return c; }
let rs = 11; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
// both clay textures tile seamlessly: every mark is drawn 9 times (shifted by the texture size), so marks crossing an edge come back
// on the other side; otherwise each repeat of the texture shows as a faint straight line on the clay (it did, across Haru's face)
const W9 = (g, n, draw) => { for (const ox of [-n, 0, n]) for (const oy of [-n, 0, n]) { g.save(); g.translate(ox, oy); draw(); g.restore(); } };
const detailC = canvas(1024, (g, n) => {
  g.fillStyle = '#808080'; g.fillRect(0, 0, n, n);
  for (let k = 0; k < 70; k++) { const cx = rnd() * n, cy = rnd() * n, m = 8 + rnd() * 10, ro = rnd() * 3, sx = .7 + rnd() * .5;   // fingerprints
    W9(g, n, () => { for (let i = 0; i < m; i++) { const v = i % 2 ? 70 : 190; g.strokeStyle = `rgba(${v},${v},${v},.22)`; g.lineWidth = 1.3;
      g.beginPath(); g.ellipse(cx, cy, 3 + i * 2.6, (3 + i * 2.6) * sx, ro, 0, 6.3); g.stroke(); } }); }
  for (let k = 0; k < 160; k++) { const x = rnd() * n, y = rnd() * n, a = rnd() * 6.3, L = 20 + rnd() * 70, c = rnd() < .5 ? 60 : 200, lw = 2 + rnd() * 5;   // tool smears
    W9(g, n, () => { const gr = g.createLinearGradient(x, y, x + Math.cos(a) * L, y + Math.sin(a) * L); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(.5, `rgba(${c},128,128,.18)`); gr.addColorStop(1, 'rgba(255,255,255,0)');
      g.strokeStyle = gr; g.lineWidth = lw; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * L, y + Math.sin(a) * L); g.stroke(); }); }
  for (let k = 0; k < 1600; k++) { const v = rnd() < .6 ? 50 : 210, x = rnd() * n, y = rnd() * n, r = .6 + rnd() * 1.8;   // pits and specks
    W9(g, n, () => { g.fillStyle = `rgba(${v},${v},${v},.2)`; g.beginPath(); g.arc(x, y, r, 0, 6.3); g.fill(); }); }
});
const mottleC = canvas(512, (g, n) => {
  g.fillStyle = '#f2f2f2'; g.fillRect(0, 0, n, n);
  for (let k = 0; k < 400; k++) { const r = 10 + rnd() * 50, v = 205 + rnd() * 50, x = rnd() * n, y = rnd() * n;
    W9(g, n, () => { const gr = g.createRadialGradient(0, 0, 0, 0, 0, r);
      gr.addColorStop(0, `rgba(${v},${v},${v},.35)`); gr.addColorStop(1, `rgba(${v},${v},${v},0)`); g.save(); g.translate(x, y); g.fillStyle = gr; g.fillRect(-r, -r, 2 * r, 2 * r); g.restore(); }); }
});
const tex = c => { const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t; };
const detail = tex(detailC), mottle = tex(mottleC); mottle.colorSpace = THREE.SRGBColorSpace;
// knitted stripes: both colours painted into the texture (base and bands), then the clay mottle multiplied over them;
// the material colour is set to white so it does not tint the bands
const stripeCache = new Map();
function stripes(c2, base) {
  const key = c2 + '/' + base; if (stripeCache.has(key)) return stripeCache.get(key);
  const hex = c => '#' + new THREE.Color(c).getHexString();
  const cv = canvas(512, (g, n) => {
    g.fillStyle = hex(base); g.fillRect(0, 0, n, n);
    g.fillStyle = hex(c2); for (let y = 0; y < n; y += n / 4) g.fillRect(0, y, n, n / 8);
    g.globalCompositeOperation = 'multiply'; g.drawImage(mottleC, 0, 0); });
  const t = tex(cv); t.colorSpace = THREE.SRGBColorSpace; stripeCache.set(key, t); return t;
}
export const clay3 = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, map: mottle, bumpMap: detail, bumpScale: 1.8,
  roughness: .86, metalness: 0, sheen: .3, sheenRoughness: .8, sheenColor: new THREE.Color(c).lerp(new THREE.Color(0xffffff), .3)}, o));

// ---------------------------------------------------------------- the puppet
const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); parent.add(g); return g; };
const B = (parent, pos) => { const b = new THREE.Bone(); b.position.set(...pos); if (parent) parent.add(b); return b; };
const segDist = (p, a, b) => { const ab = b.clone().sub(a), t = Math.min(1, Math.max(0, p.clone().sub(a).dot(ab) / ab.lengthSq())); return p.distanceTo(a.clone().add(ab.multiplyScalar(t))); };

export function makeHaru3(o = {}) {
  DETAIL = o.detail || 1;
  GEO_CACHE = true; GEO_KEY = JSON.stringify(Object.assign({}, o, {detail: DETAIL})); GEO_N = 0;      // same options = same meshes: built once, copied after
  // ---- options (defaults = Haru). top: hoodie | sweater | cardigan; bottom: pants | skirt; hairStyle: haru | bun | horseshoe | curlybob
  const TOP = o.top || 'hoodie', BOTTOM = o.bottom || 'pants', HAIR = o.hairStyle || 'haru';   // + top tshirt, bottom shorts, hair ponytail | boyshort
  const SHORT_SLEEVES = TOP === 'tshirt', SHORTS = BOTTOM === 'shorts';
  const LEG = o.legs === undefined ? .152 : o.legs;          // extra leg length (adults: more)
  const HEAD = o.head || 1.37, BELLY = o.belly || 0, AGE = o.age || 0, HEIGHT = o.height || 1;
  const M = {
    skin: clay3(o.skin || 0xe39a72, {bumpScale: .9, roughness: .66}), hood: clay3(o.hood || 0xcf9132), pants: clay3(o.pants || 0x5c5b60, {bumpScale: 1.8}),
    shoe: clay3(o.shoe || 0xf0eee8, {bumpScale: 1.0}), sole: clay3(o.sole || new THREE.Color(o.shoe || 0xf0eee8).multiplyScalar(.8).getHex(), {bumpScale: .6}), skirt: clay3(o.skirt || 0x4d4a5c, {bumpScale: 1.6}), button: gloss(o.button || 0xe8e0cc),
    crease: clay3(new THREE.Color(o.skin || 0xe39a72).multiplyScalar(.62).getHex(), {bumpScale: .3}), rim: gloss(o.rim || 0x2a2522), lens: new THREE.MeshPhysicalMaterial({color: 0xffffff, roughness: .05, transmission: .9, transparent: true, opacity: .25}),
    hair: clay3(o.hair || 0x2a2a2f, {bumpScale: 1.4, roughness: .78, sheen: .35}),
    eye: gloss(0x0a0a0c), white: gloss(0xf6f4ee), dark: clay3(o.brow || 0x2a1a16, {bumpScale: .3}), nose: clay3(0xd98a62, {bumpScale: .6}),
    mouthIn: clay3(0x4a1418, {bumpScale: .2}), tongue: clay3(0xd06a70, {bumpScale: .4}), teeth: gloss(0xfaf6ee),
    tear: new THREE.MeshPhysicalMaterial({color: 0xcfe8ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .75}),
    sweat: new THREE.MeshPhysicalMaterial({color: 0x9fd0ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .85}),
  };
  const root = new THREE.Group();
  // ---- skeleton (bind pose: arms a little out, legs straight)
  const BIND_ARM = .75;                                  // the hoodie is built with the arms held out (A-pose), so the sleeves are
                                                          // separate from the body and lift cleanly; Pp.rest() lowers them to .24
  const DY = LEG;                                         // leg lengthening (Haru: .152, measured against the sheet)
  const hips = B(null, [0, .55 + DY, 0]); root.add(hips);
  // the head sits so the chin rests just above the collar: chin = head + .03 - .13 * head size (Haru: .24, chin at the hood roll)
  const CHIN = TOP === 'hoodie' ? 1.122 : 1.075, HB = CHIN - 1.06 + .13 * HEAD;
  const chest = B(hips, [0, .04, 0]), neck = B(chest, [0, .44, 0]), head = B(neck, [0, HB, 0]);
  const arms = [-1, 1].map(sd => { const up = B(chest, [sd * .185, .32, 0]); up.rotation.z = sd * BIND_ARM; const fo = B(up, [0, -.2, 0]); const hand = B(fo, [0, -.24, 0]); return {up, fo, hand, sd}; });
  const legs = [-1, 1].map(sd => { const th = B(hips, [sd * .098, 0, 0]); const sh = B(th, [0, -.33, 0]); const ft = B(sh, [0, -.31, 0]); return {th, sh, ft, sd}; });
  root.updateMatrixWorld(true);
  const W = b => b.getWorldPosition(V(0, 0, 0));
  const J = {hips: W(hips), chest: W(chest), neck: W(neck), head: W(head)};
  arms.forEach(a => { a.U = W(a.up); a.F = W(a.fo); a.H = W(a.hand); });
  legs.forEach(l => { l.T = W(l.th); l.S = W(l.sh); l.F = W(l.ft); });

  // one sleeve (shoulder cap, upper sleeve, forearm, cuff), in the hoodie's frame (y already shifted by DY)
  const sleeveSDF = (a, x, y, z) => {
    const U = a.U.clone().add(V(0, -DY, 0)), F = a.F.clone().add(V(0, -DY, 0)), Hh = a.H.clone().add(V(0, -DY, 0));
    const cuffDir = Hh.clone().sub(F).normalize(), cuff = Hh.clone().sub(cuffDir.clone().multiplyScalar(.012));
    let d = sdEll(x, y, z, a.U.clone().add(V(-a.sd * .03, -.04 - DY, 0)), V(.07, .075, .07));
    if (SHORT_SLEEVES) {                                                               // T-shirt: the sleeve ends half way down the upper arm
      const E = U.clone().lerp(F, .55), dir = F.clone().sub(U).normalize();
      d = smin(d, sdRoundCone(x, y, z, U, E, .068, .066), .03);
      d = smax(d, sdPlane(x, y, z, E, dir), .01);
      return smin(d, sdTorusAxis(x, y, z, E.clone().sub(dir.clone().multiplyScalar(.008)), dir, .058, .012), .008);
    }
    d = smin(d, sdRoundCone(x, y, z, U, F, .064, .062), .03);
    d = smin(d, sdRoundCone(x, y, z, F, cuff, .06, .058), .025);                         // forearm: straight, not a bulb
    return smin(d, sdTorusAxis(x, y, z, cuff, cuffDir, .044, .016), .01);
  };
  // bare arms under short sleeves, bare legs under shorts: one skin piece, bending with the bones
  const limbsSDF = (x, y, z) => { let d = 1e9;
    if (SHORT_SLEEVES) for (const a of arms) { d = Math.min(d, sdRoundCone(x, y, z, a.U.clone().lerp(a.F, .3), a.F, .042, .038)); d = smin(d, sdRoundCone(x, y, z, a.F, a.H, .038, .033), .02); }
    if (SHORTS) for (const l of legs) { d = Math.min(d, sdRoundCone(x, y, z, l.T.clone().lerp(l.S, .5), l.S, .055, .048)); d = smin(d, sdRoundCone(x, y, z, l.S, l.F.clone().add(V(0, .04, 0)), .048, .036), .02); }
    return d + lumps(x, y, z, .4); };
  const belly = (d, x, y, z) => BELLY ? smin(d, sdEll(x, y, z, V(0, .6, .03), V(.16 + .03 * BELLY, .14, .13 + .07 * BELLY)), .06) : d;
  const torsoSDF = (x, y, z) => { y -= DY;
    const d = smax(belly(sdRoundCone(x / 1.08, y, z / .8, V(0, .45, 0), V(0, .88, 0), .175, .13) * .8, x, y, z), .5 - y, .03);
    return smin(d, sdTorusAxis(x, y, z, V(0, 1.06, -.025), V(0, .8, .6), .115, .056), .035);
  };
  // ---- the hoodie: torso, hem, hood roll, hood, shoulders, sleeves (wider at the cuff), cuffs, pocket: ONE piece
  const hoodSDF = (x, y, z) => { y -= DY;
    let d = sdRoundCone(x / 1.08, y, z / .8, V(0, .45, 0), V(0, .88, 0), .175, .13) * .8;                 // narrower at the top: sloping shoulders
    d = belly(d, x, y, z);
    d = smax(d, .5 - y, .03);                                                                                   // flat-bottomed, like a real hoodie
    d = smin(d, sdTorusY(x, y, z, V(0, .505, 0), .15, .03, 1.03, .82), .025);                               // ribbed hem
    if (TOP === 'hoodie') {
      d = smin(d, sdTorusAxis(x, y, z, V(0, 1.06, -.025), V(0, .8, .6), .115, .056), .035);                  // hood roll
      d = smin(d, sdEll(x, y, z, V(0, .95, -.085), V(.085, .065, .045)), .04);                                // the hood behind
    } else {
      d = smin(d, sdTorusY(x, y, z, V(0, .99, .005), .082, .028, 1, .95), .03);                               // thick knitted collar, sitting on the shoulders
    }
    for (const a of arms) d = smin(d, sleeveSDF(a, x, y, z), .03);
    if (TOP === 'hoodie') {
      d = smin(d, sdRoundBox(x, y, z, V(0, .615, .118), V(.085, .042, .006), .012), .012);                     // pocket
      d = smax(d, -sdCapsule(x, y, z, V(-.085, .657, .135), V(.085, .657, .135), .005), .004);                 // its top seam
    }
    if (TOP === 'cardigan') d = smax(d, -sdCapsule(x, y, z, V(0, .5, .142 + .07 * BELLY), V(0, 1.0, .108), .006), .005);      // the opening down the front
    return d + lumps(x, y, z);
  };
  // ---- trousers: pelvis + two straight legs + hems: ONE piece
  const pantsSDF = (x, y, z) => {
    let d = sdEll(x, y, z, V(0, .6 + DY, 0), V(.16, .075, .114));
    for (const l of legs) {
      const ankle = l.F.clone().add(V(0, .05, 0));
      d = smin(d, sdCapsule(x, y, z, l.T.clone().add(V(0, .02, 0)), l.S, .073), .03);
      d = smin(d, sdRoundCone(x, y, z, l.S, ankle, .072, .075), .02);
      d = smin(d, sdTorusY(x, y, z, ankle.clone().add(V(0, .01, 0)), .072, .011), .01);
    }
    d = smax(d, y - (.56 + DY), .02);                // nothing above the hoodie hem (+.06): it could only poke through the hoodie
    if (SHORTS) { const ky = legs[0].S.y + .1; d = smax(d, ky - y, .015); for (const l of legs) d = smin(d, sdTorusY(x, y, z, V(l.S.x, ky + .012, l.S.z), .078, .012), .01); }
    return d + lumps(x, y, z, .9);
  };
  const skinIt = (geo, mat, boneSets, groups = null) => {
    const bones = [hips, chest, neck, head, ...arms.flatMap(a => [a.up, a.fo, a.hand]), ...legs.flatMap(l => [l.th, l.sh, l.ft])];
    const segs = bones.map(b => { const p = W(b); const c = b.children.find(ch => ch.isBone); return [p, c ? W(c) : p.clone().add(V(0, -.07, 0))]; });
    const allowed = boneSets.map(b => bones.indexOf(b));
    // distance to each bone's SURFACE (minus its thickness), so a thin arm does not pull the side of a thick torso
    const rad = [.15, .16, .06, .12, ...arms.flatMap(() => [.07, .065, .05]), ...legs.flatMap(() => [.075, .07, .05])];
    const pos = geo.attributes.position, n = pos.count, si = new Uint16Array(n * 4), sw = new Float32Array(n * 4), p = V(0, 0, 0);
    if (!geo.attributes.skinIndex) {                    // a copy of a character built before already has its weights
    for (let i = 0; i < n; i++) {
      p.set(pos.getX(i), pos.getY(i), pos.getZ(i));
      const inv = k => 1 / Math.pow(Math.max(segDist(p, segs[k][0], segs[k][1]) - rad[k], .004), 4);
      let w;
      if (groups) {                                     // each group shares out its part of the weight by distance
        w = [];
        for (const [list, share] of groups(p)) { if (share < 1e-3) continue; const ks = list.map(b => bones.indexOf(b)), ws = ks.map(inv), t = ws.reduce((a, b) => a + b, 0);
          ks.forEach((k, j) => w.push([k, share * ws[j] / t])); }
        w = w.sort((a, b) => b[1] - a[1]).slice(0, 4);
      } else w = allowed.map(k => [k, inv(k)]).sort((a, b) => b[1] - a[1]).slice(0, 4);
      const s = w.reduce((a, b) => a + b[1], 0); w.forEach(([k, v], j) => { si[i * 4 + j] = k; sw[i * 4 + j] = v / s; });
    }
    geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
    }
    const m = new THREE.SkinnedMesh(geo, mat); m.castShadow = m.receiveShadow = true; m.frustumCulled = false;
    root.add(m); m.bind(new THREE.Skeleton(bones), m.matrixWorld); return m;
  };
  // each hoodie vertex is torso or sleeve depending on which shape's surface it is on; a soft band at the armpit seam
  const sstep = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
  skinIt(meshSDF(hoodSDF, V(0, .76 + DY, 0), .62, 190), M.hood,   // box wide enough for the cuffs in the arms-out building pose (at .54 they were cut off)
    [hips, chest], p => {
    const dt = torsoSDF(p.x, p.y, p.z), ds = arms.map(a => sleeveSDF(a, p.x, p.y - DY, p.z));
    const k = ds[0] < ds[1] ? 0 : 1, t = sstep(-.025, .025, dt - ds[k]), a = arms[k];
    return [[[hips, chest], 1 - t], [[a.up, a.fo], t]];      // not the hand: a sleeve does not turn with the wrist
  });
  // trousers: what is hidden under the hoodie stays on the hips, so a lifted thigh cannot push it out through the hem;
  // the thigh takes over only below the hem (soft band of .12)
  const HEM = .5 + DY;
  skinIt(meshSDF(pantsSDF, V(0, .4 + DY / 2, 0), .38, 112), M.pants, [hips], p => {
    const l = legs[p.x < 0 ? 0 : 1], t = sstep(HEM - .035, HEM - .15, p.y);
    return [[[hips], 1 - t], [[l.th, l.sh, l.ft], t]];
  });
  if (SHORT_SLEEVES || SHORTS) skinIt(meshSDF(limbsSDF, V(0, .5 + DY / 2, 0), .55, 140), M.skin, [hips, ...arms.flatMap(a => [a.up, a.fo, a.hand]), ...legs.flatMap(l => [l.th, l.sh, l.ft])]);
  if (o.stripes) { M.hood.map = stripes(o.stripes, o.hood || 0xcf9132); M.hood.color.set(0xffffff); }
  const rigid = (sdf, center, half, res, mat, parent) => { const m = new THREE.Mesh(meshSDF(sdf, center, half, res), mat); m.castShadow = m.receiveShadow = true; parent.add(m); return m; };

  // ---- drawstrings (thin, hang from the hood roll)
  if (TOP === 'hoodie') for (const x of [-.034, .034]) {
    const c = new THREE.CatmullRomCurve3([V(x, 1.03, .118), V(x * 1.08, .96, .14), V(x * 1.04, .9, .138)]);
    const m = new THREE.Mesh(new THREE.TubeGeometry(c, 16, .007, 8), M.hood); m.position.y = -.59; chest.add(m);
    const k = new THREE.Mesh(new THREE.SphereGeometry(.011, 10, 8), M.hood); k.position.set(x * 1.04, .9 - .59, .138); chest.add(k);
  }
  if (TOP === 'cardigan') for (let i = 0; i < 4; i++) {                     // buttons down the opening (chest space: y - .59 - DY)
    const yb = .93 - i * .12, zb = .112 + (.142 + .07 * BELLY - .112) * (i / 3);
    const k = new THREE.Mesh(new THREE.SphereGeometry(.014, 12, 8).scale(1, 1, .5), M.button); k.position.set(.014, yb - .59, zb + .006); chest.add(k);
  }
  // ---- skirt: one piece from the waist, flaring to below the knee, over the legs (which become tights)
  if (BOTTOM === 'skirt') {
    const skirtSDF = (x, y, z) => {
      let d = sdRoundCone(x, y, z / .85, V(0, .64 + DY, 0), V(0, .2 + DY * .5, 0), .165 + .02 * BELLY, .24) ;
      d = smax(d, (.2 + DY * .5) - y, .02);                                        // flat hem
      d = smax(d, y - (.6 + DY), .02);                                             // starts under the top
      return d + lumps(x, y, z, .9);
    };
    const ks = .5 + DY / 2;
    skinIt(meshSDF(skirtSDF, V(0, ks, 0), .4, 100), M.skirt, [hips], p => {   // follows the hips; the front of the hem a little with the thighs
      const t = Math.max(0, Math.min(1, (ks - p.y) / .3)) * .45, l = legs[p.x < 0 ? 0 : 1];
      return [[[hips], 1 - t], [[l.th], t]];
    });
  }
  // ---- head and hair (in a scaled space so the face pieces keep the v2 numbers)
  const hs = G(head, [0, .03, 0]); hs.scale.setScalar(HEAD);
  // round face like the sheet: a ball, fuller at the cheeks, chin at -.13, then a thin neck (sheet: neck = .34 face widths)
  const skinSDF = (x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.01, 0), V(.12, .122, .124));
    for (const sd of [-1, 1]) d = smin(d, sdEll(x, y, z, V(sd * .036, -.05, .05), V(.07, .07, .066)), .05);      // cheeks: full, but a round jaw
    return smin(d, sdCapsule(x, y, z, V(0, -.22, -.01), V(0, -.1, -.01), .036), .015);
  };
  rigid((x, y, z) => skinSDF(x, y, z) + lumps(x, y, z, .5), V(0, -.05, 0), .2, 88, M.skin, hs);
  // hair: a girl's hair in clay, not a cap. A thin layer over the skull with a side parting, side-swept bangs made of a few
  // soft locks, long side hair framing the face down to the shoulders, strand grooves pressed in
  const PART = .035;                                                                       // the parting, on her left
  const lock = (x, y, z, a, b, r1, r2) => sdRoundCone(x, y, z, V(...a), V(...b), r1, r2);
  if (HAIR === 'haru') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.004, -.012), V(.142, .134, .144));                     // close to the skull: no tall crown
    for (const sd of [-1, 1]) {                                                           // side hair, a little fuller at the ends
      d = smin(d, lock(x, y, z, [sd * .108, .02, -.005], [sd * .122, -.2, .005], .048, .052), .04);
      d = smin(d, lock(x, y, z, [sd * .122, -.2, .005], [sd * .13, -.31, .0], .052, .046), .03);
    }
    const bz = (z + .095) / .72; d = smin(d, sdRoundCone(x / 1.05, y, bz, V(0, -.03, 0), V(0, -.29, 0), .13, .125) * .72, .03);   // the back
    d = smax(d, -sdEll(x, y, z, V(0, -.04, .08), V(.104, .14, .085)), .025);             // the face opening
    // the parting: a shallow groove from the front of the crown to the back
    d = smax(d, -sdCapsule(x, y, z, V(PART, .135, .07), V(PART, .14, -.09), .006), .006);
    // side-swept bangs: locks from the parting over the forehead, most of them to her right, ends above the brows
    const P0 = [PART - .004, .106, .058];                                                  // starts inside the crown: no peak
    let bangs = lock(x, y, z, P0, [-.082, .05, .098], .024, .017);
    bangs = smin(bangs, lock(x, y, z, P0, [-.038, .058, .118], .024, .018), .012);
    bangs = smin(bangs, lock(x, y, z, P0, [.006, .066, .122], .023, .017), .012);
    bangs = smin(bangs, lock(x, y, z, [PART + .008, .104, .055], [.082, .058, .1], .022, .016), .012);
    d = smin(d, bangs, .02);
    // the back: long locks separated by grooves on the back surface (the back shape is a cone of radius .13 squashed to .72 in z,
    // centred at z -.095), with rounded lock ends at the bottom, a little uneven
    const backZ = gx => -.095 - .72 * Math.sqrt(Math.max(0, .0169 - (gx / 1.05) ** 2));
    for (const k of [-2, -1, 0, 1, 2]) { const gx = k * .042, zs = backZ(gx);
      if (k) d = smax(d, -sdCapsule(x, y, z, V(gx, .03, zs + .001), V(gx * 1.05, -.28, zs + .001), .008), .006);
      const ex = gx + .021; if (Math.abs(k) < 2 || k === -2) d = smin(d, sdEll(x, y, z, V(ex, -.305 - ((k + 2) % 2) * .012, backZ(ex) + .012), V(.022, .02, .018)), .018); }
    // strand grooves on the side hair
    for (const sd of [-1, 1]) for (const k of [0, 1]) {
      const ang = k ? 1.35 : .8, ox = Math.sin(ang) * .05, oz = Math.cos(ang) * .05;      // on the surface, front-outer side
      d = smax(d, -sdCapsule(x, y, z, V(sd * (.11 + ox), -.04, oz), V(sd * (.126 + ox), -.27, oz), .0035), .004);
    }
    return d + lumps(x, y, z, .7);
  }, V(0, -.1, -.02), .28, 112, M.hair, hs).scale.z = .97;
  // bun: pulled back tight over the skull, a round bun at the back, combed grooves running to it (Mum)
  if (HAIR === 'bun') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, .0, -.012), V(.134, .132, .14));
    d = smax(d, -sdEll(x, y, z, V(0, -.06, .08), V(.106, .15, .09)), .02);              // face opening (hair line high on the forehead)
    d = smax(d, (z < -.04 ? -.12 : -.07) - y, .02);                                      // ends at the ears, lower at the nape
    d = smin(d, sdEll(x, y, z, V(0, .07, -.15), V(.068, .062, .06)), .025);              // the bun
    return d + lumps(x, y, z, .7);
  }, V(0, .0, -.04), .23, 100, M.hair, hs);
  // horseshoe: bald on top, a short band of hair round the back and the sides (Grandpa)
  if (HAIR === 'horseshoe') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.012, -.015), V(.14, .136, .146));
    d = smax(d, y - (.05 - .02 * Math.max(0, -z) / .13), .02);                          // the top is bare
    d = smax(d, -(y + .085), .02);                                                       // down to the nape
    d = smax(d, z - .03, .02);                                                           // only behind the ears
    return d + lumps(x, y, z, 1.1);
  }, V(0, -.03, -.03), .2, 90, M.hair, hs);
  // ponytail: pulled back over the skull to a hair tie, a long tail down the back, a short side-swept fringe (a friend of Haru)
  if (HAIR === 'ponytail') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.004, -.012), V(.138, .134, .142));
    d = smax(d, -sdEll(x, y, z, V(0, -.05, .08), V(.106, .14, .088)), .02);             // face opening
    d = smax(d, (z < -.03 ? -.1 : -.06) - y, .02);                                       // above the ears, lower at the nape
    const tie = V(0, .02, -.155);
    d = smin(d, sdRoundCone(x, y, z, tie, V(0, -.16, -.2), .045, .03), .03);            // the tail
    d = smin(d, sdRoundCone(x, y, z, V(0, -.16, -.2), V(0, -.26, -.17), .03, .016), .02);   // its tip, curling in
    let f = sdRoundCone(x, y, z, V(.04, .1, .07), V(-.07, .055, .108), .022, .015);     // fringe: two locks swept to her right
    f = smin(f, sdRoundCone(x, y, z, V(.045, .1, .065), V(-.02, .062, .12), .021, .015), .01);
    d = smin(d, f, .02);
    for (const k of [-1, 0, 1]) d = smax(d, -sdCapsule(x, y, z, V(k * .05, .12, .04), V(k * .015, .06, -.15), .003), .003);   // combed lines
    return d + lumps(x, y, z, .7);
  }, V(0, -.08, -.06), .26, 108, M.hair, hs);
  if (HAIR === 'ponytail') { const t = new THREE.Mesh(new THREE.TorusGeometry(.03, .009, 8, 20), clay3(o.tie || 0xc94a5a, {bumpScale: .4}));
    t.position.set(0, .02, -.16); t.rotation.x = .5; hs.add(t); }
  // short boy's hair: close to the head, messy clay tufts on top, a little fringe
  if (HAIR === 'boyshort') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, .0, -.012), V(.135, .135, .142));
    d = smax(d, -sdEll(x, y, z, V(0, -.06, .085), V(.108, .15, .09)), .02);
    d = smax(d, (z < -.03 ? -.09 : -.035) - y, .02);                                     // short: above the ears
    const tufts = [[.0, .13, .02, -.02, .17, .06], [.06, .12, -.03, .1, .15, .0], [-.06, .12, -.02, -.1, .155, .02], [.03, .11, .07, .04, .07, .12],
                   [-.03, .115, .07, -.05, .07, .115], [.0, .12, -.08, .02, .15, -.11], [-.08, .1, -.07, -.12, .1, -.08], [.08, .1, -.07, .12, .1, -.06]];
    for (const [a, b, c, e, f, g] of tufts) d = smin(d, sdRoundCone(x, y, z, V(a, b, c), V(e, f, g), .03, .012), .02);
    return d + lumps(x, y, z, 1.0);
  }, V(0, .0, -.01), .22, 100, M.hair, hs);
  // curly bob: a soft cap of small curls, jaw length (Grandma)
  if (HAIR === 'curlybob') rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, .005, -.015), V(.15, .145, .152));
    d = smax(d, -sdEll(x, y, z, V(0, -.05, .085), V(.11, .14, .09)), .02);              // face opening
    d = smax(d, -(y + .13), .03);                                                         // jaw length
    let c = 1e9;                                                                          // curls: a ring of small balls on the surface
    for (let i = 0; i < 26; i++) { const a = i / 26 * Math.PI * 2, r = .155;
      for (const yy of [.07, -.01, -.09]) { const cx = Math.sin(a) * r * (yy > 0 ? .9 : 1), cz = Math.cos(a) * r * (yy > 0 ? .9 : 1) - .015;
        if (cz > .06 && yy < .09) continue;                                               // keep the face clear
        c = Math.min(c, Math.hypot(x - cx, y - yy, z - cz) - .03); } }
    d = smin(d, c, .02);
    d = smin(d, sdEll(x, y, z, V(0, .11, .02), V(.11, .05, .12)), .03);                  // the top
    return d + lumps(x, y, z, 1.4);
  }, V(0, -.02, -.02), .25, 104, M.hair, hs);
  // ---- hands and shoes (small pieces on their bones)
  // hands: wrist, rounded palm, three separate two-segment fingers curling a little (middle longest), a separate thumb
  const FL = [.026, .029, .024];                               // cartoon hand: three fingers (next to the thumb first) + a thumb
  arms.forEach(a => rigid((x, y, z) => {
    let d = sdCapsule(x, y, z, V(0, .004, 0), V(0, -.02, 0), .015);                                  // wrist
    d = smin(d, sdEll(x, y, z, V(0, -.038, .001), V(.023, .024, .011)), .012);                       // palm: soft and rounded, no block inside
    d = smin(d, sdCapsule(x, y, z, V(-.015 * a.sd, -.054, .002), V(.015 * a.sd, -.054, .002), .0085), .008);   // the knuckle row the fingers grow from
    let fingers = 1e9;
    for (let i = 0; i < 3; i++) {
      const fx = -a.sd * (-.0135 + i * .0135), L = FL[i], b0 = V(fx, -.057, .001);
      const k1 = V(fx * 1.06, -.057 - L * .55, .004), tip = V(fx * 1.1, -.057 - L, .011);
      fingers = Math.min(fingers, smin(sdCapsule(x, y, z, b0, k1, .0064), sdCapsule(x, y, z, k1, tip, .006), .003));
    }
    d = smin(d, fingers, .005);
    const t0 = V(a.sd * .016, -.03, .006), t1 = V(a.sd * .03, -.046, .014), t2 = V(a.sd * .034, -.062, .019);   // thumb: palms face forward (+z), so the thumb is on the OUTER side; left and right hands mirror
    d = smin(d, smin(sdCapsule(x, y, z, t0, t1, .0075), sdCapsule(x, y, z, t1, t2, .0066), .003), .007);
    return d + lumps(x, y, z, .25);
  }, V(0, -.045, .005), .068, 104, M.skin, a.hand).scale.setScalar(1.45));
  // shoes: a rounded clay sneaker. Upper = toe cap + heel blended, a tongue and a padded collar round the ankle; the sole follows
  // the shoe's own outline (a slice of the upper, a little wider), no flat plate under it. Sole bottom stays at y -.051 (as before).
  const shoeUpper = (x, y, z) => {
    let d = smin(sdEll(x, y, z, V(0, -.014, .072), V(.055, .034, .07)), sdEll(x, y, z, V(0, -.01, -.03), V(.05, .038, .052)), .035);
    d = smin(d, sdEll(x, y, z, V(0, .012, .03), V(.034, .022, .045)), .015);                   // tongue
    d = smin(d, sdTorusY(x, y, z, V(0, .026, -.012), .036, .011, 1, 1.15), .012);           // padded collar round the ankle
    return smax(d, -(y + .036), .006);                                                     // the upper stops where the sole begins
  };
  const shoeSole = (x, y, z) => smax(shoeUpper(x, -.03, z) - .0035, Math.abs(y + .0405) - .0105, .006);   // overlaps the upper: no gap at the toe
  legs.forEach(l => {
    rigid((x, y, z) => {
      let d = shoeUpper(x, y, z);
      for (let i = 0; i < 3; i++) d = smax(d, -sdCapsule(x, y, z, V(-.018, .03 - i * .006, .03 + i * .018), V(.018, .03 - i * .006, .03 + i * .018), .0028), .003);   // laces
      return d + lumps(x, y, z, .3);
    }, V(0, -.01, .02), .13, 64, M.shoe, l.ft).scale.set(1.3, 1.2, 1.25);
    rigid((x, y, z) => shoeSole(x, y, z) + lumps(x, y, z, .15), V(0, -.04, .02), .13, 64, M.sole, l.ft).scale.set(1.3, 1.2, 1.25);
  });

  // ---- face pieces (same as v2)
  const add = (geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0]) => { const m = new THREE.Mesh(geo, mat); m.position.set(...pos); m.rotation.set(...rot); m.castShadow = true; parent.add(m); return m; };
  const tube = (pts, r) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => V(...p))), 24, r, 8, false);
  const capTube = (pts, r, mat, parent) => { const g = G(parent); add(tube(pts, r), mat, g); for (const p of [pts[0], pts[pts.length - 1]]) add(new THREE.SphereGeometry(r, 10, 8), mat, g, p); return g; };
  const Sph = (r, sx, sy, sz) => new THREE.SphereGeometry(r, 24, 16).scale(sx, sy, sz);
  const face = G(hs, [0, -.02, .117]); face.scale.setScalar(1.18);
  // where the skin is at a face point (face units): march in from the front; pieces are placed ON the round face
  const FS = 1.18, onSkin = (xf, yf, lift = 0) => { const X = xf * FS, Y = -.02 + yf * FS; let z = .2;
    for (let i = 0; i < 80 && skinSDF(X, Y, z) > .0005; i++) z -= Math.max(skinSDF(X, Y, z), .001);
    return (z - .117) / FS + lift; };
  // sheet (neutral, front), in face widths: eyes .108 wide, .43 apart; brows .17 long, .04 thick, .16 above the eyes;
  // nose .108, .16 below the eyes; mouth .18 wide, .32 below the eyes
  const EYE = o.eyeSize || 1;                                                      // adults: smaller eyes read older
  const EY = .002, EX = .04, BROW_Y = EY + .03;
  const eyes = [], whites = [], lids = [], squeeze = [], brows = [], halfLids = [];
  for (const sd of [-1, 1]) {
    const x = sd * EX, zs = onSkin(x, EY);
    whites.push(add(Sph(.016 * EYE, 1, 1.08, .5), M.white, face, [x, EY + .002, zs - .002]));
    eyes.push(add(new THREE.SphereGeometry(.0105 * EYE, 16, 12), M.eye, face, [x, EY, zs + .001]));
    halfLids.push((() => { const g = G(face, [x, EY, zs]); const m = add(new THREE.SphereGeometry(.0125 * EYE, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), M.skin, g, [0, -.001, .001]); m.scale.set(1.12, .95, 1.2);
      capTube([[-.013 * EYE, -.001, .009], [0, -.0012, .0145], [.013 * EYE, -.001, .009]], .0018, M.dark, g); return g; })());   // a skin lid over the top half
    lids.push(capTube([[x - .013, .0, zs + .001], [x, -.004, zs + .004], [x + .013, .0, zs + .001]], .0026, M.dark, face));
    squeeze.push(capTube([[x + sd * .013, .008, zs + .001], [x - sd * .011, .0, zs + .004], [x + sd * .013, -.008, zs + .001]], .0028, M.dark, face));   // > <: points toward the nose
    const b = G(face, [x, BROW_Y, onSkin(x, BROW_Y)]); capTube([[-.016, -.001, 0], [0, .0012, .0015], [.016, -.001, 0]], .0037, M.dark, b); brows.push(b);
  }
  add(Sph(.0105, 1, .92, .85), M.nose, face, [0, -.028, onSkin(0, -.028, .002)]);
  const mouth = G(face, [0, -.058, onSkin(0, -.058, -.001)]); mouth.scale.setScalar(.8);
  const mouths = {
    line: capTube([[-.021, 0, 0], [.021, 0, 0]], .0022, M.dark, mouth),
    smile: capTube([[-.024, .006, 0], [-.012, -.004, .003], [0, -.007, .004], [.012, -.004, .003], [.024, .006, 0]], .003, M.dark, mouth),
    sad: capTube([[-.022, -.006, 0], [0, .004, .004], [.022, -.006, 0]], .003, M.dark, mouth),
    wobble: capTube([...Array(9)].map((_, i) => [-.022 + i * .0055, (i % 2 ? .004 : -.003), .003]), .0028, M.dark, mouth),
    o: (() => { const g = G(mouth); add(Sph(.011, 1, 1.15, .4), M.mouthIn, g); return g; })(),
    open: (() => { const g = G(mouth, [0, -.006, 0]); add(Sph(.034, 1.1, .8, .4), M.mouthIn, g); add(Sph(.02, 1.2, .5, .4), M.tongue, g, [0, -.014, .006]); add(new THREE.BoxGeometry(.04, .009, .006), M.teeth, g, [0, .017, .008]); return g; })(),
    // talking shapes (swapped like replacement mouths in stop motion; no teeth except F, so the teeth don't flash all the time): A open, E wide with teeth, O round, U small, M pressed, F teeth on lip
    vA: (() => { const g = G(mouth, [0, -.004, 0]); add(Sph(.022, 1.1, .75, .4), M.mouthIn, g); add(Sph(.012, 1.2, .5, .4), M.tongue, g, [0, -.009, .005]); return g; })(),
    vE: (() => { const g = G(mouth); add(Sph(.026, 1.15, .32, .4), M.mouthIn, g); return g; })(),
    vO: (() => { const g = G(mouth, [0, -.002, 0]); add(Sph(.015, 1, 1.2, .4), M.mouthIn, g); return g; })(),
    vU: (() => { const g = G(mouth); add(Sph(.009, 1, 1.1, .4), M.mouthIn, g); return g; })(),
    // C: open for EH/AE, mid between E and A; D: wide open for AA
    vC: (() => { const g = G(mouth, [0, -.002, 0]); add(Sph(.024, 1.1, .5, .4), M.mouthIn, g); add(Sph(.011, 1.2, .4, .4), M.tongue, g, [0, -.006, .005]); return g; })(),
    vD: (() => { const g = G(mouth, [0, -.007, 0]); add(Sph(.027, 1.05, 1.0, .4), M.mouthIn, g); add(Sph(.015, 1.2, .55, .4), M.tongue, g, [0, -.014, .006]); return g; })(),
    vM: capTube([[-.019, .001, 0], [0, -.001, .002], [.019, .001, 0]], .0034, M.dark, mouth),
    vF: (() => { const g = G(mouth); capTube([[-.018, -.004, 0], [.018, -.004, 0]], .0026, M.dark, g); add(new THREE.BoxGeometry(.022, .006, .006), M.teeth, g, [0, .001, .006]); return g; })(),
  };
  // ---- age: creases (forehead lines, smile lines, crow's feet) pressed into the clay, in a darker skin tone
  if (AGE > 0) {
    const crease = (pts, r = .0016) => capTube(pts.map(([x, y]) => [x, y, onSkin(x, y, .0004)]), r * (.6 + .4 * AGE), M.crease, face);
    for (const k of [0, 1]) crease([[-.04, .058 + k * .012], [0, .062 + k * .012], [.04, .058 + k * .012]]);
    for (const sd of [-1, 1]) {
      crease([[sd * .03, -.035], [sd * .036, -.05], [sd * .033, -.064]]);                // smile lines
      if (AGE > .5) crease([[sd * .062, .01], [sd * .07, .004]]), crease([[sd * .062, -.004], [sd * .07, -.008]]);   // crow's feet
    }
  }
  if (o.glasses) for (const sd of [-1, 1]) {                                            // round wire glasses
    const z0 = onSkin(sd * EX, EY) + .012;
    const rim = new THREE.Mesh(new THREE.TorusGeometry(.019, .0022, 8, 28), M.rim); rim.position.set(sd * EX, EY, z0); face.add(rim);
    const lens = new THREE.Mesh(new THREE.CircleGeometry(.019, 24), M.lens); lens.position.set(sd * EX, EY, z0); face.add(lens);
    if (sd > 0) capTube([[-EX + .019, EY + .002, z0], [0, EY + .006, z0 + .002], [EX - .019, EY + .002, z0]], .0018, M.rim, face);
    capTube([[sd * (EX + .019), EY, z0], [sd * .098, EY + .004, z0 - .04], [sd * .1, EY + .002, z0 - .09]], .0018, M.rim, face);   // arms to the ears
  }
  const tears = G(face);
  for (const sd of [-1, 1]) for (let i = 0; i < 3; i++) add(Sph(.0055 - i * .0008, 1, 1.4, .6), M.tear, tears, [sd * .044, -.016 - i * .016, onSkin(sd * .044, -.016 - i * .016, .002)]);
  const sweat = G(hs, [.088, .03, .1]); add(Sph(.014, 1, 1.5, .7), M.sweat, sweat);

  const Pp = {root, hips, chest, neck, head, face, arms, legs, M};
  // eyes: open | wide | closed | squeeze | half (heavy lids: sleepy, suspicious, dead tired)
  Pp.eyes = s => { Pp._eyes = s; const open = s === 'open' || s === 'wide' || s === 'half'; halfLids.forEach(l => l.visible = s === 'half');
    eyes.forEach(e => { e.visible = open; e.scale.setScalar(s === 'wide' ? .9 : 1); }); whites.forEach(w => w.visible = s === 'wide');
    lids.forEach(l => l.visible = s === 'closed'); squeeze.forEach(l => l.visible = s === 'squeeze'); };
  Pp.brows = (k, lift = 0) => brows.forEach((b, i) => { const sd = i ? 1 : -1; b.rotation.z = -sd * k * .45; b.position.y = BROW_Y + lift * .008 + Math.abs(k) * .0025; });
  Pp.mouth = s => { Pp._mouth = s; for (const [k, m] of Object.entries(mouths)) m.visible = k === s; };
  const showMouth = s => { for (const [k, m] of Object.entries(mouths)) m.visible = k === s; };
  // ---- lip sync from word timings: words = [[text, start, end], ...] (the words.json our voice step makes, for this character's lines).
  // Each 1/12 s shows the mouth for the letter being spoken; between words the expression's own mouth comes back.
  const VIS = c => 'ai'.includes(c) ? 'vA' : c === 'e' || c === 'y' ? 'vE' : c === 'o' ? 'vO' : 'uwq'.includes(c) ? 'vU' :
    'mbp'.includes(c) ? 'vM' : 'fv'.includes(c) ? 'vF' : 'vE';
  Pp.talk = (words, t) => {
    const q = Math.floor(t * 12) / 12;
    const w = words.find(w => q >= w[1] && q < w[2]);
    if (!w) { showMouth(Pp._mouth); return false; }
    const L = String(w[0]).toLowerCase().replace(/[^a-z]/g, '') || 'a', p = (q - w[1]) / Math.max(.05, w[2] - w[1]);
    let c = L[Math.min(L.length - 1, Math.floor(p * L.length))];
    if (p > .85 && 'mbp'.includes(L[L.length - 1])) c = L[L.length - 1];             // a word ending in m/b/p closes the lips
    showMouth(VIS(c)); return true;
  };
  // ---- lip sync from Rhubarb Lip Sync (github.com/DanielSWolf/rhubarb-lip-sync), better than letters: it listens to the audio.
  // cues = its JSON "mouthCues": [{start, end, value}] with the standard shapes A..H, X. Run on the PC:
  //   rhubarb -f json -r phonetic --dialogFile line.txt line.wav > line_mouth.json   (then add the line's start time to every cue)
  // A closed (M B P), B slightly open teeth, C open (EH), D wide (AA), E round (AO), F puckered (OO W), G teeth on lip (F V), H tongue (L)
  const RHUBARB = {A: 'vM', B: 'vE', C: 'vC', D: 'vD', E: 'vO', F: 'vU', G: 'vF', H: 'vC', X: null};
  Pp.talkCues = (cues, t) => {
    const q = Math.floor(t * 12) / 12, c = cues.find(c => q >= c.start && q < c.end), m = c && RHUBARB[c.value];
    if (!m) { showMouth(Pp._mouth); return false; }
    showMouth(m); return true;
  };
  // ---- blinking: two stop-motion frames with the eyes shut every 2 to 5 s (each character on its own rhythm)
  const seed = (o.seed !== undefined ? o.seed : JSON.stringify(o).length) * 7.31;
  Pp.blink = t => {
    const q = Math.floor(t * 12);                                                        // stop-motion frame
    let k = 0, at = (Math.sin(seed) * .5 + .5) * 2;                                     // first blink time
    while (at * 12 < q - 2) { k++; at += 2 + 3 * (Math.sin(seed + k * 12.9898) * .5 + .5); }
    const shut = q >= Math.floor(at * 12) && q < Math.floor(at * 12) + 2 && (Pp._eyes === 'open' || Pp._eyes === 'wide' || Pp._eyes === 'half');
    const s = Pp._eyes;
    if (shut) { eyes.forEach(e => e.visible = false); whites.forEach(w => w.visible = false); halfLids.forEach(l => l.visible = false); lids.forEach(l => l.visible = true); }
    else Pp.eyes(s);
    return shut;
  };
  Pp.tears = on => tears.visible = on; Pp.sweat = on => sweat.visible = on;
  Pp.expr = name => {
    Pp.tears(false); Pp.sweat(false);
    const E = {neutral: ['open', 0, 0, 'line'], nervous: ['open', .5, .2, 'wobble'], curious: ['open', .25, .4, 'sad'], smile: ['open', -.1, .2, 'smile'],
      tired: ['half', .15, -.2, 'line'], suspicious: ['half', -.45, -.3, 'line'],
      scared: ['wide', .5, 1, 'open'], scream: ['squeeze', -.6, -.2, 'open'], cry: ['open', .8, .1, 'wobble'], whisper: ['open', .35, .3, 'o']}[name] || ['open', 0, 0, 'line'];
    Pp.eyes(E[0]); Pp.brows(E[1], E[2]); Pp.mouth(E[3]);
    if (name === 'nervous') Pp.sweat(true); if (name === 'cry') Pp.tears(true);
    mouths.open.scale.setScalar(name === 'scared' ? .62 : 1);
    if (name === 'curious') { brows[0].rotation.z = .1; brows[1].rotation.z = .45; brows[1].position.y += .008; }
  };
  Pp.stoop = AGE * .22;                                     // older characters lean forward a little
  Pp.rest = () => { chest.rotation.x = Pp.stoop; neck.rotation.x = -Pp.stoop * .6; arms.forEach(a => { a.up.rotation.set(0, 0, a.sd * .24); a.fo.rotation.set(-.08, 0, 0);
    a.hand.rotation.set(-.12, -a.sd * Math.PI / 2, 0); });   // relaxed: palms face the thighs, thumbs forward, fingers curling a little
    legs.forEach(l => { l.th.rotation.set(0, 0, 0); l.sh.rotation.set(0, 0, 0); l.ft.rotation.set(0, 0, 0); }); };
  Pp.expr('neutral'); Pp.rest();
  root.scale.setScalar(HEIGHT);                            // last: everything above was built at size 1
  return Pp;
}
