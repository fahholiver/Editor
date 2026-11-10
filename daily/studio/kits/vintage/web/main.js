// Engine: toon world + ink + grade + DOF, cards for 2D cast. window.renderFrame(f) draws frame f.
import * as THREE from './three.module.js';
import * as PT from './paint.js';
import { drawChar, drawFx } from './cast.js';
import * as ST from './story.js';

const W = 1080, H = 1920;
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 900);

// ---------- toon materials ----------
const grad = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255, 255, 255, 255, 255]), 2, 1);
grad.minFilter = grad.magFilter = THREE.NearestFilter; grad.needsUpdate = true;
const texOf = (c, rx = 1, ry = 1) => { const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; t.repeat.set(rx, ry); return t; };
const toon = (c, map = null) => new THREE.MeshToonMaterial({ color: map ? 0xffffff : c, map, gradientMap: grad });
const T = {};
// ---------- ink contract: world meshes get normal/depth, cards get a mask ----------
const ndVert = `
#include <common>
varying vec3 vN; varying float vD;
void main(){
  #include <beginnormal_vertex>
  #include <defaultnormal_vertex>
  #include <begin_vertex>
  #include <project_vertex>
  vN = normalize(transformedNormal); vD = -mvPosition.z;
}`;
const ndMat = new THREE.ShaderMaterial({ vertexShader: ndVert, side: THREE.DoubleSide,
  fragmentShader: `varying vec3 vN; varying float vD; void main(){ vec3 n = gl_FrontFacing ? vN : -vN; gl_FragColor = vec4(n*0.5+0.5, vD/1000.); }` });
const cardNdMat = (map) => new THREE.ShaderMaterial({ uniforms: { map: { value: map } }, side: THREE.DoubleSide,
  vertexShader: `varying vec2 vUv; varying float vD; void main(){ vUv = uv; vec4 mv = modelViewMatrix*vec4(position,1.); vD = -mv.z; gl_Position = projectionMatrix*mv; }`,
  fragmentShader: `uniform sampler2D map; varying vec2 vUv; varying float vD; void main(){ if(texture2D(map,vUv).a<0.5) discard; gl_FragColor = vec4(0.,0.,0.,vD/1000.); }` });

