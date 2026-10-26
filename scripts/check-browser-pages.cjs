const fs=require('fs'),path=require('path'),start=require('./native-session.cjs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function check(session,root,options={}){
 fs.mkdirSync(root,{recursive:true});
 let menu=null;
 if(!options.runtimeOverlay){
  menu=await session.script(`await PanelUI.ensureReady();return {privacy:!!PanelUI.mainView.querySelector('#appMenu-rosavio-privacy'),updates:!!PanelUI.mainView.querySelector('#appMenu-rosavio-updates')};`);
  if(!menu.privacy||!menu.updates)throw Error('Rosavio information-page menu entries missing');
 }
 const names=['browser.safebrowsing.malware.enabled','browser.safebrowsing.phishing.enabled','browser.safebrowsing.downloads.enabled','browser.safebrowsing.downloads.remote.block_potentially_unwanted','browser.safebrowsing.downloads.remote.block_uncommon'];
 async function prefs(value){await session.command('Marionette:SetContext',{value:'chrome'});return session.script(`const names=${JSON.stringify(names)};${value===undefined?'':`for(const name of names)Services.prefs.setBoolPref(name,${value});`}return Object.fromEntries(names.map(n=>[n,Services.prefs.getBoolPref(n)]));`);}
 async function page(url,screenshot){
  console.log('Checking '+url);
  await session.command('Marionette:SetContext',{value:'content'});
  await session.command('WebDriver:Navigate',{url});
  let data;
  for(let i=0;i<40;i++){
   data=await session.script(`return {ready:document.documentElement.dataset.ready==='true',title:document.title,text:document.body.textContent,states:Object.fromEntries([...document.querySelectorAll('article')].map(n=>[n.id,n.querySelector('.state').className])),links:[...document.querySelectorAll('a')].map(a=>a.getAttribute('href'))};`);
   if(data.ready)break;await pause(200);
  }
  if(!data.ready)throw Error('Browser information page did not receive native settings: '+JSON.stringify(data));
  if(screenshot){const shot=(await session.command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:true})).value;fs.writeFileSync(path.join(root,screenshot+'.png'),Buffer.from(shot,'base64'));}
  await session.command('Marionette:SetContext',{value:'chrome'});
  const principal=await session.script('return gBrowser.selectedBrowser.contentPrincipal.isSystemPrincipal;');
  if(principal)throw Error('Rosavio information pages must not have system privileges');
  return data;
 }
 await prefs(true);
 const privacy=await page('about:rosavio-privacy','privacy-enabled');
 for(const name of ['sites','downloads','unwanted'])if(privacy.states[name]!=='state good')throw Error('Enabled protection is not shown correctly');
 if(privacy.links.includes('javascript:')||!privacy.links.includes('about:preferences#privacy'))throw Error('Privacy settings link missing');
 const afterRead=await prefs();if(Object.values(afterRead).some(v=>v!==true))throw Error('Page changed protection preferences');
 await session.command('Marionette:SetContext',{value:'content'});
 await session.script(`document.querySelector('#sites a').click();return true;`);
 let settingsOpened=false;
 for(let i=0;i<40;i++){
  await session.command('Marionette:SetContext',{value:'chrome'});
  settingsOpened=await session.script(`return gBrowser.selectedBrowser.currentURI.spec.startsWith('about:preferences#');`);
  if(settingsOpened)break;await pause(100);
 }
 if(!settingsOpened){const chrome=await session.script(`return {uri:gBrowser.selectedBrowser.currentURI.spec,tabs:[...gBrowser.tabs].map(t=>t.linkedBrowser.currentURI.spec),errors:Services.console.getMessageArray().map(m=>m.message).filter(x=>x.includes('Rosavio')).slice(-4)};`);await session.command('Marionette:SetContext',{value:'content'});const dom=await session.script(`return {uri:location.href,status:document.getElementById('status')?.textContent,href:document.querySelector('#sites a')?.getAttribute('href')};`);throw Error('Normal settings link did not open: '+JSON.stringify({chrome,dom}));}
 await page('about:rosavio-privacy');
 await prefs(false);
 await session.command('Marionette:SetContext',{value:'content'});
 await session.script(`document.getElementById('refresh').click();return true;`);
 let refreshed=false;
 for(let i=0;i<40;i++){
  refreshed=await session.script(`return ['sites','downloads','unwanted'].every(id=>document.querySelector('#'+id+' .state')?.classList.contains('warn'));`);
  if(refreshed)break;await pause(100);
 }
 if(!refreshed)throw Error('Refresh button did not read updated effective preferences');
 // Reload reads actual changed values; the page must never silently repair them.
 const disabled=await page('about:rosavio-privacy','privacy-disabled');
 for(const name of ['sites','downloads','unwanted'])if(disabled.states[name]!=='state warn')throw Error('Disabled protection is not shown correctly');
 const afterDisabled=await prefs();if(Object.values(afterDisabled).some(v=>v!==false))throw Error('Read-only page changed disabled test preferences');
 await prefs(true);
 const updates=await page('about:rosavio-updates','updates');
 if(!updates.text.includes('Build ')||!updates.links.includes('https://github.com/aheinen1971-cmd/rosavio/releases'))throw Error('Installed version or release link missing');
 const restored=await prefs();if(Object.values(restored).some(v=>v!==true))throw Error('Release notes changed protection preferences');
 fs.mkdirSync(root,{recursive:true});
 const report={passed:true,menu,menuClickManuallyTested:false,privacyReady:true,updatesReady:true,unprivileged:true,settingsLinkOpened:true,refreshPassed:true,enabledAndDisabledStatesAccurate:true,readOnlyPreferencesPreserved:true,privacy,disabled,updates};
 fs.writeFileSync(path.join(root,'report.json'),JSON.stringify(report,null,2));
 return report;
}
module.exports=check;
if(require.main===module)(async()=>{let session;const[binary,root]=process.argv.slice(2);try{session=await start(path.resolve(binary),path.resolve(root),2893);await check(session,root);console.log('Native read-only privacy overview and bundled release notes passed.');}finally{if(session)await session.close();}})().catch(e=>{console.error(e);process.exitCode=1});
