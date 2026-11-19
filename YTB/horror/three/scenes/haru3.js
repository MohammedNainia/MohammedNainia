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
function meshSDF(sdf, center, half, res) {
  const mc = new MarchingCubes(res, new THREE.MeshBasicMaterial(), false, false, 220000);
  const f = mc.field, h = res / 2, K = 4000;
  for (let z = 0; z < res; z++) for (let y = 0; y < res; y++) for (let x = 0; x < res; x++) {
    const px = center.x + (x - h) / h * half, py = center.y + (y - h) / h * half, pz = center.z + (z - h) / h * half;
    f[x + y * res + z * res * res] = 80 - sdf(px, py, pz) * K;
  }
  mc.update();
  const n = mc.count, pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2);
  for (let i = 0; i < n; i++) {
    const px = center.x + mc.positionArray[i * 3] * half, py = center.y + mc.positionArray[i * 3 + 1] * half, pz = center.z + mc.positionArray[i * 3 + 2] * half;
    pos[i * 3] = px; pos[i * 3 + 1] = py; pos[i * 3 + 2] = pz;
    let nx = mc.normalArray[i * 3], ny = mc.normalArray[i * 3 + 1], nz = mc.normalArray[i * 3 + 2]; const l = Math.hypot(nx, ny, nz) || 1;
    nx /= l; ny /= l; nz /= l; nor[i * 3] = nx; nor[i * 3 + 1] = ny; nor[i * 3 + 2] = nz;
    const ax = Math.abs(nx), ay = Math.abs(ny), az = Math.abs(nz), s = 5;              // box projection for the clay detail texture
    if (ax >= ay && ax >= az) { uv[i * 2] = pz * s; uv[i * 2 + 1] = py * s; } else if (ay >= az) { uv[i * 2] = px * s; uv[i * 2 + 1] = pz * s; } else { uv[i * 2] = px * s; uv[i * 2 + 1] = py * s; }
  }
  mc.geometry.dispose();
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return g;
}

// ---------------------------------------------------------------- clay surface: fingerprints, tool marks, pits, mottling
function canvas(n, draw) { const c = document.createElement('canvas'); c.width = c.height = n; draw(c.getContext('2d'), n); return c; }
let rs = 11; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
const detailC = canvas(1024, (g, n) => {
  g.fillStyle = '#808080'; g.fillRect(0, 0, n, n);
  for (let k = 0; k < 70; k++) { const cx = rnd() * n, cy = rnd() * n, m = 8 + rnd() * 10, ro = rnd() * 3, sx = .7 + rnd() * .5;   // fingerprints
    for (let i = 0; i < m; i++) { const v = i % 2 ? 70 : 190; g.strokeStyle = `rgba(${v},${v},${v},.22)`; g.lineWidth = 1.3;
      g.beginPath(); g.ellipse(cx, cy, 3 + i * 2.6, (3 + i * 2.6) * sx, ro, 0, 6.3); g.stroke(); } }
  for (let k = 0; k < 160; k++) { const x = rnd() * n, y = rnd() * n, a = rnd() * 6.3, L = 20 + rnd() * 70;                    // tool smears
    const gr = g.createLinearGradient(x, y, x + Math.cos(a) * L, y + Math.sin(a) * L); gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(.5, `rgba(${rnd() < .5 ? 60 : 200},128,128,.18)`); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.strokeStyle = gr; g.lineWidth = 2 + rnd() * 5; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * L, y + Math.sin(a) * L); g.stroke(); }
  for (let k = 0; k < 1600; k++) { const v = rnd() < .6 ? 50 : 210; g.fillStyle = `rgba(${v},${v},${v},.2)`; g.beginPath(); g.arc(rnd() * n, rnd() * n, .6 + rnd() * 1.8, 0, 6.3); g.fill(); }  // pits and specks
});
const mottleC = canvas(512, (g, n) => {
  g.fillStyle = '#f2f2f2'; g.fillRect(0, 0, n, n);
  for (let k = 0; k < 400; k++) { const r = 10 + rnd() * 50, v = 205 + rnd() * 50; const gr = g.createRadialGradient(0, 0, 0, 0, 0, r);
    gr.addColorStop(0, `rgba(${v},${v},${v},.35)`); gr.addColorStop(1, `rgba(${v},${v},${v},0)`); g.save(); g.translate(rnd() * n, rnd() * n); g.fillStyle = gr; g.fillRect(-r, -r, 2 * r, 2 * r); g.restore(); }
});
const tex = c => { const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t; };
const detail = tex(detailC), mottle = tex(mottleC); mottle.colorSpace = THREE.SRGBColorSpace;
export const clay3 = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, map: mottle, bumpMap: detail, bumpScale: 1.8,
  roughness: .86, metalness: 0, sheen: .3, sheenRoughness: .8, sheenColor: new THREE.Color(c).lerp(new THREE.Color(0xffffff), .3)}, o));

