const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('C:/Users/armin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../media'),out=path.resolve(__dirname,'evidence/filename-ui');
fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const file=path.join(root,new URL(req.url,'http://localhost').pathname);
 if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
 if(req.url==='/neutral.m3u8'){res.setHeader('Content-Type','application/vnd.apple.mpegurl');return res.end('#EXTM3U\n#EXTINF:1,\n/neutral.ts\n#EXT-X-ENDLIST');}
 if(req.url==='/neutral.ts')return res.end(fs.readFileSync(path.join(__dirname,'fixtures/video-finder/video.ts')));
 if(!fs.existsSync(file)){res.writeHead(404);return res.end();}
 res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css': 'application/javascript');res.end(fs.readFileSync(file));
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;const report=[];
 try{
 browser=await chromium.launch({headless:true,channel:'msedge'});
 for(const locale of require('../scripts/requested-languages.json').locales){
  const messages=JSON.parse(fs.readFileSync(path.join(root,'_locales',locale.replaceAll('-','_'),'messages.json')));
  const context=await browser.newContext({viewport:{width:320,height:900}});
  const errors=[];const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await context.addInitScript(({locale,messages,source})=>{
   const ev=()=>({addListener(){},removeListener(){}});
   window.sent=[];window.saved=[];
   window.browser={i18n:{getUILanguage:()=>locale,getMessage:k=>messages[k]?.message||''},
    windows:{getCurrent:async()=>({id:1}),onRemoved:ev()},browserAction:{onClicked:ev()},
    tabs:{query:async()=>[{id:1,url:'https://youtu.be/aqz-KE-bpKQ'}],onActivated:ev(),onUpdated:ev()},
    scripting:{executeScript:async()=>[]},permissions:{request:async()=>true,contains:async()=>true},
    downloads:{download:async v=>{window.saved.push(v);return window.saved.length;},search:async()=>[{state:'complete'}],onChanged:ev(),showDefaultFolder(){}},
    runtime:{getBackgroundPage:async()=>window,connectNative:()=>({onMessage:{addListener:f=>window.receive=f},onDisconnect:ev(),postMessage:m=>window.sent.push(m)})}};
   (0,eval)(source);
   let queued;
   window.getQueue=()=>queued ||= new Promise(resolve=>{
    const frame=document.createElement('iframe');frame.hidden=true;frame.src='queue.html';frame.onload=()=>resolve(frame.contentWindow);document.body.append(frame);
   });
  },{locale,messages,source:fs.readFileSync(path.join(root,'youtube-background.js'),'utf8')});
  await page.goto(`http://127.0.0.1:${server.address().port}/sidebar.html`);
  await page.locator('#youtube-detect').click();
  await page.evaluate(()=>{receive({type:'info',title:'Neutraler Film 🌹',choices:[{selector:'18',height:360,merged:false}]});receive({type:'idle'});});
  assert.equal(await page.locator('#youtube-filename').inputValue(),'Neutraler Film 🌹');
  assert.equal(await page.locator('label[for=youtube-filename]').textContent(),messages.filenameTitle.message);
  await page.locator('#youtube-filename').fill('Mein eigener Film');await page.locator('#youtube-save').click();
  assert.equal(await page.evaluate(()=>sent.at(-1).filenameTitle),'Mein eigener Film');
  assert.ok(await page.locator('#youtube-filename').isDisabled());
  await page.evaluate(()=>{receive({type:'saved',path:'test.mp4'});receive({type:'idle'});renderRow({url:'https://example.org/abc.mp4',name:'abc.mp4',title:'Neutraler Film',height:720},document.querySelector('#list'));});
  await page.locator('#list input').fill('Direkter Film');await page.locator('#list button').click();
  assert.equal(await page.evaluate(()=>saved.at(-1).filename),'Direkter Film – 720p.mp4');
  assert.equal(await page.evaluate(()=>saved.at(-1).conflictAction),'uniquify');
  await page.evaluate(async()=>{const q=await getQueue();q.addDownload(location.origin+'/neutral.m3u8','Neutraler Stream');});
  await page.locator('main .save').waitFor({state:'visible'});
  assert.equal(await page.locator('main .filename-title').inputValue(),'Neutraler Stream');
  await page.locator('main .filename-title').fill('Geänderter Stream');
  // Force a queue re-render; the copied input must retain its edited value.
  await page.evaluate(async()=>{const q=await getQueue();q.document.querySelector('.status').textContent+=' ';});
  assert.equal(await page.locator('main .filename-title').inputValue(),'Geänderter Stream');
  await page.locator('main .save').click();
  await page.waitForFunction(async()=>{const q=await getQueue();return q.saved.length>0;});
  assert.equal(await page.evaluate(async()=>(await getQueue()).saved[0].filename),'Geänderter Stream.ts');
  assert.equal(await page.evaluate(()=>document.documentElement.dir),['ar','he'].includes(locale)?'rtl':'ltr');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.deepEqual(errors,[]);
  if(['de','ar','ja'].includes(locale))await page.screenshot({path:path.join(out,locale+'.png'),fullPage:true});
  report.push({locale,passed:true,youtube:true,direct:true,hls:true,narrowLayout:true});await context.close();
 }
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:true,browser:'Chromium local UI fixture; browser APIs simulated',personalProfileUsed:false,tests:report},null,2));console.log(JSON.stringify(report));
 }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
