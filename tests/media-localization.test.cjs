const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.join(__dirname,'../media');
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const locales=require('../scripts/requested-languages.json').locales;
const catalog=locale=>JSON.parse(read('_locales/'+locale.replaceAll('-','_')+'/messages.json'));
const reference=catalog('de');
const placeholders=s=>[...s.matchAll(/\{([a-z]+)\}/g)].map(m=>m[1]).sort();
function element(key,label=false){return {dataset:label?{i18nLabel:key}:{i18n:key},textContent:'',setAttribute(k,v){this[k]=v;}};}
for(const locale of locales)test('media locale '+locale,async()=>{
 const messages=catalog(locale);
 assert.deepEqual(Object.keys(messages).sort(),Object.keys(reference).sort());
 for(const [key,{message}] of Object.entries(messages)){
  assert.ok(message.trim(),key);
  assert.deepEqual(placeholders(message),placeholders(reference[key].message),key);
 }
 const elements=[],labels=[],templates=[];
 for(const file of ['sidebar.html','queue.html','background.html']){
  const html=read(file);
  assert.ok(html.indexOf('src="l10n.js"')<html.lastIndexOf('<script src='));
  for(const [,key] of html.matchAll(/data-i18n="([^"]+)"/g))elements.push(element(key));
  for(const [,key] of html.matchAll(/data-i18n-label="([^"]+)"/g))labels.push(element(key,true));
 }
 const nested=element('save');
 templates.push({content:{querySelectorAll:s=>s==='[data-i18n]'?[nested]:[]}});
 const document={documentElement:{},querySelectorAll:s=>s==='[data-i18n]'?elements:s==='[data-i18n-label]'?labels:templates};
 const ctx=vm.createContext({document,Intl,URL,browser:{i18n:{getUILanguage:()=>locale,getMessage:key=>messages[key]?.message||''}}});
 vm.runInContext(read('l10n.js'),ctx);
 assert.equal(document.documentElement.dir,['ar','he'].includes(locale)?'rtl':'ltr');
 assert.equal(document.documentElement.lang,locale);
 for(const el of elements)assert.equal(el.textContent,messages[el.dataset.i18n].message);
 for(const el of labels)assert.equal(el['aria-label'],messages[el.dataset.i18nLabel].message);
 assert.equal(nested.textContent,messages.save.message);
 const dangerous='<img src=x onerror=alert(1)>';
 assert.ok(ctx.mediaText('manual',{name:dangerous}).includes(dangerous));
 assert.equal(ctx.mediaNumber(1234.5),new Intl.NumberFormat(locale).format(1234.5));
 vm.runInContext(read('filename.js'),ctx);
 assert.equal(ctx.videoFilename('',0,'','mp4'),messages.video.message+'.mp4');
 vm.runInContext(read('hls.js')+'\n'+read('parts.js'),ctx);
 assert.throws(()=>ctx.mediaPlan({base:'https://example.org/',lines:['#EXTM3U','#EXTINF:4,','x.ts']}),e=>e.mediaLocalized&&e.message===messages.live.message);
 await assert.rejects(ctx.readList('https://example.org/',async()=>({ok:false,status:404})),e=>e.message===ctx.mediaText('playlistHttp',{status:404}));
 assert.equal(ctx.mediaErrorText(new Error('foreign text')),messages.unexpected.message);
 for(const file of ['sidebar.js','queue.js','parts.js','hls.js','merge.mjs','youtube-sidebar.js'])for(const [,key] of read(file).matchAll(/media(?:Text|Error)\('([^']+)'/g))assert.ok(messages[key],file+':'+key);
});
test('manifest locale contract',()=>{
 const manifest=JSON.parse(read('manifest.json'));
 assert.equal(manifest.default_locale,'de');
 for(const text of [manifest.name,manifest.browser_action.default_title,manifest.sidebar_action.default_title])for(const [,key] of text.matchAll(/__MSG_(\w+)__/g))assert.ok(reference[key]);
 assert.equal(fs.readdirSync(path.join(root,'_locales')).length,20);
});