// box with world-scaled UVs (constant texel density); tile = metres per texture repeat
function tbox(w, h, d, mat, tile = 2) {
  const g = new THREE.BoxGeometry(w, h, d), uv = g.attributes.uv;
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let i = 0; i < 4; i++) { const k = f * 4 + i; uv.setXY(k, uv.getX(k) * dims[f][0] / tile, uv.getY(k) * dims[f][1] / tile); }
  return new THREE.Mesh(g, mat);
}
function add(m, x = 0, y = 0, z = 0, parent = scene, shadow = true) { m.position.set(x, y, z); m.castShadow = shadow; m.receiveShadow = true; parent.add(m); return m; }
const grp = (x = 0, y = 0, z = 0, parent = scene) => { const g = new THREE.Group(); g.position.set(x, y, z); parent.add(g); return g; };
const glowM = (c) => new THREE.MeshBasicMaterial({ color: c, fog: false });
const noNd = (m) => { m.userData.noNd = true; m.castShadow = false; return m; };
// ---------- sky ----------
const skyU = { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(600, 32, 16), new THREE.ShaderMaterial({ uniforms: skyU, side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 top, hor; varying vec3 vP; void main(){ float h = clamp(normalize(vP).y*2.2, 0., 1.); gl_FragColor = vec4(mix(hor, top, pow(h,0.8)), 1.); }` }));
sky.userData.noNd = true; scene.add(sky);

// ---------- lights ----------
const sun = new THREE.DirectionalLight(0xffffff, 2.5);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.05;
const sc = sun.shadow.camera; sc.left = -14; sc.right = 14; sc.top = 14; sc.bottom = -14; sc.near = 1; sc.far = 140;
scene.add(sun); scene.add(sun.target);
const hemi = new THREE.HemisphereLight(0xffffff, 0x886644, 1.0); scene.add(hemi);
const lamp = new THREE.PointLight(0xffc070, 0, 11, 1.4); lamp.position.set(-1.55, 2.95, -0.25); scene.add(lamp);
scene.fog = new THREE.Fog(0xcfe6f2, 40, 300);

// =====================================================================
// ---------- world ----------
// =====================================================================
T.grass = texOf(PT.grass('#79a84a'), 50, 50);
add(new THREE.Mesh(new THREE.PlaneGeometry(500, 500), toon(0, T.grass)), 0, 0, 0).rotation.x = -Math.PI / 2;
// lake (everything at z < -4)
T.water = texOf(PT.water(), 30, 22);
const lake = add(new THREE.Mesh(new THREE.PlaneGeometry(500, 300), toon(0, T.water)), 0, 0.03, -154, scene, false); lake.rotation.x = -Math.PI / 2;
const stoneM = toon(0, texOf(PT.stone('#a49c8c')));
add(tbox(120, 0.3, 0.8, stoneM, 1.2), 0, 0.1, -4.1);
// paths: one along the shore, one down to the pier
const paveM = toon(0, texOf(PT.paving()));
add(tbox(90, 0.04, 2.0, paveM, 1.4), -25, 0.02, 2.2, scene, false);
add(tbox(1.8, 0.04, 6.2, paveM, 1.4), 3.2, 0.021, -0.9, scene, false);
// bench (centre at the origin, facing +z)
const bench = grp(0, 0, 0);
const slatM = toon(0, texOf(PT.planks('#b5763e', { n: 3, vertical: false, seed: 6 }))), ironM = toon('#2e2a36');
for (let i = 0; i < 3; i++) add(tbox(1.95, 0.05, 0.14, slatM, 1), 0, 0.45, 0.17 - i * 0.17, bench);
for (let i = 0; i < 3; i++) { const s = add(tbox(1.95, 0.12, 0.04, slatM, 1), 0, 0.62 + i * 0.16, -0.3 - i * 0.02, bench); s.rotation.x = -0.12; }
for (const sx of [-0.88, 0.88]) {
  add(tbox(0.06, 0.45, 0.06, ironM), sx, 0.225, 0.2, bench); add(tbox(0.06, 0.95, 0.06, ironM), sx, 0.47, -0.3, bench).rotation.x = -0.1;
  add(tbox(0.06, 0.05, 0.6, ironM), sx, 0.66, -0.02, bench); add(tbox(0.06, 0.2, 0.06, ironM), sx, 0.56, 0.24, bench);
}
// lamp post beside the bench
const lampPost = grp(-1.55, 0, -0.25);
const postM = toon('#2f4a3a');
add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.08, 2.8, 10), postM), 0, 1.4, 0, lampPost);
add(new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.12, 0.12, 8), postM), 0, 2.84, 0, lampPost);
const lampGlass = add(new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.1, 0.32, 8), glowM('#ffe2a0')), 0, 3.06, 0, lampPost, false);
add(new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.16, 8), postM), 0, 3.3, 0, lampPost);
// more lamps along the path
for (const x of [-9, -17, -25]) { const g = grp(x, 0, 3.4); add(new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.08, 2.8, 10), postM), 0, 1.4, 0, g); add(new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.1, 0.32, 8), glowM('#ffe2a0')), 0, 3.0, 0, g, false); add(new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.16, 8), postM), 0, 3.24, 0, g); }
// bushes + flower beds
const bushM = [toon('#4f8a3f'), toon('#5f9a46'), toon('#467f3a')];
for (const [x, z, s] of [[-2.6, -1.2, 0.7], [2.0, -1.4, 0.6], [-3.4, -0.6, 0.5], [1.3, -2.2, 0.45], [-6, 0.4, 0.8], [6.5, 0.2, 0.7], [-11, -1.5, 0.9]]) {
  add(new THREE.Mesh(new THREE.SphereGeometry(s, 14, 10), bushM[(x * 7 & 3) % 3]), x, s * 0.55, z);
  add(new THREE.Mesh(new THREE.SphereGeometry(s * 0.7, 12, 8), bushM[1]), x + s * 0.6, s * 0.45, z + 0.2);
}
const flowerCols = ['#f26b8a', '#ffd23a', '#ffffff', '#b58af0'];
for (let i = 0; i < 26; i++) { const x = -4 + (i % 13) * 0.62, z = -2.4 + Math.floor(i / 13) * 0.35 + (i % 3) * 0.08; if (Math.abs(x - 3.2) < 1.2) continue; add(new THREE.Mesh(new THREE.SphereGeometry(0.07, 8, 6), toon(flowerCols[i % 4])), x, 0.12, z, scene, false); }
// trees
const treeM = [toon('#3f7a3a'), toon('#4f8a3f'), toon('#5a9a44')], trunkM = toon('#6a4a2a');
function tree(x, z, s = 1, k = 0) {
  const g = grp(x, 0, z); add(new THREE.Mesh(new THREE.CylinderGeometry(0.15 * s, 0.22 * s, 2 * s, 8), trunkM), 0, s, 0, g);
  if (k % 2) add(new THREE.Mesh(new THREE.ConeGeometry(1.4 * s, 4 * s, 10), treeM[k % 3]), 0, 3.6 * s, 0, g);
  else { add(new THREE.Mesh(new THREE.SphereGeometry(1.5 * s, 14, 10), treeM[k % 3]), 0, 3.0 * s, 0, g); add(new THREE.Mesh(new THREE.SphereGeometry(1.0 * s, 12, 8), treeM[(k + 1) % 3]), 0.8 * s, 3.8 * s, 0.3 * s, g); }
}
tree(-4.6, -1.8, 1.3, 2); tree(5.8, -2.2, 1.1, 0); tree(-8, 0.5, 1.2, 1); tree(9, 1, 1.3, 2);
for (let i = 0; i < 26; i++) { const x = -60 + i * 4.6 + (i % 3), z = 16 + (i % 4) * 3; tree(x, z, 1 + (i % 3) * 0.3, i); }
for (let i = 0; i < 14; i++) tree(-40 + i * 6, -3 + (i % 2) * 1.5 - (Math.abs(-40 + i * 6 - 3) < 10 ? 99 : 0), 1.1, i + 1);
// far shore: hills, trees, little houses
for (let i = 0; i < 16; i++) {
  const a = (i / 16) * Math.PI * 2, r = 210 + 40 * Math.sin(i * 3.3);
  const hl = add(new THREE.Mesh(new THREE.SphereGeometry(45 + 20 * Math.sin(i * 1.7) ** 2, 24, 12), toon(['#6f9e4a', '#7fae52', '#5f8e44'][i % 3])), Math.cos(a) * r, -22, Math.sin(a) * r - 30, scene, false);
  hl.scale.y = 0.55;
}
for (let i = 0; i < 22; i++) tree(-90 + i * 8.5, -140 - (i % 3) * 6, 2.2, i);
for (let i = 0; i < 8; i++) { const g = grp(-60 + i * 17, 0, -132 - (i % 2) * 5); add(tbox(5, 4, 5, toon(['#e8dcc0', '#c95a4a', '#8aa0b8', '#f2c14e'][i % 4]), 2), 0, 2, 0, g, false); const r = add(new THREE.Mesh(new THREE.ConeGeometry(4.2, 2.2, 4), toon('#6a4a3a')), 0, 5.1, 0, g, false); r.rotation.y = Math.PI / 4; }
// pier from the shore out into the lake
const pierM = toon(0, texOf(PT.planks('#a8784a', { n: 6, vertical: false, seed: 8, worn: 0.3 })));
add(tbox(1.8, 0.14, 14, pierM, 1.6), 3.2, 0.33, -11.0);
for (let i = 0; i < 8; i++) for (const sx of [-0.82, 0.82]) add(new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.0, 8), toon('#6a4a2a')), 3.2 + sx, -0.1, -4.6 - i * 1.85);
for (const sx of [-0.82, 0.82]) add(new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5, 8), toon('#6a4a2a')), 3.2 + sx, 0.6, -17.8);
// clouds
const clouds = [];
for (let i = 0; i < 10; i++) {
  const c = new THREE.Mesh(new THREE.PlaneGeometry(60, 30), new THREE.MeshBasicMaterial({ map: texOf(PT.cloud(i + 1)), transparent: true, depthWrite: false, fog: false }));
  c.position.set(-180 + i * 40, 60 + (i % 3) * 18, -300 - (i % 4) * 25); c.userData.noNd = true; scene.add(c); clouds.push(c);
}
// sun disc + halo, stars
const sunDisc = noNd(new THREE.Mesh(new THREE.CircleGeometry(16, 40), new THREE.MeshBasicMaterial({ color: '#fff4d0', fog: false })));
const sunHalo = noNd(new THREE.Mesh(new THREE.CircleGeometry(48, 40), new THREE.MeshBasicMaterial({ color: '#ffd9a0', transparent: true, opacity: 0.35, depthWrite: false, fog: false })));
scene.add(sunHalo); scene.add(sunDisc);
const starGeo = new THREE.BufferGeometry(); { const P = [], r = (s) => { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }; for (let i = 0; i < 900; i++) { const a = r(i) * Math.PI * 2, e = Math.asin(0.05 + 0.95 * r(i + 0.5)); P.push(Math.cos(e) * Math.sin(a) * 520, Math.sin(e) * 520, Math.cos(e) * Math.cos(a) * 520); } starGeo.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); }
const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({ color: '#ffffff', size: 2.6, sizeAttenuation: false, fog: false, transparent: true }));
stars.userData.noNd = true; scene.add(stars);

// ---------- the heart balloon + its string ----------
const heartShape = new THREE.Shape();
for (let i = 0; i <= 64; i++) { const t = (i / 64) * Math.PI * 2, x = 16 * Math.sin(t) ** 3 / 32, y = (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) / 32; i ? heartShape.lineTo(x, y) : heartShape.moveTo(x, y); }
const balloon = grp(0, -9, 0);
const balloonM = toon('#e8344a');
const bMesh = add(new THREE.Mesh(new THREE.ExtrudeGeometry(heartShape, { depth: 0.12, bevelEnabled: true, bevelThickness: 0.08, bevelSize: 0.06, bevelSegments: 4, curveSegments: 32 }), balloonM), 0, 0.3, -0.06, balloon);
bMesh.scale.setScalar(0.62);
add(new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.06, 8), balloonM), 0, 0.0, 0, balloon).rotation.x = Math.PI; // knot
const shine = add(new THREE.Mesh(new THREE.CircleGeometry(0.045, 12), glowM('#ffd0d6')), -0.16, 0.42, 0.13, balloon, false); noNd(shine);
let stringMesh = null;
const stringM = toon('#3a2a3a');
function setString(a, b, sag) {
  if (stringMesh) { scene.remove(stringMesh); stringMesh.geometry.dispose(); }
  if (!a) { stringMesh = null; return; }
  const mid = a.clone().lerp(b, 0.5).add(sag);
  stringMesh = new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a, mid, b), 24, 0.0075, 5), stringM);
  stringMesh.userData.noNd = true; scene.add(stringMesh);
}

// ---------- polaroids ----------
const photos = [];
for (let i = 0; i < 6; i++) { const m = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.4), new THREE.MeshBasicMaterial({ map: texOf(PT.photo(i)), side: THREE.DoubleSide })); m.visible = false; scene.add(m); photos.push(m); }

// ---------- golden thread of connection (two halves so it can snap) ----------
const threadM = glowM('#ffd86a');
const threads = [0, 1].map(() => { const m = noNd(new THREE.Mesh(new THREE.BufferGeometry(), threadM)); scene.add(m); return m; });

// ---------- the mind: a glowing brain floating in the night sky ----------
const BRAIN = ST.BRAIN;
const brain = grp(...BRAIN);
const brainM = new THREE.MeshToonMaterial({ color: '#ffc2d6', gradientMap: grad, emissive: '#b04a78' }), brainM2 = new THREE.MeshToonMaterial({ color: '#f59abb', gradientMap: grad, emissive: '#9a3a66' });
const gyrusM = new THREE.MeshToonMaterial({ color: '#d9688f', gradientMap: grad, emissive: '#7a2a50' });
for (const sx of [-1, 1]) { // two smooth hemispheres with folded grooves pressed into them
  const hemi = add(new THREE.Mesh(new THREE.SphereGeometry(1, 32, 20), brainM), sx * 0.66, 0, 0, brain); hemi.scale.set(0.72, 0.9, 1.15);
  for (let i = 0; i < 7; i++) {
    const g = new THREE.TorusGeometry(0.5 + 0.12 * (i % 3), 0.06, 6, 24, Math.PI * (0.7 + 0.25 * (i % 2)));
    const m = add(new THREE.Mesh(g, gyrusM), sx * 0.7, -0.5 + i * 0.17, 0, brain, false);
    m.scale.set(0.9, 0.55, 1.3); m.rotation.set(Math.PI / 2 + 0.3 * Math.sin(i * 2.1), sx * (0.35 + 0.2 * Math.cos(i)), i * 0.9);
  }
}
add(new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.12, 0.9, 10), brainM2), 0.1, -1.0, -0.2, brain).rotation.z = 0.2;
const brainHalo = noNd(add(new THREE.Mesh(new THREE.CircleGeometry(2.3, 40), new THREE.MeshBasicMaterial({ color: '#8a7ae8', transparent: true, opacity: 0.3, depthWrite: false, fog: false })), 0, 0, -1.6, brain, false));
// network threads from the heart (in front of the brain) to the four nodes
const links = ST.NODES.map((n) => {
  const a = new THREE.Vector3(...ST.HEARTP), b = new THREE.Vector3(...n), mid = a.clone().lerp(b, 0.5).add(new THREE.Vector3((b.x - a.x) * 0.15, 0.5, 0.4));
  const m = noNd(new THREE.Mesh(new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(a, mid, b), 64, 0.05, 6), glowM('#ffd86a')));
  scene.add(m); return m;
});
const nodeDots = ST.NODES.map((n) => { const m = noNd(new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 8), glowM('#fff3b0'))); m.position.set(...n); scene.add(m); return m; });

// =====================================================================
// ---------- cards ----------
// =====================================================================
const cards = new Map();
const blobTex = (() => { const c = PT.cv(128, 128), g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, 'rgba(40,25,30,0.55)'); gr.addColorStop(0.6, 'rgba(40,25,30,0.35)'); gr.addColorStop(1, 'rgba(40,25,30,0)'); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
const UNIT = 0.00225;
function getCard(id, res) {
  let c = cards.get(id);
  if (c) return c;
  const canvas = PT.cv(res === 'lo' ? 600 : 1200, res === 'lo' ? 1000 : 2000);
  const map = new THREE.CanvasTexture(canvas); map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = 4;
  const geo = new THREE.PlaneGeometry(600 * UNIT, 1000 * UNIT); geo.translate(0, (500 - 25) * UNIT, 0);
  const mat = new THREE.MeshBasicMaterial({ map, alphaTest: 0.5, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map, alphaTest: 0.5 });
  mesh.userData.card = true; mesh.userData.ndMat = cardNdMat(map);
  const blob = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; blob.userData.noNd = true; blob.renderOrder = 1;
  scene.add(mesh); scene.add(blob);
  c = { canvas, map, mesh, blob, key: '' };
  cards.set(id, c);
  return c;
}
const q = (v) => (typeof v === 'number' ? Math.round(v * 100) / 100 : v);
function drawActors(list, f, tint) {
  for (const c of cards.values()) { c.mesh.visible = false; c.blob.visible = false; }
  for (const a of list) {
    const c = getCard(a.id, a.res);
    const spec = a.spec, key = JSON.stringify(spec, (k, v) => q(v));
    if (key !== c.key) { (a.kind === 'fx' ? drawFx : drawChar)(c.canvas, spec); c.map.needsUpdate = true; c.key = key; }
    const m = c.mesh; m.visible = true;
    m.position.set(a.pos[0], a.pos[1], a.pos[2]);
    const s = a.s ?? 1;
    const seed = (a.seed ?? 1);
    const breathe = a.kind === 'fx' ? 1 : 1 + 0.012 * Math.sin(f * 0.13 + seed);
    m.scale.set(s * (a.sx ?? 1), s * breathe * (a.sy ?? 1), s);
    const yaw = a.yaw ?? Math.atan2(cam.position.x - a.pos[0], cam.position.z - a.pos[2]);
    m.rotation.set(0, yaw, 0);
    if (a.face) m.lookAt(cam.position); // full billboard (sky cards seen from below)
    m.rotateZ(((a.roll || 0) + (a.kind === 'fx' ? 0 : 0.7 * Math.sin(f * 0.07 + seed * 2))) * Math.PI / 180);
    m.material.color.set(a.kind === 'fx' && a.glow ? '#ffffff' : (a.tint || tint));
    m.castShadow = a.kind !== 'fx' && !a.noShadow;
    m.userData.fx = a.kind === 'fx';
    m.renderOrder = a.order || 0;
    if (a.kind !== 'fx' && a.blob !== false) { c.blob.visible = true; c.blob.position.set(a.pos[0], (a.ground ?? a.pos[1]) + 0.015, a.pos[2]); c.blob.scale.setScalar(0.9 * s); }
  }
}
/** world position of a card's hand (side 'L' | 'R'), from the hand point the cast drawer recorded */
function handWorld(id, side) {
  const c = cards.get(id);
  if (!c || !c.mesh.visible || !c.canvas.hands || !c.canvas.hands[side]) return null;
  const [hx, hy] = c.canvas.hands[side];
  c.mesh.updateMatrixWorld();
  return new THREE.Vector3((hx - 300) * UNIT, (975 - hy) * UNIT, 0.01).applyMatrix4(c.mesh.matrixWorld);
}
window.debugHand = (id, side) => { const v = handWorld(id, side); return v ? [v.x, v.y, v.z] : null; };

// =====================================================================
// ---------- render targets / post ----------
// =====================================================================
const colorRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 2 });
const ndRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
const compRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2)); const qScene = new THREE.Scene(); qScene.add(quad); const qCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const fsVert = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`;
const compMat = new THREE.ShaderMaterial({
  uniforms: { tC: { value: colorRT.texture }, tN: { value: ndRT.texture }, px: { value: new THREE.Vector2(1 / W, 1 / H) }, inkR: { value: 3.0 }, inkCol: { value: new THREE.Color('#241726') },
    sat: { value: 1.1 }, gain: { value: new THREE.Vector3(1, 1, 1) }, lift: { value: new THREE.Vector3(0, 0, 0) }, vig: { value: 0.35 }, flash: { value: 0 }, toScreen: { value: 0 } },
  vertexShader: fsVert,
  fragmentShader: `
uniform sampler2D tC, tN; uniform vec2 px; uniform float inkR, sat, vig, flash; uniform vec3 inkCol, gain, lift; varying vec2 vUv;
bool isCard(vec4 s){ return dot(s.rgb, s.rgb) < 0.0001; }
void main(){
  vec3 col = texture2D(tC, vUv).rgb;
  vec4 c0 = texture2D(tN, vUv); c0.a *= 1000.;
  float ink = 0.;
  if(!isCard(c0) && c0.a < 999.){
    vec3 n0 = c0.rgb*2.-1.;
    for(int i=0;i<8;i++){
      float a = float(i)*0.785398;
      vec2 o = vec2(cos(a), sin(a))*px*inkR;
      vec4 s = texture2D(tN, vUv+o); s.a *= 1000.;
      if(isCard(s)) continue;
      float dd = (s.a - c0.a)/c0.a;
      ink = max(ink, smoothstep(0.03, 0.09, dd));
      if(s.a < 999. && abs(dd) < 0.05){ vec3 ns = s.rgb*2.-1.; ink = max(ink, 0.85*smoothstep(0.45, 0.75, 1.-dot(n0, ns))); }
    }
    ink *= 1. - smoothstep(140., 520., c0.a);
  }
  col = mix(col, inkCol*0.35, ink);
  float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
  col = mix(vec3(l), col, sat);
  col = col*gain + lift;
  vec2 d = vUv-0.5; d.x *= 0.62; col *= 1. - vig*smoothstep(0.25, 0.75, length(d));
  col = mix(col, vec3(1.), flash);
  gl_FragColor = vec4(max(col, 0.), 1.);
}` });
const dofMat = new THREE.ShaderMaterial({
  uniforms: { tC: { value: compRT.texture }, tN: { value: ndRT.texture }, px: { value: new THREE.Vector2(1 / W, 1 / H) }, focus: { value: 5 }, cInf: { value: 0 } },
  vertexShader: fsVert,
  fragmentShader: `
uniform sampler2D tC, tN; uniform vec2 px; uniform float focus, cInf; varying vec2 vUv;
float coc(float d){ d *= 1000.; return clamp(cInf*abs(1. - focus/max(d, 0.01)), 0., 18.); }
void main(){
  float c0 = coc(texture2D(tN, vUv).a);
  vec3 acc = texture2D(tC, vUv).rgb; float wsum = 1.;
  for(int i=0;i<48;i++){
    float fi = float(i)+0.5; float r = sqrt(fi/48.)*18.; float a = fi*2.39996;
    vec2 o = vec2(cos(a), sin(a))*r;
    vec2 uv = vUv + o*px;
    float cs = coc(texture2D(tN, uv).a);
    float cmax = texture2D(tN, uv).a < texture2D(tN, vUv).a ? cs : min(cs, c0);
    float w = smoothstep(r-1., r+0.5, cmax);
    acc += texture2D(tC, uv).rgb*w; wsum += w;
  }
  gl_FragColor = vec4(acc/wsum, 1.);
  #include <colorspace_fragment>
}` });
const blitMat = new THREE.ShaderMaterial({ uniforms: { tC: { value: compRT.texture } }, vertexShader: fsVert,
  fragmentShader: `uniform sampler2D tC; varying vec2 vUv; void main(){ gl_FragColor = vec4(texture2D(tC, vUv).rgb, 1.); \n#include <colorspace_fragment>\n}` });

// ---------- light presets (blendable) ----------
const LIGHTS = {
  day: { top: '#4f9be6', hor: '#d6ecf6', sun: '#fff1d6', si: 2.6, az: 200, el: 48, hs: '#cfe4ff', hg: '#b89a6a', hi: 1.15, fog: '#d6ecf6', tint: '#ffffff', sat: 1.15, gain: [1.03, 1.0, 0.97], lift: [0.0, 0.0, 0.01], lamp: 0, disc: '#fff8e0', stars: 0 },
  golden: { top: '#d9785e', hor: '#ffcf8a', sun: '#ffa65a', si: 2.6, az: 180, el: 9, hs: '#ffcf9f', hg: '#8a5a40', hi: 1.0, fog: '#ffc890', tint: '#ffe0c0', sat: 1.12, gain: [1.06, 0.97, 0.86], lift: [0.02, 0.0, 0.0], lamp: 0, disc: '#fff0c0', stars: 0 },
  night: { top: '#0b1640', hor: '#344f8a', sun: '#a9c0ff', si: 1.0, az: 160, el: 40, hs: '#5a7ac8', hg: '#1c2238', hi: 1.0, fog: '#26396a', tint: '#aab8e8', sat: 1.0, gain: [0.85, 0.92, 1.12], lift: [0.0, 0.01, 0.04], lamp: 7, disc: null, stars: 1 },
  dusk: { top: '#2a2a66', hor: '#c88aa8', sun: '#e8a0c0', si: 1.2, az: 174, el: -2, hs: '#8a8ad0', hg: '#3a2a48', hi: 1.05, fog: '#9a7aa8', tint: '#d8c8f0', sat: 1.05, gain: [0.95, 0.92, 1.06], lift: [0.02, 0.01, 0.04], lamp: 4, disc: null, stars: 0.6 },
  dawn: { top: '#6a8ad8', hor: '#ffc0a0', sun: '#ffc890', si: 2.4, az: 174, el: 6, hs: '#ffd8c0', hg: '#8a6a60', hi: 1.1, fog: '#ffc8a8', tint: '#fff0e0', sat: 1.12, gain: [1.05, 1.0, 0.95], lift: [0.02, 0.01, 0.01], lamp: 0, disc: '#fff6d8', stars: 0 },
};
const cA = new THREE.Color(), cB = new THREE.Color();
const mixC = (a, b, t) => '#' + cA.set(a).lerp(cB.set(b), t).getHexString();
function mixL(A, B, t) {
  if (!B || t <= 0) return A;
  const o = {};
  for (const k in A) {
    const a = A[k], b = B[k];
    if (typeof a === 'number') o[k] = a + (b - a) * t;
    else if (Array.isArray(a)) o[k] = a.map((v, i) => v + (b[i] - v) * t);
    else if (a && b) o[k] = mixC(a, b, t);
    else o[k] = t < 0.5 ? a : b;
  }
  return o;
}
function applyLight(lt) {
  const L = mixL(LIGHTS[lt.preset], LIGHTS[lt.to], lt.mix || 0);
  if (lt.el !== undefined) L.el = lt.el;
  const target = lt.target;
  skyU.top.value.set(L.top); skyU.hor.value.set(L.hor);
  sun.color.set(L.sun); sun.intensity = L.si;
  const az = L.az * Math.PI / 180, elL = Math.max(L.el, 6) * Math.PI / 180;
  sun.target.position.set(target[0], 0, target[2]);
  sun.position.set(target[0] + Math.cos(elL) * Math.sin(az) * 70, Math.sin(elL) * 70, target[2] + Math.cos(elL) * Math.cos(az) * 70);
  hemi.color.set(L.hs); hemi.groundColor.set(L.hg); hemi.intensity = L.hi;
  scene.fog.color.set(L.fog);
  compMat.uniforms.sat.value = L.sat; compMat.uniforms.gain.value.set(...L.gain); compMat.uniforms.lift.value.set(...L.lift);
  lamp.intensity = L.lamp; lampGlass.material.color.set(L.lamp > 1 ? '#ffe6a0' : '#d8d0b8');
  // visible sun: on the horizon over the lake, seen from the camera
  const el = L.el * Math.PI / 180, D = 430;
  sunDisc.visible = sunHalo.visible = !!L.disc;
  if (L.disc) {
    const p = new THREE.Vector3(cam.position.x + Math.cos(el) * Math.sin(az) * D, Math.sin(el) * D + 6, cam.position.z + Math.cos(el) * Math.cos(az) * D);
    sunDisc.position.copy(p); sunHalo.position.copy(p).multiplyScalar(1.002);
    sunDisc.lookAt(cam.position); sunHalo.lookAt(cam.position);
    sunDisc.material.color.set(L.disc); sunHalo.material.color.set(L.hor);
  }
  stars.visible = L.stars > 0.05; stars.material.opacity = L.stars;
  for (const c of clouds) c.material.color.set(mixC('#ffffff', L.hor, 0.55));
  return L.tint;
}

// ---------- world state ----------
let lastKnot = null;
function applyWorld(w, f) {
  T.water.offset.set(f * 0.0006, f * 0.0011);
  // balloon
  const B = w.balloon;
  balloon.visible = !!B;
  if (B) {
    let knot, hand = null;
    if (B.mode === 'held') {
      hand = handWorld(B.actor, B.side);
      if (hand) { knot = hand.clone().add(new THREE.Vector3(B.sway[0], B.lift, B.sway[1])); lastKnot = knot.clone(); }
      else knot = new THREE.Vector3(...(B.pos || [0, -9, 0]));
    } else {
      const base = B.base ? new THREE.Vector3(...B.base) : (lastKnot || new THREE.Vector3(0, 2, 0));
      knot = base.clone().add(new THREE.Vector3(B.drift[0], B.rise, B.drift[1]));
    }
    balloon.position.copy(knot);
    balloon.scale.setScalar(B.scale || 1);
    balloon.rotation.set(0, Math.atan2(cam.position.x - knot.x, cam.position.z - knot.z), B.tilt || 0);
    if (hand) setString(hand, knot, new THREE.Vector3(B.sway[0] * -0.4, -0.08, 0));
    else setString(knot.clone().add(new THREE.Vector3(0.06, -0.9, 0)), knot, new THREE.Vector3(0.08 * Math.sin(f * 0.2), 0, 0));
  } else setString(null);
  // polaroids
  photos.forEach((m, i) => { const P = w.photos[i]; m.visible = !!P; if (P) { m.position.set(P[0], P[1], P[2]); m.lookAt(cam.position); m.rotateZ(P[3] || 0); m.scale.setScalar(P[4] ?? 1); } });
  // connection thread: from -> to, grown to `grow`, then snapped (two halves retract)
  const Th = w.thread;
  threads.forEach((m, i) => {
    m.visible = false;
    if (!Th) return;
    const a = new THREE.Vector3(...Th.from), b = new THREE.Vector3(...Th.to), mid = a.clone().lerp(b, 0.5);
    let p0, p1;
    if (Th.snap > 0) { p0 = i === 0 ? a : b; p1 = p0.clone().lerp(mid, 1 - Th.snap); } // halves spring back to their ends
    else if (i === 0) { p0 = a; p1 = a.clone().lerp(b, Th.grow); }
    else return;
    if (p0.distanceTo(p1) < 0.02) return;
    m.visible = true;
    const wob = new THREE.Vector3(0, Th.snap > 0 ? -0.15 * Th.snap : 0.04 * Math.sin(f * 0.5), 0);
    m.geometry.dispose(); m.geometry = new THREE.TubeGeometry(new THREE.QuadraticBezierCurve3(p0, p0.clone().lerp(p1, 0.5).add(wob), p1), 40, Th.r || 0.018, 6);
  });
  // the mind
  brain.visible = !!w.mind;
  links.forEach((m, i) => { const g = w.mind ? w.mind.links[i] : 0; m.visible = g > 0.001; m.geometry.setDrawRange(0, Math.floor(g * 64) * 6 * 6); });
  nodeDots.forEach((m, i) => { m.visible = !!w.mind && w.mind.links[i] > 0.98 && w.mind.dots; });
  if (w.mind) { const gl = w.mind.glow; brainM.emissive.set(mixC('#2a1020', '#b04a78', gl)); brainM2.emissive.set(mixC('#200a18', '#9a3a66', gl)); gyrusM.emissive.set(mixC('#1a0812', '#7a2a50', gl)); brainHalo.material.opacity = 0.3 * gl; brain.rotation.y = 0.12 * Math.sin(f * 0.02); brain.position.y = BRAIN[1] + 0.08 * Math.sin(f * 0.05); }
}

// ---------- render ----------
const hidden = [];
function swapForNd(on) {
  if (on) {
    scene.traverse((o) => {
      if (!o.isMesh && !o.isInstancedMesh && !o.isPoints) return;
      if (o.userData.noNd || o.userData.fx || o.isPoints) { if (o.visible) { o.visible = false; hidden.push(o); } return; }
      o.userData.savedMat = o.material; o.material = o.userData.card ? o.userData.ndMat : ndMat;
    });
    scene.fog = null;
  } else {
    scene.traverse((o) => { if (o.userData.savedMat) { o.material = o.userData.savedMat; o.userData.savedMat = null; } });
    while (hidden.length) hidden.pop().visible = true;
    scene.fog = fogRef;
  }
}
const fogRef = scene.fog;
window.renderFrame = (f) => {
  const shot = ST.shotAt(f);
  const c = window.camOverride || ST.camAt(f); // override: thumbnail framing
  cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.fov = c.fov; cam.updateProjectionMatrix();
  if (c.roll) cam.rotateZ(c.roll * Math.PI / 180);
  cam.updateMatrixWorld();
  const tint = applyLight(ST.lightFor(f));
  drawActors([...ST.actorsAt(f), ...ST.fxAt(f)], f, tint);
  applyWorld(ST.worldAt(f), f);
  clouds.forEach((cl, i) => { cl.position.x = -180 + i * 40 + f * 0.02; cl.lookAt(cam.position.x, cl.position.y, cam.position.z); });
  // colour
  renderer.shadowMap.autoUpdate = true;
  renderer.setRenderTarget(colorRT); renderer.setClearColor(0x000000, 1); renderer.render(scene, cam);
  // normal / depth
  renderer.shadowMap.autoUpdate = false;
  swapForNd(true);
  renderer.setRenderTarget(ndRT); renderer.setClearColor(new THREE.Color(0.5, 0.5, 1.0), 1.0); renderer.clear(); renderer.render(scene, cam);
  swapForNd(false);
  renderer.setClearColor(0x000000, 1);
  // ink + grade
  compMat.uniforms.flash.value = ST.flashAt(f); compMat.uniforms.vig.value = 0.34;
  quad.material = compMat; renderer.setRenderTarget(compRT); renderer.render(qScene, qCam);
  const d = ST.dofAt(f, cam);
  if (d.cInf > 0.3) { dofMat.uniforms.focus.value = d.focus; dofMat.uniforms.cInf.value = d.cInf; quad.material = dofMat; }
  else quad.material = blitMat;
  renderer.setRenderTarget(null); renderer.render(qScene, qCam);
  return shot ? shot.name : '';
};
window.ready = true;
