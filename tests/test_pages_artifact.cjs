const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {waitForArtifact} = require('../.github/actions/wait-pages-artifact/wait.cjs');
const name = 'github-pages-12345-2', id = '67890';
const valid = {name, id:Number(id), size:2048};
function fixture(sequence) {
  let time=0, calls=0;const waits=[];
  return {options:{name,id,now:()=>time,log:()=>{},sleep:async ms=>{waits.push(ms);time+=ms;},list:async()=>{
    const value=sequence[Math.min(calls++,sequence.length-1)];if(value instanceof Error)throw value;return value;
  }},calls:()=>calls,waits,time:()=>time};
}
test('visible exact uploaded artifact needs no wait',async()=>{
  const f=fixture([{artifacts:[valid]}]);assert.deepEqual(await waitForArtifact(f.options),valid);assert.equal(f.calls(),1);assert.deepEqual(f.waits,[]);
});
test('empty listings then visible succeed without repeating upload',async()=>{
  const f=fixture([{artifacts:[]},{artifacts:[]},{artifacts:[valid]}]);await waitForArtifact(f.options);assert.equal(f.calls(),3);assert.equal(f.time(),10000);
});
test('persistent empty response stops at ninety seconds',async()=>{
  const f=fixture([{artifacts:[]}]);await assert.rejects(waitForArtifact(f.options),/90 seconds/);assert.equal(f.time(),90000);assert.equal(f.calls(),18);
});
test('other run or attempt cannot satisfy readiness',async()=>{
  const f=fixture([{artifacts:[{...valid,name:'github-pages-12345-1'}]},{artifacts:[valid]}]);await waitForArtifact(f.options);assert.equal(f.calls(),2);
});
test('same name wrong id fails immediately',async()=>{
  const f=fixture([{artifacts:[{...valid,id:10}]}]);await assert.rejects(waitForArtifact(f.options),/ID differs/);assert.equal(f.calls(),1);
});
test('duplicate name fails immediately',async()=>{
  const f=fixture([{artifacts:[valid,valid]}]);await assert.rejects(waitForArtifact(f.options),/Multiple/);assert.equal(f.calls(),1);
});
test('invalid and empty sizes cannot pass',async()=>{
  for(const size of [0,-1,NaN,undefined,'2048'])await assert.rejects(waitForArtifact(fixture([{artifacts:[{...valid,size}]}]).options),/size/);
});
test('malformed response fails closed',async()=>{
  await assert.rejects(waitForArtifact(fixture([{}]).options),/Invalid artifact/);
});
test('service error not blindly retried',async()=>{
  const f=fixture([new Error('503')]);await assert.rejects(waitForArtifact(f.options));assert.equal(f.calls(),1);
});
test('bad expected identity never queries service',async()=>{
  for(const override of [{name:'github-pages'},{id:''},{id:'NaN'}]){
    const f=fixture([]);await assert.rejects(waitForArtifact({...f.options,...override}),/identity/);assert.equal(f.calls(),0);
  }
});
test('late response cannot pass deadline',async()=>{
  const f=fixture([]);f.options.list=async()=>{await f.options.sleep(90001);return {artifacts:[valid]};};await assert.rejects(waitForArtifact(f.options),/90 seconds/);
});
test('workflow has one upload then readiness then one deploy',()=>{
  const y=fs.readFileSync(path.join(__dirname,'../.github/workflows/rosavio-pages.yml'),'utf8');
  assert.equal(y.match(/uses: actions\/upload-pages-artifact/g).length,1);assert.equal(y.match(/uses: actions\/deploy-pages/g).length,1);
  assert.ok(y.indexOf('id: pages-upload')<y.indexOf('uses: ./.github/actions/wait-pages-artifact'));
  assert.ok(y.indexOf('uses: ./.github/actions/wait-pages-artifact')<y.indexOf('uses: actions/deploy-pages'));
  assert.ok(y.includes('steps.pages-upload.outputs.artifact_id'));assert.ok(y.includes('cancel-in-progress: false'));
});
