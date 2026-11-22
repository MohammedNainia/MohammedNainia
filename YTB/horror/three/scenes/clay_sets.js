// Clay set kit: furniture, room parts and props made like the puppets (rounded, sculpted, clay-textured), for the fast raster workflow.
// Every builder returns a THREE.Group standing on the floor at its origin, facing +z. Sizes in metres (Haru is ~1.55 m).
//   import {fridge, counter, ...} from './clay_sets.js';   const f = fridge(); f.position.set(1.5, 0, -1.8); room.add(f);
import {THREE} from './lib.js';
import {clay, gloss, lump, add, S, Cp, G, turn} from './clay.js';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';

let rs = 17; const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
export const rbox = (w, h, d, r = .02, a = .003, f = 8) => lump(new RoundedBoxGeometry(w, h, d, 3, Math.min(r, w / 2, h / 2, d / 2)), a, f);
const mat = (c, o) => typeof c === 'number' ? clay(c, o) : c;
const DARK = clay(0x161210), METAL = gloss(0xa8a8a4, {roughness: .35, metalness: .6}), PAPER = clay(0xeee6d4, {bumpScale: .3});

// ---------------------------------------------------------------- painted textures (canvas): wallpaper, tiles, pictures
export function canvasTex(w, h, draw, rep = [1, 1]) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t;
}
const hex = c => '#' + new THREE.Color(c).getHexString();
export function wallpaper(base = 0x8a8a6e, ink = 0x6e6e56, kind = 'stripe', rep = [4, 2]) {
  return canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = hex(base); g.fillRect(0, 0, w, h); g.fillStyle = hex(ink); g.strokeStyle = hex(ink);
    if (kind === 'stripe') { for (let x = 0; x < w; x += 64) { g.fillRect(x, 0, 18, h); g.globalAlpha = .5; g.fillRect(x + 30, 0, 4, h); g.globalAlpha = 1; } }
    else if (kind === 'damask') for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) { const cx = x * 128 + 64 + (y % 2) * 64, cy = y * 128 + 64;
      g.beginPath(); for (let a = 0; a < 6.3; a += .05) { const r = 26 + 12 * Math.sin(a * 4); g.lineTo(cx + Math.cos(a) * r * .7, cy + Math.sin(a) * r); } g.fill(); }
    else if (kind === 'dots') for (let y = 16; y < h; y += 32) for (let x = 16 + (y / 32 % 2) * 16; x < w; x += 32) { g.beginPath(); g.arc(x, y, 4, 0, 6.3); g.fill(); }
    for (let i = 0; i < 700; i++) { g.fillStyle = `rgba(0,0,0,${Math.random() * .05})`; g.fillRect(Math.random() * w, Math.random() * h, 3, 3); }   // age and grime
  }, rep);
}
export const tiles = (base = 0xd8d4c4, grout = 0x9a968a, n = 4, rep = [3, 1]) => canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = hex(grout); g.fillRect(0, 0, w, h); const s = w / n;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) { const v = (Math.random() - .5) * 18, c = new THREE.Color(base); c.offsetHSL(0, 0, v / 255);
    g.fillStyle = hex(c); g.fillRect(x * s + 3, y * s + 3, s - 6, s - 6); }
}, rep);
export const picture = (draw) => canvasTex(128, 160, draw);

