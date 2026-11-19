// Path-traced render for the clay scenes (three-gpu-pathtracer 0.0.20). Light bounces between surfaces, shadows from big
// soft boxes are soft like a real studio, depth of field comes from a real lens. Slow: meant for the final GPU render.
//   import {pathTracer} from './pt.js';
//   const PT = pathTracer({renderer, scene, cam});    // once the scene is built
//   PT.render({samples: 256, focus: worldPoint, fStop: 2.8});   // inside renderAt(t), instead of composer.render()
// Needs:  npm i three-gpu-pathtracer@0.0.20 three-mesh-bvh@0.7.6   and in the page's importmap:
//   "three/examples/jsm/": "/node_modules/three/examples/jsm/",
//   "three-gpu-pathtracer": "/node_modules/three-gpu-pathtracer/build/index.module.js",
//   "three-mesh-bvh": "/node_modules/three-mesh-bvh/build/index.module.js"
import * as THREE from 'three';
import {PathTracingRenderer, PhysicalPathTracingMaterial, DenoiseMaterial, DynamicPathTracingSceneGenerator, GradientEquirectTexture, PhysicalCamera} from 'three-gpu-pathtracer';
import {FullScreenQuad} from 'three/addons/postprocessing/Pass.js';
import {mergeVertices} from 'three/addons/utils/BufferGeometryUtils.js';

// the path tracer reads normal maps, not bump maps: turn each bump (height) canvas into a normal map once
const normalCache = new Map();
function bumpToNormal(tex, strength = 2) {
  if (normalCache.has(tex)) return normalCache.get(tex);
  const img = tex.image, w = img.width, h = img.height;
  const src = document.createElement('canvas'); src.width = w; src.height = h; const sg = src.getContext('2d'); sg.drawImage(img, 0, 0);
  const d = sg.getImageData(0, 0, w, h).data, out = document.createElement('canvas'); out.width = w; out.height = h;
  const og = out.getContext('2d'), od = og.createImageData(w, h), H = (x, y) => d[(((y + h) % h) * w + ((x + w) % w)) * 4] / 255;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const dx = (H(x + 1, y) - H(x - 1, y)) * strength, dy = (H(x, y + 1) - H(x, y - 1)) * strength, l = Math.hypot(dx, dy, 1), i = (y * w + x) * 4;
    od.data[i] = (-dx / l * .5 + .5) * 255; od.data[i + 1] = (dy / l * .5 + .5) * 255; od.data[i + 2] = (1 / l * .5 + .5) * 255; od.data[i + 3] = 255;
  }
  og.putImageData(od, 0, 0);
  const n = new THREE.CanvasTexture(out); n.wrapS = tex.wrapS; n.wrapT = tex.wrapT; n.repeat.copy(tex.repeat); n.colorSpace = THREE.NoColorSpace;
  normalCache.set(tex, n); return n;
}

