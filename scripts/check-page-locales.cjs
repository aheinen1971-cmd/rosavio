const fs=require('fs'),path=require('path');
const texts=require('./rosavio-pages/rosavio-locales.json');
module.exports=async function checkPageLocales(session,locale,root,options={}){
 const words=texts[locale];if(!words)throw Error('Unsupported page test locale: '+locale);
 const results=[];
 const expected=[['privacy','Privacy at a glance'],['updates','What’s new in Rosavio'],['addons','Rosavio Extensions']];
 if(!options.runtimeOverlay){
  await session.command('Marionette:SetContext',{value:'chrome'});
  const menu=await session.script(`await PanelUI.ensureReady();return Object.fromEntries(['privacy','updates','extensions'].map(id=>[id,PanelUI.mainView.querySelector('#appMenu-rosavio-'+id)?.getAttribute('label')]));`);
  for(const [id,key] of expected)if(menu[id==='addons'?'extensions':id]!==words[key])throw Error('Menu translation mismatch: '+locale+' '+id+': '+JSON.stringify(menu));
 }
 for(const [page,key] of expected){
  await session.command('Marionette:SetContext',{value:'content'});
  await session.command('WebDriver:Navigate',{url:'about:rosavio-'+page});
  let view;
  for(let attempt=0;attempt<50;attempt++){
   view=await session.script(`return {lang:document.documentElement.lang,dir:document.documentElement.dir,title:document.querySelector('h1')?.textContent,ready:document.documentElement.dataset.ready,text:document.body.textContent,placeholder:document.getElementById('query')?.placeholder,overflow:document.documentElement.scrollWidth>innerWidth+2};`);
   if(view.title===words[key]&&(page==='addons'||view.ready==='true'))break;
   await new Promise(resolve=>setTimeout(resolve,100));
  }
  if(view.lang!==locale||view.dir!==(['ar','he'].includes(locale)?'rtl':'ltr')||view.title!==words[key]||view.overflow)throw Error('Localized page mismatch: '+locale+' '+page+' '+JSON.stringify(view));
  if(page==='addons'){
   for(const k of ['Search','Open Mozilla catalogue'])if(!view.text.includes(words[k]))throw Error('Catalogue UI untranslated: '+locale+' '+k);
   if(view.placeholder!==words['For example: translator'])throw Error('Search placeholder untranslated');
  }else{
   if(view.ready!=='true'||!view.text.includes(words['Refresh overview']))throw Error('Native page not initialized in '+locale);
   if(page==='updates'&&!view.text.includes(words['Privacy overview, release notes and the extension catalogue interface are available in all 20 Rosavio languages.']))throw Error('Localized release note missing');
  }
  if(root&&['de','fr','ja','ar','he'].includes(locale)){
   fs.mkdirSync(root,{recursive:true});const shot=await session.command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:true});fs.writeFileSync(path.join(root,locale+'-'+page+'.png'),Buffer.from(shot.value,'base64'));
  }
  await session.command('Marionette:SetContext',{value:'chrome'});
  if(await session.script('return gBrowser.selectedBrowser.contentPrincipal.isSystemPrincipal;'))throw Error('Localized content has system privileges');
  results.push({page,...view,unprivileged:true});
 }
 return {passed:true,locale,menuChecked:!options.runtimeOverlay,pages:results};
};