// ---------------------------------------------------------------- room parts
// wall(w, h, material) : a plaster wall with a skirting board along its bottom; one side faces +z
export function wall(w = 5, h = 3, m = clay(0x8a8a6e), {skirting = 0x3a2a22, rail = null} = {}) {
  const g = new THREE.Group(); const wl = add(rbox(w, h, .1, .01, .003, 3), m, g, [0, h / 2, 0]); wl.castShadow = false;
  if (skirting) add(rbox(w, .12, .03, .008), mat(skirting), g, [0, .06, .06]);
  if (rail) add(rbox(w, .04, .025, .008), mat(rail), g, [0, 1.0, .06]);              // a dado rail
  return g;
}
export function windowFrame(w = 1.0, h = 1.1, {frame = 0xe8e2d6, view = 0xcfe0f0, curtains = 0x8a4a3a, sill = true} = {}) {
  const g = new THREE.Group(), fm = mat(frame);
  const glass = add(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({color: view}), g, [0, h / 2, -.02]); glass.castShadow = false; g.userData.glass = glass;
  for (const [x, y, ww, hh] of [[0, 0, w + .1, .06], [0, h, w + .1, .06], [-w / 2, h / 2, .06, h + .1], [w / 2, h / 2, .06, h + .1], [0, h / 2, .035, h], [0, h * .55, w, .035]])
    add(rbox(ww, hh, .06, .012), fm, g, [x, y, 0]);
  if (sill) add(rbox(w + .2, .04, .14, .012), fm, g, [0, -.04, .06]);
  if (curtains) { const cm = clay(curtains, {side: THREE.DoubleSide}); add(Cp(.012, w + .5), METAL, g, [0, h + .12, .08], [0, 0, Math.PI / 2]);
    for (const s of [-1, 1]) { const c = add(turn([[.0, .02], [.09, .0], [.1, -.4], [.12, -.9], [.13, -h - .1]], .006, 6).scale(1, 1, .35), cm, g, [s * (w / 2 + .1), h + .12, .1]); c.scale.x = 1.2; } }
  return g;
}
export function door(w = .82, h = 2.0, color = 0x4a3428) {
  const g = new THREE.Group(), m = mat(color), fr = clay(0xe8e2d6);
  add(rbox(w, h, .05, .012, .003, 4), m, g, [0, h / 2, 0]);
  for (const [y, hh] of [[h * .72, h * .38], [h * .27, h * .42]]) add(rbox(w * .66, hh, .02, .01), m, g, [0, y, .03]);    // panels
  add(S(.028, 1, 1, .7), METAL, g, [w * .38, h * .48, .05]);
  for (const [x, y, ww, hh] of [[0, h + .04, w + .16, .08], [-w / 2 - .04, h / 2, .08, h + .08], [w / 2 + .04, h / 2, .08, h + .08]]) add(rbox(ww, hh, .07, .012), fr, g, [x, y, 0]);
  return g;
}
export function rug(w = 1.6, d = 1.0, a = 0x7a3a2e, b = 0xc8a46a) {
  const t = canvasTex(256, 160, (g, W, H) => { g.fillStyle = hex(a); g.fillRect(0, 0, W, H); g.strokeStyle = hex(b); g.lineWidth = 10; g.strokeRect(16, 16, W - 32, H - 32);
    g.lineWidth = 4; g.strokeRect(34, 34, W - 68, H - 68); g.fillStyle = hex(b); g.beginPath(); g.ellipse(W / 2, H / 2, 40, 26, 0, 0, 6.3); g.fill(); });
  const g = new THREE.Group(); add(rbox(w, .015, d, .007, .002, 6), clay(0xffffff, {map: t}), g, [0, .008, 0]); return g;
}

