// node work/probe.mjs "<js expression run after window.ready>"  -> prints the result (debug helper)
import { chromium } from 'playwright';
import http from 'http'; import fs from 'fs'; import path from 'path';
const root = path.resolve('web');
const types = { '.js': 'text/javascript', '.html': 'text/html' };
const srv = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); }).listen(0);
const b = await chromium.launch({ args: ['--ignore-gpu-blocklist', '--enable-gpu'] });
const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
pg.on('pageerror', (e) => console.log('PAGEERR', e.message));
await pg.goto(`http://localhost:${srv.address().port}/index.html`);
await pg.waitForFunction('window.ready', null, { timeout: 120000 });
console.log(JSON.stringify(await pg.evaluate(process.argv[2])));
await b.close(); srv.close();
