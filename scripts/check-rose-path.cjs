const assert = require('node:assert/strict');
const select = require('./select-test-content.cjs');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

// Runs only in the isolated workspace qualification profile.
module.exports = async function checkRosePath(session, originalLink) {
  const chrome = () => session.command('Marionette:SetContext', {value:'chrome'});
  async function inspect(script) {
    const value = await session.script(script);
    if (value?.error) throw Error(value.error);
    return value;
  }
  async function ready() {
    for (let i=0;i<80;i++) {
      if (await inspect("return document.getElementById('save')?.disabled===false;")) return;
      await wait(100);
    }
    throw Error('Rose path save did not finish');
  }
  async function click(css) {
    const ref = await session.command('WebDriver:FindElement',{using:'css selector',value:css});
    await session.command('WebDriver:ElementClick',{id:(ref.value||ref)['element-6066-11e4-a52e-4f735466cecf']});
  }
  const other=new URL(originalLink);
  other.searchParams.set('second','1');
  await chrome();
  await inspect(`const module=ChromeUtils.importESModule('resource:///actors/RosavioWorkspaceParent.sys.mjs');
    await module.RosavioWorkspaceParent.addPlace(window,{url:${JSON.stringify(other.href)},quote:'Zweite Teststelle'});return true;`);
  await select(session);
  await session.command('WebDriver:Refresh');await ready();
  // Isolate from any rose path seeded by the update-preservation check.
  async function storage(action) {
    await chrome();
    const result=await inspect("const actor=gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.getActor('RosavioWorkspace');const data=await actor.receiveMessage({name:'RosavioWorkspace:Read'});"+action);
    await select(session);
    return result;
  }
  const baseline=await storage('return data;');
  await storage("delete data.trail;return await actor.receiveMessage({name:'RosavioWorkspace:Save',data});");
  await session.command('WebDriver:Refresh');await ready();
  for (const url of [originalLink,other.href]) {
    const index=await inspect(`return [...document.querySelectorAll('#reading-places a')].findIndex(a=>a.href===${JSON.stringify(url)});`);
    assert.ok(index>=0);
    await click('#reading-places li:nth-child('+(index+1)+') button:last-child');
  }
  await inspect(`for(const [id,text] of [['trail-name','Mein Ausflug'],['trail-note','Brücke merken']]){
    const el=document.getElementById(id);el.value=text;el.dispatchEvent(new Event('input'));}
    return true;`);
  assert.equal(await inspect("return !document.querySelector('#trail-save').disabled && !document.querySelector('#trail-navigation a');"),true);
  await click('#trail-steps li:first-child button:nth-of-type(2)');
  assert.equal(await inspect("return Number(document.querySelector('#trail-steps li[aria-current]').dataset.index);"),1);
  assert.equal((await storage('return data;')).trail,undefined);
  await inspect("const notes=document.querySelector('#notes');notes.value='Separater ungespeicherter Entwurf';notes.dispatchEvent(new Event('input'));return true;");
  await click('#trail-save');await ready();
  assert.equal((await storage('return data;')).notes,baseline.notes);
  assert.equal(await inspect("return document.querySelector('#notes').value;"),'Separater ungespeicherter Entwurf');
  await inspect("const notes=document.querySelector('#notes');notes.value="+JSON.stringify(baseline.notes)+";notes.dispatchEvent(new Event('input'));document.querySelector('#save').click();return true;");await ready();
  await session.command('WebDriver:Refresh');await ready();
  assert.equal(await inspect("return document.querySelector('#trail-name').value;"),'Mein Ausflug');
  assert.equal(await inspect("return document.querySelector('#trail-note').value;"),'Brücke merken');
  assert.deepEqual(await storage("return data.trail.steps.map(s=>s.url);"),[other.href,originalLink]);
  await click('#trail-navigation a:first-child');
  await chrome();
  for(let i=0;i<80;i++) {
    if(await inspect(`return gBrowser.selectedBrowser.currentURI.spec===${JSON.stringify(other.href)};`))break;
    await wait(100);
  }
  assert.equal(await inspect("return gBrowser.selectedBrowser.currentURI.spec;"),other.href);
  await select(session);await session.command('WebDriver:Navigate',{url:'about:rosavio-notes'});await ready();
  assert.equal(await inspect("return Number(document.querySelector('#trail-steps li[aria-current]').dataset.index);"),0);
  await click('#trail-steps li:first-child button:last-child');
  await click('#trail-save');await ready();
  assert.equal(await inspect("return document.querySelectorAll('#trail-steps li').length;"),1);
  // Restore the fixture for the remaining integrity checks; keep the generated revision.
  await storage(`Object.assign(data,${JSON.stringify(baseline)},{revision:data.revision});
    ${baseline.trail?'':'delete data.trail;'} data.places=data.places.filter(p=>p.url!==${JSON.stringify(other.href)});
    return await actor.receiveMessage({name:'RosavioWorkspace:Save',data});`);
  await session.command('WebDriver:Refresh');await ready();
  return {passed:true,explicitSave:true,reordered:true,notePreserved:true,resumeOpenedSource:true};
};
