// ORBIT: a space explainer engine. Canvas 2D and deterministic: window.render(t) draws the frame at t seconds.
// The scene comes from window.SCENE (injected by render.mjs) = { width, height, fps, shots:[{start,end,cam,bg,els:[...]}] }.
// World elements are drawn inside the camera (zoom/pan); overlays are fixed on screen. Every element's t0 is relative to its shot.
(() => {
const S = window.SCENE, W = S.width || 1920, H = S.height || 1080, K = H > W ? W / 1080 * (S.vk || 0.9) : Math.min(W / 1920, H / 1080);
const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const c = cv.getContext('2d');
const TAU = Math.PI * 2;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eo = t => 1 - Math.pow(1 - clamp(t), 3);
const eio = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const back = t => { t = clamp(t) - 1; return 1 + t * t * (2.7 * t + 1.7); };
const hash = n => { n = Math.sin(n * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); };
const rng = s => { s = Math.floor(s * 9973 + 1) % 2147483647 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; };
const T = Object.assign({ y: '#FFC93C', r: '#FF3B30', ink: '#F3F5FA', sub: '#8E97B0', panel: 'rgba(10,14,28,.80)', line: 'rgba(255,255,255,.14)', cyan: '#6FE3FF', green: '#4CFF8A' }, S.tokens || {});
const F = (w, s) => `${w} ${s * K}px InterE`;
const A = s => `${s * K}px Anton`;
const rgba = (hex, a) => { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; };
const mk = (w, h) => { const o = document.createElement('canvas'); o.width = Math.max(1, Math.ceil(w)); o.height = Math.max(1, Math.ceil(h)); return o; };
const IMG = {}, VID = {}; for (const sh of S.shots) for (const e of sh.els) if (e.src) {
  if (/\.(jpe?g|png|webp)$/i.test(e.src)) { const im = new Image(); im.src = e.src; IMG[e.src] = im; }
  else if (/\.(webm|mp4|mov)$/i.test(e.src)) { const v = document.createElement('video'); v.muted = true; v.preload = 'auto'; v.src = e.src; VID[e.src] = v; } }

// ───────── space backdrop ─────────
const STARS = [0, 1, 2].map(L => { const R = rng(11 + L * 7); return [...Array(280 - L * 70)].map(() => ({ x: R(), y: R(), r: (.45 + R() * (.9 + L * .8)) * K, a: .25 + R() * .7, p: R() * TAU, warm: R() < .15 })); });
function space(t, cam, o = {}) {
  const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, o.top || '#04050c'); g.addColorStop(1, o.bottom || '#0a0e20'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  for (const [x, y, r, col, a] of (o.nebula || [[.78, .28, .55, '#3b1f5e', .32], [.12, .82, .5, '#123a5c', .28]])) {
    const gr = c.createRadialGradient(x * W, y * H, 0, x * W, y * H, r * W); gr.addColorStop(0, rgba(col, a)); gr.addColorStop(1, rgba(col, 0)); c.fillStyle = gr; c.fillRect(0, 0, W, H);
  }
  STARS.forEach((layer, L) => { const par = .12 + L * .22;
    for (const s of layer) { const x = ((s.x * W - cam.px * par) % W + W) % W, y = ((s.y * H - cam.py * par) % H + H) % H;
      c.globalAlpha = s.a * (.7 + .3 * Math.sin(t * 2.2 + s.p)) * (o.stars ?? 1); c.fillStyle = s.warm ? '#ffe2b8' : '#fff'; c.beginPath(); c.arc(x, y, s.r, 0, TAU); c.fill(); } });
  c.globalAlpha = 1;
}
function vignette(a = .6) { const v = c.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .98); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, `rgba(0,0,0,${a})`); c.fillStyle = v; c.fillRect(0, 0, W, H); }
const GRAIN = (() => { const g = mk(256, 256), x = g.getContext('2d'), d = x.createImageData(256, 256), R = rng(5); for (let i = 0; i < d.data.length; i += 4) { const v = R() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 8; } x.putImageData(d, 0, 0); return g; })();
function grain(t) { c.save(); c.globalCompositeOperation = 'overlay'; c.translate(-(t * 977 % 256), -(t * 613 % 256)); c.fillStyle = c.createPattern(GRAIN, 'repeat'); c.fillRect(0, 0, W + 512, H + 512); c.restore(); }

// ───────── planet textures (equirectangular strips, generated once per kind+seed) ─────────
const PRESET = {
  venus:  { base: '#e8c98c', pal: ['#f6e3b6', '#dcb576', '#cfa264', '#f9ecd0'], atmo: '#ffd68a', style: 'venus' },
  mars:   { base: '#c1562c', pal: ['#d8743f', '#9c3f1f', '#e2925a', '#7a2c16'], atmo: '#ff9a6a', style: 'mars' },
  jupiter:{ base: '#d9b48a', pal: ['#f2dcbc', '#c08a5c', '#a86a44', '#e9cfa8', '#8c5634'], atmo: '#f5d8ae', style: 'bands', spot: '#c4552e' },
  saturn: { base: '#e2c992', pal: ['#f0dcae', '#cfb07a', '#bb9a64', '#e8d29e'], atmo: '#f3e0b0', style: 'bands', rings: true },
  neptune:{ base: '#3f66d9', pal: ['#5b82ee', '#2f4fbf', '#7aa0ff', '#2a44a8'], atmo: '#8ab4ff', style: 'bands', spot: '#1d2f80' },
  earth:  { base: '#1f5fae', pal: ['#2f8a4a', '#c9a96a', '#ffffff'], atmo: '#7fc4ff', style: 'earth' },
  moon:   { base: '#9a9a96', pal: ['#bdbdb8', '#7d7d79', '#cfcfca'], atmo: '#ffffff', style: 'cratered', glow: 1.15 },
  mercury:{ base: '#8f877e', pal: ['#ada59b', '#6f6860', '#c2bab0'], atmo: '#ffffff', style: 'cratered', glow: 1.1 },
  io:     { base: '#e3cf5a', pal: ['#f4e58a', '#c9862e', '#8a3a1a', '#fff3b0'], atmo: '#fff2a0', style: 'cratered' },
};
const TEX = {};
function texture(kind, seed, pal, base, style, spotCol) {
  const key = `${kind}|${seed}|${pal.join()}`; if (TEX[key]) return TEX[key];
  const tw = 1024, th = 512, o = mk(tw, th), x = o.getContext('2d'), R = rng(seed + 1);
  x.fillStyle = base; x.fillRect(0, 0, tw, th);
  const wrapBlob = (cx, cy, rx, ry, col, a, rot = 0) => { for (const dx of [-tw, 0, tw]) { x.save(); x.globalAlpha = a; x.fillStyle = col; x.translate(cx + dx, cy); x.rotate(rot); x.beginPath(); x.ellipse(0, 0, rx, ry, 0, 0, TAU); x.fill(); x.restore(); } };
  if (style === 'bands' || style === 'venus') {
    const n = style === 'venus' ? 14 : 22;
    for (let i = 0; i < n; i++) { const y0 = (i / n) * th, h = th / n * (0.6 + R() * 1.2), col = pal[i % pal.length];
      x.globalAlpha = style === 'venus' ? .35 : .85; x.fillStyle = col; x.beginPath(); x.moveTo(0, y0);
      for (let u = 0; u <= tw; u += 8) x.lineTo(u, y0 + Math.sin(u / tw * TAU * (2 + i % 3) + i) * h * .25);
      for (let u = tw; u >= 0; u -= 8) x.lineTo(u, y0 + h + Math.sin(u / tw * TAU * (3 + i % 2) + i * 1.7) * h * .25); x.closePath(); x.fill(); }
    x.globalAlpha = 1;
    if (style === 'venus') {  // the sideways "Y" cloud chevrons Venus shows in ultraviolet, softened
      for (let k = 0; k < 3; k++) { const cx = (k / 3) * tw + R() * 80; x.strokeStyle = rgba(pal[1], .5); x.lineCap = 'round';
        for (let j = -5; j <= 5; j++) { x.lineWidth = 18 + R() * 16; x.beginPath(); x.moveTo(cx - 180, th / 2 + j * 22); x.quadraticCurveTo(cx, th / 2 + j * 22 + (j < 0 ? -1 : 1) * 70, cx + 200, th / 2 + j * 36 + (j < 0 ? -1 : 1) * 150); x.stroke(); } }
      for (let i = 0; i < 160; i++) wrapBlob(R() * tw, R() * th, 20 + R() * 70, 6 + R() * 14, pal[3], .12 + R() * .12);
    } else {
      for (let i = 0; i < 90; i++) wrapBlob(R() * tw, R() * th, 10 + R() * 40, 3 + R() * 8, pal[(i % 2) ? 0 : 3], .25, (R() - .5) * .2);
      if (spotCol) { wrapBlob(tw * .62, th * .64, 64, 34, spotCol, .9); wrapBlob(tw * .62, th * .64, 44, 22, '#e07a50', .6); }
    }
  } else if (style === 'mars') {
    for (let i = 0; i < 40; i++) wrapBlob(R() * tw, th * .2 + R() * th * .6, 30 + R() * 110, 12 + R() * 40, pal[1], .35 + R() * .3, (R() - .5) * .6);
    for (let i = 0; i < 70; i++) wrapBlob(R() * tw, R() * th, 8 + R() * 30, 6 + R() * 20, pal[2], .25);
    x.fillStyle = 'rgba(255,255,255,.9)'; x.fillRect(0, 0, tw, th * .05); x.fillRect(0, th * .96, tw, th * .04);
    for (let i = 0; i < 60; i++) { const cx = R() * tw, cy = R() * th, r = 3 + R() * 12; x.strokeStyle = 'rgba(60,20,8,.35)'; x.lineWidth = 2; x.beginPath(); x.arc(cx, cy, r, 0, TAU); x.stroke(); }
  } else if (style === 'earth') {
    for (let i = 0; i < 9; i++) { const cx = R() * tw, cy = th * .2 + R() * th * .6; for (let k = 0; k < 9; k++) wrapBlob(cx + (R() - .5) * 140, cy + (R() - .5) * 90, 30 + R() * 60, 20 + R() * 50, k % 3 ? pal[0] : pal[1], .95); }
    x.fillStyle = 'rgba(255,255,255,.92)'; x.fillRect(0, 0, tw, th * .06); x.fillRect(0, th * .94, tw, th * .06);
    for (let i = 0; i < 120; i++) wrapBlob(R() * tw, R() * th, 20 + R() * 60, 4 + R() * 10, '#ffffff', .35 + R() * .3, (R() - .5) * .5);
  } else if (style === 'cratered') {
    for (let i = 0; i < 30; i++) wrapBlob(R() * tw, R() * th, 30 + R() * 80, 20 + R() * 60, pal[1], .35);
    for (let i = 0; i < 220; i++) { const cx = R() * tw, cy = R() * th, r = 2 + Math.pow(R(), 3) * 30;
      x.fillStyle = 'rgba(0,0,0,.22)'; x.beginPath(); x.arc(cx + r * .2, cy + r * .2, r, 0, TAU); x.fill(); x.fillStyle = rgba(pal[2], .5); x.beginPath(); x.arc(cx - r * .15, cy - r * .15, r * .8, 0, TAU); x.fill(); }
  }
  return (TEX[key] = o);
}
// a sphere: texture scrolls horizontally (spin), lit from angle `light`; optional rings
E_planet = (e, t) => {
  const P = Object.assign({}, PRESET[e.kind || 'venus'] || PRESET.venus, e), { x, y, r } = e;
  const glowK = P.glow ?? 1.45, la = P.light ?? -2.4;
  const gl = c.createRadialGradient(x, y, r * .92, x, y, r * glowK); gl.addColorStop(0, rgba(P.atmo, .42)); gl.addColorStop(1, rgba(P.atmo, 0)); c.fillStyle = gl; c.beginPath(); c.arc(x, y, r * glowK, 0, TAU); c.fill();
  if (P.rings) ring(x, y, r, P, -1);
  const tex = texture(P.kind || 'venus', P.seed || 3, P.pal, P.base, P.style, P.spot);
  c.save(); c.beginPath(); c.arc(x, y, r, 0, TAU); c.clip();
  const sp = ((P.spin ?? .02) * t % 1 + 1) % 1, tw = r * 4, ox = x - r * 2 - sp * tw;   // texture covers 2 diameters (half the strip visible)
  c.drawImage(tex, ox, y - r, tw, r * 2); c.drawImage(tex, ox + tw, y - r, tw, r * 2);
  // limb darkening + day/night terminator
  const lx = x + Math.cos(la) * r * .6, ly = y + Math.sin(la) * r * .6;
  const sh = c.createRadialGradient(lx, ly, r * .05, lx, ly, r * 2.05); sh.addColorStop(0, 'rgba(255,250,235,.20)'); sh.addColorStop(.42, 'rgba(0,0,0,0)'); sh.addColorStop(.7, 'rgba(0,0,8,.62)'); sh.addColorStop(1, 'rgba(0,0,8,.95)');
  c.fillStyle = sh; c.fillRect(x - r, y - r, r * 2, r * 2);
  const limb = c.createRadialGradient(x, y, r * .7, x, y, r); limb.addColorStop(0, 'rgba(0,0,0,0)'); limb.addColorStop(1, 'rgba(0,0,0,.35)'); c.fillStyle = limb; c.fillRect(x - r, y - r, r * 2, r * 2);
  c.restore();
  c.strokeStyle = rgba(P.atmo, .7); c.lineWidth = Math.max(2, r * .02); c.beginPath(); c.arc(x, y, r * .996, la - 1.15, la + 1.15); c.stroke();
  if (P.rings) ring(x, y, r, P, 1);
  if (P.label) { c.font = F(800, 26); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(P.label, x, y + r + 46 * K); c.textAlign = 'left'; }
};
function ring(x, y, r, P, side) {
  c.save(); c.translate(x, y); c.rotate(-.35); c.scale(1, .28);
  c.beginPath(); if (side < 0) c.rect(-r * 3, -r * 3, r * 6, r * 3); else c.rect(-r * 3, 0, r * 6, r * 3); c.clip();
  for (let i = 0; i < 7; i++) { c.strokeStyle = rgba(i % 2 ? P.pal[0] : P.pal[2], .55); c.lineWidth = r * (.05 + (i % 3) * .03); c.beginPath(); c.arc(0, 0, r * (1.35 + i * .12), 0, TAU); c.stroke(); }
  c.restore();
}
var E_planet;

