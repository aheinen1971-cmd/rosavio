const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const start=require('../scripts/native-session.cjs');
const root=path.resolve(__dirname,'../media'),out=path.resolve(__dirname,'evidence/filename-rosavio');fs.mkdirSync(out,{recursive:true});
const harness=fs.readFileSync(path.join(__dirname,'video-finder-names-ui.cjs'),'utf8');
const init=harness.slice(harness.indexOf('({locale,messages,source})=>'),harness.indexOf(',{locale,messages,source:'));
let locale='de';
const server=http.createServer((req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 if(pathname==='/neutral.m3u8')return res.end('#EXTM3U\n#EXTINF:1,\n/neutral.ts\n#EXT-X-ENDLIST');
 if(pathname==='/neutral.ts')return res.end(fs.readFileSync(path.join(__dirname,'fixtures/video-finder/video.ts')));
 if(pathname==='/init.js'){
  res.setHeader('Content-Type','application/javascript');return res.end('('+init+')('+JSON.stringify({locale,messages:JSON.parse(fs.readFileSync(path.join(root,'_locales',locale.replaceAll('-','_'),'messages.json'))),source:fs.readFileSync(path.join(root,'youtube-background.js'),'utf8')})+');');
 }
 const file=path.join(root,pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)){res.writeHead(404);return res.end();}
 let content=fs.readFileSync(file,'utf8');const html=file.endsWith('.html');
 if(html)content=content.replace('<script src="l10n.js">','<script src="/init.js"></script><script src="l10n.js">');
 res.setHeader('Content-Type',html?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':'application/javascript');res.end(content);
});
(async()=>{let s;const results=[];await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
 s=await start('C:/Program Files/Rosavio/rosavio.exe',path.join(out,'isolated-profile'),2898);
 await s.command('Marionette:SetContext',{value:'content'});
 for(locale of require('../scripts/requested-languages.json').locales){
  await s.command('WebDriver:Navigate',{url:`http://127.0.0.1:${server.address().port}/sidebar.html`});
  const result=await s.script(`
   const pause=()=>new Promise(r=>setTimeout(r,30));
   async function until(fn){for(let n=0;n<200;n++){if(await fn())return;await pause();}throw Error('UI timeout');}
   await until(()=>!document.querySelector('#youtube-detect').disabled);
   document.querySelector('#youtube-detect').click();
   receive({type:'info',title:'Neutraler Film 🌹',choices:[{selector:'18',height:360,merged:false}]});receive({type:'idle'});
   const name=document.querySelector('#youtube-filename');if(name.value!=='Neutraler Film 🌹')throw Error('Title suggestion');
   name.value='Mein eigener Film';name.dispatchEvent(new Event('input'));document.querySelector('#scan').click();await pause();if(name.value!=='Mein eigener Film')throw Error('Edited title lost after scan');document.querySelector('#youtube-save').click();
   if(sent.at(-1).filenameTitle!=='Mein eigener Film'||!name.disabled)throw Error('Edited title');
   receive({type:'saved',path:'fixture.mp4'});receive({type:'idle'});
   renderRow({url:'https://example.org/abc.mp4',name:'abc.mp4',title:'Neutraler Film',height:720},document.querySelector('#list'));
   document.querySelector('#list input').value='Direkter Film';document.querySelector('#list button').click();
   await until(()=>saved.length>0);if(saved[0].filename!=='Direkter Film – 720p.mp4')throw Error('Direct name');
   const q=await getQueue();q.addDownload(location.origin+'/neutral.m3u8','Neutraler Stream');
   await until(()=>document.querySelector('main .save')&&!document.querySelector('main .save').hidden);
   const input=document.querySelector('main .filename-title');input.value='Geänderter Stream';input.dispatchEvent(new Event('input'));
   q.document.querySelector('.status').textContent+=' ';await pause();
   if(document.querySelector('main .filename-title').value!=='Geänderter Stream')throw Error('Queue redraw');
   document.querySelector('main .save').click();await until(()=>q.saved.length>0);
   if(q.saved[0].filename!=='Geänderter Stream.ts')throw Error('HLS name');
   return {locale:document.documentElement.lang,dir:document.documentElement.dir,label:document.querySelector('label[for=youtube-filename]').textContent,passed:true};
  `);
  assert.equal(result.passed,true,JSON.stringify(result));results.push(result);
 }
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({passed:true,browser:'Rosavio 161.0, isolated local UI with simulated extension APIs',results},null,2));console.log('Rosavio UI: '+results.length+' languages passed');
 }finally{await s?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
