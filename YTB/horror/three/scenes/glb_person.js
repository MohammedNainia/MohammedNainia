// A generated 3D character (image-to-3D, e.g. data/glb/haru_rodin.glb) turned into a puppet with the SAME joints as clay.js makePerson:
// root > hips > chest > neck > head, chest > arms[i].up > fo > hand, hips > legs[i].th > sh > ft.
// The joints are THREE.Bones placed from a small rig file (data/glb/<name>.rig.json, positions measured on the mesh), and every vertex is
// skinned to them with automatic weights (by distance to each bone's segment), so pose(), walk(), look() and the scenes' reset() drive it as-is.
// The hips sit at y = .82 in the puppet's own units, like every makePerson character; P.s0 scales it to its height in the world.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

const V = (x, y, z) => new THREE.Vector3(x, y, z);

export async function makeGlbPerson(name, o = {}) {
  const [gl, R] = await Promise.all([new GLTFLoader().loadAsync('/data/glb/' + name + '.glb'), fetch('/data/glb/' + name + '.rig.json').then(r => r.json())]);
  gl.scene.updateMatrixWorld(true); let src = null; gl.scene.traverse(m => { if (m.isMesh && !src) src = m; });
  const geo = src.geometry.clone(); geo.applyMatrix4(src.matrixWorld);
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
      const fl = sm(hem + .03, hem - .08, p.y) * sm(.004, .03, ax);                                                         // how much leg
      put(segs.filter(sg => sg.arm === sd), fa * (1 - fh));
      put(segs.filter(sg => sg.leg === sd), fl * (1 - fa));
      put(TORSO, (1 - fa) * (1 - fl) * (1 - fh));
    }
    const top = [...w.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4), tot = top.reduce((s, c) => s + c[1], 0) || 1;
    top.forEach((c, k2) => { si[v * 4 + k2] = c[0]; sw[v * 4 + k2] = c[1] / tot; });
  }
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4)); geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute(sw, 4));
  // clay: matte, never metallic (the generator's gloss and metal maps make it plastic), a soft sheen
  const m0 = src.material, mat = new THREE.MeshPhysicalMaterial({map: m0.map, normalMap: m0.normalMap, roughness: .88, metalness: 0, sheen: .4, sheenRoughness: .8, sheenColor: new THREE.Color(0xfff0e0), side: m0.side});
  const mesh = new THREE.SkinnedMesh(geo, mat); mesh.castShadow = mesh.receiveShadow = true; mesh.frustumCulled = false;
  root.add(mesh); root.updateMatrixWorld(true); mesh.bind(new THREE.Skeleton(bones));
  // ---- the makePerson interface the scenes use (the face controls are stubs until the animated face goes on)
  const neckLen = J.headBase.y - J.neckBase.y, s0 = (o.height || 1.26) / J.headTop.y;
  root.scale.setScalar(s0);
  const faceLight = new THREE.PointLight(0xffe8d8, 0, 1.2); head.add(faceLight); faceLight.position.set(0, .1, .4);
  const face = new THREE.Group(); head.add(face); const back = new THREE.Group(); head.add(back);
  const P = {root, hips, chest, neck, head, back, face, arms, legs, mesh, J, faceLight, sec: {strings: []}, neckLen, s0, M: {eye: new THREE.MeshBasicMaterial(), skin: mat},
    eyes() {}, brows() {}, mouth() {}, expr() {}, lid() {}, browPair() {}, tears() {}, talkCues() {}, clothes() {}, rest() {}};
  // the scenes' reset() puts the hips at .82 and the head at neckLen; keep the chest and neck where the mesh needs them
  P.restPos = {chest: chest.position.clone(), neck: neck.position.clone()};
  return P;
}