// ───────── world elements ─────────
const E = {};
E.planet = (e, t) => E_planet(e, t);
E.sun = (e, t) => { const { x, y, r } = e;
  for (const [k, a] of [[10, .07], [5, .15], [2.4, .35]]) { const g = c.createRadialGradient(x, y, 0, x, y, r * k); g.addColorStop(0, `rgba(255,236,190,${a})`); g.addColorStop(1, 'rgba(255,200,120,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, r * k, 0, TAU); c.fill(); }
  if (e.surface) { c.save(); c.beginPath(); c.arc(x, y, r, 0, TAU); c.clip(); const g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, '#fff3c4'); g.addColorStop(.7, '#ffb347'); g.addColorStop(1, '#ff7a1a'); c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2);
    for (let i = 0; i < 300; i++) { const a = hash(i) * TAU, d = Math.sqrt(hash(i * 3.3)) * r, s = r * .03 * (1 + hash(i * 7)); c.fillStyle = `rgba(255,${180 + 60 * Math.sin(t * 2 + i)},90,.35)`; c.beginPath(); c.arc(x + Math.cos(a) * d, y + Math.sin(a) * d, s, 0, TAU); c.fill(); }
    c.restore(); } else { c.fillStyle = '#fff6df'; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
  c.save(); c.globalCompositeOperation = 'lighter'; c.strokeStyle = 'rgba(255,230,180,.10)'; c.lineWidth = 3 * K;
  for (let i = 0; i < 16; i++) { const a = i / 16 * TAU + t * .04; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(a) * r * 16, y + Math.sin(a) * r * 16); c.stroke(); } c.restore(); };
E.blackhole = (e, t) => { const { x, y, r } = e;
  const g = c.createRadialGradient(x, y, r, x, y, r * 4); g.addColorStop(0, 'rgba(255,170,80,.5)'); g.addColorStop(1, 'rgba(255,120,40,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, r * 4, 0, TAU); c.fill();
  c.save(); c.translate(x, y); c.scale(1, .3); for (let i = 0; i < 40; i++) { const rr = r * (1.3 + i * .05); c.strokeStyle = `rgba(255,${150 + i * 2},${60 + i},${.25 - i * .005})`; c.lineWidth = r * .06; c.beginPath(); c.arc(0, 0, rr, t * .6 + i, t * .6 + i + 4.5); c.stroke(); } c.restore();
  c.strokeStyle = 'rgba(255,210,150,.85)'; c.lineWidth = r * .08; c.beginPath(); c.arc(x, y, r * 1.12, 0, TAU); c.stroke();
  c.fillStyle = '#000'; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill();
  c.save(); c.beginPath(); c.rect(x - r * 4, y, r * 8, r * 4); c.clip(); c.translate(x, y); c.scale(1, .3); c.strokeStyle = 'rgba(255,200,120,.6)'; c.lineWidth = r * .25; c.beginPath(); c.arc(0, 0, r * 1.6, 0, Math.PI); c.stroke(); c.restore(); };
// astronaut: side view facing right, headlamp; s = height in px
function astro(x, y, s, rot, t, lamp = 1, flip = false) {
  c.save(); c.translate(x, y); c.rotate(rot); if (flip) c.scale(-1, 1); const k = s / 100;
  if (lamp > 0) { c.save(); c.globalCompositeOperation = 'lighter'; const g = c.createLinearGradient(20 * k, -30 * k, 380 * k, -30 * k); g.addColorStop(0, `rgba(255,240,200,${.36 * lamp})`); g.addColorStop(1, 'rgba(255,240,200,0)'); c.fillStyle = g; c.beginPath(); c.moveTo(22 * k, -34 * k); c.lineTo(400 * k, -120 * k); c.lineTo(400 * k, 55 * k); c.closePath(); c.fill(); c.restore(); }
  const suit = '#eef1f7', shade = '#b8c0d0', dark = '#8d96aa';
  c.fillStyle = shade; c.beginPath(); c.roundRect(-31 * k, -31 * k, 22 * k, 48 * k, 6 * k); c.fill(); c.fillStyle = dark; c.fillRect(-27 * k, -24 * k, 14 * k, 4 * k);
  const leg = (a, len) => { c.save(); c.translate(0, 16 * k); c.rotate(a); c.fillStyle = suit; c.beginPath(); c.roundRect(-7 * k, 0, 14 * k, len * k, 6 * k); c.fill(); c.fillStyle = dark; c.beginPath(); c.roundRect(-7 * k, (len - 9) * k, 18 * k, 9 * k, 3 * k); c.fill(); c.restore(); };
  leg(-.15 + .12 * Math.sin(t * 1.3 + 2), 42);
  c.fillStyle = suit; c.beginPath(); c.roundRect(-14 * k, -26 * k, 31 * k, 45 * k, 11 * k); c.fill();
  c.fillStyle = '#d24a3a'; c.fillRect(-6 * k, -16 * k, 10 * k, 6 * k);
  leg(.25 + .12 * Math.sin(t * 1.3), 40);
  c.save(); c.translate(5 * k, -16 * k); c.rotate(-.9 + .25 * Math.sin(t * 1.1)); c.fillStyle = suit; c.beginPath(); c.roundRect(-5 * k, 0, 11 * k, 34 * k, 5 * k); c.fill(); c.fillStyle = dark; c.beginPath(); c.arc(0, 36 * k, 6 * k, 0, TAU); c.fill(); c.restore();
  c.fillStyle = suit; c.beginPath(); c.arc(4 * k, -40 * k, 19 * k, 0, TAU); c.fill();
  const vg = c.createLinearGradient(4 * k, -52 * k, 22 * k, -28 * k); vg.addColorStop(0, '#ffd27a'); vg.addColorStop(1, '#6a3a0c');
  c.fillStyle = vg; c.beginPath(); c.ellipse(11 * k, -40 * k, 11 * k, 12.5 * k, 0, -1.45, 1.6); c.closePath(); c.fill();
  c.fillStyle = 'rgba(255,255,255,.75)'; c.beginPath(); c.ellipse(14 * k, -46 * k, 3 * k, 5 * k, .4, 0, TAU); c.fill();
  c.fillStyle = '#fff6d6'; c.beginPath(); c.arc(21 * k, -33 * k, 3.5 * k, 0, TAU); c.fill();
  c.restore();
}
E.astronaut = (e, t) => astro(e.x + (e.vx || 0) * t + Math.sin(t * .8) * 6 * K, e.y + (e.vy || 0) * t + Math.sin(t * 1.1) * 5 * K, e.s * K, (e.rot || 0) + (e.spin || 0) * t + .08 * Math.sin(t * .7), t, e.lamp ?? 1, e.flip);
// cloud decks rushing upward (a descent), with optional acid rain and lightning
E.descent = (e, t) => {
  const v = e.speed || 600, g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, e.sky[0]); g.addColorStop(1, e.sky[1]); c.fillStyle = g; c.fillRect(-W, -H, W * 3, H * 3);
  const bolt = (e.bolts || []).find(b => t >= b && t < b + .35);
  if (bolt != null) { const k = 1 - (t - bolt) / .35; c.fillStyle = `rgba(255,250,230,${.55 * k})`; c.fillRect(-W, -H, W * 3, H * 3);
    const R = rng(bolt * 13); let px = W * (.3 + R() * .4), py = -50; c.strokeStyle = `rgba(255,255,240,${k})`; c.lineWidth = 6 * K; c.shadowColor = '#fff6c0'; c.shadowBlur = 30 * K; c.beginPath(); c.moveTo(px, py);
    while (py < H * .8) { px += (R() - .5) * 140 * K; py += 60 * K + R() * 70 * K; c.lineTo(px, py); } c.stroke(); c.shadowBlur = 0; }
  e.cols.forEach((col, i) => { const par = .35 + i * .35, step = 260 * K * (1 + i * .5), off = (t * v * K * par) % (step * 3);
    for (let b = -1; b < 7; b++) { const by = H + step * 1.5 - b * step * 1.5 - off * 1.5; if (by < -step * 1.5 || by > H + step * 2) continue;
      c.fillStyle = col; c.globalAlpha = e.alpha ?? .92; c.beginPath();
      for (let k = -2; k < 13; k++) { const cx = k * 210 * K + hash(b * 9 + i + k) * 120 * K, rr = (90 + hash(k * 3 + b + i * 5) * 120) * K * (1 + i * .3); c.moveTo(cx + rr, by); c.arc(cx, by, rr, 0, TAU); }
      c.fill(); c.fillRect(-W, by, W * 3, step * .3); } });
  c.globalAlpha = 1;
  if (e.rain) { c.strokeStyle = rgba(e.rain, .5); c.lineWidth = 2 * K; const R = rng(9);
    for (let i = 0; i < 110; i++) { const x = R() * W, y = ((R() * H - t * 1500 * K) % H + H) % H; c.beginPath(); c.moveTo(x, y); c.lineTo(x - 7 * K, y + 44 * K); c.stroke(); } }
};
// a planet's ground: layered ridges, heat shimmer; kind venus | mars | moon
const GROUND = { venus: ['#5a2a0e', '#c86a1e', '#f2a248', '#a24e18', '#7a3410', '#4a1d08'], mars: ['#3a1a10', '#b5653a', '#e0a070', '#9a4a26', '#73331a', '#45200f'], moon: ['#000000', '#05060c', '#0a0c16', '#6e6e6a', '#4f4f4c', '#2c2c2a'] };
E.surface = (e, t) => {
  const G = e.cols || GROUND[e.kind || 'venus']; const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, G[0]); g.addColorStop(.55, G[1]); g.addColorStop(1, G[2]); c.fillStyle = g; c.fillRect(-W, -H, W * 3, H * 3);
  if (e.kind === 'moon') space(t, { px: 0, py: 0 }, { stars: .8 });
  const ridge = (yb, amp, col, seed, f) => { c.fillStyle = col; c.beginPath(); c.moveTo(-W, H * 2);
    for (let x = -W; x <= W * 2; x += 10 * K) { const n = Math.sin(x * f / K + seed) * .5 + Math.sin(x * f * 2.7 / K + seed * 2) * .3 + Math.sin(x * f * 6.1 / K + seed) * .12; c.lineTo(x, yb + n * amp + Math.sin(t * 7 + x * .012) * (e.heat ?? 0) * K); }
    c.lineTo(W * 2, H * 2); c.closePath(); c.fill(); };
  if (e.volcano) { c.fillStyle = G[3]; c.beginPath(); const vx = e.volcano * W; c.moveTo(vx - 520 * K, H * .66); c.lineTo(vx - 70 * K, H * .3); c.lineTo(vx + 60 * K, H * .3); c.lineTo(vx + 560 * K, H * .66); c.fill();
    const gl = c.createRadialGradient(vx, H * .29, 0, vx, H * .29, 160 * K); gl.addColorStop(0, `rgba(255,150,60,${.55 + .15 * Math.sin(t * 3)})`); gl.addColorStop(1, 'rgba(255,90,30,0)'); c.fillStyle = gl; c.fillRect(vx - 200 * K, H * .1, 400 * K, 400 * K); }
  ridge(H * .62, 70 * K, G[3], 1, .004); ridge(H * .73, 60 * K, G[4], 3, .006); ridge(H * .85, 40 * K, G[5], 5, .009);
  if (e.kind !== 'moon') { c.fillStyle = 'rgba(255,190,110,.16)'; c.fillRect(-W, H * .5, W * 3, H * .12); }
  if (e.rocks) { const R = rng(4); c.fillStyle = G[5]; for (let i = 0; i < 26; i++) { const rx = R() * W, ry = H * (.9 + R() * .08), rw = (20 + R() * 70) * K; c.beginPath(); c.ellipse(rx, ry, rw, rw * .35, 0, Math.PI, TAU); c.fill(); } }
};
// a Venera-style lander: sphere hull, landing ring, antenna dish; `dead` = t when its light stops
E.probe = (e, t) => { const { x, y } = e, k = (e.s || 100) * K / 100; c.save(); c.translate(x, y);
  c.fillStyle = 'rgba(30,12,4,.55)'; c.beginPath(); c.ellipse(0, 8 * k, 95 * k, 14 * k, 0, 0, TAU); c.fill();
  c.fillStyle = '#c9c3b6'; c.beginPath(); c.ellipse(0, 0, 80 * k, 15 * k, 0, 0, TAU); c.fill(); c.fillStyle = '#a49e92'; c.fillRect(-80 * k, -6 * k, 160 * k, 6 * k);
  for (const sx of [-1, 1]) { c.strokeStyle = '#8f897e'; c.lineWidth = 6 * k; c.beginPath(); c.moveTo(sx * 70 * k, -4 * k); c.lineTo(sx * 30 * k, -40 * k); c.stroke(); }
  const hg = c.createRadialGradient(-12 * k, -64 * k, 4 * k, 0, -50 * k, 44 * k); hg.addColorStop(0, '#f2eee6'); hg.addColorStop(1, '#8c867a'); c.fillStyle = hg; c.beginPath(); c.arc(0, -50 * k, 40 * k, 0, TAU); c.fill();
  c.fillStyle = '#d8d2c6'; c.fillRect(-7 * k, -118 * k, 14 * k, 34 * k); c.beginPath(); c.ellipse(0, -122 * k, 30 * k, 9 * k, 0, 0, TAU); c.fill();
  c.strokeStyle = '#6e685e'; c.lineWidth = 3 * k; for (let i = -2; i <= 2; i++) { c.beginPath(); c.moveTo(-34 * k, -50 * k + i * 10 * k); c.lineTo(34 * k, -50 * k + i * 10 * k); c.globalAlpha = .25; c.stroke(); } c.globalAlpha = 1;
  const alive = !(e.dead != null && t > e.dead); c.fillStyle = alive && Math.sin(t * 6) > 0 ? '#7dffa8' : 'rgba(120,255,160,.15)'; c.beginPath(); c.arc(22 * k, -60 * k, 6 * k, 0, TAU); c.fill();
  if (e.cook && t > 0) { const h = clamp(t / e.cook); c.fillStyle = `rgba(255,90,30,${.35 * h})`; c.beginPath(); c.arc(0, -50 * k, 40 * k, 0, TAU); c.fill(); }
  c.restore(); };
