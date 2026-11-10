// node render.mjs <outdir> "0-100" | "5,40,90"   (RESUME=1 skips existing)
import { chromium } from 'playwright';
import http from 'http'; import fs from 'fs'; import path from 'path';
const root = path.resolve('web'), out = process.argv[2], spec = process.argv[3];
fs.mkdirSync(out, { recursive: true });
const frames = spec.includes('-') && !spec.includes(',') ? (() => { const [a, b] = spec.split('-').map(Number); return Array.from({ length: b - a + 1 }, (_, i) => a + i); })() : spec.split(',').map(Number);
const types = { '.js': 'text/javascript', '.html': 'text/html' };
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(0);
// GPU by default; set SWIFTSHADER=1 to force the slow CPU renderer (what the cloud machine used)
const args = process.env.SWIFTSHADER ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--ignore-gpu-blocklist', '--enable-gpu'];
const b = await chromium.launch({ args });
const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('console:', m.text().slice(0, 300)); });
pg.on('pageerror', e => { console.log('PAGEERR', e.message); process.exit(2); });
await pg.goto(`http://localhost:${srv.address().port}/index.html`);
await pg.waitForFunction('window.ready', null, { timeout: 120000 });
console.log('WebGL renderer:', await pg.evaluate(() => { const g = document.createElement('canvas').getContext('webgl2'); const e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER); }));
let n = 0; const t0 = Date.now();
for (const f of frames) {
  const file = path.join(out, `f${String(f).padStart(4, '0')}.jpg`);
  if (process.env.RESUME && fs.existsSync(file)) continue;
  const data = await pg.evaluate((f) => { window.renderFrame(f); return document.querySelector('canvas').toDataURL('image/jpeg', 0.95); }, f);
  fs.writeFileSync(file, Buffer.from(data.split(',')[1], 'base64'));
  n++;
  if (n % 10 === 0 || frames.length < 40) console.log(`frame ${f} done (${n}/${frames.length}) avg ${((Date.now() - t0) / n / 1000).toFixed(2)}s`);
}
console.log('DONE', n);
await b.close(); srv.close();
