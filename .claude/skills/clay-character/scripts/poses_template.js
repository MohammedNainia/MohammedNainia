// Poses for clay Haru v3 (haru3.js), matching YTB/channel_art/haru_poses_sheet.png.
// Bone conventions (character faces +z):
//   arm up.rotation.x < 0 swings the arm forward, up.rotation.z = sd * k lifts it out to the side; fo.rotation.x < 0 bends the elbow
//   leg th.rotation.x < 0 swings the thigh forward; sh.rotation.x > 0 bends the knee; ft.rotation.x > 0 points the toe down
//   chest.rotation.x > 0 leans forward; head/neck rotation.y > 0 turns toward her left (+x)

// cheap IK: search the arm angles that put the palm on a world-space target
export function armIK(P, a, target, opt = {}) {
  const palm = opt.palm || [0, -.06, .02];
  const R = opt.range || {ux: [-3, 1], uz: [-1.6, 2.9], fx: [-2.6, 0]};
  const fy = opt.fy || 0;
  const Vt = P.root.position.clone().set(0, 0, 0); const tmp = Vt.clone();
  const score = (ux, uz, fx) => {
    a.up.rotation.set(ux, 0, a.sd * uz); a.fo.rotation.set(fx, fy, 0); a.up.updateMatrixWorld(true);
    return a.hand.localToWorld(tmp.set(...palm)).distanceTo(target);
  };
  let best = [1e9];
  for (let ux = R.ux[0]; ux <= R.ux[1]; ux += .15) for (let uz = R.uz[0]; uz <= R.uz[1]; uz += .15) for (let fx = R.fx[0]; fx <= R.fx[1]; fx += .15) {
    const d = score(ux, uz, fx); if (d < best[0]) best = [d, ux, uz, fx];
  }
  const b0 = best.slice();
  for (let ux = b0[1] - .15; ux <= b0[1] + .15; ux += .03) for (let uz = b0[2] - .15; uz <= b0[2] + .15; uz += .03) for (let fx = b0[3] - .15; fx <= Math.min(0, b0[3] + .15); fx += .03) {
    const d = score(ux, uz, fx); if (d < best[0]) best = [d, ux, uz, fx];
  }
  score(best[1], best[2], best[3]);
  if (opt.hand) a.hand.rotation.set(...opt.hand);
  return best[0];
}

const LOW_ELBOW = {ux: [-1.8, 0], uz: [-.1, 1.0], fx: [-2.4, 0]};      // hands forward and down, elbows by the body
const leg = (l, th, sh, ft = null, thz = 0) => { l.th.rotation.set(th, 0, l.sd * thz); l.sh.rotation.set(sh, 0, 0); l.ft.rotation.set(ft === null ? -(th + sh) : ft, 0, 0); };
const arm = (a, ux, uz, fx, fz = 0) => { a.up.rotation.set(ux, 0, a.sd * uz); a.fo.rotation.set(fx, 0, a.sd * fz); };
const face = (P, e, sweat = false) => { P.expr(e); P.sweat(sweat); };

// put the lowest point of the figure on the floor (skinned vertices included), then lift it by `lift`
export function groundIt(P, THREE, lift = 0) {
  P.root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(P.root, true);
  P.root.position.y += -box.min.y + lift; P.root.updateMatrixWorld(true);
}

function flashlight(P, THREE, a) {
  const M = (c, e = 0) => new THREE.MeshStandardMaterial({color: c, roughness: .45, metalness: .3, emissive: c, emissiveIntensity: e});
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(.022, .022, .16, 18), M(0xb8b8b8)); body.rotation.z = Math.PI / 2; g.add(body);
  const headM = new THREE.Mesh(new THREE.CylinderGeometry(.034, .024, .05, 18), M(0x9a9a9a)); headM.rotation.z = Math.PI / 2; headM.position.x = .1; g.add(headM);
  const lens = new THREE.Mesh(new THREE.CircleGeometry(.03, 18), M(0xfff6d8, 3)); lens.rotation.y = Math.PI / 2; lens.position.x = .126; g.add(lens);
  const cv = document.createElement('canvas'); cv.width = 4; cv.height = 128; const cx = cv.getContext('2d'); const gr = cx.createLinearGradient(0, 0, 0, 128);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.4, 'rgba(255,255,255,.35)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); cx.fillStyle = gr; cx.fillRect(0, 0, 4, 128);
  const beam = new THREE.Mesh(new THREE.ConeGeometry(.42, 1.3, 32, 1, true), new THREE.MeshBasicMaterial({color: 0xfff1cc, map: new THREE.CanvasTexture(cv), transparent: true, opacity: .32, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending}));
  beam.rotation.z = Math.PI / 2; beam.position.x = .126 + .65; g.add(beam);
  const spot = new THREE.SpotLight(0xfff1cc, 6, 4, .5, .6); spot.position.x = .13; const tgt = new THREE.Object3D(); tgt.position.x = 2; g.add(spot, tgt); spot.target = tgt;
  a.hand.add(g); return g;
}

