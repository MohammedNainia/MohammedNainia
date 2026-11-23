// Contact check: before a render, sweep a scene and report every moment a character is inside the furniture
// (sunk into a bed or a chair, through a backrest or a rail). The scene must expose window.contactAt(t) (see night_count.html).
//   node check_contact.js --scene night_count [--step .5] [--depth .04]
// Exit code 1 when any person is deeper than --depth (metres) inside a prop: fix it before rendering.
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const argv = process.argv.slice(2), opt = (k, d) => { const i = argv.indexOf('--' + k); return i < 0 ? d : argv[i + 1]; };
const SCENE = opt('scene', 'night_count'), STEP = +opt('step', .5), MAXD = +opt('depth', .04);
const TYPES = {'.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg'};
const server = http.createServer((req, res) => { const p = path.join(__dirname, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(__dirname) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, {'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream'}); fs.createReadStream(p).pipe(res); });
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const b = await chromium.launch({args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage(); p.setDefaultTimeout(900000); p.on('pageerror', e => { console.log('ERROR', e.message); process.exit(3); });
  p.on('console', m => { if (/MASK|warn/i.test(m.text())) console.log(m.text()); });
  await p.goto(`http://127.0.0.1:${server.address().port}/scenes/${SCENE}.html?s=.25`, {waitUntil: 'commit'});
  await p.waitForFunction('window.ready===true', null, {timeout: 900000, polling: 1000});
  if (!(await p.evaluate(() => !!window.contactAt))) { console.log(SCENE + ' has no window.contactAt'); process.exit(2); }
  const DUR = await p.evaluate(() => window.DUR); let bad = 0;
  for (let t = 0; t < DUR; t += STEP) {
    const r = await p.evaluate(t => window.contactAt(t), t);
    for (const x of r) if (x.depth > MAXD) { bad++; console.log(`t ${t.toFixed(1)}  ${x.who}: ${x.n} points inside, ${(x.depth * 100).toFixed(1)} cm deep`); }
  }
  console.log(bad ? `${bad} problem moments (deeper than ${MAXD * 100} cm)` : 'clean: nobody inside the furniture');
  await b.close(); server.close(); process.exit(bad ? 1 : 0);
})();