export function pathTracer({renderer, scene, cam}, {env = [0xf4f2ee, 0x9a968f], envIntensity = .5, softboxes = null, bounces = 6, denoise = false, tiles = 2} = {}) {
  // 1. materials: bump -> normal map (same strength feel), keep everything else
  scene.traverse(o => { if (!o.isMesh) return; for (const m of [].concat(o.material)) {
    if (m.bumpMap && !m.normalMap) { m.normalMap = bumpToNormal(m.bumpMap); const k = Math.min(1.2, m.bumpScale * .45); m.normalScale.set(k, -k); m.needsUpdate = true; }
  } });
  // 2. lights: the raster lights are swapped for soft boxes (area lights); point/spot lights in the scene stay (torches, lamps)
  const hidden = [];
  scene.traverse(o => { if (o.isDirectionalLight || o.isHemisphereLight || o.isAmbientLight) { hidden.push([o, o.visible]); } });
  const boxes = (softboxes || [
    {pos: [-3, 5, 6], size: [3.2, 3.2], power: 14, color: 0xfff1e2},     // key: big and soft, front left above (the sheet's light)
    {pos: [5, 2.5, 4], size: [2.5, 2.5], power: 3, color: 0xe6eeff},  // fill
    {pos: [0, 4, -6], size: [3, 1.5], power: 5, color: 0xffffff},     // rim
  ]).map(b => { const l = new THREE.RectAreaLight(b.color, b.power, b.size[0], b.size[1]); l.position.set(...b.pos); l.lookAt(0, .9, 0); l.visible = false; scene.add(l); return l; });
  // 3. the path tracer
  const ptMat = new PhysicalPathTracingMaterial(); ptMat.bounces = bounces; ptMat.transmissiveBounces = 4;
  const pt = new PathTracingRenderer(renderer); pt.material = ptMat; pt.tiles.set(tiles, tiles);
  const lens = new PhysicalCamera(); pt.camera = lens;
  const sky = new GradientEquirectTexture(256); sky.topColor.set(env[0]); sky.bottomColor.set(env[1]); sky.exponent = .7; sky.update();
  ptMat.envMapInfo.updateFrom(sky); ptMat.environmentIntensity = envIntensity;
  // the sky only lights the scene; what the camera sees behind it is the scene's own backdrop colour (not dimmed with the light)
  const bgc = scene.background && scene.background.isColor ? scene.background : new THREE.Color(0xdcdcdc);
  const back = new GradientEquirectTexture(64); back.topColor.copy(bgc); back.bottomColor.copy(bgc); back.update();
  ptMat.backgroundMap = back;
  // denoise: an edge-aware blur of the finished image, so fewer samples look clean
  const quad = new FullScreenQuad(denoise ? new DenoiseMaterial({map: pt.target.texture, sigma: 2.5, threshold: .03, kSigma: 1}) : new THREE.MeshBasicMaterial({map: pt.target.texture}));
  let gen = null;
  const size = new THREE.Vector2(), v = new THREE.Vector3();

  function build() {
    hidden.forEach(([o]) => o.visible = false); boxes.forEach(b => b.visible = true);
    scene.updateMatrixWorld(true);
    const objs = []; scene.children.forEach(o => { if (o.visible) objs.push(o); });    // only what is visible now
    // every mesh indexed (the generator needs all alike), with tangents where there is a normal map
    // (the library makes an indexed copy for tangents but leaves the mesh without it, so do it here)
    for (const o of objs) o.traverseVisible(c => { if (!c.isMesh) return; let g = c.geometry;
      if (!g.index) { g = mergeVertices(g); c.geometry = g; }
      if (c.material.normalMap && !g.attributes.tangent && g.attributes.uv) g.computeTangents(); });
    gen = new DynamicPathTracingSceneGenerator(objs);
    const {bvh, textures, materials, lights} = gen.generate(), g = bvh.geometry;
    console.log('PT triangles: ' + (g.index ? g.index.count / 3 : g.attributes.position.count / 3));
    ptMat.bvh.updateFrom(bvh);
    ptMat.attributesArray.updateFrom(g.attributes.normal, g.attributes.tangent, g.attributes.uv, g.attributes.color);
    ptMat.materialIndexAttribute.updateFrom(g.attributes.materialIndex);
    ptMat.textures.setTextures(renderer, 1024, 1024, textures);
    ptMat.materials.updateFrom(materials, textures);
    ptMat.lights.updateFrom(lights);
    hidden.forEach(([o, vis]) => o.visible = vis); boxes.forEach(b => b.visible = false);
  }

  return {
    // rebuild: true when what is visible changed (another shot); otherwise the BVH is just refitted to the new pose/lumps
    render({samples = 128, focus = null, fStop = 2.8, rebuild = false} = {}) {
      const gl = renderer.getContext(), T = [performance.now()], px = new Float32Array(4);
      // gl.finish() does not wait in Chrome: read one pixel instead, which really waits for the GPU to finish
      const sync = () => renderer.readRenderTargetPixels(pt.target, 0, 0, 1, 1, px);
      let g;
      if (!gen || rebuild) { build(); }
      else {                                      // same shot: re-bake the posed geometry, refit the BVH (no rebuild)
        const {bvh} = gen.generate(); g = bvh.geometry; T.push(performance.now());
        ptMat.bvh.updateFrom(bvh);
        // the normals moved too: without this the shading stays in the old pose
        ptMat.attributesArray.updateFrom(g.attributes.normal, g.attributes.tangent, g.attributes.uv, g.attributes.color);
      }
      sync(); T.push(performance.now());
      renderer.getSize(size); pt.setSize(size.x, size.y);
      lens.copy(cam); lens.fStop = fStop; lens.apertureBlades = 6;
      lens.focusDistance = focus ? v.copy(focus).applyMatrix4(cam.matrixWorldInverse).length() : 1e4;
      lens.updateMatrixWorld(true); ptMat.physicalCamera.updateFrom(lens);
      pt.reset();
      for (let i = 0; i < samples * tiles * tiles; i++) pt.update();   // one update per tile per sample
      sync(); T.push(performance.now());
      quad.material.map = pt.target.texture; renderer.setRenderTarget(null); quad.render(renderer);
      gl.finish(); T.push(performance.now());
      const d = T.slice(1).map((t, i) => ((t - T[i]) / 1000).toFixed(2));
      console.log('PT times (s): ' + (T.length === 5 ? `bake ${d[0]}  upload ${d[1]}  trace ${d[2]}  show ${d[3]}` : `build+upload ${d[0]}  trace ${d[1]}  show ${d[2]}`));
      return pt.samples;
    },
  };
}
