// Clay set kit: rooms and props in the same clay material as the characters, plus horror lighting presets.
// Built from a few soft shapes (rounded boxes, cylinders, spheres): low triangle counts, so path tracing stays fast.
//   import {room, bed, nightstand, lamp, wardrobe, tv, rug, chair, LIGHTS} from './sets.js';
//   const R = room({w: 4, d: 3.6, h: 2.6}); scene.add(R.group);   const b = bed(); b.position.set(...); R.group.add(b);
//   const L = LIGHTS.moon(R); scene.add(L.group);  L.update(t)  (flicker etc.)
// Units: metres-ish (Haru is 1.65 tall). The room is open towards +z, where the camera stands.
import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
import {clay3} from './haru3.js';

// clay material whose grain is the same size on a big wall as on a small prop (texture repeat follows the object size)
const mats = new Map();
export function clayM(color, size = 1, o = {}) {
  const key = color + '|' + Math.round(size * 4) + '|' + JSON.stringify(o);
  if (mats.has(key)) return mats.get(key);
  const m = clay3(color, Object.assign({bumpScale: 1.2}, o));
  const r = Math.max(1, Math.round(size * 2.5));
  m.map = m.map.clone(); m.map.repeat.set(r, r); m.map.needsUpdate = true;
  m.bumpMap = m.bumpMap.clone(); m.bumpMap.repeat.set(r * 2, r * 2); m.bumpMap.needsUpdate = true;
  mats.set(key, m); return m;
}
const mesh = (geo, mat, parent, pos = [0, 0, 0], rot = [0, 0, 0]) => {
  const m = new THREE.Mesh(geo, mat); m.position.set(...pos); m.rotation.set(...rot); m.castShadow = m.receiveShadow = true; if (parent) parent.add(m); return m; };
// a soft clay block: w x h x d, rounded edges (radius r), bottom at y = 0 unless centred
const block = (w, h, d, color, parent, pos, r = .03, o = {}) =>
  mesh(new RoundedBoxGeometry(w, h, d, 2, Math.min(r, w / 2, h / 2, d / 2) * .999), clayM(color, Math.max(w, h, d), o), parent, pos);
const cyl = (r1, r2, h, color, parent, pos, seg = 24) => mesh(new THREE.CylinderGeometry(r1, r2, h, seg), clayM(color, h), parent, pos);
const G = (parent, pos = [0, 0, 0]) => { const g = new THREE.Group(); g.position.set(...pos); if (parent) parent.add(g); return g; };

