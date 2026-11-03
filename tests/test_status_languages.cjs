'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'../docs/status');
const data=fs.readFileSync(path.join(root,'locales.js'),'utf8');
const code=fs.readFileSync(path.join(root,'i18n.js'),'utf8');
const words=vm.runInNewContext(data+'; STATUS_LOCALES');
assert.equal(Object.keys(words).length,20);
const keys=Object.keys(words.de).sort();
for(const [lang,strings] of Object.entries(words)){
 assert.deepEqual(Object.keys(strings).sort(),keys);
 for(const key of keys){assert.equal(typeof strings[key],'string');assert.ok(strings[key].trim());assert.deepEqual((strings[key].match(/\{\w+\}/g)||[]).sort(),(key.match(/\{\w+\}/g)||[]).sort());}
 const links=[],home={},html={};
 const context={location:{search:'?lang='+lang},URLSearchParams,NodeFilter:{SHOW_TEXT:4},document:{documentElement:html,createTreeWalker:()=>({nextNode:()=>false}),querySelector:s=>s==='footer nav a'?home:{after:()=>{}},createElement:tag=>({setAttribute(){},append(link){links.push(link)}})}};
 vm.createContext(context);vm.runInContext(data+'\n'+code,context);
 assert.equal(html.lang,lang);assert.equal(html.dir,['ar','he'].includes(lang)?'rtl':'ltr');
 assert.equal(home.href,lang==='de'?'../':'../'+lang+'.html');assert.equal(links.length,20);
 for(const state of ['failure','timed_out','cancelled','action_required']){
  const result=vm.runInContext(`statusText('Letzter Auftrag: ${state}; siehe Laufdetails')`,context);
  assert.ok(!result.includes('{result}'));if(lang!=='de')assert.ok(!result.includes('Letzter Auftrag'));
 }
 const phase=vm.runInContext("statusText('1 von 4 Phasen abgeschlossen')",context);assert.ok(phase.includes('1')&&phase.includes('4'));assert.ok(!phase.includes('{'));
 assert.equal(vm.runInContext("statusText('Geprüft und veröffentlicht')",context),strings['Geprüft und veröffentlicht']);
 const file=path.join(__dirname,'../docs',lang==='de'?'index.html':lang+'.html');
 assert.ok(fs.readFileSync(file,'utf8').includes('href="status/?lang='+lang+'"'));
}
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const text of html.matchAll(/>([^<>]+)</g)){
 const value=text[1].trim();if(!value||value==='—'||value==='🌹')continue;
 const plain=value.replace(/^(🟢|🟡|🔴|⚪)\s+/u,'');assert.ok(Object.hasOwn(words.de,plain),'Untranslated static text: '+plain);
}
console.log('20 languages: complete keys, placeholders, dynamic failures/progress, RTL and matching website links passed.');
