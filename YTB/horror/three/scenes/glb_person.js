// A generated 3D character (image-to-3D, e.g. data/glb/haru_rodin.glb) turned into a puppet with the SAME joints as clay.js makePerson:
// root > hips > chest > neck > head, chest > arms[i].up > fo > hand, hips > legs[i].th > sh > ft.
// The joints are THREE.Bones placed from a small rig file (data/glb/<name>.rig.json, positions measured on the mesh), and every vertex is
// skinned to them with automatic weights (by distance to each bone's segment), so pose(), walk(), look() and the scenes' reset() drive it as-is.
// The hips sit at y = .82 in the puppet's own units, like every makePerson character; P.s0 scales it to its height in the world.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {EXPR} from './clay.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export async function makeGlbPerson(name, o = {}) {
  const base = name.includes('/') ? '/data/' + name : '/data/glb/' + name;            // 'haru_blank' (data/glb) or 'lib/chars/mum' (the library)
  const [gl, R] = await Promise.all([new GLTFLoader().loadAsync(base + '.glb'), fetch(base + '.rig.json').then(r => r.json())]);
  gl.scene.updateMatrixWorld(true); let src = null; gl.scene.traverse(m => { if (m.isMesh && !src) src = m; });
  const geo = src.geometry.clone(); geo.applyMatrix4(src.matrixWorld);
  if (R.rot) geo.rotateY(R.rot * Math.PI / 180);                                          // a model that came out facing sideways (glb_autorig.py --rot)
  if (R.note && R.note.startsWith('measured by tools/glb_autorig')) { geo.computeBoundingBox(); const bb = geo.boundingBox; geo.translate(-(bb.min.x + bb.max.x) / 2, 0, -(bb.min.z + bb.max.z) / 2); }   // the auto-rig measured it centred
  // puppet units: the hip joint at .82 above the floor, the floor at 0
  const k = .82 / (R.hip[1] - R.floor), P0 = a => V(a[0] * k, (a[1] - R.floor) * k, a[2] * k);
  geo.translate(0, -R.floor, 0); geo.scale(k, k, k);
  const J = {}; for (const n of ['hip', 'pelvis', 'chestBase', 'neckBase', 'headBase', 'headTop', 'shoulder', 'elbow', 'wrist', 'fingerTip', 'knee', 'ankle', 'toe']) J[n] = P0(R[n]);

  // ---- the skeleton (bones at the measured joints, named like makePerson's groups)
  const B = (parent, at, from) => { const b = new THREE.Bone(); b.position.copy(at.clone().sub(from)); if (parent) parent.add(b); return b; };
  const root = new THREE.Group(), hips = B(null, J.pelvis, V(0, 0, 0)); root.add(hips);
  const chest = B(hips, J.chestBase, J.pelvis), neck = B(chest, J.neckBase, J.chestBase), head = B(neck, J.headBase, J.neckBase);
  const side = (p, s) => V(p.x * s, p.y, p.z);
  const arms = [-1, 1].map(s => {
    const up = B(chest, side(J.shoulder, s), J.chestBase), fo = B(up, side(J.elbow, s), side(J.shoulder, s)), hand = B(fo, side(J.wrist, s), side(J.elbow, s));
    return {up, fo, hand, s};
  });
  const legs = [-1, 1].map(s => {
    const th = B(hips, side(J.hip, s), J.pelvis), sh = B(th, side(J.knee, s), side(J.hip, s)), ft = B(sh, side(J.ankle, s), side(J.knee, s));
    return {th, sh, ft, s};
  });
  // ---- automatic skin weights: each vertex follows the bones whose segments are nearest (inverse distance^4, best 4), with simple region rules:
  // the arms only take vertices out at the sides, the legs only below the hem, the head everything above the chin
  const segs = [
    {b: hips, a: J.pelvis, e: J.chestBase}, {b: chest, a: J.chestBase, e: J.neckBase}, {b: neck, a: J.neckBase, e: J.headBase}, {b: head, a: J.headBase, e: J.headTop},
    ...arms.flatMap(({up, fo, hand, s}) => [{b: up, a: side(J.shoulder, s), e: side(J.elbow, s), arm: s}, {b: fo, a: side(J.elbow, s), e: side(J.wrist, s), arm: s}, {b: hand, a: side(J.wrist, s), e: side(J.fingerTip, s), arm: s}]),
    ...legs.flatMap(({th, sh, ft, s}) => [{b: th, a: side(J.hip, s), e: side(J.knee, s), leg: s}, {b: sh, a: side(J.knee, s), e: side(J.ankle, s), leg: s}, {b: ft, a: side(J.ankle, s), e: side(J.toe, s), leg: s}])];
  const bones = []; segs.forEach(sg => { if (!bones.includes(sg.b)) bones.push(sg.b); sg.i = bones.indexOf(sg.b); });
  // ---- the hair: a bone hanging from the back of the head; long hair (found by its colour in the texture) below ear level follows it,
  // more the lower it hangs, so followFrame() can swing it behind the head and let it settle (P.sec.hair)
  const hairPivot = V(0, J.headBase.y + (J.headTop.y - J.headBase.y) * .3, -.04 * k), hairB = B(head, hairPivot, J.headBase); bones.push(hairB); const HI = bones.length - 1;
  let isHair = null;
  { const map0 = src.material.map, uv = geo.attributes.uv;
    if (map0 && map0.image && uv && R.hair !== false) { const im = map0.image, W = 256, Hh = 256, cv = document.createElement('canvas'); cv.width = W; cv.height = Hh;
      const c2 = cv.getContext('2d'); c2.drawImage(im, 0, 0, W, Hh); const px = c2.getImageData(0, 0, W, Hh).data; isHair = new Uint8Array(geo.attributes.position.count);
      const hc = R.hairColor ? new THREE.Color(R.hairColor) : null;
      for (let v = 0; v < uv.count; v++) { let u = uv.getX(v) % 1, w2 = uv.getY(v) % 1; if (u < 0) u += 1; if (w2 < 0) w2 += 1; if (!map0.flipY) w2 = w2; else w2 = 1 - w2;
        const i = (Math.min(Hh - 1, Math.floor(w2 * Hh)) * W + Math.min(W - 1, Math.floor(u * W))) * 4, r = px[i], g = px[i + 1], b = px[i + 2];
        const lum = .3 * r + .59 * g + .11 * b, sat = Math.max(r, g, b) - Math.min(r, g, b);
        isHair[v] = hc ? (Math.abs(r / 255 - hc.r) + Math.abs(g / 255 - hc.g) + Math.abs(b / 255 - hc.b) < .25) : (lum < 105 && sat < 40) ? 1 : 0; } } }
  const pos = geo.attributes.position, n = pos.count, si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
  // blend zones instead of hard cuts: a vertex in the armpit or at the shoulder cap is part sleeve, part body; at the hem part leg, part hips
  const sm = (a, b, x) => { const t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  const SR0 = .11 * k, SR1 = .17 * k;   // the sleeve's radius (model units .065 measured at the elbow), and where it fades into the body
  const ax0 = Math.abs(J.shoulder.x) * .72, ax1 = Math.abs(J.shoulder.x) * 1.02, hem = J.pelvis.y + .02, chin = J.headBase.y - .02;
  const p = V(0, 0, 0), ab = V(0, 0, 0), ap = V(0, 0, 0), q = V(0, 0, 0);
  const near = (sg) => { ab.copy(sg.e).sub(sg.a); const t = Math.max(0, Math.min(1, ap.copy(p).sub(sg.a).dot(ab) / ab.lengthSq())); q.copy(sg.a).addScaledVector(ab, t); return 1 / Math.max(.006, p.distanceTo(q)) ** 3; };
  const BODY = segs.filter(sg => !sg.arm && !sg.leg), HEADS = BODY.filter(sg => sg.b === head || sg.b === neck), TORSO = BODY.filter(sg => sg.b !== head);
  for (let v = 0; v < n; v++) {
    p.fromBufferAttribute(pos, v); const sd = p.x >= 0 ? 1 : -1, ax = Math.abs(p.x);
    const w = new Map(), put = (list, g) => { if (g <= 0) return; let tot = 0; const r = list.map(sg => { const x = near(sg); tot += x; return [sg.i, x]; }); r.forEach(([i, x]) => w.set(i, (w.get(i) || 0) + g * x / tot)); };
    const fh = sm(chin - .16, chin + .08, p.y) * (ax > ax0 * .9 ? 1 - sm(J.shoulder.y - .05, J.shoulder.y - .25, p.y) : 1);   // how much head: a soft band across the chin and neck, so the hair and neck bend instead of tearing
    if (fh >= .999) put(HEADS.filter(sg => sg.b === head), 1);                                                             // the head and the hair on it
    else {
      put([HEADS.find(sg => sg.b === head)], fh * .7); put([HEADS.find(sg => sg.b === neck)], fh * .3);
      const dArm = Math.min(...segs.filter(sg => sg.arm === sd).map(sg => 1 / Math.cbrt(near(sg))));                     // distance to the arm's centre line
      const fa = sm(ax0, ax1, ax) * (1 - sm(J.shoulder.y + .02, J.shoulder.y + .12, p.y)) * sm(SR1, SR0, dArm);          // how much sleeve: out at the side, and not far from the arm
      const fl = R.skirt ? sm(J.knee.y + .05, J.knee.y - .12, p.y) * sm(.004, .05, ax) * .9 + sm(J.ankle.y + .1, J.ankle.y, p.y) * .1   // a skirt or long coat swings with the hips; only its hem and the legs below it follow the legs
                         : sm(hem + .03, hem - .08, p.y) * sm(.004, .03, ax);                                                // how much leg
      put(segs.filter(sg => sg.arm === sd), fa * (1 - fh));
      put(segs.filter(sg => sg.leg === sd), fl * (1 - fa));
      put(TORSO, (1 - fa) * (1 - fl) * (1 - fh));
    }
    if (isHair && isHair[v] && p.y < hairPivot.y && p.y > J.shoulder.y - .35 * (J.headTop.y - J.headBase.y)) {   // long hair: from the head into the hair bone, more the lower it hangs
      const wh = sm(hairPivot.y - .02, hairPivot.y - .22 * (J.headTop.y - J.headBase.y) / .5, p.y) * .95;
      w.clear(); w.set(HI, wh); w.set(head.userData.i ?? bones.indexOf(head), 1 - wh); }
    const top = [...w.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4), tot = top.reduce((s, c) => s + c[1], 0) || 1;
    top.forEach((c, k2) => { si[v * 4 + k2] = c[0]; sw[v * 4 + k2] = c[1] / tot; });
  }
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
  // ---- the skin: the generator painted it browner than the sheet; shift every skin-coloured texel toward the sheet's peach (the hoodie, hair and trousers stay)
  const m0 = src.material, F = R.face || null;
  let map = m0.map;
  if (map && map.image && F && !R.skinDone) {
    const im = map.image, cv = document.createElement('canvas'); cv.width = im.width; cv.height = im.height; const cx = cv.getContext('2d'); cx.drawImage(im, 0, 0);
    const d = cx.getImageData(0, 0, cv.width, cv.height), a = d.data, tgt = new THREE.Color(F.skinTarget), src0 = [196, 127, 91];   // the measured face skin
    const gain = [tgt.r * 255 / src0[0], tgt.g * 255 / src0[1], tgt.b * 255 / src0[2]];
    for (let i = 0; i < a.length; i += 4) { const r = a[i], g = a[i + 1], b = a[i + 2], br = b / (r || 1);
      if (r > g && g > b && br > .33 && br < .7 && r > 70) { const w = sm(.33, .42, br) * (1 - sm(.6, .7, br)); for (let c = 0; c < 3; c++) a[i + c] = Math.min(255, a[i + c] * (1 + (gain[c] - 1) * w)); } }
    cx.putImageData(d, 0, 0); const t = new THREE.CanvasTexture(cv); t.flipY = map.flipY; t.colorSpace = THREE.SRGBColorSpace; t.wrapS = map.wrapS; t.wrapT = map.wrapT; t.anisotropy = 4; map = t;
  }
  // clay: matte, never metallic (the generator's gloss and metal maps make it plastic), a soft sheen
  const mat = new THREE.MeshPhysicalMaterial({map, normalMap: m0.normalMap, roughness: .88, metalness: 0, sheen: .4, sheenRoughness: .8, sheenColor: new THREE.Color(0xfff0e0), side: m0.side});
  const mesh = new THREE.SkinnedMesh(geo, mat); mesh.castShadow = mesh.receiveShadow = true; mesh.frustumCulled = false;
  const skel = new THREE.Skeleton(bones);
  root.add(mesh); root.updateMatrixWorld(true); mesh.bind(skel);

  // ---- the 2D face: a thin skin layer over the face (covering the painted features), with eyes, brows and a mouth DRAWN on it,
  // redrawn when the expression changes. It is cut from the mesh's own face triangles, so it follows every bump, and skinned like them.
  const FS = 512, fcv = document.createElement('canvas'); fcv.width = fcv.height = FS; const fx = fcv.getContext('2d');
  const ftex = new THREE.CanvasTexture(fcv); ftex.colorSpace = THREE.SRGBColorSpace; ftex.anisotropy = 4;
  let faceMesh = null;
  if (F && F.plate) {
    // the face plate (tools/glb_face_clean.py): a smooth clay shell over the face, laid like a tarp over the sculpted brows and lips;
    // a grid from its height map, skinned like the face under it (all head above the chin, blending into the neck below)
    const {nx, ny, z: hz} = F.plate, chinP = J.headBase.y - .02, verts = [], uvs = [], ind = [], wi = [], ww = [], idmap = new Int32Array(nx * ny).fill(-1);
    const hi = bones.indexOf(head), ni = bones.indexOf(neck), ci = bones.indexOf(chest);
    for (let r = 0; r < ny; r++) for (let c = 0; c < nx; c++) {
      const u = c / (nx - 1), v = r / (ny - 1), mxm = F.x[0] + u * (F.x[1] - F.x[0]), mym = F.y[0] + v * (F.y[1] - F.y[0]);
      if (((u - .5) / .5) ** 2 + ((v - .5) / .5) ** 2 > 1.0) continue;                                  // an oval face
      idmap[r * nx + c] = verts.length / 3; verts.push(mxm * k, (mym - R.floor) * k, hz[r * nx + c] * k); uvs.push(u, v);
      const fh = sm(chinP - .16, chinP + .08, (mym - R.floor) * k); wi.push(hi, ni, ci, 0); ww.push(fh * .7, fh * .3, 1 - fh, 0); }
    for (let r = 0; r < ny - 1; r++) for (let c = 0; c < nx - 1; c++) { const a = idmap[r * nx + c], b = idmap[r * nx + c + 1], d = idmap[(r + 1) * nx + c], e2 = idmap[(r + 1) * nx + c + 1];
      if (a >= 0 && b >= 0 && d >= 0 && e2 >= 0) ind.push(a, b, d, b, e2, d); }
    const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3)); fg.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2)); fg.setIndex(ind);
    fg.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(wi, 4)); fg.setAttribute('skinWeight', new THREE.Float32BufferAttribute(ww, 4)); fg.computeVertexNormals();
    const fm = new THREE.MeshPhysicalMaterial({map: ftex, transparent: true, roughness: .88, metalness: 0, sheen: .4, sheenRoughness: .8, sheenColor: new THREE.Color(0xfff0e0), normalMap: m0.normalMap ? null : null});
    faceMesh = new THREE.SkinnedMesh(fg, fm); faceMesh.frustumCulled = false; faceMesh.castShadow = true; root.add(faceMesh); faceMesh.bind(skel, mesh.bindMatrix);
  } else if (F) {
    const toP = (mx, my) => [mx * k, (my - R.floor) * k];                                  // model units -> puppet units
    const [x0, y0] = toP(F.x[0], F.y[0]), [x1, y1] = toP(F.x[1], F.y[1]);
    const nrm = geo.attributes.normal, uv = geo.attributes.uv, idx = geo.index, tri = idx ? idx.count / 3 : pos.count / 3, keep = [];
    const inFace = v => { const x = pos.getX(v), y = pos.getY(v), z = pos.getZ(v); const ex = (x / ((x1 - x0) / 2)) ** 2 + ((y - (y0 + y1) / 2) / ((y1 - y0) / 2)) ** 2;
      return ex < 1.08 && nrm.getZ(v) > .15 && z > .06 * k; };
    for (let t = 0; t < tri; t++) { const a = idx ? idx.getX(t * 3) : t * 3, b = idx ? idx.getX(t * 3 + 1) : t * 3 + 1, c = idx ? idx.getX(t * 3 + 2) : t * 3 + 2; if (inFace(a) && inFace(b) && inFace(c)) keep.push(a, b, c); }
    const m = keep.length, fp = new Float32Array(m * 3), fn = new Float32Array(m * 3), fu = new Float32Array(m * 2), fi = new Uint16Array(m * 4), fw = new Float32Array(m * 4);
    keep.forEach((v, q2) => { const lift = .0012 * k;                                                                        // a hair above the clay
      fp[q2 * 3] = pos.getX(v) + nrm.getX(v) * lift; fp[q2 * 3 + 1] = pos.getY(v) + nrm.getY(v) * lift; fp[q2 * 3 + 2] = pos.getZ(v) + nrm.getZ(v) * lift;
      fn[q2 * 3] = nrm.getX(v); fn[q2 * 3 + 1] = nrm.getY(v); fn[q2 * 3 + 2] = nrm.getZ(v);
      fu[q2 * 2] = (pos.getX(v) - x0) / (x1 - x0); fu[q2 * 2 + 1] = (pos.getY(v) - y0) / (y1 - y0);                       // a flat front projection: the drawing is a face seen from the front
      for (let c = 0; c < 4; c++) { fi[q2 * 4 + c] = si[v * 4 + c]; fw[q2 * 4 + c] = sw[v * 4 + c]; } });
    const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.BufferAttribute(fp, 3)); fg.setAttribute('normal', new THREE.BufferAttribute(fn, 3)); fg.setAttribute('uv', new THREE.BufferAttribute(fu, 2));
    fg.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(fi, 4)); fg.setAttribute('skinWeight', new THREE.Float32BufferAttribute(fw, 4));
    const fm = new THREE.MeshPhysicalMaterial({map: ftex, transparent: true, roughness: .88, metalness: 0, sheen: .4, sheenRoughness: .8, sheenColor: new THREE.Color(0xfff0e0), polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, depthWrite: false});
    faceMesh = new THREE.SkinnedMesh(fg, fm); faceMesh.frustumCulled = false; faceMesh.renderOrder = 1; root.add(faceMesh); faceMesh.bind(skel, mesh.bindMatrix);
  }
  // face drawing: positions in the canvas, from the measured features (model units)
  const cX = mx => (mx - F.x[0]) / (F.x[1] - F.x[0]) * FS, cY = my => (1 - (my - F.y[0]) / (F.y[1] - F.y[0])) * FS, sc = FS / (F.x[1] - F.x[0]);
  const skinCss = F ? F.skinTarget : '#e8a27c', ST = {eyes: 'open', lid: .1, brows: [0, 0, 0], mouth: 'closed', open: 1, tears: false};
  let drawn = '';
  function drawFace() {
    if (!F) return; const key = JSON.stringify(ST); if (key === drawn) return; drawn = key;
    fx.clearRect(0, 0, FS, FS);
    // the skin layer: solid in the middle, fading out at the edge into the clay's own skin
    // the skin base (a plate fades to nothing before its own edge, so the edge never shows)
    if (!R.clean || F.plate) { const g = fx.createRadialGradient(FS / 2, FS / 2, FS * (F.plate ? .36 : .3), FS / 2, FS / 2, FS * (F.plate ? .485 : .52)); g.addColorStop(0, skinCss); g.addColorStop(1, skinCss + '00'); fx.fillStyle = g; fx.fillRect(0, 0, FS, FS); }   // a cleaned model already has bare skin: draw only the features
    const er = F.eyes[2] * sc * .55, ink = '#1c1414';
    for (const s of [-1, 1]) {                       // s: the character's right (-1) and left (+1), as seen from the front: right is on the image's left
      const ex = cX(s * F.eyes[0]), ey = cY(F.eyes[1]);
      const lid = ST.eyes === 'closed' ? 1 : ST.eyes === 'squeeze' ? 1 : ST.eyes === 'wide' ? 0 : Math.max(0, ST.lid - .2) * 1.3;   // a calm face has open eyes: only sad, sleepy, sly faces lower the lids
      if (lid >= .9) { fx.strokeStyle = ink; fx.lineWidth = er * .45; fx.lineCap = 'round'; fx.beginPath();
        if (ST.eyes === 'squeeze') { fx.moveTo(ex - er * 1.2, ey - er * .5); fx.lineTo(ex, ey); fx.lineTo(ex - er * 1.2 * -1, ey - er * .5); }
        else fx.arc(ex, ey - er * .3, er * 1.1, Math.PI * .15, Math.PI * .85); fx.stroke(); }
      else { const big = ST.eyes === 'wide' ? 1.25 : 1;
        if (ST.eyes === 'wide') { fx.fillStyle = '#f4efe6'; fx.beginPath(); fx.ellipse(ex, ey, er * 1.9, er * 1.9, 0, 0, 7); fx.fill(); }
        fx.fillStyle = ink; fx.beginPath(); fx.ellipse(ex, ey, er * big, er * 1.12 * big, 0, 0, 7); fx.fill();
        fx.fillStyle = '#ffffff'; fx.beginPath(); fx.arc(ex - er * .3, ey - er * .38, er * .28, 0, 7); fx.fill();   // the catch-light
        if (lid > .05) { fx.save(); fx.beginPath(); fx.ellipse(ex, ey, er * 1.05 * big, er * 1.17 * big, 0, 0, 7); fx.clip(); fx.fillStyle = skinCss; fx.fillRect(ex - er * 1.6, ey - er * 1.4, er * 3.2, er * (.2 + 2.3 * lid)); fx.restore();   // the lid: only over the eye itself
          fx.strokeStyle = ink; fx.lineWidth = er * .18; fx.beginPath(); fx.moveTo(ex - er * 1.05, ey - er * 1.17 + er * (.2 + 2.3 * lid)); fx.lineTo(ex + er * 1.05, ey - er * 1.17 + er * (.2 + 2.3 * lid)); fx.stroke(); } }   // the upper lid comes down
      // the brow: a thick soft dash; worried tilts the inner end up, angry tilts it down
      const k2 = s < 0 ? ST.brows[0] : ST.brows[1], bx = cX(s * F.brows[0]), by = cY(F.brows[1]) - ST.brows[2] * sc * 2;
      fx.save(); fx.translate(bx, by - Math.abs(k2) * er * .4); fx.rotate(-s * k2 * .45); fx.fillStyle = '#2a2026'; fx.beginPath(); fx.ellipse(0, 0, er * 1.7, er * .42, 0, 0, 7); fx.fill(); fx.restore();
      if (ST.tears) { fx.fillStyle = 'rgba(160,210,240,.85)'; fx.beginPath(); fx.ellipse(ex + s * er * .4, ey + er * 2.2, er * .35, er * .6, 0, 0, 7); fx.fill(); }
    }
    // the mouth
    const mx = cX(F.mouth[0]), my = cY(F.mouth[1]), mw = F.mouth[2] * sc * .5, s2 = ST.mouth, amt = ST.open;
    fx.lineCap = 'round'; fx.strokeStyle = '#5a1e22'; fx.lineWidth = mw * .16;
    const shape = {open: [.9, .35 + .65 * amt], gums: [.9, .35 + .65 * amt], o: [.45, .55 + .3 * amt], grimace: [1.25, .35 + .15 * amt], scream: [.85, 1 + .7 * amt]}[s2];
    if (!shape) { fx.beginPath(); const c = s2 === 'smile' ? -.45 : s2 === 'frown' ? .5 : s2 === 'pressed' ? .05 : .2;   // a line: curved up (smile) or down
      fx.moveTo(mx - mw * .7, my + c * mw * .4); fx.quadraticCurveTo(mx, my - c * mw * .5, mx + mw * .7, my + c * mw * .4); fx.stroke(); }
    else { const w = mw * shape[0], h = mw * .55 * shape[1]; fx.fillStyle = '#3a0c12'; fx.beginPath(); fx.ellipse(mx, my + h * .3, w, h, 0, 0, 7); fx.fill();
      if (s2 === 'open' || s2 === 'grimace' || s2 === 'scream') { fx.fillStyle = '#f6f1e8'; fx.beginPath(); fx.ellipse(mx, my + h * .3 - h * .72, w * .8, h * .28, 0, 0, 7); fx.fill(); }
      if (s2 === 'gums') { fx.fillStyle = '#d86a78'; fx.fillRect(mx - w * .8, my + h * .3 - h * .85, w * 1.6, h * .3); } }
    ftex.needsUpdate = true;
  }
  drawFace();
  const neckLen = J.headBase.y - J.neckBase.y - (R.neckDrop || 0) * k, s0 = (o.height || 1.26) / J.headTop.y;
  root.scale.setScalar(s0);
  const faceLight = new THREE.PointLight(0xffe8d8, 0, 1.2); head.add(faceLight); faceLight.position.set(0, .1, .4);
  const face = new THREE.Group(); head.add(face); const back = new THREE.Group(); head.add(back);
  // the makePerson face interface (the same calls drive it: P.expr('scared'), P.mouth('open', .6), P.eyes('closed'), P.brows(1)...)
  const P = {root, hips, chest, neck, head, back, face, arms, legs, mesh, faceMesh, J, faceLight, sec: {strings: [], hair: isHair ? hairB : null}, neckLen, s0, M: {eye: new THREE.MeshBasicMaterial(), skin: mat},
    eyes(s) { ST.eyes = s; drawFace(); }, lid(v) { ST.eyes = v >= .9 ? 'closed' : 'open'; ST.lid = v; drawFace(); },
    brows(kk) { ST.brows = [kk, kk, Math.abs(kk) * .004]; drawFace(); }, browPair(r, l, raise = 0) { ST.brows = [r, l, raise]; drawFace(); },
    mouth(s, amt = 1) { ST.mouth = s; ST.open = amt; drawFace(); }, tears(b) { ST.tears = !!b; drawFace(); },
    expr(name) { const e = EXPR[name] || EXPR.neutral; ST.eyes = (e.lid ?? 0) >= .9 ? 'closed' : 'open'; ST.lid = Math.min(.6, e.lid ?? .15); ST.brows = [e.brows[0], e.brows[1], e.brows[2] || 0]; ST.mouth = e.mouth; ST.open = e.open ?? 1; ST.tears = !!e.tears; drawFace(); },
    talkCues() {}, clothes() {}, rest() { ST.eyes = 'open'; ST.lid = .15; ST.brows = [0, 0, 0]; ST.mouth = 'closed'; ST.open = 1; ST.tears = false; drawFace(); }};
  // the scenes' reset() puts the hips at .82 and the head at neckLen; keep the chest and neck where the mesh needs them
  P.restPos = {chest: chest.position.clone(), neck: neck.position.clone()};
  return P;
}