// ---- the room: floor, three walls, ceiling, skirting, a window (left wall) and a door that opens (back wall)
export function room({w = 4, d = 3.6, h = 2.6, wall = 0x8a8f8a, floor = 0x6b5040, ceil = 0x9a9890, door: doorOn = true, window: winOn = true} = {}) {
  const g = new THREE.Group(), T = .1;
  block(w + T * 2, T, d + T, floor, g, [0, -T / 2, -d / 2 + T / 2], .02);                              // floor boards
  for (let i = -w / 2 + .25; i < w / 2; i += .25) block(.006, .004, d, 0x4a382c, g, [i, .001, -d / 2], .002);   // board gaps
  block(w + T * 2, T, d + T, ceil, g, [0, h + T / 2, -d / 2 + T / 2], .02);
  // back wall with a door opening, left wall with a window opening, right wall plain
  const back = G(g, [0, 0, -d - T / 2]), dw = .85, dh = 2.0, dx = w * .25;
  const xa = dx - dw / 2, xb = dx + dw / 2;                                                // door opening from xa to xb
  block(xa + w / 2, h, T, wall, back, [(-w / 2 + xa) / 2, h / 2, 0], .01);
  block(w / 2 - xb, h, T, wall, back, [(xb + w / 2) / 2, h / 2, 0], .01);
  block(dw, h - dh, T, wall, back, [dx, dh + (h - dh) / 2, 0], .01);
  const side = (sx, hole) => {
    const s = G(g, [sx * (w / 2 + T / 2), 0, 0]);
    if (!hole) { block(T, h, d, wall, s, [0, h / 2, -d / 2], .01); return s; }
    const wz = -d * .45, ww = 1.0, wy0 = .9, wy1 = 2.0;                 // window opening
    const za = wz + ww / 2, zb = wz - ww / 2;                                            // window opening from zb to za
    block(T, h, -za, wall, s, [0, h / 2, za / 2], .01);                                  // front part (towards the camera)
    block(T, h, zb + d, wall, s, [0, h / 2, (zb - d) / 2], .01);                         // back part
    block(T, wy0, ww, wall, s, [0, wy0 / 2, wz], .01); block(T, h - wy1, ww, wall, s, [0, wy1 + (h - wy1) / 2, wz], .01);
    // frame, cross bars, sill
    for (const [y, hh] of [[wy0, .05], [wy1, .05], [(wy0 + wy1) / 2, .035]]) block(T * 1.2, hh, ww, 0xd8d2c4, s, [0, y, wz], .01);
    for (const z of [wz - ww / 2, wz, wz + ww / 2]) block(T * 1.2, wy1 - wy0, z === wz ? .035 : .05, 0xd8d2c4, s, [0, (wy0 + wy1) / 2, z], .01);
    block(T * 2.2, .04, ww + .12, 0xd8d2c4, s, [-sx * T * .6, wy0 - .02, wz], .01);
    // curtains: soft draped clay, a little open
    for (const k of [-1, 1]) { const c = G(s, [-sx * (T + .03), 0, wz + k * (ww / 2 + .02)]);
      for (let i = 0; i < 4; i++) cyl(.035, .045, wy1 - wy0 + .45, 0x5a4652, c, [0, (wy0 + wy1) / 2 + .1, -k * i * .055]); }
    s.userData.window = {z: wz, w: ww, y0: wy0, y1: wy1};
    return s;
  };
  const L = side(-1, winOn), R = side(1, false);
  block(w, .08, .03, 0xc9c2b2, g, [0, .04, -d + .015], .01);                                             // skirting
  // the door: a panel on a hinge, with a knob; door.open(k) 0..1
  const hinge = G(g, [dx - dw / 2, 0, -d]), panel = G(hinge, [dw / 2, 0, 0]);
  block(dw - .02, dh - .02, .045, 0x7a5a42, panel, [0, dh / 2, 0], .01);
  for (const y of [.55, 1.4]) block(dw - .25, .55, .015, 0x6a4c38, panel, [0, y, .025], .008);
  mesh(new THREE.SphereGeometry(.035, 16, 12), new THREE.MeshPhysicalMaterial({color: 0xb08a4a, roughness: .3, metalness: .8}), panel, [dw / 2 - .1, .98, .05]);
  for (const x of [dx - dw / 2 - .04, dx + dw / 2 + .04]) block(.06, dh + .06, .06, 0xd8d2c4, g, [x, (dh + .06) / 2, -d + .03], .01);
  block(dw + .14, .06, .06, 0xd8d2c4, g, [dx, dh + .03, -d + .03], .01);
  const doorObj = {hinge, x: dx, w: dw, h: dh, z: -d, open: k => { hinge.rotation.y = k * 1.2; }};
  return {group: g, w, d, h, door: doorOn ? doorObj : null, window: winOn ? L.userData.window : null, wallX: w / 2};
}

