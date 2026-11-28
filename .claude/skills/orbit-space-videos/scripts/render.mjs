// node scripts/render.mjs scene.json out.mp4 [--audio vo.wav] [--music bed.mp3] [--stills 1,2.5,7 --dir stills/]
import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process'; import { fileURLToPath } from 'url';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url)), ROOT = path.resolve(HERE, '..');
process.env.PATH = path.join(ROOT, 'bin') + path.delimiter + process.env.PATH;   // ffmpeg installed by setup lives here
let pw; try { pw = require(require.resolve('playwright', { paths: [ROOT] })); } catch { pw = require('playwright'); }
const a = process.argv.slice(2), opt = k => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : null; };
const scenePath = a[0], out = a[1], scene = JSON.parse(fs.readFileSync(scenePath, 'utf8'));
for (const sh of scene.shots) for (const e of sh.els) if (e.src && !/^(file|https?):/.test(e.src)) e.src = 'file://' + path.resolve(path.dirname(scenePath), e.src);
// real video clips: Chromium can't decode H.264, so convert each one to WebM once (cached next to the scene)
import { execFileSync } from 'child_process';
for (const sh of scene.shots) for (const e of sh.els) if (e.type === 'clip' && /\.(mp4|mov|m4v)$/i.test(e.src)) {
  const src = e.src.replace(/^file:\/\//, ''), cache = path.join(path.dirname(src), '.orbit-cache'); fs.mkdirSync(cache, { recursive: true });
  const dst = path.join(cache, path.basename(src).replace(/\.\w+$/, '.webm'));
  if (!fs.existsSync(dst)) { console.log('converting clip', path.basename(src)); execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', src, '-an', '-vf', 'scale=1280:-2', '-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8', '-crf', '32', '-b:v', '0', '-g', '15', dst]); }
  e.src = 'file://' + dst;
}
const W = scene.width || 1920, H = scene.height || 1080, FPS = scene.fps || 30;
const exe = process.env.CHROME_PATH || undefined;
let browser;   // Playwright's own Chromium first; if it isn't installed, fall back to the Chrome or Edge already on the computer
for (const o of [{ executablePath: exe }, { channel: 'chrome' }, { channel: 'msedge' }]) { try { browser = await pw.chromium.launch(o); break; } catch (e) { if (o.channel === 'msedge') { console.error('No browser found. Run setup again, or install Google Chrome.\n' + e.message); process.exit(1); } } }
const page = await browser.newPage({ viewport: { width: W, height: H } });
await page.addInitScript(s => { window.SCENE = s; }, scene);
page.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
await page.goto('file://' + path.join(ROOT, 'engine/index.html'));
await page.evaluate(() => window.READY);
const DUR = await page.evaluate(() => window.DUR);
const shot = async t => { await page.evaluate(t => window.render(t), t); return page.screenshot({ type: 'jpeg', quality: 92, clip: { x: 0, y: 0, width: W, height: H } }); };
if (opt('--stills')) {
  const dir = opt('--dir') || 'stills'; fs.mkdirSync(dir, { recursive: true });
  for (const t of opt('--stills').split(',').map(Number)) { fs.writeFileSync(path.join(dir, `t_${t}.jpg`), await shot(t)); }
  await browser.close(); console.log('stills ->', dir); process.exit(0);
}
const silent = out.replace(/\.mp4$/, '') + '_silent.mp4';
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
const N = Math.round(DUR * FPS), t0 = Date.now();
for (let f = 0; f < N; f++) {
  const buf = await shot(f / FPS);
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % 60 === 0) process.stdout.write(`\r${f}/${N} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
const audio = opt('--audio'), music = opt('--music');
if (!audio && !music) { fs.renameSync(silent, out); console.log('\ndone', out); process.exit(0); }
const args = ['-y', '-loglevel', 'error', '-i', silent];
if (audio) args.push('-i', audio); if (music) args.push('-stream_loop', '-1', '-i', music);
const fc = audio && music ? '[2:a]volume=0.16[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]' : '[1:a]anull[a]';
args.push('-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out);
await new Promise(r => spawn('ffmpeg', args, { stdio: 'inherit' }).on('close', r)); fs.unlinkSync(silent); console.log('\ndone', out);
