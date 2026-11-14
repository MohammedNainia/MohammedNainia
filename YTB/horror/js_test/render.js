// Render scene.html to video, frame by frame, with headless Chromium.
//   node render.js                         full video -> test.mp4 (auto: GPU on Windows/Mac, CPU here)
//   node render.js --gpu                   force the graphics card (opens a Chromium window while it renders)
//   node render.js --cpu --workers 4       software rendering, 4 parallel browsers (cloud)
//   node render.js --frames 0,60,130       only those frames, as PNGs in frames/
//   node render.js --dur 8 --fps 30 --out test.mp4
// Needs: npm install (three + playwright), npx playwright install chromium, and ffmpeg on PATH (or set FFMPEG=C:\path\ffmpeg.exe).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http'), os = require('os'), { spawn } = require('child_process');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i < 0 ? d : argv[i + 1]; };
const flag = k => argv.includes('--' + k);
const FPS = +opt('fps', 30), DUR = +opt('dur', 8), W = 1080, H = 1920;
const OUT = path.resolve(__dirname, opt('out', 'test.mp4'));
const ONLY = opt('frames', null) ? opt('frames').split(',').map(Number) : null;
const GPU = flag('gpu') || (!flag('cpu') && process.platform !== 'linux');
const WORKERS = +opt('workers', GPU ? 2 : Math.max(1, os.cpus().length));
const FFMPEG = process.env.FFMPEG || 'ffmpeg';

// tiny static server for this folder (ES modules need http://, not file://)
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const p = path.join(__dirname, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(__dirname) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`http://127.0.0.1:${port}/scene.html`);
  await page.waitForFunction('window.ready === true', null, { timeout: 120000 });
  return page;
}
const grab = (page, t, type) => page.evaluate(([t, type]) => {
  window.renderAt(t); return document.querySelector('canvas').toDataURL(type, .95);
}, [t, type]).then(u => Buffer.from(u.split(',')[1], 'base64'));

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r)); const port = server.address().port;
  const args = GPU ? ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-zero-copy']
                   : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'];
  const browser = await chromium.launch({ headless: !GPU, args });   // a visible window is the reliable way to get the GPU
  const probe = await openPage(browser, port);
  const gpuName = await probe.evaluate(() => {
    const gl = document.createElement('canvas').getContext('webgl2'); const e = gl && gl.getExtension('WEBGL_debug_renderer_info');
    return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'unknown';
  });
  console.log(`renderer: ${gpuName}  |  mode: ${GPU ? 'GPU' : 'CPU'}  |  workers: ${WORKERS}`);

  if (ONLY) {
    fs.mkdirSync(path.join(__dirname, 'frames'), { recursive: true });
    for (const i of ONLY) fs.writeFileSync(path.join(__dirname, 'frames', `f${String(i).padStart(4, '0')}.png`), await grab(probe, i / FPS, 'image/png'));
    await browser.close(); server.close(); return;
  }

  const N = Math.round(FPS * DUR), tmp = path.join(__dirname, 'frames_tmp');
  fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp);
  const t0 = Date.now(); let done = 0;
  const pages = [probe]; for (let k = 1; k < WORKERS; k++) pages.push(await openPage(browser, port));
  await Promise.all(pages.map(async (page, k) => {              // each browser renders every WORKERS-th frame
    for (let i = k; i < N; i += WORKERS) {
      fs.writeFileSync(path.join(tmp, `${String(i).padStart(5, '0')}.jpg`), await grab(page, i / FPS, 'image/jpeg'));
      if (++done % 60 === 0) console.log(`  ${done}/${N} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
  }));
  await browser.close(); server.close();
  console.log(`rendered ${N} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s (${((Date.now() - t0) / N).toFixed(0)} ms/frame)`);
  await new Promise((res, rej) => spawn(FFMPEG, ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, '%05d.jpg'),
    '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: 'inherit' })
    .on('close', c => c ? rej(new Error('ffmpeg failed')) : res()));
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('saved', OUT);
})().catch(e => { console.error(e); process.exit(1); });