// ---- props (each one a group, standing on y = 0, facing +z)
export function bed({w = 1.0, l = 2.0, frame = 0x6e4e38, sheet = 0xd9d2c2, blanket = 0x4f6a8a, pillow = 0xe6e0d2} = {}) {
  const g = G();
  block(w + .08, .28, l + .08, frame, g, [0, .14, 0], .03);                                // base
  block(w + .08, .75, .08, frame, g, [0, .375, -l / 2 - .02], .03);                        // headboard
  block(w + .08, .45, .07, frame, g, [0, .225, l / 2 + .02], .03);                         // footboard
  block(w, .2, l, sheet, g, [0, .38, 0], .07);                                             // mattress
  block(w * .7, .12, .38, pillow, g, [0, .53, -l / 2 + .28], .055);                        // pillow
  const bl = block(w + .1, .07, l * .62, blanket, g, [0, .5, l * .17], .035);             // blanket, folded over the edges
  for (const sx of [-1, 1]) block(.05, .22, l * .62, blanket, g, [sx * (w / 2 + .05), .4, l * .17], .025);
  block(w + .1, .1, .12, 0xe6e0d2, g, [0, .52, l * .17 - l * .31 + .02], .045);             // the sheet turned back over it
  g.userData = {top: .5, blanket: bl}; return g;
}
export function nightstand({c = 0x6e4e38} = {}) {
  const g = G(); block(.45, .55, .4, c, g, [0, .275, 0], .03);
  block(.38, .18, .02, 0x5e4230, g, [0, .38, .205], .01); mesh(new THREE.SphereGeometry(.018, 12, 8), clayM(0xc9b48a, .1), g, [0, .38, .225]);
  g.userData = {top: .55}; return g;
}
export function lamp({shade = 0xe8d9b8} = {}) {
  const g = G(); cyl(.07, .09, .05, 0x5a5048, g, [0, .025, 0]); cyl(.012, .012, .3, 0x5a5048, g, [0, .2, 0]);
  const s = mesh(new THREE.CylinderGeometry(.09, .15, .2, 24, 1, true), Object.assign(clayM(shade, .3), {side: THREE.DoubleSide}), g, [0, .38, 0]);
  const bulb = mesh(new THREE.SphereGeometry(.035, 12, 10), new THREE.MeshStandardMaterial({color: 0xfff1d0, emissive: 0xffd9a0, emissiveIntensity: 0}), g, [0, .34, 0]);
  g.userData = {bulb, shade: s, lightPos: new THREE.Vector3(0, .34, 0)}; return g;
}
export function wardrobe({c = 0x5e4636} = {}) {
  const g = G(); block(1.0, 2.0, .55, c, g, [0, 1.0, 0], .035);
  for (const sx of [-1, 1]) { block(.47, 1.85, .02, 0x6e5240, g, [sx * .245, 1.0, .285], .01); cyl(.012, .012, .2, 0xb08a4a, g, [sx * .04, 1.05, .31]); }
  const gap = block(.012, 1.8, .02, 0x120c0a, g, [0, 1.0, .29], .003);                    // the dark crack between the doors
  g.userData = {gap}; return g;
}
export function tv({c = 0x3a3634} = {}) {
  const g = G();
  block(.9, .5, .45, 0x5e4636, g, [0, .25, 0], .03);                                        // low cabinet
  block(.62, .48, .45, c, g, [0, .5 + .24, -.02], .06);                                     // old CRT box
  const screen = mesh(new RoundedBoxGeometry(.5, .37, .02, 2, .03), new THREE.MeshStandardMaterial({color: 0x1a2028, emissive: 0x9fc8ff, emissiveIntensity: 0, roughness: .2}), g, [0, .74, .21]);
  for (const sx of [-1, 1]) cyl(.004, .004, .3, 0x222222, g, [sx * .08, 1.1, -.05]);       // antenna
  g.userData = {screen, lightPos: new THREE.Vector3(0, .74, .3)}; return g;
}
export function rug({w = 1.6, d = 1.1, c = 0x8a4a3a} = {}) { const g = G(); block(w, .02, d, c, g, [0, .01, 0], .01); return g; }
export function chair({c = 0x6e4e38} = {}) {
  const g = G(); block(.45, .05, .45, c, g, [0, .46, 0], .02); block(.45, .5, .05, c, g, [0, .72, -.2], .02);
  for (const [x, z] of [[-.19, -.19], [.19, -.19], [-.19, .19], [.19, .19]]) block(.045, .46, .045, c, g, [x, .23, z], .01);
  return g;
}

