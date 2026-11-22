// The library's places: whole lit sets made from the library's generated models plus our own ground, sky, fog and lights.
//   import {buildSet, SETS} from './lib_sets.js';
//   const S = await buildSet('cemetery', scene);            // adds the set to the scene, sets fog and background
//   S.root (Group; move it with {at: [x, 0, z]})  S.spots.haru (where a character stands)  S.shots (named cameras: {pos, look, fov})
//   S.apply()  re-applies this set's sky and fog (when a reel cuts between sets)    S.update(t)  flicker, drift, sway (call each frame)
//   options: {at: [x, y, z], time: 'night' | 'dusk' | 'day'}
// Sets: street, hospital, ward, church, church_in, cemetery, desert, playground, forest.  Everything faces +z: the camera looks down -z.
import * as THREE from 'three';
import {lib} from './library.js';
import {clay, add, G} from './clay.js';
import {rbox, lampPool} from './clay_sets.js';

const PI = Math.PI, V = (x, y, z) => new THREE.Vector3(x, y, z);
const rng = s => () => (s = (s * 16807) % 2147483647) / 2147483647;

// ---------------------------------------------------------------- shared pieces
function skyDome(parent, top, horizon, {moon = null, r = 140} = {}) {        // a gradient sky that ignores the fog; an optional moon disc
  const m = new THREE.ShaderMaterial({side: THREE.BackSide, depthWrite: false, fog: false, uniforms: {top: {value: new THREE.Color(top)}, hor: {value: new THREE.Color(horizon)}},
    vertexShader: 'varying vec3 p; void main(){ p = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: 'uniform vec3 top; uniform vec3 hor; varying vec3 p; void main(){ float k = smoothstep(-.05, .55, p.y); gl_FragColor = vec4(mix(hor, top, k), 1.); }'});
  const dome = new THREE.Mesh(new THREE.SphereGeometry(r, 32, 16), m); dome.renderOrder = -10; dome.castShadow = dome.receiveShadow = false; parent.add(dome);
  if (moon) { const d = new THREE.Mesh(new THREE.CircleGeometry(r * .035, 40), new THREE.MeshBasicMaterial({color: moon, fog: false}));
    d.position.set(-r * .35, r * .45, -r * .8); d.lookAt(0, 0, 0); parent.add(d); }
  return dome;
}
function ground(parent, size, color, {bump = 2, hills = 0, seed = 3, flat = 8} = {}) {   // a ground plane; hills: gentle bumps away from the middle
  const g = new THREE.PlaneGeometry(size, size, 120, 120).rotateX(-PI / 2), p = g.attributes.position;
  if (hills) for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), d = Math.hypot(x, z), k = THREE.MathUtils.smoothstep(d, flat, flat * 2.5);
    p.setY(i, k * hills * (Math.sin(x * .09 + seed) * Math.cos(z * .07 - seed) + .5 * Math.sin(x * .23 + z * .19 + seed * 2))); }
  g.computeVertexNormals(); const m = add(g, clay(color, {bumpScale: bump}), parent); m.castShadow = false; m.receiveShadow = true; return m;
}
function groundFog(parent, {n = 14, area = [30, 30], y = .25, color = 0xb8c4d8, opacity = .12, seed = 5} = {}) {   // low drifting fog sheets
  const c = document.createElement('canvas'); c.width = c.height = 128; const x = c.getContext('2d'), gr = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c), r = rng(seed), sheets = [];
  for (let i = 0; i < n; i++) { const s = 6 + r() * 8, m = new THREE.Mesh(new THREE.PlaneGeometry(s, s * .6).rotateX(-PI / 2),
      new THREE.MeshBasicMaterial({map: tex, color, transparent: true, opacity: opacity * (.6 + r() * .6), depthWrite: false}));
    m.position.set((r() - .5) * area[0], y + r() * .5, (r() - .5) * area[1]); m.castShadow = m.receiveShadow = false; m.renderOrder = 5; parent.add(m);
    sheets.push({m, x0: m.position.x, sp: .1 + r() * .2, ph: r() * 6}); }
  return t => sheets.forEach(s => { s.m.position.x = s.x0 + Math.sin(t * s.sp + s.ph) * 1.5; });
}
function moonLight(parent, color, power, from = [-18, 26, 14], target = [0, 0, -4], span = 22) {
  const l = new THREE.DirectionalLight(color, power); l.position.set(...from); l.target.position.set(...target); l.castShadow = true;
  l.shadow.mapSize.set(2048, 2048); l.shadow.bias = -.0005; Object.assign(l.shadow.camera, {left: -span, right: span, top: span, bottom: -span, near: 1, far: 90});
  parent.add(l, l.target); return l;
}
async function put(parent, name, x, z, ry = 0, o = {}) { const g = await lib.prop(name, o); g.position.set(x, o.y || 0, z); g.rotation.y = ry; parent.add(g); return g; }
function flicker(light, base, seed = 1) {   // a failing bulb: mostly on, short drops
  return t => { const k = Math.floor(t * 24), h = Math.abs(Math.sin(k * 12.9898 + seed * 78.233) * 43758.5453) % 1, w = Math.sin(t * 1.3 + seed) > .2;
    light.intensity = base * (w && h > .82 ? .15 + h * .3 : 1); };
}
// a room: floor, ceiling and four walls of the given size, the open side (+z) left out for the camera
function room(parent, w, d, h, {floor = 0x6a6a66, wall = 0x8a9a8a, ceil = 0x4a4a48, open = true} = {}) {
  add(rbox(w, .1, d, .01, .003, 2), clay(floor, {bumpScale: .6}), parent, [0, -.05, 0]);
  add(rbox(w, .1, d, .01, .003, 2), clay(ceil), parent, [0, h + .05, 0]);
  const wm = clay(wall, {bumpScale: 1});
  for (const s of [-1, 1]) add(rbox(.12, h, d, .01, .004, 2), wm, parent, [s * w / 2, h / 2, 0]);
  add(rbox(w, h, .12, .01, .004, 2), wm, parent, [0, h / 2, -d / 2]);
  if (!open) add(rbox(w, h, .12, .01, .004, 2), wm, parent, [0, h / 2, d / 2]);
}

