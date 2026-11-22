// The clay library (data/lib): generated characters and props, saved once and reused in every reel.
//   import {lib} from './library.js';
//   const mum = await lib.char('mum');                 // a puppet with makePerson's joints and a drawn 2D face: pose(), walk(), look(), expr(), mouth() all work
//   const chair = await lib.prop('chair');             // a Group standing on y = 0, centred, at its real size (metres; Haru is 1.26 m tall)
//   const tree = await lib.prop('tree', {height: 7});  // any other size
// data/lib/index.json lists every item: its file, its size, what it is, and how it was made. Add new items with tools/lib_add.py.
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {makeGlbPerson} from './glb_person.js';

let INDEX = null; const loader = new GLTFLoader(), cache = new Map();
async function index() { if (!INDEX) INDEX = await (await fetch('/data/lib/index.json')).json(); return INDEX; }
// clay: matte, never metallic, a soft sheen (the generators' gloss and metal maps make it look like plastic)
function clayify(root) {
  root.traverse(o => { if (!o.isMesh) return; o.castShadow = o.receiveShadow = true; const m0 = o.material;
    o.material = new THREE.MeshPhysicalMaterial({map: m0.map || null, color: m0.map ? 0xffffff : (m0.color || new THREE.Color(0xcccccc)), normalMap: m0.normalMap || null,
      roughness: .88, metalness: 0, sheen: .35, sheenRoughness: .8, sheenColor: new THREE.Color(0xfff0e0), side: m0.side}); });
}
export const lib = {
  async list() { return index(); },
  async prop(name, o = {}) {
    const I = await index(), e = I.props[name]; if (!e) throw new Error('no prop ' + name + ' in data/lib/index.json');
    if (!cache.has(name)) cache.set(name, loader.loadAsync('/data/lib/props/' + e.file).then(g => { clayify(g.scene); return g.scene; }));
    const src = await cache.get(name), g = src.clone(true);
    g.rotation.y = (e.rot || 0) * Math.PI / 180; g.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(g), size = box.getSize(new THREE.Vector3());
    const k = o.height ? o.height / size.y : o.length ? o.length / Math.max(size.x, size.z) : e.height ? e.height / size.y : e.length / Math.max(size.x, size.z);
    const holder = new THREE.Group(); holder.add(g); g.scale.multiplyScalar(k);
    g.position.set(-(box.min.x + size.x / 2) * k, -box.min.y * k, -(box.min.z + size.z / 2) * k); holder.userData.lib = name; return holder;
  },
  async char(name, o = {}) {
    const I = await index(), e = I.chars[name]; if (!e) throw new Error('no character ' + name + ' in data/lib/index.json');
    const P = await makeGlbPerson('lib/chars/' + e.file.replace('.glb', ''), {height: o.height || e.height}); P.root.userData.lib = name; return P;
  },
};