// ---- lighting presets for the moods we use. Only light types that work in BOTH the quick preview and the path tracer:
// rectangular area lights (soft), spot lights and point lights. Each returns {group, update(t)}.
// Call setupLights(renderer) once (area lights in the preview need it).
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
let rectInit = false;
export const setupLights = () => { if (!rectInit) { RectAreaLightUniformsLib.init(); rectInit = true; } };
const rect = (color, power, w, h, pos, target) => { const l = new THREE.RectAreaLight(color, power, w, h); l.position.set(...pos); l.lookAt(...target); return l; };
const fill = (g, power = .25) => g.add(rect(0x6a7fa8, power, 4, 3, [0, 2.2, 3.5], [0, 1, -1]));   // a faint night fill from the camera side
export const LIGHTS = {
  // moonlight through the window: cold, soft, from the left
  moon: R => { const g = new THREE.Group(); const W = R.window;
    g.add(rect(0x9ab8ff, 22, W.w * .9, W.y1 - W.y0, [-R.wallX - .25, (W.y0 + W.y1) / 2, W.z], [0, .3, W.z + .6])); fill(g);
    return {group: g, update() {}}; },
  // the TV left on: blue, flickering
  tv: (R, tvProp) => { const g = new THREE.Group(); tvProp.updateMatrixWorld(true);
    const p = tvProp.localToWorld(tvProp.userData.lightPos.clone()), f = tvProp.localToWorld(new THREE.Vector3(0, .74, 2));
    const l = rect(0x9fc8ff, 45, .5, .37, p.toArray(), f.toArray()); g.add(l); fill(g, .12);
    const scr = tvProp.userData.screen.material;
    return {group: g, update(t) { const k = .75 + .25 * Math.sin(t * 23) * Math.sin(t * 7.3 + 1) + .1 * Math.sin(t * 61); l.intensity = 45 * k; scr.emissiveIntensity = 1.6 * k; }}; },
  // a thin line of warm light under the closed door (someone is on the other side)
  door: R => { const g = new THREE.Group(); const D = R.door;
    g.add(rect(0xffc27a, 500, D.w * .9, .025, [D.x, .014, D.z + .03], [D.x, .2, D.z + 2]));           // the bright line
    g.add(rect(0xffb060, 14, D.w, .9, [D.x, .25, D.z + .12], [D.x, -.2, D.z + 1.2]));                  // its glow spreading over the floor boards
    const strip = new THREE.Mesh(new THREE.PlaneGeometry(D.w * .9, .012), new THREE.MeshBasicMaterial({color: 0xffd9a0})); strip.position.set(D.x, .006, D.z + .025); g.add(strip);
    fill(g, .1); return {group: g, update() {}}; },
  // a bedside lamp: warm and close
  lamp: (R, lampProp) => { const g = new THREE.Group(); lampProp.updateMatrixWorld(true);
    const l = new THREE.PointLight(0xffc98a, 3.2, 6, 2); l.position.copy(lampProp.localToWorld(lampProp.userData.lightPos.clone())); l.castShadow = true; g.add(l);
    // the light that leaves the shade: a soft warm patch on the wall/ceiling and a downward pool (direct light = little grain when path traced)
    const lp = l.position;
    g.add(rect(0xffc98a, 14, .5, .5, [lp.x, lp.y + .15, lp.z], [lp.x, lp.y + 2, lp.z]));
    g.add(rect(0xffc98a, 12, .45, .45, [lp.x, lp.y - .05, lp.z], [lp.x, 0, lp.z + .3]));
    const shadeM = lampProp.userData.shade.material; shadeM.emissive = new THREE.Color(0xffb870);   // the lit shade glows (only while this preset is on)
    lampProp.userData.bulb.material.emissiveIntensity = 2.5; fill(g, .08);
    // path traced: drop the tiny point light inside the shade (it makes the shade blinding and speckles the room); the soft lights above carry it
    return {group: g, point: l, forPathTracing() { g.remove(l); }, update() {}, on(k) { shadeM.emissiveIntensity = k ? .35 : 0; lampProp.userData.bulb.material.emissiveIntensity = k ? 2.5 : 0; }}; },
  // only a flashlight (the character holds it: pass its hand group); everything else dark
  flashlight: (R, hand) => { const g = new THREE.Group();
    const l = new THREE.SpotLight(0xfff1cc, 30, 9, .42, .55, 2); l.castShadow = true; hand.add(l); l.position.set(.13, 0, 0);
    const tgt = new THREE.Object3D(); tgt.position.set(3, 0, 0); hand.add(tgt); l.target = tgt; fill(g, .05);
    return {group: g, light: l, update() {}}; },
};

// ================================================================ more rooms: kitchen, hallway, bathroom (+ the magic lamp)
const gloss = (c, o = {}) => new THREE.MeshPhysicalMaterial(Object.assign({color: c, roughness: .25, clearcoat: .6, clearcoatRoughness: .2}, o));
const metal = (c, r = .3) => new THREE.MeshPhysicalMaterial({color: c, metalness: 1, roughness: r});
// a door on its own: hinge at x = 0, opening into +z; frame included. door(...).open(k), k 0..1
export function door({w = .85, h = 2.0, c = 0x7a5a42} = {}) {
  const g = G(), hinge = G(g, [-w / 2, 0, 0]), panel = G(hinge, [w / 2, 0, 0]);
  block(w - .02, h - .02, .045, c, panel, [0, h / 2, 0], .01);
  for (const y of [.55, 1.4]) block(w - .25, .55, .015, new THREE.Color(c).multiplyScalar(.85).getHex(), panel, [0, y, .025], .008);
  mesh(new THREE.SphereGeometry(.035, 16, 12), metal(0xb08a4a), panel, [w / 2 - .1, .98, .05]);
  for (const x of [-w / 2 - .04, w / 2 + .04]) block(.06, h + .06, .06, 0xd8d2c4, g, [x, (h + .06) / 2, .03], .01);
  block(w + .14, .06, .06, 0xd8d2c4, g, [0, h + .03, .03], .01);
  g.userData = {open: k => { hinge.rotation.y = k * 1.2; }, w, h}; return g;
}
// clay tiles: a grout grid painted into the clay colour (bathroom, kitchen splashback)
const tileCache = new Map();
export function tiles(color, grout = 0x8a8a84, size = 1, n = 6) {
  const key = color + '/' + grout + '/' + size; if (tileCache.has(key)) return tileCache.get(key);
  const m = clayM(color, size, {bumpScale: .8}); const t = m.clone();
  const cv = document.createElement('canvas'); cv.width = cv.height = 256; const x = cv.getContext('2d');
  x.drawImage(m.map.image, 0, 0, 256, 256); x.strokeStyle = '#' + new THREE.Color(grout).getHexString(); x.lineWidth = 6;
  for (let i = 0; i <= 4; i++) { x.beginPath(); x.moveTo(i * 64, 0); x.lineTo(i * 64, 256); x.stroke(); x.beginPath(); x.moveTo(0, i * 64); x.lineTo(256, i * 64); x.stroke(); }
  t.map = new THREE.CanvasTexture(cv); t.map.colorSpace = THREE.SRGBColorSpace; t.map.wrapS = t.map.wrapT = THREE.RepeatWrapping;
  const r = Math.max(1, Math.round(size * n / 4)); t.map.repeat.set(r, r); t.color.set(0xffffff);
  tileCache.set(key, t); return t;
}
const tiled = (w, h, d, color, parent, pos) => mesh(new RoundedBoxGeometry(w, h, d, 1, .005), tiles(color, 0x9a968c, Math.max(w, h, d)), parent, pos);