// ---------------------------------------------------------------- kitchen
export function fridge({w = .74, h = 1.8, d = .68, color = 0xd8d2c4} = {}) {
  const g = new THREE.Group(), m = mat(color);
  add(rbox(w, h, d, .06, .004, 5), m, g, [0, h / 2, 0]);
  add(rbox(w - .04, h * .34, .05, .03), m, g, [0, h * .82, d / 2 + .01]); add(rbox(w - .04, h * .6, .05, .03), m, g, [0, h * .32, d / 2 + .01]);   // two doors, a gap between
  for (const [y, l] of [[h * .73, .22], [h * .5, .34]]) add(Cp(.016, l), METAL, g, [w / 2 - .07, y, d / 2 + .055]);
  const notes = [[-.15, 1.25, 0xf0d860, .1], [.05, 1.15, 0xf0a0a0, .07], [-.05, .95, 0xffffff, .14], [.12, .8, 0x9ad0f0, .08]];   // a child's drawing, notes, magnets
  for (const [x, y, c, s] of notes) { add(new THREE.PlaneGeometry(s, s * 1.3), clay(c, {side: THREE.DoubleSide, bumpScale: .2}), g, [x, y, d / 2 + .04], [0, 0, (rnd() - .5) * .3]);
    add(S(.012, 1, 1, .6), clay([0xd03030, 0x3070d0, 0x30a050][Math.floor(rnd() * 3)]), g, [x, y + s * .55, d / 2 + .045]); }
  add(rbox(.2, .28, .07, .01), clay(0xc87830), g, [-.15, h + .14, 0]); add(rbox(.14, .2, .06, .01), clay(0x3a6a9a), g, [.12, h + .1, .05]);   // boxes on top
  return g;
}
export function counter({len = 2.4, d = .6, h = .9, body = 0x5a6a56, top = 0xcfc8b4, splash = true} = {}) {
  const g = new THREE.Group(), m = mat(body), n = Math.max(1, Math.round(len / .55));
  add(rbox(len, h - .1, d - .04, .02, .003, 4), m, g, [0, (h - .1) / 2 + .1, -.02]);
  add(rbox(len - .02, .1, d - .12, .01), DARK, g, [0, .05, -.06]);                                        // toe kick
  for (let i = 0; i < n; i++) { const x = -len / 2 + (i + .5) * len / n;
    add(rbox(len / n - .03, h - .2, .03, .015), m, g, [x, (h - .2) / 2 + .12, d / 2 - .02]);
    add(Cp(.009, .09), METAL, g, [x + (i % 2 ? -1 : 1) * (len / n / 2 - .07), h - .2, d / 2 + .01], [0, 0, Math.PI / 2]); }
  add(rbox(len + .04, .05, d + .03, .012, .002, 6), mat(top), g, [0, h + .02, 0]);
  if (splash) add(new THREE.PlaneGeometry(len, .5), clay(0xffffff, {map: tiles(0xd8d4c4, 0x9a968a, 4, [len / .5, 1])}), g, [0, h + .3, -d / 2 + .01]);
  g.userData.top = h + .045; return g;
}
export function stove() {                                   // sits on a counter top (y = counter top)
  const g = new THREE.Group(); add(rbox(.6, .03, .52, .01), clay(0x1e1c1c), g, [0, .015, 0]);
  for (const [x, z] of [[-.14, -.11], [.14, -.11], [-.14, .11], [.14, .11]]) add(lump(new THREE.TorusGeometry(.065, .01, 6, 20), .001, 20), clay(0x3a3634), g, [x, .035, z], [Math.PI / 2, 0, 0]);
  for (let i = 0; i < 4; i++) add(new THREE.CylinderGeometry(.018, .02, .025, 12), METAL, g, [-.2 + i * .13, .02, .27], [Math.PI / 2, 0, 0]);
  return g;
}
export function pan(r = .13) { const g = new THREE.Group(); add(turn([[0, 0], [r * .9, 0], [r, .012], [r * 1.02, .06]], .002, 12), clay(0x2a2826, {side: THREE.DoubleSide}), g);
  add(Cp(.014, .26), clay(0x2a2826), g, [r + .13, .045, 0], [0, 0, Math.PI / 2 - .12]); return g; }
export function sink(w = .55) { const g = new THREE.Group(); add(rbox(w, .03, .42, .01), METAL, g, [0, .01, 0]); add(rbox(w - .08, .02, .32, .02), clay(0x6a6a68), g, [0, .022, 0]);
  const tap = G(g, [0, 0, -.18]); add(Cp(.015, .2), METAL, tap, [0, .12, 0]); add(Cp(.013, .14), METAL, tap, [0, .23, .06], [Math.PI / 2, 0, 0]); return g; }
export function wallCabinets({len = 1.6, h = .7, d = .34, body = 0x5a6a56} = {}) {
  const g = new THREE.Group(), m = mat(body), n = Math.max(1, Math.round(len / .5));
  add(rbox(len, h, d, .02), m, g, [0, 0, 0]);
  for (let i = 0; i < n; i++) { const x = -len / 2 + (i + .5) * len / n; add(rbox(len / n - .03, h - .06, .03, .015), m, g, [x, 0, d / 2]); add(Cp(.009, .07), METAL, g, [x + (i % 2 ? -1 : 1) * (len / n / 2 - .06), -h / 2 + .08, d / 2 + .03]); }
  return g;
}
export function table({w = 1.2, d = .8, h = .74, color = 0x6a4a30} = {}) {
  const g = new THREE.Group(), m = mat(color); add(rbox(w, .05, d, .02, .003, 6), m, g, [0, h - .025, 0]);
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) add(turn([[.03, 0], [.025, .1], [.028, h * .5], [.022, h - .05]], .003, 10), m, g, [x * (w / 2 - .07), 0, z * (d / 2 - .07)]);
  return g;
}
export function chair({color = 0x6a4a30} = {}) {
  const g = new THREE.Group(), m = mat(color); add(rbox(.42, .04, .4, .015), m, g, [0, .45, 0]);
  for (const [x, z] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) add(Cp(.018, .42), m, g, [x * .18, .22, z * .17]);
  for (const x of [-.18, .18]) add(Cp(.018, .5), m, g, [x, .72, -.18]); for (const y of [.62, .8]) add(rbox(.38, .05, .03, .01), m, g, [0, y, -.18]);
  return g;
}
export function mug(c = 0xd8d0c0) { const g = new THREE.Group(); add(turn([[0, 0], [.04, 0], [.042, .09], [.038, .095]], .001, 20), clay(c), g);
  add(lump(new THREE.TorusGeometry(.025, .007, 6, 12, Math.PI), .001, 20), clay(c), g, [.042, .05, 0], [0, 0, -Math.PI / 2]); return g; }