// ---------------------------------------------------------------- the sets
// Each builder fills `g` and returns {sky: [background, fogColour, fogDensity], spots, shots, updates: [fn]}
const BUILD = {
  // a night street: three houses across the road, street lamps, a parked car, trees
  async street(g, o) {
    ground(g, 160, 0x34452e, {hills: 1.2, flat: 22});
    add(rbox(80, .06, 7, .01, .002, 2), clay(0x2a2a2e, {bumpScale: 1.6}), g, [0, .02, 0]);                       // road (x along), z -3.5 .. 3.5
    for (const z of [-4.6, 4.6]) add(rbox(80, .16, 2.2, .01, .002, 2), clay(0x6a6864), g, [0, .08, z]);          // pavements
    for (let x = -38; x < 40; x += 4) add(rbox(1.8, .02, .14, .005), clay(0xd8d2b8), g, [x, .06, 0]);          // centre line
    await put(g, 'house_family', -10, -12, 0); await put(g, 'house_old', 0, -12.5, 0); await put(g, 'cottage', 9.5, -11, 0);
    const ups = [];
    for (const x of [-15, -5, 5, 15]) { await put(g, 'street_lamp', x, -4.2, 0, {y: .16});
      const L = new THREE.PointLight(0xffd8a0, 26, 14, 1.6); L.position.set(x, 4.1, -3.4); L.castShadow = true; L.shadow.mapSize.set(1024, 1024); g.add(L);
      if (x === 5) ups.push(flicker(L, 26, 3)); }
    for (const [x, z] of [[-6, -9], [6, -9], [-13, -10]]) { const L = new THREE.PointLight(0xffb060, 6, 6, 2); L.position.set(x, 2.2, z); g.add(L); }   // porch and window glow
    await put(g, 'car', -8, 2, PI / 2); await put(g, 'bin', 2.5, -5, .3, {y: .16}); await put(g, 'tree', -19, -9, 0, {height: 6}); await put(g, 'tree', 16, -8.5, 1, {height: 5.5});
    g.add(new THREE.HemisphereLight(0x5a6a8a, 0x141210, .7)); moonLight(g, 0x8aa0d8, .9);
    skyDome(g, 0x0a1020, 0x1c2a40, {moon: 0xe8ecf4});
    return {sky: [0x101828, 0x101828, .022], spots: {haru: V(0, 0, 3.2), door: V(0, 0, -9.2)}, updates: ups,
      shots: {wide: {pos: [3, 2.2, 13], look: [0, 3, -9], fov: 50}, low: {pos: [-1.5, .35, 4.5], look: [0, 4, -12], fov: 55}}};
  },
  // outside the hospital at night: the building, a car park, a flickering lamp
  async hospital(g) {
    ground(g, 160, 0x2e3a2a, {hills: 1, flat: 24});
    add(rbox(30, .06, 16, .01, .002, 2), clay(0x2e2e32, {bumpScale: 1.6}), g, [0, .02, -2]);                    // car park
    for (let x = -12; x <= 12; x += 3) add(rbox(.1, .02, 4, .005), clay(0xd8d2b8), g, [x, .06, 2]);            // bay lines
    await put(g, 'hospital', 0, -16, 0);
    await put(g, 'car', -7.5, 2, 0); await put(g, 'car_wreck', 4.5, 2.4, PI);
    const ups = [];
    for (const [x, z, f] of [[-10, -4, 0], [10, -4, 1]]) { await put(g, 'street_lamp', x, z, 0);
      const L = new THREE.PointLight(0xd8f0ff, 22, 14, 1.6); L.position.set(x, 4.1, z + .8); L.castShadow = true; L.shadow.mapSize.set(1024, 1024); g.add(L); if (f) ups.push(flicker(L, 22, 7)); }
    const door = new THREE.PointLight(0xe8fff0, 14, 10, 1.8); door.position.set(0, 2.8, -11.5); g.add(door);          // the entrance light
    g.add(new THREE.HemisphereLight(0x4a5a7a, 0x101010, .6)); moonLight(g, 0x8aa0d8, .7, [-18, 26, 14], [0, 0, -8], 26);
    skyDome(g, 0x0a1020, 0x1c2a40, {moon: 0xe8ecf4});
    return {sky: [0x101828, 0x101828, .02], spots: {haru: V(0, 0, 4), door: V(0, 0, -11)}, updates: ups,
      shots: {wide: {pos: [4, 2.5, 16], look: [0, 4.5, -14], fov: 52}, low: {pos: [-1, .3, 5], look: [0, 6, -16], fov: 58}}};
  },
  // a hospital ward inside: a long room, green walls, two beds, a drip stand, a screen, a wheelchair, buzzing strip lights (one failing)
  async ward(g) {
    room(g, 7, 12, 3, {floor: 0x8a8e88, wall: 0x8aa094, ceil: 0x6a6e6a});
    add(rbox(7, .9, .06, .005), clay(0x5a7466), g, [0, .45, -5.9]);                                           // a darker band along the back wall
    for (const s of [-1, 1]) add(rbox(.06, .9, 12, .005), clay(0x5a7466), g, [s * 3.42, .45, 0]);
    await put(g, 'hospital_bed', -2, -3.6, PI / 2); await put(g, 'hospital_bed', 2, -3.6, PI / 2);
    await put(g, 'drip_stand', -.9, -4.6, .4); await put(g, 'screen', .3, -2.4, .3); await put(g, 'wheelchair', 2.2, 1.8, -2.4);
    await put(g, 'bed', -2.3, 2.6, PI / 2, {length: 2.0});
    const ups = [];
    for (const [z, f] of [[-4, 0], [0, 1], [4, 0]]) {
      add(rbox(1.4, .05, .25, .01), new THREE.MeshBasicMaterial({color: 0xeaffff}), g, [0, 2.97, z]);
      const L = new THREE.PointLight(0xdff8f0, 6, 9, 1.4); L.position.set(0, 2.75, z); L.castShadow = z === -4; if (L.castShadow) L.shadow.mapSize.set(1024, 1024); g.add(L);
      if (f) ups.push(flicker(L, 6, 11)); }
    g.add(new THREE.HemisphereLight(0x7a8a8a, 0x1a1a1a, .35));
    return {sky: [0x0a0c0c, 0x0a0c0c, .03], spots: {haru: V(0, 0, 1.5), bed: V(-2, 0, -3.6)}, updates: ups,
      shots: {wide: {pos: [0, 1.6, 6], look: [0, 1.1, -4], fov: 55}, bed: {pos: [-.4, 1.3, -.8], look: [-2, .7, -3.8], fov: 45}}};
  },
  // the church from outside: the church, a few graves, a dead tree, a lantern by the door
  async church(g) {
    ground(g, 160, 0x34452e, {hills: 1.6, flat: 20});
    add(rbox(2.2, .05, 14, .01, .002, 2), clay(0x7a746a, {bumpScale: 1.4}), g, [0, .02, -4]);                 // the path to the door
    await put(g, 'church', 0, -16, 0);
    const r = rng(11);
    for (let i = 0; i < 10; i++) { const x = (i % 2 ? 1 : -1) * (3 + r() * 6), z = -2 - r() * 9; await put(g, r() > .5 ? 'gravestone' : 'cross_grave', x, z, (r() - .5) * .4, {height: .8 + r() * .5}); }
    await put(g, 'dead_tree', -9, -9, .6, {height: 7});
    const lan = new THREE.PointLight(0xffb060, 10, 9, 1.8); lan.position.set(1.4, 2.6, -10.5); lan.castShadow = true; lan.shadow.mapSize.set(1024, 1024); g.add(lan);
    g.add(new THREE.HemisphereLight(0x4a5a80, 0x0a0808, .7)); moonLight(g, 0x8aa0d8, 1.0, [-18, 26, 14], [0, 0, -10], 26);
    skyDome(g, 0x0a1020, 0x1c2a40, {moon: 0xe8ecf4});
    return {sky: [0x101828, 0x101828, .02], spots: {haru: V(0, 0, 3), door: V(0, 0, -10)}, updates: [],
      shots: {wide: {pos: [5, 2.5, 14], look: [0, 6, -14], fov: 52}, low: {pos: [-1.2, .3, 4], look: [0, 8, -16], fov: 58}}};
  },
  // inside the church: a long nave, pews in two rows, the altar, candles, tall moonlit windows
  async church_in(g) {
    room(g, 9, 20, 7, {floor: 0x5a544c, wall: 0x8a8274, ceil: 0x2a2622});
    for (let i = 0; i < 5; i++) for (const s of [-1, 1]) await put(g, 'pew', s * 2.3, -5.2 + i * 1.9, 0, {length: 3.2});
    add(rbox(9, .3, 4, .01), clay(0x6a6258), g, [0, .15, -8]);                                                 // the raised end
    await put(g, 'altar', 0, -8.6, 0, {y: .3});
    const ups = [];
    for (const x of [-2.4, 2.4]) { await put(g, 'candle_stand', x, -8, 0, {y: .3});
      const L = new THREE.PointLight(0xffa850, 16, 14, 1.4); L.position.set(x, 2.0, -7.7); L.castShadow = true; L.shadow.mapSize.set(512, 512); g.add(L);
      ups.push(t => { L.intensity = 16 * (.85 + .15 * Math.sin(t * 9 + x) * Math.sin(t * 13.7 + x * 3)); }); }
    const win = new THREE.MeshBasicMaterial({color: 0x9ab0e0});
    for (let i = 0; i < 4; i++) for (const s of [-1, 1]) {
      const w = add(new THREE.PlaneGeometry(1.0, 3.0), win, g, [s * 4.43, 3.8, -6 + i * 4], [0, -s * PI / 2, 0]); w.castShadow = false;
      const top = add(new THREE.CircleGeometry(.5, 20, 0, PI), win, g, [s * 4.43, 5.3, -6 + i * 4], [0, -s * PI / 2, 0]); top.castShadow = false; }
    for (const z of [-2, 4]) { const lamp = new THREE.PointLight(0xffb870, 5, 9, 1.6); lamp.position.set(0, 4.6, z); g.add(lamp);
      add(new THREE.SphereGeometry(.12, 12, 8), new THREE.MeshBasicMaterial({color: 0xffd8a0}), g, [0, 4.6, z]).castShadow = false; add(new THREE.CylinderGeometry(.01, .01, 2.4), clay(0x222222), g, [0, 5.8, z]); }
    const moon = new THREE.SpotLight(0x9ab0e8, 70, 30, .45, .5, 1.2); moon.position.set(-4.2, 5.2, 2); moon.target.position.set(1.5, 0, 0); moon.castShadow = true; moon.shadow.mapSize.set(1024, 1024); g.add(moon, moon.target);
    g.add(new THREE.HemisphereLight(0x6a6a78, 0x2a1f18, .7));
    return {sky: [0x08080a, 0x08080a, .02], spots: {haru: V(0, 0, 5.5), altar: V(0, .3, -7.6)}, updates: ups,
      shots: {wide: {pos: [0, 2.6, 9.4], look: [0, 1.4, -8], fov: 55}, altar: {pos: [0, 1.3, -3.9], look: [0, 1.3, -8.6], fov: 45}}};
  },
  // the cemetery at night: the gate, iron fence, rows of graves, the weeping angel, a crypt, dead trees, ground fog
  async cemetery(g) {
    ground(g, 160, 0x2e3a28, {hills: 1.8, flat: 16, bump: 3});
    add(rbox(2.4, .05, 26, .01, .002, 2), clay(0x5a5448, {bumpScale: 2}), g, [0, .02, -9]);                   // the gravel path
    await put(g, 'cemetery_gate', 0, 4, 0);
    for (let x = 3; x < 22; x += 3) for (const s of [-1, 1]) await put(g, 'fence', s * (x + .1), 4, 0, {length: 3.0});
    const r = rng(21);
    for (let row = 0; row < 6; row++) for (let i = 0; i < 6; i++) { const s = i < 3 ? -1 : 1, x = s * (2.4 + (i % 3) * 2.3 + (r() - .5) * .5), z = -1 - row * 3.2 + (r() - .5) * .6;
      await put(g, r() > .45 ? 'gravestone' : 'cross_grave', x, z, (r() - .5) * .5, {height: .7 + r() * .6}); }
    await put(g, 'angel', 3.6, -8.5, -.5, {height: 2.2}); await put(g, 'crypt', -6, -20, .25, {height: 4});
    await put(g, 'dead_tree', -9, -6, 0, {height: 7.5}); await put(g, 'dead_tree', 10, -14, 2, {height: 6.5}); await put(g, 'dead_tree', 2, -24, 4, {height: 8});
    const lan = new THREE.PointLight(0xffb060, 9, 9, 1.8); lan.position.set(1.6, 3.2, 4.4); lan.castShadow = true; lan.shadow.mapSize.set(1024, 1024); g.add(lan);   // a lamp on the gate
    g.add(new THREE.HemisphereLight(0x4a5a80, 0x0a0808, .6)); moonLight(g, 0x9ab0e8, 1.3, [-14, 22, -10], [0, 0, -8], 28);   // backlit: the moon behind the graves
    skyDome(g, 0x0a1020, 0x24344c, {moon: 0xf0f2f8});
    return {sky: [0x121a2a, 0x121a2a, .028], spots: {haru: V(0, 0, 1), gate: V(0, 0, 4.5), angel: V(3.6, 0, -8.5), crypt: V(-6, 0, -17.5)}, updates: [],
      shots: {wide: {pos: [0, 2.2, 13], look: [0, 1.5, -6], fov: 50},
        angel: {pos: [1.4, 1.1, -5.2], look: [3.6, 1.6, -8.5], fov: 40}, crypt: {pos: [-3, 1.5, -11], look: [-6, 1.8, -20], fov: 45}}};
  },
  // the desert: endless dunes, a fading road, the dead gas station, a wreck, a skull, rocks. time: 'dusk' (default) or 'night'
  async desert(g, o) {
    const night = o.time === 'night';
    ground(g, 260, 0xc89a64, {hills: 4, flat: 18, bump: 2.5, seed: 7});
    const road = add(rbox(5, .04, 200, .01, .002, 2), clay(0x5a5048, {bumpScale: 2}), g, [6, .02, -80]); road.receiveShadow = true;
    for (let z = 0; z > -180; z -= 6) add(rbox(.14, .02, 2.4, .005), clay(0xc8a850), g, [6, .05, z - 2]);
    await put(g, 'gas_station', -3, -8, .35, {height: 5}); await put(g, 'car_wreck', 2.5, -2.5, -.6);
    await put(g, 'cow_skull', -.8, 1.4, .8); await put(g, 'rocks', -9, -1, .5, {height: 2.2}); await put(g, 'rocks', 11, -14, 2, {height: 3.2});
    await put(g, 'dead_tree', 9, -4, 1.2, {height: 5}); await put(g, 'street_lamp', 3.2, -7, 0);
    const ups = [];
    if (night) {
      const L = new THREE.PointLight(0xffe0a0, 18, 12, 1.6); L.position.set(-3, 4.2, -6); L.castShadow = true; L.shadow.mapSize.set(1024, 1024); g.add(L); ups.push(flicker(L, 18, 5));
      g.add(new THREE.HemisphereLight(0x3a4a70, 0x1a1208, .7)); moonLight(g, 0x8aa0d8, 1.0, [16, 22, -20], [0, 0, -4], 26);
      skyDome(g, 0x060a18, 0x1a2238, {moon: 0xf0f0f4});
      return {sky: [0x141a2a, 0x141a2a, .018], spots: {haru: V(0, 0, 3)}, updates: ups, shots: desertShots};
    }
    const sun = new THREE.DirectionalLight(0xffa060, 2.4); sun.position.set(30, 8, -40); sun.target.position.set(0, 0, -4); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.bias = -.0005; Object.assign(sun.shadow.camera, {left: -26, right: 26, top: 26, bottom: -26, near: 1, far: 120}); g.add(sun, sun.target);
    g.add(new THREE.HemisphereLight(0x7a6a9a, 0x6a4a2a, .9));
    const L = new THREE.PointLight(0xffe0a0, 8, 10, 1.6); L.position.set(-3, 4.2, -6); g.add(L); ups.push(flicker(L, 8, 5));
    skyDome(g, 0x2a2a5a, 0xf08a4a, {moon: null});
    return {sky: [0xd08860, 0xc88060, .012], spots: {haru: V(0, 0, 3)}, updates: ups, shots: desertShots};
  },
  // an empty playground at night: swings, a slide, the roundabout, a bench, one lamp, trees, fog
  async playground(g) {
    ground(g, 160, 0x30402a, {hills: 1.2, flat: 16});
    add(new THREE.CircleGeometry(9, 48).rotateX(-PI / 2), clay(0x6a5844, {bumpScale: 2.5}), g, [0, .03, -3]);    // bare earth under the play things
    await put(g, 'swings', -3.5, -4, .2); await put(g, 'slide', 3.2, -5, -.5); const rb = await put(g, 'roundabout', .5, -1, 0);
    await put(g, 'bench', 5.5, 1.5, -1.2); await put(g, 'bin', 7, 1.2, -.8); await put(g, 'street_lamp', 6.2, 2.6, 0);
    for (let x = -12; x <= 12; x += 3) await put(g, 'fence', x, -11, 0, {length: 3.0});
    await put(g, 'tree', -10, -8, 0, {height: 6}); await put(g, 'dead_tree', 10, -9, 1, {height: 6}); await put(g, 'tree', -13, 0, 2, {height: 5});
    const L = new THREE.PointLight(0xffd8a0, 22, 14, 1.6); L.position.set(6.2, 4.1, 3.3); L.castShadow = true; L.shadow.mapSize.set(1024, 1024); g.add(L);
    const ups = [flicker(L, 22, 9), t => { rb.rotation.y = t * .25; }];                                     // the roundabout turns slowly on its own
    g.add(new THREE.HemisphereLight(0x4a5a80, 0x0a0a08, .6)); moonLight(g, 0x8aa0d8, .8);
    skyDome(g, 0x0a1020, 0x1c2a40, {moon: 0xe8ecf4});
    return {sky: [0x101828, 0x101828, .03], spots: {haru: V(0, 0, 3.5)}, updates: ups,
      shots: {wide: {pos: [1.5, 1.8, 8], look: [0, 1.0, -4], fov: 50}, swings: {pos: [-2.4, 1.2, 1.2], look: [-3.5, 1.0, -4], fov: 40}}};
  },
  // a dark forest clearing: bare trunks all round (leafy crowns far back), fog they fade into, moonlight onto the middle
  async forest(g) {
    ground(g, 160, 0x26301e, {hills: 1.5, flat: 6, bump: 3});
    const r = rng(31);
    for (let i = 0; i < 110; i++) { const a = r() * PI * 2, d = 6 + r() * 26, x = Math.cos(a) * d, z = Math.sin(a) * d - 4;
      if (Math.hypot(x, z + 1) < 9 || (z > 0 && Math.abs(x) < 13)) continue;                                  // the clearing, and the camera side, stay open
      const leafy = d > 17 && r() > .3;                                                                       // bare trunks near, leafy crowns far back
      const t = await put(g, leafy ? 'tree' : 'dead_tree', x, z, r() * 6, {height: 6 + r() * 5}); t.scale.set(.55, 1, .55); }
    await put(g, 'rocks', -3, -3, 1, {height: 1.0}); await put(g, 'dead_tree', 4.5, -6, 2, {height: 5});
    const beam = new THREE.SpotLight(0xa8c0f0, 120, 40, .32, .6, 1.2); beam.position.set(-5, 18, -6); beam.target.position.set(0, 0, -1); beam.castShadow = true; beam.shadow.mapSize.set(2048, 2048); g.add(beam, beam.target);
    g.add(new THREE.HemisphereLight(0x4a5a80, 0x0a0c08, .8));
    return {sky: [0x1e2a3c, 0x1e2a3c, .045], spots: {haru: V(0, 0, 0)}, updates: [],
      shots: {wide: {pos: [0, 1.8, 9], look: [0, 1.4, -3], fov: 52}, low: {pos: [.8, .3, 2.6], look: [0, 6, -10], fov: 60}}};
  },
};
const desertShots = {wide: {pos: [5, 2.4, 14], look: [0, 2, -8], fov: 50}, road: {pos: [7.5, 1.4, 6], look: [6, 1, -60], fov: 45}};