// ---- kitchen props
export function counter({len = 2.4, c = 0x7d8a76, top = 0xcfc6b4, sink = true, stove = true} = {}) {
  const g = G(); block(len, .86, .6, c, g, [0, .43, 0], .02);                                      // cupboards
  block(len + .04, .05, .64, top, g, [0, .885, 0], .015);                                          // worktop
  for (let x = -len / 2 + .3; x < len / 2; x += .6) { block(.56, .7, .02, new THREE.Color(c).multiplyScalar(1.08).getHex(), g, [x, .45, .305], .01);
    cyl(.012, .012, .1, 0xb8b0a0, g, [x + .2, .62, .325]); }
  if (sink) { const s = G(g, [-len / 4, .885, 0]); mesh(new RoundedBoxGeometry(.5, .06, .4, 2, .02), metal(0xa8acb0, .35), s, [0, .01, 0]);
    block(.44, .02, .34, 0x2a2c2e, s, [0, .03, 0], .008);
    const f = G(s, [0, 0, -.24]); cyl(.02, .025, .32, 0xb8bcc0, f, [0, .16, 0]); mesh(new THREE.TorusGeometry(.09, .016, 8, 16, Math.PI), metal(0xb8bcc0, .2), f, [0, .32, .09], [0, Math.PI / 2, 0]); }
  if (stove) { const s = G(g, [len / 4, .9, 0]); block(.6, .02, .55, 0x2b2b2b, s, [0, .01, 0], .01);
    for (const [x, z] of [[-.14, -.12], [.14, -.12], [-.14, .12], [.14, .12]]) mesh(new THREE.TorusGeometry(.07, .012, 8, 20), metal(0x3a3a3a, .5), s, [x, .03, z], [Math.PI / 2, 0, 0]);
    block(.5, .34, .02, 0x2a2a2a, g, [len / 4, .4, .31], .01); block(.3, .14, .01, 0x0e0e10, g, [len / 4, .44, .322], .006); }
  return g;
}
export function upperCabinets({len = 2.4, c = 0x7d8a76} = {}) {
  const g = G(); block(len, .7, .35, c, g, [0, 0, 0], .02);
  for (let x = -len / 2 + .3; x < len / 2; x += .6) { block(.56, .62, .02, new THREE.Color(c).multiplyScalar(1.08).getHex(), g, [x, 0, .18], .01); cyl(.012, .012, .1, 0xb8b0a0, g, [x + .2, -.22, .2]); }
  return g;
}
export function fridge({c = 0xe6e2d6} = {}) {
  const g = G(), body = block(.75, 1.8, .7, c, g, [0, .9, 0], .06);
  const hinge = G(g, [-.375, 0, .35]), dr = G(hinge, [.375, 0, 0]);
  block(.73, 1.12, .05, c, dr, [0, 1.22, .02], .04); cyl(.015, .015, .4, 0xb8b0a0, dr, [.3, 1.2, .07]);
  block(.73, .62, .05, c, g, [0, .33, .37], .04); cyl(.015, .015, .25, 0xb8b0a0, g, [.3, .5, .42]);
  const inner = block(.68, 1.05, .02, 0xf4f4ee, g, [0, 1.22, .34], .01); inner.material = new THREE.MeshStandardMaterial({color: 0xf2f6ff, emissive: 0xcfe2ff, emissiveIntensity: 0});
  g.userData = {open: k => { hinge.rotation.y = k * 1.6; }, inner, lightPos: new THREE.Vector3(0, 1.25, .5)}; return g;
}
export function table({w = 1.2, d = .8, c = 0x7a5a42} = {}) {
  const g = G(); block(w, .05, d, c, g, [0, .74, 0], .02);
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) block(.05, .72, .05, c, g, [x * (w / 2 - .06), .36, z * (d / 2 - .06)], .01);
  return g;
}
export function pendant({cord = .7, shade = 0x4a5a52} = {}) {                                     // hangs from y = 0 downwards
  const g = G(); cyl(.004, .004, cord, 0x222222, g, [0, -cord / 2, 0], 6);
  const s = mesh(new THREE.ConeGeometry(.2, .16, 24, 1, true), Object.assign(clayM(shade, .4), {side: THREE.DoubleSide}), g, [0, -cord - .06, 0]);
  const bulb = mesh(new THREE.SphereGeometry(.04, 12, 10), new THREE.MeshStandardMaterial({color: 0xfff1d0, emissive: 0xffd9a0, emissiveIntensity: 0}), g, [0, -cord - .1, 0]);
  g.userData = {bulb, shade: s, lightPos: new THREE.Vector3(0, -cord - .13, 0)}; return g;
}
// ---- hallway props
export function frame({w = .4, h = .5, c = 0x5a4232, pic = 0x8a9a8a} = {}) {          // a picture on the wall (faces +z)
  const g = G(); block(w, h, .03, c, g, [0, 0, 0], .01); block(w - .08, h - .08, .01, pic, g, [0, 0, .016], .004); return g;
}
export function runner({w = .7, d = 4, c = 0x6a3a3a} = {}) { const g = G(); block(w, .015, d, c, g, [0, .0075, 0], .006); block(w - .1, .016, d - .1, 0x8a5a3a, g, [0, .008, 0], .005); return g; }
export function ceilingLight() {                                                       // flush dome, hangs from y = 0
  const g = G(); cyl(.12, .12, .03, 0xd8d2c4, g, [0, -.015, 0]);
  const dome = mesh(new THREE.SphereGeometry(.11, 20, 10, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), new THREE.MeshStandardMaterial({color: 0xf6f0e0, emissive: 0xfff0d0, emissiveIntensity: 0, roughness: .6}), g, [0, -.03, 0]);
  g.userData = {dome, lightPos: new THREE.Vector3(0, -.15, 0)}; return g;
}
// ---- bathroom props
export function bathtub({c = 0xeeeae2} = {}) {
  const g = G(); block(1.6, .55, .75, c, g, [0, .275, 0], .1);
  block(1.4, .06, .56, 0xdedad0, g, [0, .53, 0], .08).scale.y = .4;
  const water = mesh(new THREE.BoxGeometry(1.36, .01, .52), new THREE.MeshPhysicalMaterial({color: 0x9ab0b8, roughness: .05, transmission: .6, transparent: true, opacity: .8}), g, [0, .44, 0]);
  const f = G(g, [-.7, .55, 0]); cyl(.02, .02, .2, 0xb8bcc0, f, [0, .1, 0]); mesh(new THREE.TorusGeometry(.06, .014, 8, 12, Math.PI), metal(0xb8bcc0, .2), f, [.06, .2, 0]);
  g.userData = {water}; return g;
}
export function toilet({c = 0xeeeae2} = {}) {
  const g = G(); cyl(.15, .12, .38, c, g, [0, .19, .05]); block(.4, .06, .48, c, g, [0, .41, .06], .08);
  block(.42, .38, .18, c, g, [0, .6, -.2], .05); block(.44, .04, .2, c, g, [0, .8, -.2], .02); return g;
}
export function bathSink({c = 0xeeeae2} = {}) {
  const g = G(); cyl(.08, .12, .78, c, g, [0, .39, 0]); block(.6, .14, .45, c, g, [0, .84, 0], .06);
  block(.46, .05, .3, 0xd0ccc2, g, [0, .9, .02], .04); cyl(.015, .015, .14, 0xb8bcc0, g, [0, .97, -.15]); return g;
}
export function mirror({w = .6, h = .8} = {}) {                                             // a real mirror (the path tracer reflects the room)
  const g = G(); block(w + .06, h + .06, .03, 0x8a7a62, g, [0, 0, 0], .015);
  mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshPhysicalMaterial({color: 0xdfe4e8, metalness: 1, roughness: .03}), g, [0, 0, .017]);
  return g;
}
export function curtainRail({len = 1.6, c = 0x7a9aa8} = {}) {                               // shower curtain, hangs from y = 0
  const g = G(); cyl(.012, .012, len, 0xb8bcc0, g, [0, 0, 0]).rotation.z = Math.PI / 2;
  for (let i = 0; i < 10; i++) cyl(.04, .05, 1.6, c, g, [-len / 2 + .1 + i * .08, -.82, (i % 2) * .03]);
  return g;
}
// ---- the magic lamp: brass oil lamp (body, spout, handle, lid with a knob). glow(k) lights it up from inside
export function magicLamp({c = 0xc49a3a} = {}) {
  const g = G(), brass = new THREE.MeshPhysicalMaterial({color: c, metalness: 1, roughness: .32, clearcoat: .3});
  const prof = [[0, 0], [.06, .005], [.08, .02], [.11, .05], [.12, .08], [.1, .11], [.06, .125], [.035, .13], [.03, .15], [0, .155]].map(([x, y]) => new THREE.Vector2(x, y));
  const body = mesh(new THREE.LatheGeometry(prof, 32), brass, g); body.scale.z = .8;
  cyl(.05, .06, .02, c, g, [0, .01, 0]).material = brass;                                       // foot
  const spout = new THREE.CatmullRomCurve3([[.09, .07, 0], [.17, .09, 0], [.24, .14, 0], [.29, .17, 0]].map(p => new THREE.Vector3(...p)));
  mesh(new THREE.TubeGeometry(spout, 20, .018, 10, false), brass, g); const tip = mesh(new THREE.SphereGeometry(.014, 10, 8), brass, g, [.29, .17, 0]);
  mesh(new THREE.TorusGeometry(.055, .012, 8, 20, Math.PI * 1.2), brass, g, [-.13, .09, 0], [0, 0, Math.PI * .4]);   // handle
  mesh(new THREE.SphereGeometry(.03, 14, 10), brass, g, [0, .165, 0]); mesh(new THREE.SphereGeometry(.012, 10, 8), brass, g, [0, .2, 0]);   // lid and knob
  const glowM = new THREE.MeshStandardMaterial({color: 0xffc070, emissive: 0xffa040, emissiveIntensity: 0});
  const mouthGlow = mesh(new THREE.SphereGeometry(.012, 10, 8), glowM, g, [.297, .175, 0]);
  const light = new THREE.PointLight(0xffa040, 0, 2.5, 2); light.position.set(.3, .2, 0); g.add(light);
  g.userData = {glow: k => { glowM.emissiveIntensity = 3 * k; light.intensity = .6 * k; }, tip}; return g;
}