export const POSES = [
  {name: 'walk', fn: (P) => {
    P.root.rotation.y = Math.PI / 2; face(P, 'neutral');
    const [L, R] = P.legs; leg(L, -.42, .12, -.05); leg(R, .38, .3, -.25);
    const [aL, aR] = P.arms; arm(aR, -.38, .12, -.35); arm(aL, .4, .12, -.15);
    P.chest.rotation.x = .04; P.head.rotation.x = .06;
  }},
  {name: 'run', fn: (P) => {
    P.root.rotation.y = .75; face(P, 'nervous');
    P.hips.rotation.x = .2; P.head.rotation.x = -.22; P.chest.rotation.x = .1;
    const [L, R] = P.legs; leg(L, -1.05, .95, .0); leg(R, .3, 1.6, .3);
    const [aL, aR] = P.arms; arm(aR, -1.35, .3, -.55); arm(aL, .95, .3, -.9);
  }, lift: .04},
  {name: 'crouch', fn: (P, THREE) => {
    P.root.rotation.y = .15; face(P, 'nervous');
    for (const l of P.legs) leg(l, -2.25, 1.95, null, .14);
    P.chest.rotation.x = .38; P.head.rotation.x = -.3;
    P.root.updateMatrixWorld(true);
    for (const a of P.arms) { const l = P.legs[a.sd < 0 ? 0 : 1]; const k = l.sh.getWorldPosition(new THREE.Vector3()); k.y += .03; k.z += .06; k.x += a.sd * .02;
      armIK(P, a, k, {hand: [-.4, 0, 0], range: LOW_ELBOW}); }
  }},
  {name: 'sit hugging knees', fn: (P, THREE) => {
    P.root.rotation.y = .25; face(P, 'nervous');
    for (const l of P.legs) leg(l, -2.6, 2.05, null, .08);
    P.chest.rotation.x = .32; P.head.rotation.x = -.22;
    P.root.updateMatrixWorld(true);
    for (const a of P.arms) { const l = P.legs[a.sd < 0 ? 0 : 1]; const k = l.sh.getWorldPosition(new THREE.Vector3());
      const p = k.clone().add(new THREE.Vector3(a.sd * .03, -.02, .08).applyQuaternion(P.root.quaternion));
      armIK(P, a, p, {hand: [-.5, 0, 0], range: LOW_ELBOW}); }
  }},
  {name: 'reach', fn: (P) => {
    face(P, 'nervous'); P.mouth('o');
    const [aL, aR] = P.arms; arm(aR, -.25, 1.45, -.12); aR.hand.rotation.set(0, -Math.PI / 2, -.15);   // palm down, fingers reaching
    P.chest.rotation.y = .06;
  }},
  {name: 'look back', fn: (P) => {
    P.root.rotation.y = Math.PI - .35; face(P, 'nervous');
    P.neck.rotation.y = -.4; P.head.rotation.y = -.85; P.chest.rotation.y = .12;
    const [L, R] = P.legs; leg(R, -.18, .05); leg(L, .3, .35, .15);
    const [aL, aR] = P.arms; arm(aL, -.15, .2, -.1); arm(aR, .2, .2, -.15);
  }},
  {name: 'flashlight', fn: (P, THREE) => {
    P.root.rotation.y = .15; face(P, 'nervous');
    const a = P.arms[1]; P.root.updateMatrixWorld(true);
    const t = P.root.localToWorld(new THREE.Vector3(.27, .95, .14));
    armIK(P, a, t, {hand: [0, 0, 0]});
    P.root.updateMatrixWorld(true);
    const g = flashlight(P, THREE, a);
    // aim the torch along the figure's +x, whatever the hand's angle
    const q = a.hand.getWorldQuaternion(new THREE.Quaternion()).invert();
    g.quaternion.copy(q.multiply(P.root.quaternion)); g.position.set(0, -.05, .02);
  }},
  {name: 'jump back', fn: (P) => {
    face(P, 'scared');
    for (const a of P.arms) { arm(a, -.1, 2.75, -.35); a.hand.rotation.set(-.2, 0, 0); }
    const [L, R] = P.legs; L.th.rotation.set(0, 1.4, -.6); L.sh.rotation.set(1.7, 0, 0); L.ft.rotation.set(.4, 0, 0);
    leg(R, -.3, .75, .5, .15);
    P.chest.rotation.x = -.08;
  }, lift: .28},
];

// ---- getting up from a crouch (any character): lean the weight over the feet, push up with the legs while the back is still
// bent (the arms just hang), straighten the back last. Use in poseBlend / perform keys:  ...getUp(1.2, wary, {dur: 1.1})
const hang = (P, lean) => P.arms.forEach(a => { a.up.rotation.set(-lean * .95, 0, a.sd * .12); a.fo.rotation.set(-.15, 0, 0); a.hand.rotation.set(-.12, -a.sd * Math.PI / 2, 0); });
export const RISE = {
  lean: P => { for (const l of P.legs) leg(l, -2.1, 1.95, null, .12); P.chest.rotation.x = .78; P.neck.rotation.x = -.25; P.head.rotation.x = -.3; hang(P, .78 + .3); },
  push: P => { for (const l of P.legs) leg(l, -1.05, 1.3, null, .06); P.chest.rotation.x = .55; P.neck.rotation.x = -.2; P.head.rotation.x = -.2; hang(P, .55); },
  almost: P => { for (const l of P.legs) leg(l, -.3, .35, null, 0); P.chest.rotation.x = .22; P.neck.rotation.x = -.05; hang(P, .22); },
};
export function getUp(t0, endPose, {dur = 1.2, from = null} = {}) {
  const crouch = from || POSES.find(p => p.name === 'crouch').fn;
  return [[t0, crouch], [t0 + .22 * dur, RISE.lean], [t0 + .55 * dur, RISE.push], [t0 + .8 * dur, RISE.almost], [t0 + dur, endPose]];
}
