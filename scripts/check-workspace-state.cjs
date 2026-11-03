// This helper is exclusively for isolated release-test profiles.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const select=require('./select-test-content.cjs');
const fixture={revision:1,notes:'Rosavio update fixture 🌹\n<plain text> bleibt erhalten',links:[{title:'Erhaltene Testseite',url:'https://example.com/rosavio-preserved'}]};
async function capability(session){await session.command('Marionette:SetContext',{value:'chrome'});const r=await session.script(`return Components.manager.QueryInterface(Ci.nsIComponentRegistrar).isContractIDRegistered('@mozilla.org/network/protocol/about;1?what=rosavio-notes');`);if(typeof r!=='boolean')throw Error('Workspace capability check failed');return r;}
async function state(session,root,mode){
 if(!['seed','verify'].includes(mode))throw Error('Invalid workspace preservation mode');
 const included=await capability(session);fs.mkdirSync(root,{recursive:true});
 if(mode==='seed'){
  // Old released versions cannot open the new pages. Seed a clearly reported data
  // fixture in that case; never claim that the old release had workspace UI.
  if(included){
   await select(session);await session.command('WebDriver:Navigate',{url:'about:rosavio-notes'});
   await session.command('Marionette:SetContext',{value:'chrome'});
   const result=await session.script(`const a=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');const current=await a.receiveMessage({name:'RosavioWorkspace:Read'});if(current.revision!==0)throw Error('Fresh isolated workspace required');return await a.receiveMessage({name:'RosavioWorkspace:Save',data:${JSON.stringify({...fixture,revision:0})}});`);
   assert.deepEqual(result,fixture);
  }else{
   const result=await session.script(`const file=PathUtils.join(PathUtils.profileDir,'rosavio-workspace.json');if(await IOUtils.exists(file))throw Error('Fresh isolated profile required');await IOUtils.writeJSON(file,${JSON.stringify(fixture)},{tmpPath:file+'.tmp'});return true;`);assert.equal(result,true);
  }
  const report={passed:true,baselineWorkspaceAvailable:included,legacyDataFixture:!included,fixture};
  fs.writeFileSync(path.join(root,'workspace-before.json'),JSON.stringify(report,null,2));return report;
 }
 const before=JSON.parse(fs.readFileSync(path.join(root,'workspace-before.json'),'utf8'));
 if(!included)throw Error('New package must contain workspace pages');
 const actual=await session.script(`return await IOUtils.readJSON(PathUtils.join(PathUtils.profileDir,'rosavio-workspace.json'));`);assert.deepEqual(actual,before.fixture);
 for(const page of ['notes','home']){
  await select(session);await session.command('WebDriver:Navigate',{url:'about:rosavio-'+page});
  let data;
  for(let i=0;i<50;i++){data=await session.script(`return {ready:document.getElementById('save')?.disabled===false,notes:document.getElementById('notes')?.value,links:Array.from(document.querySelectorAll('#links a')).map(a=>({title:a.textContent,url:a.href}))};`);if(data.ready)break;await new Promise(r=>setTimeout(r,100));}
  assert.equal(data.ready,true);assert.equal(data.notes,before.fixture.notes);assert.deepEqual(data.links,before.fixture.links);
 }
 await session.command('Marionette:SetContext',{value:'chrome'});
 const result={passed:true,notesAndShortcutsPreserved:true,baselineWorkspaceAvailable:before.baselineWorkspaceAvailable,legacyDataFixture:before.legacyDataFixture};
 fs.writeFileSync(path.join(root,'workspace-after.json'),JSON.stringify(result,null,2));return result;
}
module.exports=state;module.exports.capability=capability;