// ---- the three rooms assembled (each returns the room R from room() plus the props by name)
export function kitchen() {
  const R = room({w: 4, d: 3.6, h: 2.6, wall: 0x8f9a86, floor: 0x7a6a58}), g = R.group, P = {};
  P.counter = counter(); P.counter.position.set(-.4, 0, -3.25); g.add(P.counter);
  P.upper = upperCabinets(); P.upper.position.set(-.4, 1.75, -3.38); g.add(P.upper);
  const back = tiled(2.4, .75, .02, 0xe6e0d0, g, [-.4, 1.28, -3.54]);
  P.fridge = fridge(); P.fridge.position.set(1.45, 0, -3.15); g.add(P.fridge);
  P.table = table(); P.table.position.set(-.6, 0, -1.4); g.add(P.table);
  for (const [x, z, r] of [[-1.3, -1.4, Math.PI / 2], [.1, -1.4, -Math.PI / 2]]) { const c = chair(); c.position.set(x, 0, z); c.rotation.y = r; g.add(c); }
  P.lamp = pendant(); P.lamp.position.set(-.6, R.h, -1.4); g.add(P.lamp);
  return {R, P};
}
export function hallway() {
  const R = room({w: 1.8, d: 6, h: 2.6, wall: 0x8a7f72, floor: 0x5e4636, window: false}), g = R.group, P = {doors: [], lights: []};
  for (const [sx, z] of [[-1, -1.6], [1, -2.8], [-1, -4.2]]) { const d = door({c: 0x6a5040}); d.position.set(sx * (R.w / 2 - .02), 0, z); d.rotation.y = -sx * Math.PI / 2; g.add(d); P.doors.push(d); }
  for (const [sx, z, c] of [[1, -1.4, 0x6a8a9a], [-1, -3.1, 0x9a7a5a], [1, -4.6, 0x7a6a8a]]) { const f = frame({pic: c}); f.position.set(sx * (R.w / 2 - .02), 1.55, z); f.rotation.y = -sx * Math.PI / 2; g.add(f); }
  P.runner = runner({d: 5}); P.runner.position.set(0, 0, -3.2); g.add(P.runner);
  for (const z of [-1.2, -3.0, -4.8]) { const l = ceilingLight(); l.position.set(0, R.h, z); g.add(l); P.lights.push(l); }
  return {R, P};
}
export function bathroom() {
  const R = room({w: 2.8, d: 2.8, h: 2.5, wall: 0xb8c4c4, floor: 0x9aa4a4, window: false}), g = R.group, P = {};
  tiled(R.w, 1.3, .02, 0xdfe8e6, g, [0, .65, -R.d + .012]);                                    // tiled lower walls
  for (const sx of [-1, 1]) tiled(.02, 1.3, R.d, 0xdfe8e6, g, [sx * (R.w / 2 - .012), .65, -R.d / 2]);
  P.tub = bathtub(); P.tub.position.set(-.55, 0, -2.38); g.add(P.tub);
  P.curtain = curtainRail(); P.curtain.position.set(-.55, 2.1, -1.95); g.add(P.curtain);
  P.toilet = toilet(); P.toilet.position.set(1.05, 0, -1.2); P.toilet.rotation.y = -Math.PI / 2; g.add(P.toilet);
  P.sink = bathSink(); P.sink.position.set(1.12, 0, -2.2); P.sink.rotation.y = -Math.PI / 2; g.add(P.sink);
  P.mirror = mirror(); P.mirror.position.set(1.38, 1.5, -2.2); P.mirror.rotation.y = -Math.PI / 2; g.add(P.mirror);
  P.mirrorLight = G(g, [1.36, 1.98, -2.2]); block(.04, .05, .5, 0xeeeae2, P.mirrorLight, [0, 0, 0], .01);
  return {R, P};
}

