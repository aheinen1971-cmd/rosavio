// Rebind Marionette to the actual selected tab after chrome/content transitions.
// No retry, replacement tab, arbitrary handle fallback, or suppressed error.
module.exports=async function selectTestContent(session){
 await session.command('Marionette:SetContext',{value:'chrome'});
 const handle=await session.script(`await gBrowserInit.delayedStartupPromise;
 const browser=gBrowser.selectedBrowser;
 if(!browser || !browser.browsingContext || browser.browsingContext.isDiscarded)throw Error('Selected test tab is not live');
 const {NavigableManager}=ChromeUtils.importESModule('chrome://remote/content/shared/NavigableManager.sys.mjs');
 return NavigableManager.getIdForBrowser(browser);`);
 if(typeof handle!=='string'||!handle)throw Error('Cannot identify selected test tab: '+JSON.stringify(handle));
 await session.command('Marionette:SetContext',{value:'content'});
 await session.command('WebDriver:SwitchToWindow',{handle});
 return handle;
};
