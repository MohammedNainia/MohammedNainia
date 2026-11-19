// node shot.js scene t1,t2 out.png [scale]   (EX=1 adds &ex=1 to the url)
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = process.env.THREE_ROOT || process.cwd();   // the folder holding scenes/ and node_modules/
const {chromium} = require(ROOT + '/node_modules/playwright');
const [, , scn, t, out, sc = '.5'] = process.argv;
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.statusCode = 404; return r.end(); } r.setHeader('Content-Type', f.endsWith('.js') ? 'text/javascript' : 'text/html'); r.end(d); }); });
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage(); p.setDefaultTimeout(900000);
  p.on('pageerror', e => console.log('ERR', e.message));
  const url = 'http://127.0.0.1:' + srv.address().port + '/scenes/' + scn + '.html?s=' + sc + (process.env.EX ? '&ex=1' : '') + (process.env.IDM ? '&id=1' : '');
  await p.goto(url, {timeout: 900000, waitUntil: 'commit'});
  await p.waitForFunction('window.ready===true', null, {timeout: 900000, polling: 2000});
  for (const tt of t.split(',')) {
    const u = await p.evaluate(t => { window.renderAt(+t); return document.querySelector('canvas').toDataURL('image/png'); }, tt);
    fs.writeFileSync(out.replace('.png', '_' + tt + '.png'), Buffer.from(u.split(',')[1], 'base64'));
  }
  await b.close(); srv.close();
})();