// ---- lighting presets for the new rooms (same rules: area, spot and point lights only)
Object.assign(LIGHTS, {
  // kitchen: the pendant over the table, warm
  pendant: (R, p) => { const g = new THREE.Group(); p.updateMatrixWorld(true); const lp = p.localToWorld(p.userData.lightPos.clone());
    g.add(rect(0xffc98a, 50, .3, .3, [lp.x, lp.y, lp.z], [lp.x, 0, lp.z])); fill(g, .1);
    return {group: g, update() {}, on(k) { p.userData.bulb.material.emissiveIntensity = k ? 2 : 0; }}; },
  // kitchen at night: only the open fridge, cold
  fridge: (R, f) => { const g = new THREE.Group(); f.updateMatrixWorld(true); const lp = f.localToWorld(f.userData.lightPos.clone()), to = f.localToWorld(new THREE.Vector3(0, 1, 3));
    g.add(rect(0xdfeaff, 18, .6, 1.0, lp.toArray(), to.toArray())); fill(g, .05);
    return {group: g, update() {}, on(k) { f.userData.open(k ? .85 : 0); f.userData.inner.material.emissiveIntensity = k ? 1.2 : 0; }}; },
  // hallway: ceiling lights, one of them failing (flickers)
  hall: (R, lights) => { const g = new THREE.Group(), ls = lights.map(l => { l.updateMatrixWorld(true); const p = l.localToWorld(l.userData.lightPos.clone());
      const r = rect(0xffe2b8, 10, .3, .3, p.toArray(), [p.x, 0, p.z]); g.add(r); return r; });
    fill(g, .04);
    return {group: g, update(t) { const k = Math.sin(t * 31) * Math.sin(t * 7) > .2 ? .1 : 1; ls[1].intensity = 10 * k; lights[1].userData.dome.material.emissiveIntensity = .8 * k; },
      on(k) { lights.forEach(l => l.userData.dome.material.emissiveIntensity = k ? .8 : 0); }}; },
  // bathroom: the strip light over the mirror, cold and hard
  mirror: (R, strip) => { const g = new THREE.Group(); strip.updateMatrixWorld(true); const p = strip.localToWorld(new THREE.Vector3(-.05, -.03, 0));
    g.add(rect(0xe8f2ff, 80, .5, .05, p.toArray(), [p.x - 1, p.y - .6, p.z])); fill(g, .06);
    return {group: g, update() {}}; },
});