export function jar(c = 0xc87830, h = .16) { const g = new THREE.Group(); add(turn([[0, 0], [.05, 0], [.055, h * .8], [.045, h]], .001, 16), gloss(0xe8e0d0, {transparent: true, opacity: .55}), g);
  add(turn([[0, 0], [.048, 0], [.05, h * .7], [0, h * .72]], .001, 16), clay(c), g); add(new THREE.CylinderGeometry(.05, .05, .02, 16), clay(0xb03030), g, [0, h + .01, 0]); return g; }
export function plant(h = .35) { const g = new THREE.Group(); add(turn([[0, 0], [.07, 0], [.09, .14], [.095, .15]], .002, 12), clay(0xb8643c), g);
  for (let i = 0; i < 9; i++) { const a = i * 2.4, l = h * (.6 + rnd() * .5); add(S(.03, .6, 1, .25, .002, 14).scale(1, l / .06, 1), clay(0x4a7a3a), g, [Math.sin(a) * .03, .14 + l / 2, Math.cos(a) * .03], [Math.cos(a) * .5, 0, Math.sin(a) * .5]); }
  return g; }
export function clock(r = .14) { const g = new THREE.Group(); add(new THREE.CylinderGeometry(r, r, .04, 32), clay(0xefe8d8), g, [0, 0, 0], [Math.PI / 2, 0, 0]);
  add(lump(new THREE.TorusGeometry(r, .015, 8, 32), .001, 16), clay(0x3a2a22), g); for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; add(S(.006), DARK, g, [Math.sin(a) * r * .8, Math.cos(a) * r * .8, .022]); }
  const hh = G(g, [0, 0, .025]), mh = G(g, [0, 0, .03]); add(new THREE.BoxGeometry(.008, r * .5, .004), DARK, hh, [0, r * .22, 0]); add(new THREE.BoxGeometry(.006, r * .75, .004), DARK, mh, [0, r * .35, 0]);
  g.userData.hour = hh; g.userData.minute = mh; return g; }       // turn userData.minute.rotation.z to move it
export function frame(w = .3, h = .38, drawFn = null, color = 0x5a3a22) {
  const g = new THREE.Group(); add(rbox(w, h, .03, .01), mat(color), g);
  add(new THREE.PlaneGeometry(w - .07, h - .07), new THREE.MeshStandardMaterial({map: picture(drawFn || ((c, W, H) => { c.fillStyle = '#8aa0b0'; c.fillRect(0, 0, W, H);
    c.fillStyle = '#5a7a4a'; c.fillRect(0, H * .6, W, H); c.fillStyle = '#d8c8a0'; c.beginPath(); c.arc(W * .7, H * .3, 14, 0, 6.3); c.fill(); })), roughness: .9}), g, [0, 0, .017]);
  return g; }
export function books(n = 6, h = .22) { const g = new THREE.Group(); let x = 0;
  for (let i = 0; i < n; i++) { const t = .03 + rnd() * .025, hh = h * (.8 + rnd() * .25); add(rbox(t, hh, .15, .004), clay([0x8a3a32, 0x3a5a7a, 0x6a7a3a, 0xc9a24a, 0x4a3a5a][i % 5]), g, [x + t / 2, hh / 2, 0], [0, 0, i === n - 1 ? -.25 : 0]); x += t + .003; }
  return g; }