// airship: a floating habitat above the clouds (NASA has studied the idea)
E.airship = (e, t) => { const k = (e.s || 100) * K / 100; c.save(); c.translate(e.x + Math.sin(t * .6) * 8 * K, e.y + Math.sin(t * .9) * 6 * K); c.rotate(Math.sin(t * .5) * .02);
  const g = c.createLinearGradient(0, -60 * k, 0, 60 * k); g.addColorStop(0, '#f4f6fb'); g.addColorStop(1, '#a9b2c6'); c.fillStyle = g; c.beginPath(); c.ellipse(0, 0, 190 * k, 58 * k, 0, 0, TAU); c.fill();
  c.strokeStyle = 'rgba(80,90,120,.25)'; c.lineWidth = 2 * k; for (let i = -3; i <= 3; i++) { c.beginPath(); c.ellipse(0, 0, 190 * k * Math.cos(i * .4), 58 * k, 0, -Math.PI / 2, Math.PI / 2); c.stroke(); }
  c.fillStyle = '#8f98ad'; c.beginPath(); c.moveTo(-170 * k, -10 * k); c.lineTo(-230 * k, -50 * k); c.lineTo(-215 * k, 0); c.lineTo(-230 * k, 50 * k); c.lineTo(-170 * k, 10 * k); c.fill();
  c.strokeStyle = '#6d7488'; c.lineWidth = 3 * k; for (const sx of [-50, 50]) { c.beginPath(); c.moveTo(sx * k, 50 * k); c.lineTo(sx * .6 * k, 92 * k); c.stroke(); }
  c.fillStyle = '#e1e5ee'; c.beginPath(); c.roundRect(-60 * k, 88 * k, 120 * k, 34 * k, 10 * k); c.fill();
  c.fillStyle = '#ffd27a'; for (let i = 0; i < 5; i++) { c.beginPath(); c.roundRect(-48 * k + i * 22 * k, 96 * k, 12 * k, 12 * k, 3 * k); c.fill(); }
  c.restore(); };
E.rocket = (e, t) => { const k = (e.s || 100) * K / 100; c.save(); c.translate(e.x + (e.vx || 0) * t, e.y + (e.vy || 0) * t); c.rotate(e.rot || 0);
  const fl = 1 + .2 * Math.sin(t * 40); c.fillStyle = '#ffb347'; c.beginPath(); c.moveTo(-14 * k, 60 * k); c.lineTo(0, (60 + 70 * fl) * k); c.lineTo(14 * k, 60 * k); c.fill();
  c.fillStyle = '#e9edf5'; c.beginPath(); c.moveTo(0, -80 * k); c.quadraticCurveTo(26 * k, -40 * k, 22 * k, 60 * k); c.lineTo(-22 * k, 60 * k); c.quadraticCurveTo(-26 * k, -40 * k, 0, -80 * k); c.fill();
  c.fillStyle = T.r; c.beginPath(); c.moveTo(-22 * k, 30 * k); c.lineTo(-40 * k, 64 * k); c.lineTo(-22 * k, 60 * k); c.fill(); c.beginPath(); c.moveTo(22 * k, 30 * k); c.lineTo(40 * k, 64 * k); c.lineTo(22 * k, 60 * k); c.fill();
  c.fillStyle = '#6fb6ff'; c.beginPath(); c.arc(0, -20 * k, 9 * k, 0, TAU); c.fill(); c.restore(); };

// ───────── overlays (screen space) ─────────
function rich(txt, x, y, size, align = 'center') {   // *word* = yellow, !word! = red
  const parts = txt.split(/(\*[^*]+\*|![^!]+!)/).filter(Boolean).map(p => p[0] === '*' ? [p.slice(1, -1), T.y] : p[0] === '!' ? [p.slice(1, -1), T.r] : [p, T.ink]);
  c.font = A(size); const w = parts.reduce((s, [p]) => s + c.measureText(p).width, 0);
  let cx = align === 'center' ? x - w / 2 : x; c.textBaseline = 'middle';
  for (const [p, col] of parts) { c.fillStyle = 'rgba(0,0,0,.6)'; c.fillText(p, cx + 3 * K, y + 4 * K); c.fillStyle = col; c.fillText(p, cx, y); cx += c.measureText(p).width; }
  return w;
}
const O = {};
O.caption = (e, t) => { const d = e.dur ?? 2, a = seg(t, 0, .15) * (1 - seg(t, d - .18, d)); if (a <= 0) return; c.globalAlpha = a; c.save();
  const y = (e.y ?? .87) * H, s = .86 + .14 * back(seg(t, 0, .28)); c.translate(W / 2, y); c.scale(s, s); rich(e.text.toUpperCase(), 0, 0, e.size || 74); c.restore(); c.globalAlpha = 1; };
O.title = (e, t) => { const d = e.dur ?? 3, a = eo(seg(t, 0, .4)) * (1 - seg(t, d - .3, d)); if (a <= 0) return; c.globalAlpha = a;
  const x = 90 * K + (1 - a) * -40 * K, y = 120 * K; c.font = A(120); c.fillStyle = T.ink; c.textBaseline = 'alphabetic'; c.fillText(e.text, x, y + 50 * K);
  c.fillStyle = T.y; c.fillRect(x, y + 70 * K, 120 * K * a, 6 * K); c.font = F(700, 26); c.fillStyle = T.sub; c.fillText(e.sub || '', x, y + 112 * K); c.globalAlpha = 1; };
