// Read the existing native protection controls without changing any settings.
module.exports=async function(browser){
 await browser.command('Marionette:SetContext',{value:'chrome'});
 const url=await browser.script(`return Services.prefs.getBoolPref('browser.settings-redesign.enabled',false)?'about:preferences#connectionSecurity':'about:preferences#privacy';`);
 await browser.command('Marionette:SetContext',{value:'content'});
 await browser.command('WebDriver:Navigate',{url});
 const controls=await browser.script(`
 const ids=['enableSafeBrowsing','blockDownloads','blockUncommonUnwanted'];
 const find=(root,id)=>{for(const e of root.querySelectorAll('*')){const w=e.wrappedJSObject||e;if(e.id===id||w.setting?.id===id||w.config?.id===id)return w.controlRef?.value||e;if(e.shadowRoot){const hit=find(e.shadowRoot,id);if(hit)return hit;}}return null;};
 for(let i=0;i<100;i++){if(ids.every(id=>find(document,id)))break;await new Promise(r=>setTimeout(r,100));}
 return ids.map(id=>{const e=find(document,id);if(e)e.scrollIntoView();return {id,exists:!!e,checked:e?.checked===true};});`);
 if(!Array.isArray(controls)||controls.length!==3||controls.some(c=>!c.exists||!c.checked))throw Error('Native protection controls are not all enabled: '+JSON.stringify(controls));
 await browser.command('Marionette:SetContext',{value:'chrome'});
 const active=await browser.script(`const tab=gBrowser.tabs.find(t=>t.linkedBrowser.currentURI.spec.startsWith('about:preferences'));if(!tab)throw Error('Native settings tab missing');gBrowser.selectedTab=tab;await new Promise(r=>setTimeout(r,500));return true;`);
 if(active!==true)throw Error('Native settings tab is not selected');
 return controls;
};
