const fs=require('fs'),path=require('path'),start=require('./native-session.cjs');
const [binary,root]=process.argv.slice(2),pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{let session;try{
 session=await start(path.resolve(binary),path.resolve(root),2871);
 const menu=await session.script(`return {present:!!document.getElementById('appMenu-rosavio-extensions'),label:document.getElementById('appMenu-rosavio-extensions')?.getAttribute('label')};`);
 if(!menu.present)throw Error('Rosavio catalogue menu is missing');
 await session.command('Marionette:SetContext',{value:'content'});
 await session.command('WebDriver:Navigate',{url:'about:rosavio-addons'});
 const initial=await session.script(`return {url:location.href,title:document.title,form:!!document.getElementById('search'),manager:document.getElementById('manage')?.getAttribute('href')};`);
 if(initial.url!=='about:rosavio-addons'||!initial.form||initial.manager!=='about:addons')throw Error('Native catalogue page is unavailable');
 await session.script(`document.getElementById('query').value='ublock';document.getElementById('search').requestSubmit();return true;`);
 let results;
 for(let i=0;i<45;i++){
  results=await session.script(`return {status:document.getElementById('status').textContent,links:[...document.querySelectorAll('#results a')].map(a=>a.href)};`);
  if(results.links.length)break;await pause(1000);
 }
 if(!results.links.length||results.links.some(u=>!u.startsWith('https://addons.mozilla.org/')))throw Error('Official extension search failed: '+JSON.stringify(results));
 await session.command('Marionette:SetContext',{value:'chrome'});
 const principal=await session.script(`return {system:gBrowser.selectedBrowser.contentPrincipal.isSystemPrincipal};`);
 if(principal.system)throw Error('Catalogue must not run with browser system privileges');
 fs.mkdirSync(root,{recursive:true});fs.writeFileSync(path.join(root,'report.json'),JSON.stringify({passed:true,menu,initial,results,unprivileged:true,installationMethod:'official Mozilla page and normal browser permission prompt',installationPromptManuallyTested:false},null,2));
 console.log('Native Rosavio catalogue, official search and unprivileged content passed; installation prompt requires separate verification.');
}finally{if(session)await session.close();}})().catch(e=>{console.error(e);process.exitCode=1});