O.tag = (e, t) => { const a = eo(seg(t, 0, .3)); if (a <= 0) return; c.globalAlpha = a; c.font = F(800, 22); const w = c.measureText(e.text).width + 40 * K;
  const x = (e.x ?? .03) * W, y = (e.y ?? .04) * H; c.fillStyle = T.panel; c.beginPath(); c.roundRect(x, y, w, 46 * K, 23 * K); c.fill(); c.fillStyle = T.y; c.beginPath(); c.arc(x + 20 * K, y + 23 * K, 6 * K, 0, TAU); c.fill();
  c.fillStyle = T.ink; c.textBaseline = 'middle'; c.fillText(e.text, x + 34 * K, y + 24 * K); c.globalAlpha = 1; };
O.you = (e, t) => { const p = eo(seg(t, 0, .5)); if (p <= 0) return; const d = e.dur ?? 99, out = 1 - seg(t, d - .25, d); c.globalAlpha = out; const x = e.x * K, y = e.y * K, lx = (e.lx ?? e.x - 260) * K, ly = (e.ly ?? e.y - 230) * K;
  c.strokeStyle = T.r; c.lineWidth = 9 * K; c.lineCap = 'round'; c.beginPath();
  const cx = lx + 40 * K, cy = (ly + y) / 2 + 40 * K, N = 30; for (let i = 0; i <= N * p; i++) { const u = i / N, px = (1 - u) ** 2 * lx + 2 * (1 - u) * u * cx + u * u * (x - 18 * K), py = (1 - u) ** 2 * (ly + 30 * K) + 2 * (1 - u) * u * cy + u * u * (y - 18 * K); i ? c.lineTo(px, py) : c.moveTo(px, py); } c.stroke();
  if (p > .95) { const a = Math.atan2(y - cy, x - cx); c.fillStyle = T.r; c.beginPath(); c.moveTo(x - 6 * K, y - 6 * K); c.lineTo(x - 6 * K - Math.cos(a - .5) * 34 * K, y - 6 * K - Math.sin(a - .5) * 34 * K); c.lineTo(x - 6 * K - Math.cos(a + .5) * 34 * K, y - 6 * K - Math.sin(a + .5) * 34 * K); c.closePath(); c.fill(); }
  c.save(); c.translate(lx, ly); const s = back(seg(t, 0, .35)); c.scale(s, s); c.font = A(96); c.textBaseline = 'middle'; c.textAlign = 'center'; c.fillStyle = 'rgba(0,0,0,.5)'; c.fillText(e.text || 'YOU', 4 * K, 5 * K); c.fillStyle = T.r; c.fillText(e.text || 'YOU', 0, 0); c.textAlign = 'left'; c.restore(); c.globalAlpha = 1; };
O.pill = (e, t) => { const p = eo(seg(t, 0, .35)); if (p <= 0) return; const out = e.dur ? 1 - seg(t, e.dur - .25, e.dur) : 1; c.globalAlpha = Math.min(p, out);
  c.font = F(800, e.size || 30); const tw = c.measureText(e.text).width, w = tw + 56 * K, h = 64 * K, x = e.x * W - (e.align === 'right' ? w : 0) + (1 - p) * 60 * K, y = e.y * H;
  const red = e.tone === 'red'; c.fillStyle = red ? 'rgba(170,22,18,.94)' : T.panel; c.beginPath(); c.roundRect(x, y, w, h, 14 * K); c.fill(); c.strokeStyle = red ? '#ff6a5e' : T.line; c.lineWidth = 2 * K; c.stroke();
  c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.fillText(e.text, x + 28 * K, y + h / 2 + 1); c.globalAlpha = 1; };
O.stamp = (e, t) => { const d = e.dur ?? 99; const s = lerp(2.4, 1, eo(seg(t, 0, .22))), a = seg(t, 0, .1) * (1 - seg(t, d - .2, d)); c.save(); c.globalAlpha = a; c.translate(e.x * W, e.y * H); c.rotate(e.rot ?? -.12); c.scale(s, s);
  c.font = A(e.size || 92); const w = c.measureText(e.text).width, col = e.tone === 'yellow' ? T.y : e.tone === 'green' ? T.green : T.r; c.strokeStyle = col; c.lineWidth = 8 * K; c.strokeRect(-w / 2 - 30 * K, -62 * K, w + 60 * K, 124 * K);
  c.fillStyle = col; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(e.text, 0, 6 * K); c.textAlign = 'left'; c.restore(); };
O.big = (e, t) => { const d = e.dur ?? 99, a = seg(t, 0, .12) * (1 - seg(t, d - .2, d)); if (a <= 0) return; c.save(); c.globalAlpha = a; c.translate((e.x ?? .5) * W, (e.y ?? .45) * H); const s = .7 + .3 * back(seg(t, 0, .3)); c.scale(s, s);
  c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = A(e.size || 260); c.fillStyle = 'rgba(0,0,0,.5)'; c.fillText(e.text, 6 * K, 8 * K); c.fillStyle = e.tone === 'red' ? T.r : e.tone === 'yellow' ? T.y : T.ink; c.fillText(e.text, 0, 0);
  if (e.sub) { c.font = F(800, 32); const sw = c.measureText(e.sub).width, sy = (e.size || 260) * .64 * K; c.fillStyle = 'rgba(6,8,16,.72)'; c.beginPath(); c.roundRect(-sw / 2 - 22 * K, sy - 28 * K, sw + 44 * K, 56 * K, 12 * K); c.fill(); c.fillStyle = T.ink; c.fillText(e.sub, 0, sy + 1); } c.restore(); };
function panel(x, y, w, h, red) { c.fillStyle = T.panel; c.beginPath(); c.roundRect(x, y, w, h, 18 * K); c.fill(); c.strokeStyle = red ? T.r : T.line; c.lineWidth = 2 * K; c.stroke(); }
O.counter = (e, t) => { const a = seg(t, 0, .3); if (a <= 0) return; const v = lerp(e.from, e.to, eio(seg(t, e.t1a ?? 0, e.t1 ?? 2))); c.globalAlpha = a;
  const x = e.x * W, y = e.y * H; panel(x, y, 330 * K, 150 * K); c.font = F(700, 20); c.fillStyle = T.sub; c.textBaseline = 'top'; c.fillText(e.label, x + 26 * K, y + 22 * K);
  const txt = (e.decimals ? v.toFixed(e.decimals) : Math.round(v).toLocaleString('en-US')); c.font = A(72); c.fillStyle = e.col || T.ink; c.fillText(txt, x + 26 * K, y + 52 * K); const nw = c.measureText(txt).width;
  c.font = F(800, 30); c.fillStyle = T.sub; c.fillText(e.unit || '', x + 40 * K + nw, y + 88 * K); c.globalAlpha = 1; };
O.gauge = (e, t) => { const a = eo(seg(t, 0, .35)); if (a <= 0) return; const d = e.dur ?? 99, out = 1 - seg(t, d - .25, d); const x = e.x * W, y = e.y * H, r = (e.r || 170) * K, v = lerp(e.from || 0, e.to, eo(seg(t, e.t1a ?? .2, e.t1 ?? 1.4))), u = clamp(v / e.max);
  c.globalAlpha = a * out; panel(x - r - 40 * K, y - r - 50 * K, r * 2 + 80 * K, r + 170 * K);
  c.lineWidth = 22 * K; c.lineCap = 'butt'; c.strokeStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.arc(x, y, r, Math.PI, TAU); c.stroke();
  const gg = c.createLinearGradient(x - r, 0, x + r, 0); gg.addColorStop(0, T.cyan); gg.addColorStop(.6, T.y); gg.addColorStop(1, T.r); c.strokeStyle = gg; c.beginPath(); c.arc(x, y, r, Math.PI, Math.PI + Math.PI * u); c.stroke();
  const na = Math.PI + Math.PI * u + Math.sin(t * 30) * .01 * u; c.strokeStyle = T.ink; c.lineWidth = 6 * K; c.lineCap = 'round'; c.beginPath(); c.moveTo(x, y); c.lineTo(x + Math.cos(na) * r * .82, y + Math.sin(na) * r * .82); c.stroke(); c.fillStyle = T.ink; c.beginPath(); c.arc(x, y, 12 * K, 0, TAU); c.fill();
  c.textAlign = 'center'; c.font = A(70); c.fillStyle = u > .8 ? T.r : T.ink; c.textBaseline = 'top'; c.fillText(`${Math.round(v)}${e.unit || ''}`, x, y + 22 * K);
  c.font = F(700, 20); c.fillStyle = T.sub; c.fillText(e.label, x, y - r - 34 * K); c.textAlign = 'left'; c.globalAlpha = 1; };
O.depth = (e, t) => { const a = eo(seg(t, 0, .35)); if (a <= 0) return; const dd = e.dur ?? 99; c.globalAlpha = a * (1 - seg(t, dd - .25, dd)); const x = e.x * W, y = e.y * H, w = 300 * K, h = 520 * K, max = e.max || 900, d = eio(seg(t, .2, 1.8)) * (e.to ?? max) / max;
  c.save(); c.beginPath(); c.roundRect(x, y, w, h, 20 * K); c.clip();
  const g = c.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, '#2a7fb8'); g.addColorStop(.4, '#0b3a66'); g.addColorStop(1, '#020a18'); c.fillStyle = g; c.fillRect(x, y, w, h);
  c.fillStyle = 'rgba(255,255,255,.55)'; c.font = F(700, 18); c.textBaseline = 'middle'; for (let m = 0; m <= max; m += max / 3) { const yy = y + 40 * K + (m / max) * (h - 90 * K); c.fillRect(x, yy, 22 * K, 2 * K); c.fillText(`${Math.round(m)} m`, x + 30 * K, yy); }
  const dy = y + 40 * K + d * (h - 90 * K); c.save(); c.translate(x + w * .66, dy); c.fillStyle = '#05080f'; c.beginPath(); c.ellipse(0, 0, 34 * K, 9 * K, 0, 0, TAU); c.fill(); c.beginPath(); c.arc(30 * K, -2 * K, 9 * K, 0, TAU); c.fill(); c.fillRect(-60 * K, -4 * K, 30 * K, 7 * K); c.restore();
  c.restore(); c.strokeStyle = T.line; c.lineWidth = 2 * K; c.beginPath(); c.roundRect(x, y, w, h, 20 * K); c.stroke();
  c.font = F(800, 24); c.fillStyle = T.ink; c.textBaseline = 'alphabetic'; c.fillText(e.label || 'SAME PRESSURE AS', x, y - 18 * K); c.globalAlpha = 1; };
O.thermo = (e, t) => { const a = eo(seg(t, 0, .3)); if (a <= 0) return; const dd = e.dur ?? 99; const x = e.x * W, y = e.y * H, h = 460 * K, v = lerp(e.from ?? 0, e.to, eo(seg(t, e.t1a ?? .2, e.t1 ?? 1.2))), u = clamp((v - (e.min ?? 0)) / (e.max - (e.min ?? 0)));
  c.globalAlpha = a * (1 - seg(t, dd - .25, dd)); const cold = e.to < 0; const col = cold ? T.cyan : T.r;
  c.fillStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.roundRect(x - 22 * K, y - h, 44 * K, h, 22 * K); c.fill(); c.beginPath(); c.arc(x, y + 20 * K, 46 * K, 0, TAU); c.fill();
  const gl = c.createRadialGradient(x, y, 0, x, y, 220 * K); gl.addColorStop(0, rgba(col, .45 * (cold ? 1 - u : u))); gl.addColorStop(1, rgba(col, 0)); c.fillStyle = gl; c.fillRect(x - 240 * K, y - 240 * K, 480 * K, 480 * K);
  c.fillStyle = col; c.beginPath(); c.arc(x, y + 20 * K, 34 * K, 0, TAU); c.fill(); c.beginPath(); c.roundRect(x - 13 * K, y - h * u + 10 * K, 26 * K, h * u, 13 * K); c.fill();
  c.font = A(150); c.fillStyle = T.ink; c.textBaseline = 'middle'; c.fillText(`${Math.round(v)}°C`, x + 90 * K, y - h * .55);
  c.font = F(700, 26); c.fillStyle = T.sub; c.fillText(e.label || '', x + 96 * K, y - h * .55 + 100 * K); c.globalAlpha = 1; };