export function shelf(w = 1.0) { const g = new THREE.Group(); add(rbox(w, .03, .22, .008), clay(0x4a3424), g); for (const x of [-w / 2 + .1, w / 2 - .1]) add(rbox(.025, .12, .18, .006), clay(0x3a2a22), g, [x, -.07, 0]); return g; }

// ---------------------------------------------------------------- attic
export function cardBox(w = .5, h = .38, d = .4) {
  const g = new THREE.Group(), m = clay(0x9a7a52);
  add(rbox(w, h, d, .015, .004, 6), m, g, [0, h / 2, 0]);
  add(rbox(w + .004, .03, .06, .004), clay(0xc8b088, {bumpScale: .2}), g, [0, h + .002, 0]);                 // tape
  add(new THREE.PlaneGeometry(w * .4, h * .3), clay(0xe8e0cc, {bumpScale: .2}), g, [-w * .15, h * .55, d / 2 + .003]);   // a label
  return g;
}
export function sheetChair() {                                // an armchair under a dust sheet
  const g = new THREE.Group(), m = clay(0xd8d2c4, {bumpScale: 1.4});
  add(turn([[0, 0], [.42, 0], [.46, .3], [.4, .5], [.36, .62], [.3, .9], [.12, 1.02], [0, 1.03]], .012, 4).scale(1, 1, .8), m, g);
  for (const x of [-.3, .3]) add(S(.12, 1, 1.5, 1.6, .01, 5), m, g, [x, .55, .05]);
  return g;
}
export function oldLamp() { const g = new THREE.Group(); add(turn([[0, 0], [.12, 0], [.1, .04], [.03, .06], [.025, .9], [0, .92]], .002, 12), clay(0x6a5a3a), g);
  add(turn([[.2, 0], [.18, .04], [.1, .26], [.08, .28]], .003, 10), clay(0xc8a878, {side: THREE.DoubleSide}), g, [0, .78, 0]); return g; }
export function cobweb(size = .5) {                           // a few sagging threads between two beams
  const g = new THREE.Group(), m = new THREE.MeshBasicMaterial({color: 0xd8d8d0, transparent: true, opacity: .35});
  for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * .5; add(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0), new THREE.Vector3(Math.cos(a) * size * .5, -Math.sin(a) * size * .5 - .04, 0), new THREE.Vector3(Math.cos(a) * size, -Math.sin(a) * size, 0)]), 8, .0015, 3), m, g).castShadow = false; }
  for (let k = 1; k < 4; k++) { const r = size * k / 4, pts = []; for (let i = 0; i <= 8; i++) { const a = i / 8 * Math.PI * .5; pts.push(new THREE.Vector3(Math.cos(a) * r, -Math.sin(a) * r - .02 * Math.sin(i / 8 * Math.PI), 0)); }
    add(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, .0012, 3), m, g).castShadow = false; }
  return g;
}

