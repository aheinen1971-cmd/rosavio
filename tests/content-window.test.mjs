import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const select=require('../scripts/select-test-content.cjs');
test('rebinds exactly the selected live content tab, without arbitrary first-window fallback',async()=>{
 const calls=[];const s={command:async(n,a)=>calls.push([n,a]),script:async code=>{assert.match(code,/delayedStartupPromise/);assert.match(code,/isDiscarded/);assert.match(code,/getIdForBrowser\(browser\)/);return 'selected-tab';}};
 assert.equal(await select(s),'selected-tab');
 assert.deepEqual(calls,[['Marionette:SetContext',{value:'chrome'}],['Marionette:SetContext',{value:'content'}],['WebDriver:SwitchToWindow',{handle:'selected-tab'}]]);
});
test('missing or failed selected tab cannot silently pass',async()=>{
 for(const value of [null,undefined,'',{error:'closed'}]){let switches=0;await assert.rejects(select({script:async()=>value,command:async n=>{if(n==='WebDriver:SwitchToWindow')switches++;}}),/Cannot identify/);assert.equal(switches,0);}
});
test('window closure and session errors propagate without retry',async()=>{
 let count=0;await assert.rejects(select({script:async()=>'gone',command:async n=>{if(n==='WebDriver:SwitchToWindow'){count++;throw Error('no such window');}}}),/no such window/);assert.equal(count,1);
});
test('startup or chrome inspection failure is not converted into a replacement tab',async()=>{
 const calls=[];await assert.rejects(select({script:async()=>{throw Error('browser crashed');},command:async n=>calls.push(n)}),/browser crashed/);
 assert.deepEqual(calls,['Marionette:SetContext']);
});