O.melt = (e, t) => { const a = seg(t, 0, .25); if (a <= 0) return; const dd = e.dur ?? 99; const x = e.x * W, y = e.y * H, m = eio(seg(t, .4, 2.0)); c.globalAlpha = a * (1 - seg(t, dd - .25, dd));
  const glow = c.createRadialGradient(x, y, 0, x, y, 220 * K); glow.addColorStop(0, `rgba(255,120,40,${.25 + .4 * m})`); glow.addColorStop(1, 'rgba(255,120,40,0)'); c.fillStyle = glow; c.fillRect(x - 240 * K, y - 240 * K, 480 * K, 480 * K);
  const bh = 120 * K * (1 - m * .88), bw = 230 * K * (1 + m * .9); const mg = c.createLinearGradient(0, y - bh, 0, y); mg.addColorStop(0, m > .3 ? '#ffe2c0' : '#b8bec9'); mg.addColorStop(1, m > .3 ? '#d9a074' : '#7e8594'); c.fillStyle = mg;
  c.beginPath(); c.moveTo(x - bw / 2, y); c.lineTo(x - bw / 2 + 22 * K * (1 - m), y - bh); c.quadraticCurveTo(x, y - bh - 14 * K * (1 - m), x + bw / 2 - 22 * K * (1 - m), y - bh); c.lineTo(x + bw / 2, y);
  for (let i = 0; i <= 8; i++) { const px = x + bw / 2 - i * bw / 8; c.lineTo(px, y + (Math.sin(i * 2.3) * .5 + .5) * 18 * K * m); } c.closePath(); c.fill();
  for (let i = 0; i < 4; i++) { const dx = x + (i - 1.5) * bw * .22, dl = 50 * K * m * (0.5 + hash(i)); c.beginPath(); c.ellipse(dx, y + dl * .5, 8 * K * m, dl * .5 + 1, 0, 0, TAU); c.fill(); }
  c.font = A(44); c.fillStyle = '#2a2f3a'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.globalAlpha = a * (1 - m); c.fillText('Pb', x, y - bh / 2); c.textAlign = 'left'; c.globalAlpha = 1; };
O.timer = (e, t) => { const a = eo(seg(t, 0, .3)); if (a <= 0) return; const sec = lerp(e.from || 0, e.to, eio(seg(t, .1, e.t1 ?? 3))), dead = e.dead != null && t > e.dead;
  const x = e.x * W, y = e.y * H; c.globalAlpha = a; panel(x, y, 430 * K, 170 * K, dead); c.font = F(700, 20); c.fillStyle = T.sub; c.textBaseline = 'top'; c.fillText(e.label, x + 28 * K, y + 22 * K);
  const hh = Math.floor(sec / 3600), mm = Math.floor(sec / 60) % 60, s2 = Math.floor(sec % 60); c.font = A(88); c.fillStyle = dead ? T.r : T.ink; c.fillText(`${hh}:${String(mm).padStart(2, '0')}:${String(s2).padStart(2, '0')}`, x + 28 * K, y + 54 * K); c.globalAlpha = 1; };
// lineup: planets side by side on a baseline, growing in one by one. items: [{kind, r (px), label, sun?}]
O.lineup = (e, t) => { const items = e.items, gap = (e.gap ?? 60) * K, base = (e.y ?? .62) * H; let tot = items.reduce((s, i) => s + i.r * 2 * K, 0) + gap * (items.length - 1), x = (W - tot) / 2;
  items.forEach((it, i) => { const p = eo(seg(t, (it.at ?? i * .5), (it.at ?? i * .5) + .5)); const r = it.r * K; if (p > 0) { c.save(); c.globalAlpha = p;
      if (it.kind === 'sun') E.sun({ x: x + r, y: base - r, r, surface: true }, t); else E_planet({ ...it, x: x + r, y: base - r, r: r * (.8 + .2 * p), light: -2.3, glow: 1.2, label: null }, t);
      c.font = F(800, 24); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(it.label || '', x + r, base + 40 * K); if (it.note) { c.font = F(700, 20); c.fillStyle = T.sub; c.fillText(it.note, x + r, base + 72 * K); } c.textAlign = 'left'; c.restore(); }
    x += r * 2 + gap; }); };
// fit: "N small bodies fit inside a big one": dots fill the big disc, counter counts up
O.fit = (e, t) => { const x = (e.x ?? .5) * W, y = (e.y ?? .5) * H, R = (e.r || 380) * K, n = e.show || 300, p = eio(seg(t, .3, e.t1 ?? 3));
  E_planet({ kind: e.big || 'jupiter', x, y, r: R, light: -2.4, glow: 1.25 }, t); c.save(); c.beginPath(); c.arc(x, y, R * .97, 0, TAU); c.clip();
  const rs = R * Math.sqrt(.82 / n), Rg = rng(3); let k = 0;
  for (let gy = -R; gy < R; gy += rs * 1.75) for (let gx = -R + ((gy / (rs * 1.75)) & 1) * rs; gx < R; gx += rs * 2) { if (gx * gx + gy * gy > (R - rs) ** 2) continue; if (k++ > n * p) break;
    c.fillStyle = '#2f7fd6'; c.beginPath(); c.arc(x + gx, y + gy, rs * .92, 0, TAU); c.fill(); c.fillStyle = 'rgba(80,190,110,.9)'; c.beginPath(); c.arc(x + gx - rs * .25, y + gy - rs * .1, rs * .4, 0, TAU); c.fill(); }
  c.restore(); c.font = A(110); c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = 'rgba(0,0,0,.6)'; c.fillText(`${Math.round(lerp(0, e.count, p)).toLocaleString('en-US')}`, x + 4 * K, y + 6 * K); c.fillStyle = T.ink; c.fillText(`${Math.round(lerp(0, e.count, p)).toLocaleString('en-US')}`, x, y);
  c.font = F(800, 30); c.fillText(e.label || 'EARTHS FIT INSIDE', x, y + 86 * K); c.textAlign = 'left'; };
// radar: sweeping scope with labelled blips
O.radar = (e, t) => { const a = eo(seg(t, 0, .35)); if (a <= 0) return; const x = (e.x ?? .5) * W, y = (e.y ?? .5) * H, R = (e.r || 300) * K; c.globalAlpha = a;
  c.fillStyle = 'rgba(2,14,8,.88)'; c.beginPath(); c.arc(x, y, R, 0, TAU); c.fill(); c.strokeStyle = 'rgba(76,255,138,.35)'; c.lineWidth = 2 * K; for (let i = 1; i <= 4; i++) { c.beginPath(); c.arc(x, y, R * i / 4, 0, TAU); c.stroke(); }
  c.beginPath(); c.moveTo(x - R, y); c.lineTo(x + R, y); c.moveTo(x, y - R); c.lineTo(x, y + R); c.stroke();
  const sw = t * 1.6; const g = c.createConicGradient ? c.createConicGradient(sw - .9, x, y) : null; if (g) { g.addColorStop(0, 'rgba(76,255,138,0)'); g.addColorStop(.14, 'rgba(76,255,138,.35)'); g.addColorStop(.145, 'rgba(76,255,138,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, R, 0, TAU); c.fill(); }
  for (const b of e.blips || []) { const bx = x + b.x * R, by = y + b.y * R, ang = (Math.atan2(by - y, bx - x) + TAU) % TAU, since = ((sw % TAU) - ang + TAU) % TAU, k = Math.max(.25, 1 - since / 3);
    c.fillStyle = rgba(b.red ? T.r : T.green, k); c.beginPath(); c.arc(bx, by, 9 * K, 0, TAU); c.fill(); c.font = F(800, 20); c.fillText(b.label || '', bx + 16 * K, by + 6 * K); }
  c.font = F(800, 22); c.fillStyle = T.green; c.textAlign = 'center'; c.fillText(e.label || '', x, y - R - 24 * K); c.textAlign = 'left'; c.globalAlpha = 1; };
// evidence: a real image (or video frame) in a white frame with a tag and credit; slow push-in
O.evidence = (e, t) => { const d = e.dur ?? 99, p = eo(seg(t, 0, .35)) * (1 - seg(t, d - .25, d)); if (p <= 0) return; const im = IMG[e.src]; c.save(); c.globalAlpha = p;
  const w = (e.w || 900) * K, h = (e.h || 560) * K, x = (e.x ?? .5) * W, y = (e.y ?? .47) * H; c.translate(x, y); c.rotate(e.rot ?? -.015); c.scale(.92 + .08 * p, .92 + .08 * p);
  c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 40 * K; c.fillStyle = '#f4f2ec'; c.fillRect(-w / 2 - 12 * K, -h / 2 - 12 * K, w + 24 * K, h + 24 * K); c.shadowBlur = 0;
  c.beginPath(); c.rect(-w / 2, -h / 2, w, h); c.clip(); c.fillStyle = '#111'; c.fillRect(-w / 2, -h / 2, w, h);
  if (im && im.complete && im.naturalWidth) { const z = 1 + (e.zoom ?? .08) * seg(t, 0, d === 99 ? 6 : d), sc = Math.max(w / im.naturalWidth, h / im.naturalHeight) * z, iw = im.naturalWidth * sc, ih = im.naturalHeight * sc;
    const fx = (e.fx ?? .5), fy = (e.fy ?? .5); c.drawImage(im, -iw * fx + (fx - .5) * 0, -ih * fy, iw, ih); }
  c.restore(); c.save(); c.globalAlpha = p; c.translate(x, y);
  c.font = F(900, 22); const tg = e.tag || 'REAL IMAGE'; const tw = c.measureText(tg).width + 36 * K; c.fillStyle = T.r; c.fillRect(-w / 2 - 12 * K, -h / 2 - 58 * K, tw, 40 * K); c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.fillText(tg, -w / 2 + 6 * K, -h / 2 - 37 * K);
  c.font = F(700, 18); c.fillStyle = 'rgba(255,255,255,.75)'; c.fillText(e.credit || '', -w / 2, h / 2 + 34 * K); c.restore(); };
// chapter: full-screen number + title, yellow circle wipe
O.chapter = (e, t) => { const d = e.dur ?? 1.4; if (t > d + .35) return; const open = eo(seg(t, 0, .3)), close = seg(t, d, d + .35), r = (open - close * close) * Math.hypot(W, H) * .6;
  c.save(); c.beginPath(); c.arc(W / 2, H / 2, Math.max(0, r), 0, TAU); c.clip(); c.fillStyle = T.y; c.fillRect(0, 0, W, H);
  c.fillStyle = '#0b0d14'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = F(800, 30); c.fillText(e.n || '', W / 2, H / 2 - 120 * K); c.font = A(170); c.fillText(e.text, W / 2, H / 2 + 20 * K); c.textAlign = 'left'; c.restore(); };
O.flash = (e, t) => { const k = 1 - seg(t, 0, e.dur || .35); if (k <= 0) return; c.fillStyle = `rgba(255,255,255,${k * (e.a ?? .6)})`; c.fillRect(0, 0, W, H); };

// ───────── props & infographics (v2: the "joke gets a gag" toolkit) ─────────
const PX = e => [(e.x ?? .5) * W, (e.y ?? .5) * H];
const fadeIO = (e, t, d = .3) => { const dd = e.dur ?? 999; return eo(seg(t, 0, d)) * (1 - seg(t, dd - .25, dd)); };
// label: small bold uppercase text, one at a time; underline:true draws a red rule under it
O.label = (e, t) => { const a = fadeIO(e, t, .25); if (a <= 0) return; const [x, y] = PX(e); c.save(); c.globalAlpha = a; c.font = F(900, e.size || 30); c.textAlign = e.align || 'center'; c.textBaseline = 'middle';
  const txt = (e.text || '').toUpperCase(), w = c.measureText(txt).width; c.fillStyle = 'rgba(0,0,0,.55)'; c.fillText(txt, x + 2 * K, y + 3 * K); c.fillStyle = e.tone === 'red' ? T.r : e.tone === 'yellow' ? T.y : e.tone === 'green' ? T.green : T.ink; c.fillText(txt, x, y);
  if (e.underline) { const x0 = e.align === 'left' ? x : x - w / 2; c.fillStyle = T.r; c.fillRect(x0, y + (e.size || 30) * .62 * K, w * eo(seg(t, .1, .45)), 4 * K); }
  if (e.sub) { c.font = F(700, (e.size || 30) * .55); c.fillStyle = T.sub; c.fillText(e.sub, x, y + (e.size || 30) * 1.1 * K); } c.restore(); };
// receipt: a long till receipt that scrolls up; items:[text,...]; title; total
O.receipt = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), w = (e.w || 330) * K, items = e.items || [], lh = 34 * K, h = (110 + items.length * 34 + 70) * K, rise = (1 - eo(seg(t, 0, 1.2))) * H * .6;
  c.save(); c.globalAlpha = a; c.translate(x, y + rise); c.rotate(e.rot ?? -.02); c.shadowColor = 'rgba(0,0,0,.5)'; c.shadowBlur = 30 * K; c.fillStyle = '#f6f3ea'; c.beginPath(); c.moveTo(-w / 2, -h / 2);
  for (let i = 0; i <= 20; i++) c.lineTo(-w / 2 + i * w / 20, -h / 2 + (i % 2 ? 8 : 0) * K); for (let i = 20; i >= 0; i--) c.lineTo(-w / 2 + i * w / 20, h / 2 - (i % 2 ? 8 : 0) * K); c.closePath(); c.fill(); c.shadowBlur = 0;
  c.fillStyle = '#1b1b1b'; c.textBaseline = 'middle'; c.textAlign = 'center'; c.font = F(900, 24); c.fillText((e.title || 'RECEIPT').toUpperCase(), 0, -h / 2 + 48 * K); c.fillRect(-w / 2 + 24 * K, -h / 2 + 74 * K, w - 48 * K, 2 * K);
  c.font = F(700, 20); items.forEach((it, i) => { const iy = -h / 2 + 106 * K + i * lh; if (t < .3 + i * .08) return; const [l, r] = Array.isArray(it) ? it : [it, '×1']; c.textAlign = 'left'; c.fillText(l, -w / 2 + 28 * K, iy); c.textAlign = 'right'; c.fillText(r, w / 2 - 28 * K, iy); });
  if (e.total) { c.fillRect(-w / 2 + 24 * K, h / 2 - 66 * K, w - 48 * K, 2 * K); c.font = F(900, 24); c.textAlign = 'left'; c.fillText('TOTAL', -w / 2 + 28 * K, h / 2 - 38 * K); c.textAlign = 'right'; c.fillStyle = T.r; c.fillText(e.total, w / 2 - 28 * K, h / 2 - 38 * K); }
  c.restore(); };
