const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const select=require('./select-test-content.cjs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function checkWorkspace(s,root,options={}){
 fs.mkdirSync(root,{recursive:true});
 async function wait(script){let r;for(let i=0;i<50;i++){r=await s.script(script);if(r===true)return;await pause(100);}throw Error(JSON.stringify(r));}
 await select(s);await s.command('WebDriver:Navigate',{url:'about:rosavio-notes'});
 await wait("return document.getElementById('notes')?.disabled===false;");
 assert.equal(await s.script("return document.querySelector('.project-tile').getClientRects().length;"),0);
 await s.script(`document.getElementById('notes').value='Rosavio test 🌹 <script>not executable</script>';document.getElementById('notes').dispatchEvent(new Event('input'));document.getElementById('save').click();return true;`);
 await wait("return document.getElementById('save').disabled===false && document.getElementById('status').textContent==='Gespeicherter Stand geladen';");
 await s.command('WebDriver:Refresh');await wait("return document.getElementById('notes')?.disabled===false;");
 assert.equal(await s.script("return document.getElementById('notes').value;"),'Rosavio test 🌹 <script>not executable</script>');
 await s.command('Marionette:SetContext',{value:'chrome'});
 assert.equal(await s.script('return gBrowser.selectedBrowser.contentPrincipal.isSystemPrincipal;'),false);
 await select(s);await s.command('WebDriver:Navigate',{url:'about:rosavio-home'});
 await wait("return document.getElementById('add')?.disabled===false;");
 const pdfTile=await s.script("const a=document.querySelector('.project-tile');return {url:a?.href,visible:!!a?.getClientRects().length};");
 assert.deepEqual(pdfTile,{url:'https://github.com/aheinen1971-cmd/pdf-digital/releases/latest',visible:true});
 const tile=await s.command('WebDriver:FindElement',{using:'css selector',value:'.project-tile'});
 const tileElement=(tile.value||tile)['element-6066-11e4-a52e-4f735466cecf'];
 await s.command('WebDriver:ElementClick',{id:tileElement});
 await s.command('Marionette:SetContext',{value:'chrome'});
 const pdfDigitalRelease=await s.script(`
  const startPage=gBrowser.tabs.find(tab=>tab.linkedBrowser.currentURI.spec==='about:rosavio-home');
  if(!startPage)throw Error('Rosavio home tab was not preserved');
  const deadline=Date.now()+20000;
  while(Date.now()<deadline){
   const downloadTab=gBrowser.tabs.find(tab=>/^https:\\/\\/github\\.com\\/aheinen1971-cmd\\/pdf-digital\\/releases\\/tag\\/v[0-9.]+$/.test(tab.linkedBrowser.currentURI.spec));
   if(downloadTab){
    const url=downloadTab.linkedBrowser.currentURI.spec;
    gBrowser.removeTab(downloadTab);
    gBrowser.selectedTab=startPage;
    return url;
   }
   await new Promise(resolve=>setTimeout(resolve,250));
  }
  throw Error('PDF Digital release did not open: '+gBrowser.tabs.map(tab=>tab.linkedBrowser.currentURI.spec).join(', '));
 `);
 assert.match(pdfDigitalRelease,/^https:\/\/github\.com\/aheinen1971-cmd\/pdf-digital\/releases\/tag\/v[0-9.]+$/);
 await select(s);
 await s.script(`document.getElementById('link-title').value='Example';document.getElementById('link-url').value='https://example.com/';document.getElementById('add').click();document.getElementById('save').click();return true;`);
 await wait("return document.getElementById('save').disabled===false && Array.from(document.querySelectorAll('#links a')).some(a=>a.href==='https://example.com/');");
 const shot=(await s.command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:true})).value;
 fs.writeFileSync(path.join(root,'workspace-home.png'),Buffer.from(shot,'base64'));
 await s.command('Marionette:SetContext',{value:'chrome'});
 const actor=await s.script(`const a=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');return typeof a.receiveMessage;`);assert.equal(actor,'function');
 const guards=await s.script(`const a=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');const current=await a.receiveMessage({name:'RosavioWorkspace:Read'});let badURL=false,conflict=false,unknown=false;
 try{await a.receiveMessage({name:'RosavioWorkspace:Save',data:{...current,links:[{title:'bad',url:'javascript:alert(1)'}]}})}catch{badURL=true}
 try{await a.receiveMessage({name:'RosavioWorkspace:Save',data:{...current,revision:0}})}catch{conflict=true}
 try{await a.receiveMessage({name:'DeleteAnything'})}catch{unknown=true}
 return {badURL,conflict,unknown,notes:current.notes,links:current.links};`);
 assert.equal(guards.badURL,true);assert.equal(guards.conflict,true);assert.equal(guards.unknown,true);
 if(options.runtimeOverlay)await options.runtimeOverlay(s);
 await s.script(`await PanelUI.ensureReady();RosavioTools.refresh();return true;`);
 async function clickTool(id){
  await s.command('Marionette:SetContext',{value:'chrome'});
  await s.script(`RosavioTools.refresh();await PanelUI.show();return true;`);
  await s.command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:false});
  const found=await s.command('WebDriver:FindElement',{using:'css selector',value:'#appMenu-rosavio-'+id});
  const value=found.value||found;await s.command('WebDriver:ElementClick',{id:value['element-6066-11e4-a52e-4f735466cecf']});
 }
 await clickTool('notes');await wait("return gBrowser.selectedBrowser.currentURI.spec==='about:rosavio-notes';");
 await clickTool('home');await wait("return gBrowser.selectedBrowser.currentURI.spec==='about:rosavio-home';");
 const disabled=await s.script(`RosavioTools.refresh();return {qr:PanelUI.mainView.querySelector('#appMenu-rosavio-qr').disabled,reader:PanelUI.mainView.querySelector('#appMenu-rosavio-reader').disabled};`);assert.equal(disabled.qr,true);assert.equal(disabled.reader,true);
 // Native split operation uses real tabs, never iframe embedding or protection overrides.
 await clickTool('split');
 const split=await s.script(`return {count:gBrowser.selectedTab.splitview?.tabs.length,selected:gBrowser.selectedBrowser.currentURI.spec};`);
 assert.equal(split.count,2);
 await clickTool('split');
 const http=require('node:http');
 const article='<html><head><title>Rosavio article test</title></head><body><article><h1>A quiet garden in spring</h1>'+Array.from({length:30},()=>'<p>A quiet garden changes with the seasons. The gardener carefully plants flowers and vegetables in rich soil. Rain and sunshine support their growth. This long article describes the landscape, the birds and the work of caring for plants. Every morning the garden offers something new to discover.</p>').join('')+'</article></body></html>';
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(article);});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 let qr,reader;
 try{
  const base='http://127.0.0.1:'+server.address().port;
  const url=base+'/article?text='+encodeURIComponent('Rosavio 🌹 Grüße 日本語 '.repeat(8));
  await select(s);await s.command('WebDriver:Navigate',{url});await s.command('Marionette:SetContext',{value:'chrome'});
  await clickTool('split');await select(s);await s.command('WebDriver:Navigate',{url:base+'/second'});await s.command('Marionette:SetContext',{value:'chrome'});
  const both=await s.script(`return gBrowser.selectedTab.splitview.tabs.map(t=>({uri:t.linkedBrowser.currentURI.spec,document:t.linkedBrowser.browsingContext.currentWindowGlobal.documentURI.spec}));`);
  assert.equal(both.length,2);assert.deepEqual(both.map(x=>x.uri).sort(),[url,base+'/second'].sort());assert.ok(both.every(x=>x.uri===x.document));
  const splitShot=(await s.command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:false})).value;fs.writeFileSync(path.join(root,'workspace-split.png'),Buffer.from(splitShot,'base64'));
  await clickTool('split');await select(s);await s.command('WebDriver:Navigate',{url});await s.command('Marionette:SetContext',{value:'chrome'});
  await wait('return gBrowser.selectedBrowser.isArticle===true;');
  await clickTool('qr');
  await wait(`const d=gBrowser.getTabDialogBox(gBrowser.selectedBrowser)._tabDialogManager._dialogs[0];return !!d?._frame?.contentDocument?.getElementById('qrcode-image')?.src?.startsWith('data:image/png;base64,');`);
  qr=await s.script(`const d=gBrowser.getTabDialogBox(gBrowser.selectedBrowser)._tabDialogManager._dialogs[0];const doc=d._frame.contentDocument;return {url:doc.getElementById('qrcode-url').textContent,image:doc.getElementById('qrcode-image').src};`);
  assert.equal(qr.url,url);assert.ok(qr.image.startsWith('data:image/png;base64,'));
  fs.writeFileSync(path.join(root,'workspace-qr.png'),Buffer.from(qr.image.split(',')[1],'base64'));qr={dialogImage:true,url:qr.url};
  await s.script(`gBrowser.getTabDialogBox(gBrowser.selectedBrowser)._tabDialogManager.abortDialogs();return true;`);
  await clickTool('reader');
  await wait("return gBrowser.selectedBrowser.currentURI.spec.startsWith('about:reader?');");
  reader=true;
  await clickTool('reader');
  await wait(`return gBrowser.selectedBrowser.currentURI.spec===${JSON.stringify(url)};`);
 }finally{await new Promise(r=>server.close(r));}
 const privateCheck=await s.script(`const pw=OpenBrowserWindow({private:true});try{await new Promise(resolve=>pw.addEventListener('load',resolve,{once:true}));if(!pw.delayedStartupPromise)throw Error("Private startup promise unavailable");await pw.delayedStartupPromise;const privateTab=pw.gBrowser.addTrustedTab('about:rosavio-notes');pw.gBrowser.selectedTab=privateTab;const b=privateTab.linkedBrowser;for(let i=0;i<100;i++){if(b.browsingContext.currentWindowGlobal?.documentURI.spec==='about:rosavio-notes')break;await new Promise(r=>setTimeout(r,100));}if(b.browsingContext.currentWindowGlobal?.documentURI.spec!=='about:rosavio-notes')throw Error('Private test page did not load: '+JSON.stringify({uri:b.currentURI.spec,global:b.browsingContext.currentWindowGlobal?.documentURI.spec,tabs:pw.gBrowser.tabs.map(t=>t.linkedBrowser.currentURI.spec)}));const a=b.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');try{await a.receiveMessage({name:'RosavioWorkspace:Read'});return false;}catch(e){return String(e).includes('private windows');}}finally{pw.close();}`);
 assert.equal(privateCheck,true);
 const readingPlaces=await require('./check-reading-places.cjs')(s);
 const report={passed:true,pdfDigitalRelease,readingPlaces,runtimeOverlayOnly:!!options.runtimeOverlay,notesReloadPreserved:true,shortcutSaved:true,noSystemPrincipal:true,guards,nativeMenuClicksAllFive:true,nativeSplitTwoLoadedPages:true,unsupportedReaderDisabled:true,privatePersistenceBlocked:true,qr,readerEnterAndExit:reader,updateRestartTested:false};
 fs.writeFileSync(path.join(root,'report.json'),JSON.stringify(report,null,2));return report;
}
module.exports=checkWorkspace;
if(require.main===module){let session;const start=require('./native-session.cjs');const root=path.resolve(process.argv[3]);(async()=>{try{session=await start(path.resolve(process.argv[2]),path.join(root,'isolated-profile'),2921);await checkWorkspace(session,root);}finally{if(session)await session.close();}})().catch(e=>{console.error(e);process.exitCode=1});}
