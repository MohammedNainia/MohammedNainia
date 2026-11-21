// Shared low-poly horror kit: renderer + post (AO, bloom, grain, vignette), faceted helpers, paper masks, people.
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';
export {THREE};
export let W = 1080, H = 1920;

export function setup({bloom = .45, ao = true, w = 1080, h = 1920, dof = false} = {}) {
  W = w; H = h;
  const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
  renderer.setPixelRatio(1); renderer.setSize(W, H);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping;
  document.body.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(46, W / H, .03, 80);
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, cam));
  if (ao) { const p = new GTAOPass(scene, cam, W, H); p.updateGtaoMaterial({radius: .3, distanceExponent: 1.5, thickness: 1, scale: 1.2}); composer.addPass(p); }
  // depth of field (a real lens on a miniature set): dofPass.set(focusDistance, strength) each shot; strength 0 = off. Page option ?dof=0 turns it off.
  const useDof = dof && !/[?&]dof=0/.test(location.search);
  const bokeh = useDof ? new BokehPass(scene, cam, {focus: 2, aperture: .0007, maxblur: .012}) : null;
  if (bokeh) composer.addPass(bokeh);
  const dofPass = {set(dist, k = 1) { if (!bokeh) return; bokeh.enabled = k > 0; bokeh.uniforms.focus.value = dist; bokeh.uniforms.aperture.value = .0007 * k; }};
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), bloom, .6, .85));
  composer.addPass(new OutputPass());
  const grain = new ShaderPass({uniforms: {tDiffuse: {value: null}, seed: {value: 0}, vig: {value: .55}},
    vertexShader: 'varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: `uniform sampler2D tDiffuse; uniform float seed; uniform float vig; varying vec2 vUv;
      float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+seed*7.13)*43758.5453);}
      void main(){ vec4 c=texture2D(tDiffuse,vUv); float d=distance(vUv,vec2(.5)); c.rgb*=1.-vig*smoothstep(.3,.85,d);
        c.rgb+=(h(vUv*1000.)-.5)*.05; gl_FragColor=c; }`});
  composer.addPass(grain);
  const render = t => { grain.uniforms.seed.value = t; composer.render(); };
  return {renderer, scene, cam, composer, grain, render, dofPass};
}

export const ease = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
export const clamp01 = x => Math.min(1, Math.max(0, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const flat = (c, o = {}) => new THREE.MeshStandardMaterial(Object.assign({color: c, flatShading: true, roughness: .85, metalness: 0}, o));
export function mesh(parent, geo, mat, x = 0, y = 0, z = 0, shadow = true) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = shadow; m.receiveShadow = true; parent.add(m); return m;
}
export function jitterGeo(g, amt, seed) {               // nudge shared vertices: the hand-made faceted look
  let s = seed; const r = () => (s = (s * 9301 + 49297) % 233280) / 233280 - .5;
  const p = g.attributes.position, seen = {};
  for (let i = 0; i < p.count; i++) {
    const k = p.getX(i).toFixed(3) + p.getY(i).toFixed(3) + p.getZ(i).toFixed(3);
    if (!seen[k]) seen[k] = [r() * amt, r() * amt, r() * amt];
    p.setXYZ(i, p.getX(i) + seen[k][0], p.getY(i) + seen[k][1], p.getZ(i) + seen[k][2]);
  }
  g.computeVertexNormals(); return g;
}
export function canvasTex(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  t.redraw = (...a) => { draw(g, w, h, ...a); t.needsUpdate = true; }; t.redraw(); return t;
}
export const maskTex = canvasTex(256, 300, (g, w, h) => {      // flat paper face: off-white, pin-prick eyes, too-wide grin
  g.fillStyle = '#ece6d8'; g.fillRect(0, 0, w, h);
  let s = 5; const r = () => (s = (s * 9301 + 49297) % 233280) / 233280;
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(120,100,80,${r() * .07})`; g.fillRect(r() * w, r() * h, 3, 3); }
  g.fillStyle = '#111'; g.beginPath(); g.arc(85, 120, 9, 0, 7); g.arc(171, 120, 9, 0, 7); g.fill();
  g.strokeStyle = '#111'; g.lineWidth = 7; g.beginPath(); g.moveTo(48, 182); g.quadraticCurveTo(128, 262, 208, 182); g.stroke();
});

