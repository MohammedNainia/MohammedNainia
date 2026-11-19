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