// doc: an official-looking paper with a title, field rows and an optional stamp. fields:[[label, value], ...]
O.doc = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), w = (e.w || 640) * K, rows = e.fields || [], h = (e.h || (190 + rows.length * 62)) * K;
  c.save(); c.globalAlpha = a; c.translate(x, y + (1 - eo(seg(t, 0, .5))) * 60 * K); c.rotate(e.rot ?? .03); c.shadowColor = 'rgba(0,0,0,.55)'; c.shadowBlur = 40 * K; c.fillStyle = '#f4f1e8'; c.fillRect(-w / 2, -h / 2, w, h); c.shadowBlur = 0;
  c.fillStyle = '#7c7768'; c.font = F(700, 16); c.textAlign = 'center'; c.textBaseline = 'middle'; if (e.org) c.fillText(e.org.toUpperCase(), 0, -h / 2 + 40 * K);
  c.fillStyle = '#1b1b1b'; c.font = F(900, 34); c.fillText((e.title || '').toUpperCase(), 0, -h / 2 + (e.org ? 86 : 64) * K);
  rows.forEach(([l, v], i) => { const ry = -h / 2 + (e.org ? 150 : 128) * K + i * 62 * K; if (t < .35 + i * .25) return; c.textAlign = 'left'; c.font = F(900, 18); c.fillStyle = '#4a463c'; c.fillText(l.toUpperCase(), -w / 2 + 40 * K, ry); c.font = F(500, 21); c.fillStyle = '#1b1b1b'; c.fillText(v, -w / 2 + 210 * K, ry); c.fillStyle = 'rgba(0,0,0,.12)'; c.fillRect(-w / 2 + 210 * K, ry + 18 * K, w - 250 * K, 1.5 * K); });
  if (!rows.length) { c.fillStyle = 'rgba(0,0,0,.14)'; for (let i = 0; i < 6; i++) c.fillRect(-w / 2 + 60 * K, -h / 2 + 150 * K + i * 34 * K, (w - 120 * K) * (i === 5 ? .6 : 1), 10 * K); }
  if (e.stamp && t >= (e.stampAt ?? 1.2)) { const st = t - (e.stampAt ?? 1.2), s = lerp(2.2, 1, eo(seg(st, 0, .2))); c.save(); c.translate(w * .18, h * .32); c.rotate(-.14); c.scale(s, s); c.globalAlpha = a * seg(st, 0, .08);
    c.font = A(56); const sw = c.measureText(e.stamp).width, col = e.stampTone === 'green' ? '#1f9d4c' : T.r; c.strokeStyle = col; c.lineWidth = 6 * K; c.strokeRect(-sw / 2 - 18 * K, -40 * K, sw + 36 * K, 80 * K); c.fillStyle = col; c.textAlign = 'center'; c.fillText(e.stamp, 0, 4 * K); c.restore(); }
  c.restore(); };
// loading: a progress box ("TRANSLATING…") that fills to `to` (0-1) then can freeze
O.loading = (e, t) => { const a = fadeIO(e, t, .2); if (a <= 0) return; const [x, y] = PX(e), w = 460 * K, h = 120 * K, p = lerp(0, e.to ?? .4, eio(seg(t, .2, e.t1 ?? 1.8)));
  c.save(); c.globalAlpha = a; panel(x - w / 2, y - h / 2, w, h); c.font = F(900, 22); c.fillStyle = T.ink; c.textBaseline = 'middle'; c.fillText((e.text || 'LOADING…').toUpperCase(), x - w / 2 + 30 * K, y - 18 * K);
  c.fillStyle = 'rgba(255,255,255,.12)'; c.beginPath(); c.roundRect(x - w / 2 + 30 * K, y + 14 * K, w - 60 * K, 14 * K, 7 * K); c.fill(); c.fillStyle = e.tone === 'red' ? T.r : T.cyan; c.beginPath(); c.roundRect(x - w / 2 + 30 * K, y + 14 * K, (w - 60 * K) * p, 14 * K, 7 * K); c.fill(); c.restore(); };
// options: the survival-game list. items:[{text, at, out}] — the item lights up at `at` and is struck through at `out`
O.options = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), items = e.items || []; c.save(); c.globalAlpha = a;
  c.font = F(900, 30); c.fillStyle = T.ink; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText((e.title || 'YOUR OPTIONS').toUpperCase(), x, y);
  items.forEach((it, i) => { const iy = y + (64 + i * 58) * K, on = t >= (it.at ?? i), out = it.out != null && t >= it.out, act = on && !out; if (t < (it.at ?? i) - .6 && !e.showAll) return;
    c.font = F(800, 28); const txt = `${i + 1}. ${it.text.toUpperCase()}`, tw = c.measureText(txt).width;
    if (act) { c.strokeStyle = T.r; c.lineWidth = 3 * K; c.beginPath(); c.roundRect(x - 18 * K, iy - 26 * K, tw + 36 * K, 52 * K, 10 * K); c.stroke(); c.fillStyle = 'rgba(255,59,48,.14)'; c.fill(); }
    c.fillStyle = out ? 'rgba(243,245,250,.35)' : on ? T.ink : 'rgba(243,245,250,.45)'; c.fillText(txt, x, iy);
    if (out) { const p = eo(seg(t, it.out, it.out + .3)); c.fillStyle = T.r; c.fillRect(x - 6 * K, iy - 2 * K, (tw + 12 * K) * p, 4 * K); } });
  if (e.verdict && t >= e.verdict.at) { const p = eo(seg(t, e.verdict.at, e.verdict.at + .3)); c.globalAlpha = a * p; c.font = A(64); c.fillStyle = T.r; c.fillText(e.verdict.text.toUpperCase(), x, y + (90 + items.length * 58) * K); }
  c.restore(); };
// panels: split screen frames with titles; put other elements inside each panel
O.panels = (e, t) => { const a = fadeIO(e, t, .2); if (a <= 0) return; const n = (e.titles || []).length || 2, pw = W / n; c.save(); c.globalAlpha = a;
  for (let i = 0; i < n; i++) { const p = eo(seg(t, i * (e.stagger ?? .25), i * (e.stagger ?? .25) + .35)); if (p <= 0) continue; c.fillStyle = (e.bg || [])[i] || (i % 2 ? '#0b1430' : '#120c22'); c.globalAlpha = a * p; c.fillRect(i * pw, 0, pw, H);
    c.fillStyle = 'rgba(255,255,255,.18)'; c.fillRect((i + 1) * pw - 2 * K, 0, 4 * K, H); c.font = F(900, 30); c.fillStyle = T.ink; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(((e.titles || [])[i] || '').toUpperCase(), i * pw + pw / 2, 70 * K); }
  c.restore(); };
// stick: a stick-figure "YOU" for relatable gags. pose: stand | wave | panic | sit
function stick(x, y, s, pose, t, col) { const k = s / 100; c.save(); c.translate(x, y); c.strokeStyle = col; c.fillStyle = col; c.lineWidth = 7 * k; c.lineCap = 'round';
  c.beginPath(); c.arc(0, -82 * k, 15 * k, 0, TAU); c.stroke(); c.beginPath(); c.moveTo(0, -66 * k); c.lineTo(0, -10 * k); c.stroke();
  const arm = pose === 'panic' ? [[-34, -96 + 8 * Math.sin(t * 20)], [34, -96 - 8 * Math.sin(t * 20)]] : pose === 'wave' ? [[-26, -26], [34, -92 + 10 * Math.sin(t * 8)]] : [[-24, -24], [24, -24]];
  for (const [ax, ay] of arm) { c.beginPath(); c.moveTo(0, -56 * k); c.lineTo(ax * k, ay * k); c.stroke(); }
  if (pose === 'sit') { c.beginPath(); c.moveTo(0, -10 * k); c.lineTo(30 * k, -10 * k); c.lineTo(30 * k, 30 * k); c.stroke(); } else { c.beginPath(); c.moveTo(0, -10 * k); c.lineTo(-18 * k, 34 * k); c.moveTo(0, -10 * k); c.lineTo(18 * k, 34 * k); c.stroke(); }
  c.restore(); }
