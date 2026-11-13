const assert=require('node:assert/strict'),select=require('./select-test-content.cjs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
module.exports=async function checkTrailBackup(s){
 async function chrome(script){await s.command('Marionette:SetContext',{value:'chrome'});return s.script(script);}
 async function content(script){await select(s);return s.script(script);}
 async function ready(){for(let i=0;i<100;i++){if(await content("return document.getElementById('save')?.disabled===false;"))return;await pause(100);}throw Error('Backup UI remained busy');}
 async function disk(){return chrome("return await IOUtils.readJSON(PathUtils.join(PathUtils.profileDir,'rosavio-workspace.json'));");}
 const baseline=await disk();assert.ok(baseline.trail);
 const before=await chrome(`const {Downloads}=ChromeUtils.importESModule('resource://gre/modules/Downloads.sys.mjs');
  const dir=PathUtils.join(PathUtils.profileDir,'trail-backup-test');await IOUtils.makeDirectory(dir);
  Services.prefs.setIntPref('browser.download.folderList',2);Services.prefs.setBoolPref('browser.download.useDownloadDir',true);
  const f=Cc['@mozilla.org/file/local;1'].createInstance(Ci.nsIFile);f.initWithPath(dir);Services.prefs.setComplexValue('browser.download.dir',Ci.nsIFile,f);
  return (await (await Downloads.getList(Downloads.ALL)).getAll()).length;`);
 await content("document.getElementById('trail-export').click();return true;");
 let exported;
 for(let i=0;i<100;i++){
  exported=await chrome(`const {Downloads}=ChromeUtils.importESModule('resource://gre/modules/Downloads.sys.mjs');const all=await (await Downloads.getList(Downloads.ALL)).getAll();const d=all[${before}];return d?.succeeded?await IOUtils.readUTF8(d.target.path):null;`);
  if(exported)break;await pause(100);
 }
 assert.ok(exported,'A real JSON backup must finish downloading');
 assert.deepEqual(JSON.parse(exported),{format:'rosavio-rose-trail',version:1,trail:baseline.trail});
 const imported={...baseline.trail,name:'Backup 🌹 日本語 العربية',current:0};
 const file=await chrome(`const f=PathUtils.join(PathUtils.tempDir,'rosavio-restore-'+Date.now()+'.json');await IOUtils.writeUTF8(f,${JSON.stringify(JSON.stringify({format:'rosavio-rose-trail',version:1,trail:imported}))});return f;`);
 await content("document.getElementById('notes').value='Unrelated draft';document.getElementById('notes').dispatchEvent(new Event('input'));return true;");
 async function chooseFile(){
  await chrome(`const registrar=Components.manager.QueryInterface(Ci.nsIComponentRegistrar);
   if(!window.rosavioBackupPicker){
    const file=Cc['@mozilla.org/file/local;1'].createInstance(Ci.nsIFile);file.initWithPath(${JSON.stringify(file)});
    const factory={QueryInterface:ChromeUtils.generateQI(['nsIFactory']),createInstance(){return {
     QueryInterface:ChromeUtils.generateQI(['nsIFilePicker']),init(){},appendFilter(){},appendFilters(){},
     open(callback){callback.done(Ci.nsIFilePicker.returnOK);},file,
     get files(){let done=false;return {QueryInterface:ChromeUtils.generateQI(['nsISimpleEnumerator']),hasMoreElements(){return !done;},getNext(){done=true;return file;}};},
     filterIndex:0,displayDirectory:null,defaultString:'',defaultExtension:''
    };}};
    const id=Components.ID('{a204c355-b048-4c56-9775-babeb88d89d1}');
    registrar.registerFactory(id,'Isolated backup file selection','@mozilla.org/filepicker;1',factory);
    window.rosavioBackupPicker={id,factory};
   }return true;`);
  await select(s);
  const e=await s.command('WebDriver:FindElement',{using:'css selector',value:'#trail-import'});
  await s.command('WebDriver:ElementClick',{id:(e.value||e)['element-6066-11e4-a52e-4f735466cecf']});
 }
 await chooseFile();
 let cancelled=false;
 for(let i=0;i<50;i++){try{await s.command('WebDriver:DismissAlert');cancelled=true;break;}catch{await pause(100);}}
 assert.ok(cancelled,'Restore can be cancelled');await ready();
 assert.deepEqual(await disk(),baseline);
 assert.equal(await content("return document.getElementById('trail-name').value;"),baseline.trail.name);
 await chooseFile();
 let accepted=false;
 for(let i=0;i<50;i++){try{await s.command('WebDriver:AcceptAlert');accepted=true;break;}catch{await pause(100);}}
 assert.ok(accepted,'Restore confirmation must appear');await ready();
 assert.deepEqual(await disk(),baseline,'Import must not write before Save');
 assert.equal(await content("return document.getElementById('trail-name').value;"),imported.name);
 await content("document.getElementById('trail-save').click();return true;");await ready();
 const saved=await disk();assert.deepEqual(saved.trail,imported);assert.equal(saved.notes,baseline.notes);assert.deepEqual(saved.links,baseline.links);assert.deepEqual(saved.places,baseline.places);
 assert.equal(await content("return document.getElementById('notes').value;"),'Unrelated draft');
 // Invalid files must leave the saved state and the unsaved draft unchanged.
 await chrome(`await IOUtils.writeUTF8(${JSON.stringify(file)},'{invalid json');return true;`);
 await chooseFile();await pause(300);await ready();
 assert.deepEqual(await disk(),saved);
 assert.equal(await content("return document.getElementById('notes').value;"),'Unrelated draft');
 await chrome(`const a=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');const current=await a.receiveMessage({name:'RosavioWorkspace:Read'});return await a.receiveMessage({name:'RosavioWorkspace:Save',data:{...${JSON.stringify(baseline)},revision:current.revision}});`);
 await select(s);await s.command('WebDriver:Refresh');await ready();
 await chrome("const p=window.rosavioBackupPicker;Components.manager.QueryInterface(Ci.nsIComponentRegistrar).unregisterFactory(p.id,p.factory);delete window.rosavioBackupPicker;return true;");
 return {passed:true,realFileExport:true,explicitRestoreConfirmation:true,cancelPreservedState:true,stagedUntilSave:true,unrelatedDraftPreserved:true,invalidFileRejected:true};
};