// A person. pose: 'stand' | 'sit'. Local +z is the way they face.
export function person(parent, o) {
  const g = new THREE.Group(); parent.add(g);
  const coat = flat(o.coat), skin = flat(o.skin || 0xf1c9a5), hairM = flat(o.hair || 0x1d1714), pants = flat(o.pants || 0x6c6f78);
  const seed = o.seed || 7, sit = o.pose === 'sit';
  const hipY = sit ? .6 : .82;
  for (const sx of [-.1, .1]) {
    if (sit) {
      mesh(g, jitterGeo(new THREE.BoxGeometry(.15, .14, .42), .02, seed), pants, sx, .6, .18);
      mesh(g, jitterGeo(new THREE.BoxGeometry(.13, .45, .14), .02, seed + 1), pants, sx, .3, .38);
      mesh(g, new THREE.BoxGeometry(.13, .07, .22), flat(0x2a2522), sx, .04, .43);
    } else {
      mesh(g, jitterGeo(new THREE.BoxGeometry(.14, .8, .15), .02, seed), pants, sx, .42, 0);
      mesh(g, new THREE.BoxGeometry(.13, .07, .24), flat(0x2a2522), sx, .035, .04);
    }
  }
  const body = new THREE.Group(); body.position.set(0, hipY, -.02); g.add(body);
  mesh(body, jitterGeo(new THREE.CylinderGeometry(.17, .23, .62, 6), .03, seed + 2), coat, 0, .3, 0);
  const headPivot = new THREE.Group(); headPivot.position.set(0, .72, .02); body.add(headPivot);
  headPivot.scale.setScalar(o.headScale || 1.45);
  const head = mesh(headPivot, jitterGeo(new THREE.IcosahedronGeometry(.16, 2), .018, seed + 3), skin, 0, .12, 0); head.scale.set(1, 1.08, .95);
  const hair = mesh(headPivot, jitterGeo(new THREE.IcosahedronGeometry(.172, 1), .03, seed + 4), hairM, 0, .17, -.04); hair.scale.set(1.04, 1.0, 1);
  if (o.long) {
    for (const sx of [-.13, .13]) mesh(headPivot, jitterGeo(new THREE.BoxGeometry(.06, .42, .14), .03, seed + 5), hairM, sx, -.05, -.01);
    mesh(headPivot, jitterGeo(new THREE.BoxGeometry(.3, .45, .07), .03, seed + 6), hairM, 0, -.05, -.12);
    mesh(headPivot, jitterGeo(new THREE.BoxGeometry(.27, .07, .08), .02, seed + 7), hairM, 0, .23, .12);
  }
  const face = new THREE.Group(); headPivot.add(face);            // nose, mouth, dot eyes (hidden under a mask)
  mesh(face, new THREE.ConeGeometry(.02, .05, 4), skin, 0, .09, .16).rotation.x = Math.PI / 2;
  const mouth = mesh(face, new THREE.BoxGeometry(.04, .006, .01), new THREE.MeshBasicMaterial({color: 0x6b3b2e}), 0, .035, .148);
  const eyes = [];
  for (const sx of [-.058, .058]) {
    const e = mesh(face, new THREE.SphereGeometry(.02, 8, 6), new THREE.MeshBasicMaterial({color: 0x0b0b0b}), sx, .125, .145); e.scale.set(1, 1.35, .5);
    mesh(face, new THREE.SphereGeometry(.006, 6, 4), new THREE.MeshBasicMaterial({color: 0xffffff}), sx + .007, .135, .153);
    eyes.push(e);
  }
  const mask = mesh(headPivot, new THREE.PlaneGeometry(.31, .34), new THREE.MeshStandardMaterial({map: maskTex, roughness: 1, side: THREE.DoubleSide}), 0, .11, .175);
  mask.rotation.x = -.05; mask.visible = !!o.mask;
  const arms = [];
  for (const sx of [-1, 1]) {
    const sh = new THREE.Group(); sh.position.set(sx * .2, .55, 0); body.add(sh);
    mesh(sh, jitterGeo(new THREE.CylinderGeometry(.055, .05, .32, 5), .015, seed + 8), coat, 0, -.16, 0);
    const el = new THREE.Group(); el.position.set(0, -.31, 0); sh.add(el);
    mesh(el, jitterGeo(new THREE.CylinderGeometry(.05, .045, .28, 5), .015, seed + 9), coat, 0, -.14, 0);
    mesh(el, new THREE.IcosahedronGeometry(.045, 0), skin, 0, -.3, 0);
    if (sit) { sh.rotation.set(-.35, 0, -sx * .12); el.rotation.set(-1.2, 0, sx * .35); }
    else { sh.rotation.set(0, 0, -sx * .1); el.rotation.set(-.15, 0, 0); }
    arms.push({sh, el});
  }
  g.position.set(o.x || 0, 0, o.z || 0); g.rotation.y = o.face || 0;
  return {g, body, headPivot, mask, face, eyes, mouth, arms, o};
}
