const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
test('toolbar opens sidebar; queues survive sidebar reopening and are isolated by window',async()=>{
  let click,removed,opened=0;const frames=[];
  const document={createElement:()=>{const frame={contentWindow:{},addEventListener(name,fn){this.load=fn;},remove(){this.removed=true;}};return frame;},body:{append(frame){frames.push(frame);frame.load();}}};
  const browser={browserAction:{onClicked:{addListener(fn){click=fn;}}},sidebarAction:{open(){opened++;}},windows:{onRemoved:{addListener(fn){removed=fn;}}}};
  const ctx=vm.createContext({browser,document});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../media/background.js'),'utf8'),ctx);
  click();assert.equal(opened,1);
  const first=await ctx.getQueue(1);
  const repeated=await Promise.all(Array.from({length:35},()=>ctx.getQueue(1)));
  assert.ok(repeated.every(x=>x===first));assert.equal(frames.length,1);
  assert.notEqual(await ctx.getQueue(2),first);
  removed(1);assert.equal(frames[0].removed,true);
  assert.notEqual(await ctx.getQueue(1),first);assert.equal(frames.length,3);
});
