// node render.js            -> test.mp4 (8 s, 1080x1920, 30 fps)
// node render.js 0,100,200  -> only those frames as PNGs in frames/
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const FPS = 30, DUR = 8, W = 1080, H = 1920;
(async () => {
  const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.error('page error:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto('http://127.0.0.1:8765/scene.html');
  await page.waitForFunction('window.ready === true');
  const grab = async i => {
    const url = await page.evaluate(t => { window.renderAt(t); return document.querySelector('canvas').toDataURL('image/png'); }, i / FPS);
    return Buffer.from(url.split(',')[1], 'base64');
  };
  if (only) {
    fs.mkdirSync(path.join(__dirname, 'frames'), { recursive: true });
    for (const i of only) fs.writeFileSync(path.join(__dirname, 'frames', `f${String(i).padStart(4, '0')}.png`), await grab(i));
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', path.join(__dirname, 'test.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < FPS * DUR; i++) {
      const buf = await grab(i);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 30 === 0) console.log('frame', i, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
