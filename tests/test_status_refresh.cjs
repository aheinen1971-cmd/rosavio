'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=__dirname+'/../docs/status/';
const code=fs.readFileSync(base+'status.js','utf8').split("document.getElementById('refresh').addEventListener")[0];
const els={notice:{},refresh:{},retrieved:{textContent:'old fetch'}};
let fail=false;
const ctx={document:{getElementById:id=>els[id]},statusText:x=>x,statusLanguage:'de',Date,Intl,fetch:async()=>{if(fail)throw Error('offline');return {ok:true,json:async()=>({checkedAt:'2000-01-01T00:00:00Z'})}}};
vm.createContext(ctx);vm.runInContext(code+"\nrender=function(data){last=data;ageNotice();};",ctx);
(async()=>{
 await vm.runInContext('refresh()',ctx);
 assert.notEqual(els.retrieved.textContent,'old fetch');
 assert.match(els.notice.textContent,/Prüfstand veraltet/);
 assert.equal(vm.runInContext('last.checkedAt',ctx),'2000-01-01T00:00:00Z');
 const lastFetch=els.retrieved.textContent;fail=true;
 await vm.runInContext('refresh()',ctx);
 assert.equal(els.retrieved.textContent,lastFetch);
 assert.match(els.notice.textContent,/Aktueller Abruf nicht möglich/);
 assert.equal(els.refresh.disabled,false);
 const html=fs.readFileSync(base+'index.html','utf8');
 const links=[...html.matchAll(/class="report-button" href="([^"]+)"/g)];assert.equal(links.length,2);
 for(const [i,m] of links.entries()){const url=new URL(m[1].replaceAll('&amp;','&'));assert.equal(url.hostname,'github.com');assert.equal(url.pathname,'/aheinen1971-cmd/'+['rosavio','pdf-digital'][i]+'/issues/new');assert.match(url.searchParams.get('body'),/Version:/);assert.match(url.searchParams.get('body'),/Steps to reproduce:/);}
 console.log('Stale-data notice, separate fetch timestamp, failure preservation and two report forms passed.');
})().catch(e=>{console.error(e);process.exit(1)});
