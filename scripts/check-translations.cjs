const fs=require('fs'),path=require('path'),http=require('http'),start=require('./native-session.cjs');
const [binary,root]=process.argv.slice(2),pause=ms=>new Promise(r=>setTimeout(r,ms));
const original='The garden is full of beautiful flowers. The children are playing outside. This browser can translate a complete web page.';
let session,server;
(async()=>{try{
 server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><html lang="en"><title>English translation test</title><h1>A beautiful garden</h1><p id="sample">'+original+'</p></html>');});
 await new Promise(resolve=>server.listen(8773,'127.0.0.1',resolve));
 session=await start(path.resolve(binary),path.resolve(root),2873);
 const support=await session.script(`return {enabled:Services.prefs.getBoolPref('browser.translations.enable',false),menu:!!document.getElementById('appMenu-translate-button'),name:Services.appinfo.name};`);
 if(!support.enabled||support.name!=='Rosavio')throw Error('Native translations unavailable: '+JSON.stringify(support));
 await session.command('Marionette:SetContext',{value:'content'});
 await session.command('WebDriver:Navigate',{url:'http://127.0.0.1:8773/'});
 await session.command('Marionette:SetContext',{value:'chrome'});
 const launch=await session.script(`const actor=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('Translations');actor.translate({sourceLanguage:'en',targetLanguage:'de'},false);return {started:true};`);
 if(launch.error)throw Error(launch.error);
 let translated='';
 for(let i=0;i<180;i++){
  await session.command('Marionette:SetContext',{value:'content'});
  const result=await session.script(`return {text:document.getElementById('sample')?.textContent,title:document.querySelector('h1')?.textContent};`);
  translated=result.text||'';
  if(translated!==original&&/Garten|Blumen|Kinder|Browser/.test(translated)){
   fs.mkdirSync(root,{recursive:true});fs.writeFileSync(path.join(root,'report.json'),JSON.stringify({passed:true,testedAt:new Date().toISOString(),sourceLanguage:'en',targetLanguage:'de',support,original,translated,title:result.title},null,2));
   console.log('Native English-to-German whole-page translation passed.');return;
  }
  await session.command('Marionette:SetContext',{value:'chrome'});await pause(1000);
 }
 throw Error('Whole-page translation did not complete: '+translated);
}finally{if(session)await session.close();if(server)await new Promise(resolve=>server.close(resolve));}})().catch(e=>{console.error(e);process.exitCode=1});