O.stick = (e, t) => { const a = fadeIO(e, t, .2); if (a <= 0) return; const [x, y] = PX(e); c.save(); c.globalAlpha = a; stick(x, y, (e.s || 160) * K, e.pose || 'stand', t, e.col || '#f3f5fa');
  if (e.label) { c.font = F(900, 26); c.fillStyle = T.r; c.textAlign = 'center'; c.fillText(e.label.toUpperCase(), x, y - (e.s || 160) * 1.25 * K); } c.restore(); };
// eyes: a dark room full of eyes looking at `you` (x,y = where they look)
O.eyes = (e, t) => { const a = fadeIO(e, t, .4); if (a <= 0) return; const R = rng(21), lx = (e.lookX ?? .7) * W, ly = (e.lookY ?? .7) * H; c.save(); c.globalAlpha = a; c.fillStyle = '#1a1a26'; c.fillRect(0, 0, W, H);
  for (let i = 0; i < (e.n || 60); i++) { const ex = R() * W, ey = R() * H * .9, r = (16 + R() * 18) * K, open = Math.min(1, (t - R() * 1.2) * 4); if (open <= 0) continue;
    c.fillStyle = '#f6f6f2'; c.beginPath(); c.ellipse(ex, ey, r, r * .75 * open, 0, 0, TAU); c.fill(); const ang = Math.atan2(ly - ey, lx - ex); c.fillStyle = '#111'; c.beginPath(); c.arc(ex + Math.cos(ang) * r * .4, ey + Math.sin(ang) * r * .3, r * .42 * open, 0, TAU); c.fill(); }
  stick(lx, ly, 150 * K, 'panic', t, '#f3f5fa'); c.restore(); };
// balance: a scale weighing two things. left/right labels, tilt (+ = right side heavier)
O.balance = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), r = 260 * K, tilt = (e.tilt ?? .25) * eio(seg(t, .4, 1.4)); c.save(); c.globalAlpha = a; c.strokeStyle = '#c9ccd6'; c.fillStyle = '#c9ccd6'; c.lineWidth = 8 * K; c.lineCap = 'round';
  c.beginPath(); c.moveTo(x, y + 220 * K); c.lineTo(x, y); c.stroke(); c.fillRect(x - 90 * K, y + 214 * K, 180 * K, 12 * K);
  const lx = x - Math.cos(tilt) * r, ly = y - Math.sin(tilt) * r, rx = x + Math.cos(tilt) * r, ry = y + Math.sin(tilt) * r; c.beginPath(); c.moveTo(lx, ly); c.lineTo(rx, ry); c.stroke(); c.beginPath(); c.arc(x, y, 12 * K, 0, TAU); c.fill();
  for (const [px, py, lab] of [[lx, ly, e.left], [rx, ry, e.right]]) { c.lineWidth = 3 * K; c.beginPath(); c.moveTo(px, py); c.lineTo(px - 60 * K, py + 110 * K); c.moveTo(px, py); c.lineTo(px + 60 * K, py + 110 * K); c.stroke();
    c.beginPath(); c.ellipse(px, py + 112 * K, 80 * K, 14 * K, 0, 0, Math.PI); c.fill(); c.font = F(900, 26); c.textAlign = 'center'; c.fillStyle = T.ink; c.fillText((lab || '').toUpperCase(), px, py + 160 * K); }
  c.restore(); };
// pie: slices:[{v, label, col}]; a side stat box via `stat` {big, small}
O.pie = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), r = (e.r || 240) * K, sl = e.slices || [], tot = sl.reduce((s, q) => s + q.v, 0), p = eio(seg(t, .2, 1.2)); c.save(); c.globalAlpha = a; let ang = -Math.PI / 2;
  sl.forEach((q, i) => { const sw = q.v / tot * TAU * p; c.fillStyle = q.col || [T.r, '#3b6fb6', T.y, T.green][i % 4]; c.beginPath(); c.moveTo(x, y); c.arc(x, y, r, ang, ang + sw); c.closePath(); c.fill();
    if (p > .9) { const m = ang + sw / 2; c.font = F(900, 20); c.fillStyle = '#fff'; c.textAlign = 'center'; c.fillText((q.label || '').toUpperCase(), x + Math.cos(m) * r * .58, y + Math.sin(m) * r * .58); } ang += sw; });
  if (e.title) { c.font = F(900, 28); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(e.title.toUpperCase(), x, y - r - 40 * K); }
  if (e.stat && t > 1.2) { const sx = x + r + 90 * K; panel(sx, y - 90 * K, 300 * K, 180 * K); c.textAlign = 'center'; c.font = F(900, 26); c.fillStyle = T.ink; c.fillText(e.stat.label.toUpperCase(), sx + 150 * K, y - 40 * K); c.font = A(76); c.fillStyle = T.r; c.fillText(e.stat.big, sx + 150 * K, y + 24 * K); c.font = F(700, 16); c.fillStyle = T.sub; c.fillText((e.stat.small || '').toUpperCase(), sx + 150 * K, y + 66 * K); }
  c.restore(); };
// icons: an isotype grid. count icons, `from`→`to` lit (the rest fade to red ghosts); icon: dot | planet | astronaut | rocket | person
O.icons = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const n = e.count || 100, cols = e.cols || 20, gs = (e.size || 56) * K, x0 = (e.x ?? .5) * W - cols * gs / 2, y0 = (e.y ?? .3) * H, lit = Math.round(lerp(e.from ?? n, e.to ?? n, eio(seg(t, e.t1a ?? .8, e.t1 ?? 2))));
  c.save(); c.globalAlpha = a; for (let i = 0; i < n; i++) { const ix = x0 + (i % cols) * gs + gs / 2, iy = y0 + Math.floor(i / cols) * gs + gs / 2, on = i < lit, appear = seg(t, i * .006, i * .006 + .2); if (appear <= 0) continue; c.globalAlpha = a * appear * (on ? 1 : .35);
    const col = on ? (e.col || T.ink) : T.r; c.fillStyle = col; c.strokeStyle = col;
    if (e.icon === 'astronaut') astro(ix, iy + gs * .25, gs * .7, 0, 0, 0); else if (e.icon === 'person') stick(ix, iy + gs * .35, gs * .55, 'stand', 0, col); else if (e.icon === 'rocket') { c.beginPath(); c.moveTo(ix, iy - gs * .35); c.lineTo(ix + gs * .14, iy + gs * .3); c.lineTo(ix - gs * .14, iy + gs * .3); c.fill(); } else { c.beginPath(); c.arc(ix, iy, gs * .32, 0, TAU); c.fill(); } }
  c.globalAlpha = a; if (e.label) { c.font = F(900, 26); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(e.label.toUpperCase(), (e.x ?? .5) * W, y0 - 40 * K); }
  if (e.caption) { c.font = F(700, 16); c.fillStyle = T.sub; c.textAlign = 'left'; c.fillText(e.caption.toUpperCase(), x0, y0 + Math.ceil(n / cols) * gs + 26 * K); }
  if (e.big) { c.font = A(72); c.fillStyle = lit < n ? T.r : T.ink; c.textAlign = 'left'; c.fillText(typeof e.big === 'string' ? e.big : lit.toLocaleString('en-US'), x0 + cols * gs + 40 * K, y0 + 60 * K); } c.restore(); };
// xray: a body outline with a glowing highlight and a pointer label
O.xray = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), k = (e.s || 100) * K / 100; c.save(); c.globalAlpha = a; c.strokeStyle = 'rgba(76,255,138,.25)'; c.lineWidth = 1; for (let gx = 0; gx < W; gx += 60 * K) { c.beginPath(); c.moveTo(gx, 0); c.lineTo(gx, H); c.stroke(); } for (let gy = 0; gy < H; gy += 60 * K) { c.beginPath(); c.moveTo(0, gy); c.lineTo(W, gy); c.stroke(); }
  c.strokeStyle = T.green; c.lineWidth = 5 * k; c.beginPath(); c.arc(x, y - 250 * k, 60 * k, 0, TAU); c.stroke(); c.beginPath(); c.roundRect(x - 110 * k, y - 175 * k, 220 * k, 300 * k, 30 * k); c.stroke();
  const hl = e.part === 'heart' ? [[x - 10 * k, y - 80 * k, 40 * k]] : e.part === 'brain' ? [[x, y - 255 * k, 40 * k]] : e.part === 'blood' ? [[x - 40 * k, y - 60 * k, 50 * k], [x + 40 * k, y - 60 * k, 50 * k], [x, y + 40 * k, 50 * k]] : [[x - 45 * k, y - 90 * k, 52 * k], [x + 45 * k, y - 90 * k, 52 * k]];
  const gl = .55 + .35 * Math.sin(t * 5); for (const [hx, hy, hr] of hl) { const g = c.createRadialGradient(hx, hy, 0, hx, hy, hr); g.addColorStop(0, `rgba(190,255,210,${gl})`); g.addColorStop(1, 'rgba(76,255,138,0)'); c.fillStyle = g; c.beginPath(); c.arc(hx, hy, hr, 0, TAU); c.fill(); }
  if (e.label && t > .5) { const [hx, hy] = hl[0]; c.strokeStyle = T.r; c.lineWidth = 3 * K; c.beginPath(); c.moveTo(hx, hy); c.lineTo(hx - 260 * K, hy - 70 * K); c.stroke(); panel(hx - 520 * K, hy - 100 * K, 260 * K, 56 * K); c.font = F(900, 20); c.fillStyle = T.ink; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText(e.label.toUpperCase(), hx - 390 * K, hy - 72 * K); }
  if (e.title) { c.font = F(900, 32); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(e.title.toUpperCase(), x, 80 * K); } c.restore(); };
// meters: two level meters side by side ("volume contest"); bars:[{label, level 0-1, note}]
O.meters = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const bars = e.bars || [], [x, y] = PX(e), bw = 90 * K, bh = 420 * K, gap = 260 * K, x0 = x - (bars.length - 1) * gap / 2; c.save(); c.globalAlpha = a;
  if (e.title) { c.font = F(900, 34); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText(e.title.toUpperCase(), x, y - bh / 2 - 70 * K); }
  bars.forEach((b, i) => { const bx = x0 + i * gap - bw / 2, by = y - bh / 2, lv = (b.level ?? .5) * eio(seg(t, b.at ?? (.3 + i * .8), (b.at ?? (.3 + i * .8)) + .7)); c.fillStyle = 'rgba(255,255,255,.08)'; c.fillRect(bx, by, bw, bh);
    const segs = 16; for (let s = 0; s < segs; s++) { if (s / segs >= lv) break; const sy = by + bh - (s + 1) * bh / segs; c.fillStyle = s > segs * .8 ? T.r : s > segs * .6 ? T.y : T.green; c.fillRect(bx + 6 * K, sy + 3 * K, bw - 12 * K, bh / segs - 6 * K); }
    c.font = F(900, 20); c.fillStyle = T.ink; c.textAlign = 'center'; c.fillText((b.label || '').toUpperCase(), bx + bw / 2, by + bh + 40 * K); if (b.note && lv > .05) { c.font = F(700, 18); c.fillStyle = T.sub; c.fillText(b.note, bx + bw / 2 + 110 * K, by + bh * (1 - lv)); } });
  c.restore(); };