// ================================================================ lighting and atmosphere
// lampPool(parent, [x,y,z], {color, power, dist, shade}): a practical lamp: a bulb you can see, a shade, a warm pool of light with shadows
export function lampPool(parent, pos, {color = 0xffc878, power = 2.5, dist = 4, shade = true, shadows = true} = {}) {
  const g = G(parent, pos), l = new THREE.PointLight(color, power, dist, 1.6); l.castShadow = shadows; l.shadow.mapSize.set(512, 512); g.add(l);
  add(S(.035), new THREE.MeshBasicMaterial({color: new THREE.Color(color).lerp(new THREE.Color(0xffffff), .6)}), g).castShadow = false;
  if (shade) add(turn([[.16, -.02], [.14, .03], [.07, .14], [.05, .16]], .002, 10), clay(0x3a3430, {side: THREE.DoubleSide}), g, [0, -.02, 0]).castShadow = false;
  return {group: g, light: l};
}
// windowBeam(parent, {from, to, color, power, width}): light through a window: a spot with shadows, a visible beam in the air, dust drifting in it.
// Call beam.update(t) each frame (the dust moves with time, the same at any frame).
export function windowBeam(parent, {from = [0, 2, -2], to = [0, 0, 0], color = 0xdfe8ff, power = 6, width = .5, dust = 160, beamOpacity = .07} = {}) {
  const g = new THREE.Group(); parent.add(g); const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), dir = b.clone().sub(a), L = dir.length();
  const sp = new THREE.SpotLight(color, power, L * 1.6, Math.atan(width / L) * 1.6, .6, 1.2); sp.position.copy(a); sp.target.position.copy(b); sp.castShadow = true; sp.shadow.mapSize.set(1024, 1024); g.add(sp, sp.target);
  const cone = new THREE.Mesh(new THREE.CylinderGeometry(width * .45, width * 1.1, L, 24, 1, true).translate(0, -L / 2, 0),
    new THREE.MeshBasicMaterial({color, transparent: true, opacity: beamOpacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide}));
  cone.position.copy(a); cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), dir.clone().normalize()); cone.castShadow = cone.receiveShadow = false; g.add(cone);
  const n = dust, seeds = Array.from({length: n}, () => [rnd(), rnd(), rnd(), rnd()]), pos = new Float32Array(n * 3);
  const pts = new THREE.Points(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(pos, 3)),
    new THREE.PointsMaterial({color: 0xfff6e0, size: .012, transparent: true, opacity: .7, depthWrite: false, blending: THREE.AdditiveBlending}));
  g.add(pts); const side = new THREE.Vector3(), up2 = new THREE.Vector3();
  side.crossVectors(dir, new THREE.Vector3(0, 1, 0)).normalize(); if (side.lengthSq() < .1) side.set(1, 0, 0); up2.crossVectors(side, dir).normalize();
  const update = t => { seeds.forEach(([u, v, w, s], i) => { const along = (u + t * .012 * (.5 + s)) % 1, r = width * (.45 + .65 * along) * Math.sqrt(v), an = w * 6.28 + t * .15 * (s - .5);
      const p = a.clone().addScaledVector(dir, along).addScaledVector(side, Math.cos(an) * r).addScaledVector(up2, Math.sin(an) * r + Math.sin(t * .7 + s * 9) * .01);
      pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z; }); pts.geometry.attributes.position.needsUpdate = true; };
  update(0); return {group: g, light: sp, beam: cone, update};
}
// haze(scene, color, density): air you can see: far things fade into it (set the scene background to the same colour)
export function haze(scene, color = 0x0a0c10, density = .06) { scene.fog = new THREE.FogExp2(color, density); return scene.fog; }

