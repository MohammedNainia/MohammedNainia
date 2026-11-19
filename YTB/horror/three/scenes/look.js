// "Real puppet" look for the clay scenes: light that soaks into the clay, soft studio environment light, macro depth of field.
//   import {studioLook, clayLook} from './look.js';
//   const L = studioLook({scene, renderer, composer, cam});   // once, after setup()
//   clayLook(P.root);                                          // once per puppet / clay set piece
//   L.focus(worldPoint, aperture)                              // every frame (or once): what is sharp, how shallow
import * as THREE from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {BokehPass} from 'three/addons/postprocessing/BokehPass.js';

// ---- 1. light that soaks into the material (cheap subsurface scattering)
// Plain lighting stops dead at the shadow line. Clay and skin let light in: it wraps a little past that line and comes
// out warmer (red for skin). We replace the diffuse term of three's physical material:
//   wrapped = (N.L + w) / (1 + w), tinted toward `tint` where the light is grazing.
const patched = new WeakSet();
export function sss(mat, {wrap = .45, tint = 0xd8402a, amount = 1} = {}) {
  if (!mat || patched.has(mat) || !mat.isMeshPhysicalMaterial) return mat;
  patched.add(mat);
  const tc = new THREE.Color(tint);
  mat.onBeforeCompile = sh => {
    sh.uniforms.uWrap = {value: wrap}; sh.uniforms.uTint = {value: new THREE.Vector3(tc.r, tc.g, tc.b)}; sh.uniforms.uSss = {value: amount};
    const chunk = THREE.ShaderChunk.lights_physical_pars_fragment.replace(
      'reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );',
      `float nlRaw = dot( geometryNormal, directLight.direction );
       float wrapped = saturate( ( nlRaw + uWrap ) / ( 1.0 + uWrap ) );
       float band = saturate( 1.0 - abs( nlRaw - 0.05 ) * 2.2 );          // the terminator, where light enters the clay
       vec3 soak = mix( vec3( 1.0 ), uTint * 1.35, band * uSss );
       reflectedLight.directDiffuse += directLight.color * mix( saturate( nlRaw ), wrapped, uSss ) * soak * BRDF_Lambert( material.diffuseColor );`);
    sh.fragmentShader = 'uniform float uWrap; uniform vec3 uTint; uniform float uSss;\n' +
      sh.fragmentShader.replace('#include <lights_physical_pars_fragment>', chunk);
  };
  mat.customProgramCacheKey = () => 'sss';
  mat.needsUpdate = true; return mat;
}

// every clay material on a puppet (skin materials named by the caller) : skin gets the strong red soak, the rest a gentle one in its own colour
export function clayLook(root, {skinMats = [], skin = 1, clay = .55} = {}) {   // skinMats: e.g. [P.M.skin, P.M.nose]
  root.traverse(o => {
    if (!o.isMesh) return;
    for (const m of [].concat(o.material)) {
      if (!m.isMeshPhysicalMaterial || m.transparent || m.clearcoat > .5) continue;          // not eyes, tears, gloss
      const c = m.color;
      if (skinMats.includes(m)) sss(m, {wrap: .5, tint: 0xe0402c, amount: skin});
      else { const t = c.clone().multiplyScalar(1.25); sss(m, {wrap: .3, tint: t.getHex(), amount: clay}); }
    }
  });
  return root;
}

// ---- 2 + 3. studio environment light and depth of field
export function studioLook({scene, renderer, composer, cam}, {env = .35, exposure = .9, dof = true, aperture = .0018, maxblur = .008} = {}) {
  renderer.toneMappingExposure = exposure;
  const pm = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment(renderer);
  scene.environment = pm.fromScene(room, .04).texture;
  // environment light: a soft fill on everything (puppets and set) at `env`; the key light still does the shaping
  scene.traverse(o => { if (o.isMesh && o.material && o.material.envMapIntensity !== undefined) o.material.envMapIntensity = env; });
  let bokeh = null;
  if (dof) {
    bokeh = new BokehPass(scene, cam, {focus: 5, aperture, maxblur});
    // after the render and AO passes, before bloom / output / grain
    const i = composer.passes.findIndex(p => p.constructor.name === 'UnrealBloomPass');
    composer.insertPass(bokeh, i < 0 ? 1 : i);
  }
  const v = new THREE.Vector3();
  return {
    bokeh,
    // focus on a world point (the face, usually); aperture: bigger = shallower
    focus(p, ap) { if (!bokeh) return; v.copy(p).applyMatrix4(cam.matrixWorldInverse); bokeh.uniforms.focus.value = -v.z;
      if (ap !== undefined) bokeh.uniforms.aperture.value = ap; },
  };
}