// orbitmap: a solar-system diagram (sun + orbit rings), highlighting one planet; the space version of a map inset
O.orbitmap = (e, t) => { const a = fadeIO(e, t); if (a <= 0) return; const [x, y] = PX(e), ring = (e.ring || 70) * K, n = e.n || 4, hl = e.highlight ?? 1; c.save(); c.globalAlpha = a;
  const g = c.createRadialGradient(x, y, 0, x, y, ring * .6); g.addColorStop(0, '#fff2c4'); g.addColorStop(1, 'rgba(255,190,80,0)'); c.fillStyle = g; c.beginPath(); c.arc(x, y, ring * .6, 0, TAU); c.fill();
  for (let i = 0; i < n; i++) { const r = ring * (i + 1) * .9 + ring * .4; c.strokeStyle = i === hl ? rgba(T.y, .7) : 'rgba(255,255,255,.18)'; c.lineWidth = (i === hl ? 3 : 1.5) * K; c.beginPath(); c.arc(x, y, r, 0, TAU); c.stroke();
    const an = (e.angles || [])[i] ?? (i * 1.7 + t * .2 / (i + 1)), px = x + Math.cos(an) * r, py = y + Math.sin(an) * r; c.fillStyle = i === hl ? T.y : '#8e97b0'; c.beginPath(); c.arc(px, py, (i === hl ? 12 : 7) * K, 0, TAU); c.fill();
    if (i === hl && e.label) { c.font = F(900, 22); c.fillStyle = T.y; c.textAlign = 'left'; c.fillText(e.label.toUpperCase(), px + 22 * K, py + 6 * K); } }
  c.restore(); };
// endcard: thanks + a comment bubble + a "watch next" box
O.endcard = (e, t) => { const a = fadeIO(e, t, .4); if (a <= 0) return; c.save(); c.globalAlpha = a; c.font = F(900, 46); c.fillStyle = T.ink; c.textAlign = 'left'; c.textBaseline = 'middle'; c.fillText((e.text || 'THANKS FOR WATCHING').toUpperCase(), 130 * K, 330 * K);
  if (t > .6) { c.font = F(700, 24); const q = e.ask || 'Which planet should we survive next?', qw = c.measureText(q).width; panel(130 * K, 390 * K, qw + 50 * K, 70 * K); c.beginPath(); c.moveTo(170 * K, 460 * K); c.lineTo(190 * K, 490 * K); c.lineTo(205 * K, 460 * K); c.fillStyle = T.panel; c.fill(); c.fillStyle = T.ink; c.fillText(q, 155 * K, 426 * K); }
  if (t > 1.0) { c.setLineDash([10 * K, 8 * K]); c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 2 * K; c.strokeRect(1120 * K, 250 * K, 660 * K, 372 * K); c.setLineDash([]); c.font = F(900, 26); c.fillStyle = T.r; c.textAlign = 'center'; c.fillText('WATCH NEXT', 1450 * K, 670 * K); }
  c.restore(); };
// clip: a short real video (converted to WebM by render.mjs), framed like evidence
O.clip = (e, t) => { const d = e.dur ?? 99, p = eo(seg(t, 0, .3)) * (1 - seg(t, d - .25, d)); if (p <= 0) return; const v = VID[e.src]; c.save(); c.globalAlpha = p;
  const full = e.full, w = full ? W : (e.w || 1000) * K, h = full ? H : (e.h || 562) * K, x = full ? W / 2 : (e.x ?? .5) * W, y = full ? H / 2 : (e.y ?? .47) * H; c.translate(x, y); if (!full) { c.rotate(e.rot ?? -.012); c.shadowColor = 'rgba(0,0,0,.6)'; c.shadowBlur = 40 * K; c.fillStyle = '#f4f2ec'; c.fillRect(-w / 2 - 12 * K, -h / 2 - 12 * K, w + 24 * K, h + 24 * K); c.shadowBlur = 0; }
  c.beginPath(); c.rect(-w / 2, -h / 2, w, h); c.clip(); c.fillStyle = '#000'; c.fillRect(-w / 2, -h / 2, w, h);
  if (v && v.videoWidth) { const sc = Math.max(w / v.videoWidth, h / v.videoHeight) * (1 + (e.zoom ?? .05) * seg(t, 0, Math.min(d, 8))); c.drawImage(v, -v.videoWidth * sc / 2, -v.videoHeight * sc / 2, v.videoWidth * sc, v.videoHeight * sc); }
  c.restore(); c.save(); c.globalAlpha = p; c.translate(x, y); if (!full) { c.font = F(900, 22); const tg = e.tag || 'REAL FOOTAGE', tw = c.measureText(tg).width + 36 * K; c.fillStyle = T.r; c.fillRect(-w / 2 - 12 * K, -h / 2 - 58 * K, tw, 40 * K); c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.fillText(tg, -w / 2 + 6 * K, -h / 2 - 37 * K); }
  c.font = F(700, 18); c.fillStyle = 'rgba(255,255,255,.8)'; c.textBaseline = 'middle'; c.fillText(e.credit || '', -w / 2 + (full ? 30 * K : 0), h / 2 + (full ? -30 : 34) * K); c.restore(); };
// scanline: the "you're being scanned" effect — a green sweep and tint over the world
O.scan = (e, t) => { const a = fadeIO(e, t, .2); if (a <= 0) return; c.save(); c.globalAlpha = a * .35; c.fillStyle = '#0f3a1e'; c.globalCompositeOperation = 'color'; c.fillRect(0, 0, W, H); c.globalCompositeOperation = 'source-over'; c.globalAlpha = a;
  const sy = ((t * .6) % 1) * H; const g = c.createLinearGradient(0, sy - 80 * K, 0, sy + 10 * K); g.addColorStop(0, 'rgba(76,255,138,0)'); g.addColorStop(1, 'rgba(76,255,138,.6)'); c.fillStyle = g; c.fillRect(0, sy - 80 * K, W, 90 * K);
  if (e.text) { c.font = F(900, 40); c.fillStyle = T.r; c.textAlign = 'center'; c.fillText(e.text.toUpperCase(), W / 2, H * .86); } c.restore(); };

// ───────── shots ─────────
const WORLD = new Set(['planet', 'sun', 'blackhole', 'astronaut', 'descent', 'surface', 'probe', 'rocket', 'airship']);
function camera(sh, tl) { const d = sh.end - sh.start, u = eio(tl / d), cm = sh.cam || {}, z = lerp(cm.zoomFrom ?? 1, cm.zoomTo ?? 1.08, u);
  const shake = cm.shake ? cm.shake * (Math.sin(tl * 37) * Math.sin(tl * 23)) * K : 0;
  return { z, px: lerp(cm.panFrom ?? 0, cm.panTo ?? 0, u) * K + shake, py: lerp(cm.panYFrom ?? 0, cm.panYTo ?? 0, u) * K + shake * .6, fx: (cm.fx ?? .5) * W, fy: (cm.fy ?? .5) * H }; }
function drawShot(sh, t) {
  const tl = t - sh.start, cam = camera(sh, tl);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  if (!sh.els.some(e => e.type === 'descent' || e.type === 'surface')) space(t, cam, sh.bg || {});
  c.translate(cam.fx, cam.fy); c.scale(cam.z, cam.z); c.translate(-cam.fx - cam.px, -cam.fy - cam.py);
  for (const e of sh.els) if (WORLD.has(e.type) && tl >= (e.t0 || 0) && (e.dur == null || tl - (e.t0 || 0) <= e.dur)) { const lt = tl - (e.t0 || 0), mv = e.type !== 'astronaut' && e.type !== 'rocket', dy = e.drop ? -(1 - eo(seg(lt, 0, e.drop))) * 800 : 0;
      E[e.type]({ ...e, x: ((e.x ?? 960) + (mv ? (e.vx || 0) * lt : 0)) * K, y: ((e.y ?? 540) + (mv ? (e.vy || 0) * lt : 0) + dy) * K, r: (e.r ?? 100) * K }, lt); }
  c.restore();
  vignette(sh.vig ?? .55);
  for (const e of sh.els) if (!WORLD.has(e.type)) { const lt = tl - (e.t0 || 0); if (lt >= 0) { if (!O[e.type]) throw new Error('unknown element ' + e.type); O[e.type](e, lt); } }
}
window.DUR = S.shots[S.shots.length - 1].end;
const prevBuf = mk(W, H), pc = prevBuf.getContext('2d');
async function seekClips(t) {   // move every visible clip to its frame before drawing
  const jobs = [];
  for (const sh of S.shots) { if (t < sh.start - .1 || t > sh.end + .1) continue;
    for (const e of sh.els) if (e.type === 'clip' && VID[e.src]) { const lt = t - sh.start - (e.t0 || 0), v = VID[e.src]; if (lt < 0 || lt > (e.dur ?? 99)) continue;
      const want = Math.min((v.duration || 1) - .05, (e.from || 0) + lt * (e.rate || 1)); if (Math.abs(v.currentTime - want) < .004) continue;
      jobs.push(new Promise(r => { v.onseeked = () => r(); v.currentTime = want; setTimeout(r, 3000); })); } }
  await Promise.all(jobs);
}
window.render = async t => { await seekClips(t); draw(t); };
function draw(t) {
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
  let i = S.shots.findIndex(s => t >= s.start && t < s.end); if (i < 0) i = S.shots.length - 1; const sh = S.shots[i], prev = S.shots[i - 1], tl = t - sh.start;
  const tr = sh.trans || 'whip';
  if (prev && tr === 'fade' && tl < .5) { drawShot(prev, t); pc.clearRect(0, 0, W, H); pc.drawImage(cv, 0, 0); drawShot(sh, t); c.globalAlpha = 1 - tl / .5; c.drawImage(prevBuf, 0, 0); c.globalAlpha = 1; }
  else drawShot(sh, t);
  if (prev && tr === 'whip' && tl < .18) { const k = 1 - tl / .18; pc.clearRect(0, 0, W, H); pc.drawImage(cv, 0, 0); c.globalAlpha = .4 * k; for (const dx of [-60, -30, 30, 60]) c.drawImage(prevBuf, dx * K * k, 0); c.globalAlpha = 1; }
  grain(t);
  const fade = Math.min(seg(t, 0, .35), 1 - seg(t, window.DUR - .6, window.DUR)); if (fade < 1) { c.fillStyle = `rgba(0,0,0,${1 - fade})`; c.fillRect(0, 0, W, H); }
};
window.READY = Promise.all([document.fonts.ready, ...['40px Anton', '900 10px InterE', '800 10px InterE', '700 10px InterE', '500 10px InterE'].map(f => document.fonts.load(f)),
  ...Object.values(IMG).map(im => im.complete ? 0 : new Promise(r => { im.onload = im.onerror = r; })),
  ...Object.values(VID).map(v => v.readyState >= 2 ? 0 : new Promise(r => { v.onloadeddata = v.onerror = r; setTimeout(r, 8000); }))]);
})();
