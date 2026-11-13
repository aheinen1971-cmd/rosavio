const assert=require('node:assert/strict'),texts=require('./rosavio-pages/rosavio-workspace-locales.json'),select=require('./select-test-content.cjs');
module.exports=async(session,locale)=>{
 const words=texts[locale];assert.ok(words);
 await session.command('Marionette:SetContext',{value:'chrome'});
 const menu=await session.script(`await PanelUI.ensureReady();RosavioTools.refresh();return Object.fromEntries(['qr','notes','home','reader','split'].map(id=>[id,PanelUI.mainView.querySelector('#appMenu-rosavio-'+id)?.getAttribute('label')]));`);
 for(const [id,key] of [['qr','Webseite als QR-Code'],['notes','Meine Notizen'],['home','Meine Startseite'],['reader','Lesemodus ein/aus'],['split','Zwei Webseiten nebeneinander']])assert.equal(menu[id],words[key]);
 for(const [page,key] of [['notes','Meine Notizen · Rosavio'],['home','Meine Startseite · Rosavio']]){
  await select(session);await session.command('WebDriver:Navigate',{url:'about:rosavio-'+page});let data;
  for(let i=0;i<50;i++){data=await session.script(`return {backupLabels:['trail-export','trail-import','trail-backup-hint'].map(id=>document.getElementById(id)?.textContent),trailTitle:document.querySelector('#rose-path h2 span')?.textContent,trailSave:document.querySelector('#trail-save')?.textContent,placeTitle:document.querySelector("#notes-panel h2")?.textContent,title:document.title,lang:document.documentElement.lang,dir:document.documentElement.dir,ready:document.getElementById('save')?.disabled===false,overflow:document.documentElement.scrollWidth>innerWidth+2};`);if(data.ready)break;await new Promise(r=>setTimeout(r,100));}
  assert.equal(data.ready,true);assert.deepEqual(data.backupLabels,['Rosenpfad sichern','Sicherung öffnen','Die Datei enthält deinen gespeicherten Rosenpfad mit Zitaten und Notizen. Bewahre sie privat auf.'].map(k=>words[k]));assert.equal(data.trailTitle,words['Rosenpfad']);assert.equal(data.trailSave,words['Speichern']);assert.equal(data.placeTitle,words['Später hier weiterlesen']);assert.equal(data.title,words[key]);assert.equal(data.lang,locale);assert.equal(data.dir,['ar','he'].includes(locale)?'rtl':'ltr');assert.equal(data.overflow,false);
  await session.command('Marionette:SetContext',{value:'chrome'});assert.equal(await session.script('return gBrowser.selectedBrowser.contentPrincipal.isSystemPrincipal;'),false);
 }
 return {passed:true,locale,menuLabels:5,pages:2};
};