// ---------------------------------------------------------------- the puppet
const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); parent.add(g); return g; };
const B = (parent, pos) => { const b = new THREE.Bone(); b.position.set(...pos); if (parent) parent.add(b); return b; };
const segDist = (p, a, b) => { const ab = b.clone().sub(a), t = Math.min(1, Math.max(0, p.clone().sub(a).dot(ab) / ab.lengthSq())); return p.distanceTo(a.clone().add(ab.multiplyScalar(t))); };

export function makeHaru3(o = {}) {
  const M = {
    skin: clay3(o.skin || 0xe39a72, {bumpScale: .9, roughness: .66}), hood: clay3(o.hood || 0xcf9132), pants: clay3(o.pants || 0x5c5b60, {bumpScale: 1.8}),
    shoe: clay3(0xf0eee8, {bumpScale: 1.0}), hair: clay3(o.hair || 0x2a2a2f, {bumpScale: 1.4, roughness: .78, sheen: .35}),
    eye: gloss(0x0a0a0c), white: gloss(0xf6f4ee), dark: clay3(0x2a1a16, {bumpScale: .3}), nose: clay3(0xd98a62, {bumpScale: .6}),
    mouthIn: clay3(0x4a1418, {bumpScale: .2}), tongue: clay3(0xd06a70, {bumpScale: .4}), teeth: gloss(0xfaf6ee),
    tear: new THREE.MeshPhysicalMaterial({color: 0xcfe8ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .75}),
    sweat: new THREE.MeshPhysicalMaterial({color: 0x9fd0ff, roughness: .05, clearcoat: 1, transparent: true, opacity: .85}),
  };
  const root = new THREE.Group();
  // ---- skeleton (bind pose: arms a little out, legs straight)
  const BIND_ARM = .75;                                  // the hoodie is built with the arms held out (A-pose), so the sleeves are
                                                          // separate from the body and lift cleanly; Pp.rest() lowers them to .24
  const DY = .152;                                        // leg lengthening measured against the sheet
  const hips = B(null, [0, .55 + DY, 0]); root.add(hips);
  const chest = B(hips, [0, .04, 0]), neck = B(chest, [0, .44, 0]), head = B(neck, [0, .24, 0]);
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
    d = smin(d, sdRoundCone(x, y, z, U, F, .064, .062), .03);
    d = smin(d, sdRoundCone(x, y, z, F, cuff, .062, .07), .025);
    return smin(d, sdTorusAxis(x, y, z, cuff, cuffDir, .048, .022), .012);
  };
  const torsoSDF = (x, y, z) => { y -= DY;
    const d = smax(sdRoundCone(x / 1.08, y, z / .8, V(0, .45, 0), V(0, .88, 0), .175, .13) * .8, .5 - y, .03);
    return smin(d, sdTorusAxis(x, y, z, V(0, 1.06, -.025), V(0, .8, .6), .115, .056), .035);
  };
  // ---- the hoodie: torso, hem, hood roll, hood, shoulders, sleeves (wider at the cuff), cuffs, pocket: ONE piece
  const hoodSDF = (x, y, z) => { y -= DY;
    let d = sdRoundCone(x / 1.08, y, z / .8, V(0, .45, 0), V(0, .88, 0), .175, .13) * .8;                 // narrower at the top: sloping shoulders
    d = smax(d, .5 - y, .03);                                                                                   // flat-bottomed, like a real hoodie
    d = smin(d, sdTorusY(x, y, z, V(0, .505, 0), .15, .03, 1.03, .82), .025);
    d = smin(d, sdTorusAxis(x, y, z, V(0, 1.06, -.025), V(0, .8, .6), .115, .056), .035);
    d = smin(d, sdEll(x, y, z, V(0, .95, -.085), V(.085, .065, .045)), .04);
    for (const a of arms) d = smin(d, sleeveSDF(a, x, y, z), .03);
    d = smin(d, sdRoundBox(x, y, z, V(0, .615, .118), V(.085, .042, .006), .012), .012);                       // pocket
    d = smax(d, -sdCapsule(x, y, z, V(-.085, .657, .135), V(.085, .657, .135), .005), .004);                   // its top seam
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
    return d + lumps(x, y, z, .9);
  };
  const skinIt = (geo, mat, boneSets, groups = null) => {
    const bones = [hips, chest, neck, head, ...arms.flatMap(a => [a.up, a.fo, a.hand]), ...legs.flatMap(l => [l.th, l.sh, l.ft])];
    const segs = bones.map(b => { const p = W(b); const c = b.children.find(ch => ch.isBone); return [p, c ? W(c) : p.clone().add(V(0, -.07, 0))]; });
    const allowed = boneSets.map(b => bones.indexOf(b));
    // distance to each bone's SURFACE (minus its thickness), so a thin arm does not pull the side of a thick torso
    const rad = [.15, .16, .06, .12, ...arms.flatMap(() => [.07, .065, .05]), ...legs.flatMap(() => [.075, .07, .05])];
    const pos = geo.attributes.position, n = pos.count, si = new Uint16Array(n * 4), sw = new Float32Array(n * 4), p = V(0, 0, 0);
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
    const m = new THREE.SkinnedMesh(geo, mat); m.castShadow = m.receiveShadow = true; m.frustumCulled = false;
    root.add(m); m.bind(new THREE.Skeleton(bones), m.matrixWorld); return m;
  };
  // each hoodie vertex is torso or sleeve depending on which shape's surface it is on; a soft band at the armpit seam
  const sstep = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
  skinIt(meshSDF(hoodSDF, V(0, .76 + DY, 0), .54, 166), M.hood, [hips, chest], p => {
    const dt = torsoSDF(p.x, p.y, p.z), ds = arms.map(a => sleeveSDF(a, p.x, p.y - DY, p.z));
    const k = ds[0] < ds[1] ? 0 : 1, t = sstep(-.025, .025, dt - ds[k]), a = arms[k];
    return [[[hips, chest], 1 - t], [[a.up, a.fo, a.hand], t]];
  });
  // trousers: what is hidden under the hoodie stays on the hips, so a lifted thigh cannot push it out through the hem;
  // the thigh takes over only below the hem (soft band of .12)
  const HEM = .5 + DY;
  skinIt(meshSDF(pantsSDF, V(0, .4 + DY / 2, 0), .38, 112), M.pants, [hips], p => {
    const l = legs[p.x < 0 ? 0 : 1], t = sstep(HEM - .035, HEM - .15, p.y);
    return [[[hips], 1 - t], [[l.th, l.sh, l.ft], t]];
  });
  const rigid = (sdf, center, half, res, mat, parent) => { const m = new THREE.Mesh(meshSDF(sdf, center, half, res), mat); m.castShadow = m.receiveShadow = true; parent.add(m); return m; };

  // ---- drawstrings (thin, hang from the hood roll)
  for (const x of [-.034, .034]) {
    const c = new THREE.CatmullRomCurve3([V(x, 1.03, .118), V(x * 1.08, .96, .14), V(x * 1.04, .9, .138)]);
    const m = new THREE.Mesh(new THREE.TubeGeometry(c, 16, .007, 8), M.hood); m.position.y = -.59; chest.add(m);
    const k = new THREE.Mesh(new THREE.SphereGeometry(.011, 10, 8), M.hood); k.position.set(x * 1.04, .9 - .59, .138); chest.add(k);
  }
  // ---- head and hair (in a scaled space so the face pieces keep the v2 numbers)
  const hs = G(head, [0, .03, 0]); hs.scale.setScalar(1.37);
  rigid((x, y, z) => smin(sdEll(x, y, z, V(0, -.018, 0), V(.124, .14, .128)), sdCapsule(x, y, z, V(0, -.2, 0), V(0, -.1, 0), .04), .03) + lumps(x, y, z, .5),
    V(0, -.05, 0), .2, 80, M.skin, hs);
  rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, .0, -.03), V(.142, .134, .146));
    const fr = V(x + .006, y - .085, z - .01).applyAxisAngle(V(0, 0, 1), .14).applyAxisAngle(V(1, 0, 0), -.5);        // the swept fringe
    d = smin(d, sdEll(fr.x, fr.y, fr.z, V(0, 0, 0), V(.15, .06, .14)), .02);
    for (const sd of [-1, 1]) d = smin(d, sdRoundCone(x, y, z, V(sd * .106, -.02, -.01), V(sd * .114, -.31, .0), .05, .045), .03);   // side panels
    const bz = (z + .095) / .72; d = smin(d, sdRoundCone(x / 1.05, y, bz, V(0, -.03, 0), V(0, -.28, 0), .13, .125) * .72, .03);   // the back
    d = smax(d, -sdEll(x, y, z, V(0, -.04, .08), V(.104, .14, .085)), .025);                                        // the face opening
    return d + lumps(x, y, z, .7);
  }, V(0, -.1, -.02), .28, 112, M.hair, hs).scale.z = .97;
  // ---- hands and shoes (small pieces on their bones)
  arms.forEach(a => rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.035, 0), V(.032, .045, .022));
    for (let k = 0; k < 4; k++) d = smin(d, sdCapsule(x, y, z, V(-.018 + k * .012, -.06, .002), V(-.018 + k * .012, -.082, .004), .0085), .006);
    d = smin(d, sdCapsule(x, y, z, V(-a.sd * .028, -.03, .01), V(-a.sd * .036, -.05, .018), .01), .008);
    return d + lumps(x, y, z, .3);
  }, V(0, -.05, 0), .07, 48, M.skin, a.hand).scale.setScalar(1.45));
  legs.forEach(l => rigid((x, y, z) => {
    let d = sdEll(x, y, z, V(0, -.01, .03), V(.064, .04, .11));
    d = smin(d, sdRoundBox(x, y, z, V(0, -.043, .03), V(.058, .008, .1), .008), .01);
    for (let i = 0; i < 3; i++) d = smax(d, -sdCapsule(x, y, z, V(-.02, .026 - i * .003, .05 + i * .02), V(.02, .026 - i * .003, .05 + i * .02), .003), .003);
    return d + lumps(x, y, z, .3);
  }, V(0, -.01, .03), .13, 56, M.shoe, l.ft).scale.set(1.3, 1.2, 1.25));

  // ---- face pieces (same as v2)
  const add = (geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0]) => { const m = new THREE.Mesh(geo, mat); m.position.set(...pos); m.rotation.set(...rot); m.castShadow = true; parent.add(m); return m; };
  const tube = (pts, r) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map(p => V(...p))), 24, r, 8, false);
  const capTube = (pts, r, mat, parent) => { const g = G(parent); add(tube(pts, r), mat, g); for (const p of [pts[0], pts[pts.length - 1]]) add(new THREE.SphereGeometry(r, 10, 8), mat, g, p); return g; };
  const Sph = (r, sx, sy, sz) => new THREE.SphereGeometry(r, 24, 16).scale(sx, sy, sz);
  const face = G(hs, [0, -.02, .117]); face.scale.setScalar(1.18);
  const eyes = [], whites = [], lids = [], squeeze = [], brows = [];
  for (const sd of [-1, 1]) {
    const x = sd * .046;
    whites.push(add(Sph(.026, 1, 1.08, .4), M.white, face, [x, .004, -.004]));
    eyes.push(add(new THREE.SphereGeometry(.0165, 16, 12), M.eye, face, [x, .002, .004]));
    lids.push(capTube([[x - .02, .0, .004], [x, -.006, .008], [x + .02, .0, .004]], .0035, M.dark, face));
    squeeze.push(capTube([[x - sd * .02, .012, .004], [x + sd * .016, .0, .008], [x - sd * .02, -.012, .004]], .0038, M.dark, face));
    const b = G(face, [x, .042, .0]); capTube([[-.024, -.002, 0], [0, .004, .004], [.024, -.002, 0]], .0052, M.dark, b); brows.push(b);
  }
  add(Sph(.016, 1, .9, .8), M.nose, face, [0, -.03, .014]);
  const mouth = G(face, [0, -.068, .006]);
  const mouths = {
    line: capTube([[-.016, 0, 0], [.016, 0, 0]], .0028, M.dark, mouth),
    smile: capTube([[-.024, .006, 0], [-.012, -.004, .003], [0, -.007, .004], [.012, -.004, .003], [.024, .006, 0]], .003, M.dark, mouth),
    sad: capTube([[-.022, -.006, 0], [0, .004, .004], [.022, -.006, 0]], .003, M.dark, mouth),
    wobble: capTube([...Array(9)].map((_, i) => [-.022 + i * .0055, (i % 2 ? .004 : -.003), .003]), .0028, M.dark, mouth),
    o: (() => { const g = G(mouth); add(Sph(.011, 1, 1.15, .4), M.mouthIn, g); return g; })(),
    open: (() => { const g = G(mouth, [0, -.006, 0]); add(Sph(.034, 1.1, .8, .4), M.mouthIn, g); add(Sph(.02, 1.2, .5, .4), M.tongue, g, [0, -.014, .006]); add(new THREE.BoxGeometry(.04, .009, .006), M.teeth, g, [0, .017, .008]); return g; })(),
  };
  const tears = G(face);
  for (const sd of [-1, 1]) for (let i = 0; i < 3; i++) add(Sph(.0065 - i * .001, 1, 1.4, .6), M.tear, tears, [sd * .052, -.024 - i * .018, .006]);
  const sweat = G(hs, [.088, .03, .1]); add(Sph(.014, 1, 1.5, .7), M.sweat, sweat);

  const Pp = {root, hips, chest, neck, head, face, arms, legs, M};
  Pp.eyes = s => { const open = s === 'open' || s === 'wide';
    eyes.forEach(e => { e.visible = open; e.scale.setScalar(s === 'wide' ? .9 : 1); }); whites.forEach(w => w.visible = s === 'wide');
    lids.forEach(l => l.visible = s === 'closed'); squeeze.forEach(l => l.visible = s === 'squeeze'); };
  Pp.brows = (k, lift = 0) => brows.forEach((b, i) => { const sd = i ? 1 : -1; b.rotation.z = -sd * k * .45; b.position.y = .042 + lift * .01 + Math.abs(k) * .003; });
  Pp.mouth = s => { for (const [k, m] of Object.entries(mouths)) m.visible = k === s; };
  Pp.tears = on => tears.visible = on; Pp.sweat = on => sweat.visible = on;
  Pp.expr = name => {
    Pp.tears(false); Pp.sweat(false);
    const E = {neutral: ['open', 0, 0, 'line'], nervous: ['open', .5, .2, 'wobble'], curious: ['open', .25, .4, 'sad'], smile: ['open', -.1, .2, 'smile'],
      scared: ['wide', .5, 1, 'open'], scream: ['squeeze', -.6, -.2, 'open'], cry: ['open', .8, .1, 'wobble'], whisper: ['open', .35, .3, 'o']}[name] || ['open', 0, 0, 'line'];
    Pp.eyes(E[0]); Pp.brows(E[1], E[2]); Pp.mouth(E[3]);
    if (name === 'nervous') Pp.sweat(true); if (name === 'cry') Pp.tears(true);
    mouths.open.scale.setScalar(name === 'scared' ? .62 : 1);
    if (name === 'curious') { brows[0].rotation.z = .1; brows[1].rotation.z = .45; brows[1].position.y += .008; }
  };
  Pp.rest = () => { arms.forEach(a => { a.up.rotation.set(0, 0, a.sd * .24); a.fo.rotation.set(-.08, 0, 0); a.hand.rotation.set(0, 0, 0); });
    legs.forEach(l => { l.th.rotation.set(0, 0, 0); l.sh.rotation.set(0, 0, 0); l.ft.rotation.set(0, 0, 0); }); };
  Pp.expr('neutral'); Pp.rest();
  return Pp;
}
