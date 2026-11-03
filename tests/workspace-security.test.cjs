const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function setup(){
 let disk=null,writes=0,isPrivate=false;
 const source=fs.readFileSync(path.join(__dirname,'../scripts/rosavio-pages/RosavioWorkspaceParent.sys.mjs'),'utf8').replace(/^import .*;$/m,'').replace('export class','class')+'\nglobalThis.Actor=RosavioWorkspaceParent;';
 const context={URL,JSWindowActorParent:class{},PrivateBrowsingUtils:{isWindowPrivate:()=>isPrivate},PathUtils:{profileDir:'/isolated-test',join:(...p)=>p.join('/')},IOUtils:{exists:async()=>disk!==null,stat:async()=>({size:JSON.stringify(disk).length}),readJSON:async()=>JSON.parse(JSON.stringify(disk)),writeJSON:async(file,data,options)=>{assert.equal(file,'/isolated-test/rosavio-workspace.json');assert.equal(options.backupFile,file+'.bak');disk=JSON.parse(JSON.stringify(data));writes++;}}};
 vm.createContext(context);vm.runInContext(source,context);
 const a=new context.Actor();a.manager={documentURI:{spec:'about:rosavio-notes'}};a.browsingContext={parent:null,top:{embedderElement:{documentGlobal:{}}}};
 return {a,get disk(){return disk},get writes(){return writes},private(){isPrivate=true}};
}
test('untrusted origin, subframe and unknown messages cannot read or write',()=>{
 const t=setup();t.a.manager.documentURI.spec='https://example.com';assert.throws(()=>t.a.receiveMessage({name:'RosavioWorkspace:Read'}));
 t.a.manager.documentURI.spec='about:rosavio-notes';t.a.browsingContext.parent={};assert.throws(()=>t.a.receiveMessage({name:'RosavioWorkspace:Read'}));
 t.a.browsingContext.parent=null;assert.throws(()=>t.a.receiveMessage({name:'ReadArbitraryFile',data:{path:'/secret'}}));assert.equal(t.writes,0);
});
test('private windows cannot access persistent workspace',()=>{const t=setup();t.private();assert.throws(()=>t.a.receiveMessage({name:'RosavioWorkspace:Read'}));assert.throws(()=>t.a.receiveMessage({name:'RosavioWorkspace:Save'}));assert.equal(t.writes,0);});
test('only bounded plain text and HTTP(S) links are persisted',async()=>{
 const t=setup();
 for(const data of [
  {revision:0,notes:'',links:[{title:'bad',url:'javascript:alert(1)'}]},
  {revision:0,notes:'',links:[{title:'bad',url:'file:///secret'}]},
  {revision:0,notes:'',links:[{title:'bad',url:'https://user:password@example.com'}]},
  {revision:0,notes:'x'.repeat(100001),links:[]},
  {revision:0,notes:'',links:[],path:'/outside'},
 ])await assert.rejects(t.a.receiveMessage({name:'RosavioWorkspace:Save',data}));
 assert.equal(t.writes,0);
 await t.a.receiveMessage({name:'RosavioWorkspace:Save',data:{revision:0,notes:'<script>plain text 🌹</script>',links:[{title:'Example',url:'https://example.com'}]}});
 assert.equal(t.disk.notes,'<script>plain text 🌹</script>');assert.equal(t.disk.links[0].url,'https://example.com/');assert.equal(t.writes,1);
});
test('concurrent stale edits cannot silently overwrite newer notes',async()=>{
 const t=setup(),save=notes=>t.a.receiveMessage({name:'RosavioWorkspace:Save',data:{revision:0,notes,links:[]}});
 const results=await Promise.allSettled([save('first'),save('second')]);
 assert.equal(results[0].status,'fulfilled');assert.equal(results[1].status,'rejected');assert.equal(t.disk.notes,'first');assert.equal(t.writes,1);
});
