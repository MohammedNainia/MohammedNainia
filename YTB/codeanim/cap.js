// node cap.js <scene.html relative to three/> <frames> <outdir>   -> outdir/f000.png ...  (calls window.renderAt(i/frames))
const fs=require('fs'),path=require('path'),http=require('http');
const ROOT=path.join(__dirname,'..','horror','three');
const {chromium}=require(path.join(ROOT,'node_modules','playwright'));
const [,,scn,N,out]=process.argv; fs.mkdirSync(out,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.png':'image/png'};
const srv=http.createServer((q,r)=>{const f=path.join(ROOT,decodeURIComponent(q.url.split('?')[0]));
 fs.readFile(f,(e,d)=>{if(e){r.statusCode=404;return r.end();}r.setHeader('Content-Type',types[path.extname(f)]||'application/octet-stream');r.end(d);});});
(async()=>{await new Promise(r=>srv.listen(0,'127.0.0.1',r));
 const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage();
 p.on('console',m=>console.log('page:',m.text()));p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto(`http://127.0.0.1:${srv.address().port}/${scn}`);await p.waitForFunction(()=>window.renderAt);
 for(let i=0;i<+N;i++){const d=await p.evaluate(t=>{window.renderAt(t);return document.querySelector('canvas').toDataURL('image/png');},i/+N);
  fs.writeFileSync(path.join(out,'f'+String(i).padStart(3,'0')+'.png'),Buffer.from(d.split(',')[1],'base64'));}
 await b.close();srv.close();})();