export const SETS = Object.keys(BUILD);
export async function buildSet(name, scene, o = {}) {
  if (!BUILD[name]) throw new Error('no set ' + name + ' (have: ' + SETS.join(', ') + ')');
  const root = G(scene, o.at || [0, 0, 0]); root.userData.set = name;
  const R = await BUILD[name](root, o), off = root.position;
  const [bg, fogC, dens] = R.sky;
  const apply = () => { scene.background = new THREE.Color(bg); scene.fog = new THREE.FogExp2(fogC, dens); };
  apply();
  const spots = Object.fromEntries(Object.entries(R.spots).map(([k, v]) => [k, v.clone().add(off)]));
  const shots = Object.fromEntries(Object.entries(R.shots).map(([k, s]) => [k, {pos: V(...s.pos).add(off), look: V(...s.look).add(off), fov: s.fov}]));
  // 'haru': a medium shot of whoever stands on the haru spot, the set behind them
  // a soft fill on the haru spot, so a face reads in the dark (o.fill = 0 turns it off)
  if (o.fill !== 0) { const f = new THREE.PointLight(0xdfe6ff, o.fill || 2.2, 5, 1.5); f.position.copy(R.spots.haru).add(V(.8, 1.7, 2.0)); f.castShadow = false; root.add(f); root.userData.fill = f; }
  const h = spots.haru; shots.haru = {pos: h.clone().add(V(.75, 1.05, 3.1)), look: h.clone().add(V(0, .9, 0)), fov: 38};
  return {root, spots, shots, apply, update: t => R.updates.forEach(f => f(t))};
}