// ================================================================ the street
// house({w, h, color, roof, lit}): a terraced house front: brick or render, framed windows (some lit), a panelled door on steps, a chimney, a gutter
export function house({w = 1.9, h = 2.7, color = 0x6a3a2e, roof = 0x2a2224, lit = [false, true, false], door = 0x3a2a3e} = {}) {
  const g = new THREE.Group(), wallM = clay(color, {bumpScale: 1.4});
  add(rbox(w, h, 1.2, .03, .006, 3), wallM, g, [0, h / 2, 0]);
  const rf = add(turn([[w * .76, 0], [w * .72, .06], [.02, .85]], .006, 4, Math.PI / 4, Math.PI * 2, 4), clay(roof), g, [0, h, 0]); rf.scale.set(1, 1, .7);   // the roof
  add(rbox(.22, .5, .22, .02), clay(color), g, [w * .3, h + .5, -.1]); add(rbox(.26, .05, .26, .01), clay(0x3a3632), g, [w * .3, h + .76, -.1]);   // chimney
  add(Cp(.025, w), clay(0x2a2a2a), g, [0, h - .02, .62], [0, 0, Math.PI / 2]);                                                       // gutter
  const winAt = [[.4, .78], [-.4, 1.85], [.4, 1.85]];
  winAt.forEach(([x, y], i) => { const on = lit[i]; const fr = clay(0xe8e2d6);
    const wp = add(new THREE.PlaneGeometry(.42, .52), new THREE.MeshBasicMaterial({color: on ? 0xd8a860 : 0x0a0c12}), g, [x, y, .605]); wp.castShadow = false; wp.userData.on = on;
    for (const [dx, dy, ww, hh] of [[0, .27, .5, .05], [0, -.27, .5, .05], [-.23, 0, .05, .56], [.23, 0, .05, .56], [0, 0, .025, .52], [0, .05, .44, .025]]) add(rbox(ww, hh, .04, .01), fr, g, [x + dx, y + dy, .615]);
    add(rbox(.56, .04, .1, .01), fr, g, [x, y - .3, .64]); });
  const d = G(g, [-.42, 0, .6]); add(rbox(.42, .88, .05, .01), clay(door), d, [0, .5, .02]); add(S(.018), clay(0xc8a860), d, [.15, .5, .055]);
  add(rbox(.6, .06, .25, .01), clay(0x8a847a), g, [-.42, .03, .72]);                                                                 // the step
  g.userData.lit = lit; return g;
}
export function streetLamp(h = 3.1, color = 0xd8f0c8, power = 3) {
  const g = new THREE.Group(), m = clay(0x2a2c2a); add(turn([[.07, 0], [.06, .2], [.035, .25], [.032, h - .1], [.02, h]], .002, 10), m, g);
  add(Cp(.02, .35), m, g, [0, h - .02, .16], [Math.PI / 2, 0, 0]); add(turn([[.12, -.06], [.1, .02], [.04, .08]], .002, 10), m, g, [0, h - .05, .33]);
  add(S(.06, 1, .5, 1), new THREE.MeshBasicMaterial({color}), g, [0, h - .1, .33]).castShadow = false;
  const l = new THREE.PointLight(color, power, 6, 1.4); l.position.set(0, h - .2, .33); g.add(l); g.userData.light = l; return g;
}
export function car(color = 0x8a2a24) {                       // a small rounded car, nose towards +x
  const g = new THREE.Group(), b = clay(color), glass = gloss(0x1a2430, {roughness: .15});
  add(rbox(1.55, .4, .76, .12, .004, 4), b, g, [0, .36, 0]); add(rbox(.9, .34, .7, .14, .004, 4), b, g, [-.08, .68, 0]);
  for (const z of [.351, -.351]) add(new THREE.PlaneGeometry(.75, .22), glass, g, [-.08, .7, z], [0, z > 0 ? 0 : Math.PI, 0]);
  add(new THREE.PlaneGeometry(.62, .24), glass, g, [.37, .7, 0], [0, Math.PI / 2, -.45]); add(new THREE.PlaneGeometry(.62, .24), glass, g, [-.53, .7, 0], [0, -Math.PI / 2, .45]);
  for (const [x, z] of [[-.48, .37], [.48, .37], [-.48, -.37], [.48, -.37]]) { add(lump(new THREE.TorusGeometry(.11, .055, 10, 20), .003, 10), clay(0x141414), g, [x, .16, z]); add(new THREE.CylinderGeometry(.07, .07, .1, 16), METAL, g, [x, .16, z], [Math.PI / 2, 0, 0]); }
  for (const z of [.24, -.24]) { add(S(.05, .5, 1, 1), new THREE.MeshBasicMaterial({color: 0xfff2c8}), g, [.77, .4, z]); add(S(.04, .5, 1, 1), new THREE.MeshBasicMaterial({color: 0xff2010}), g, [-.77, .4, z]); }
  add(rbox(.08, .1, .7, .03), clay(0x3a3a3a), g, [.8, .24, 0]); add(rbox(.08, .1, .7, .03), clay(0x3a3a3a), g, [-.8, .24, 0]);   // bumpers
  return g;
}
export function bin(color = 0x2a4a2e) { const g = new THREE.Group(); add(rbox(.5, .85, .5, .04), clay(color), g, [0, .44, 0]); add(rbox(.54, .06, .56, .02), clay(color), g, [0, .9, 0], [-.05, 0, 0]);
  for (const x of [-.18, .18]) add(lump(new THREE.TorusGeometry(.06, .025, 8, 14), .001, 20), clay(0x141414), g, [x, .06, -.25], [0, Math.PI / 2, 0]); return g; }
export function fence(len = 2, color = 0xd8d2c4) { const g = new THREE.Group(), m = clay(color); const n = Math.round(len / .14);
  for (let i = 0; i < n; i++) add(rbox(.08, .7 + (i % 2) * .04, .03, .01), m, g, [-len / 2 + i * .14, .35, 0]); for (const y of [.18, .52]) add(rbox(len, .06, .025, .01), m, g, [0, y, -.025]); return g; }
export function hedge(len = 1.4) { const g = new THREE.Group(); for (let i = 0; i < Math.round(len / .3); i++) add(S(.24, 1, .9, .8, .03, 3), clay(0x2e4a2e, {bumpScale: 2}), g, [-len / 2 + .15 + i * .3, .38, 0]); return g; }
