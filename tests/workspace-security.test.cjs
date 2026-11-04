const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function setup(){
 let disk=null,writes=0,isPrivate=false;
 const source=fs.readFileSync(path.join(__dirname,'../scripts/rosavio-pages/RosavioWorkspaceParent.sys.mjs'),'utf8').replace(/^import .*;$/m,'').replace('export class','class')+'\nglobalThis.Actor=RosavioWorkspaceParent;';
 const context={TextEncoder,URL,JSWindowActorParent:class{},PrivateBrowsingUtils:{isWindowPrivate:()=>isPrivate},PathUtils:{profileDir:'/isolated-test',join:(...p)=>p.join('/')},IOUtils:{exists:async()=>disk!==null,stat:async()=>({size:JSON.stringify(disk).length}),readJSON:async()=>JSON.parse(JSON.stringify(disk)),writeJSON:async(file,data,options)=>{assert.equal(file,'/isolated-test/rosavio-workspace.json');assert.equal(options.backupFile,file+'.bak');disk=JSON.parse(JSON.stringify(data));writes++;}}};
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
 await t.a.receiveMessage({name:'RosavioWorkspace:Save',data:{revision:0,notes:'<script>plain text ðŸŒ¹</script>',links:[{title:'Example',url:'https://example.com'}]}});
 assert.equal(t.disk.notes,'<script>plain text ðŸŒ¹</script>');assert.equal(t.disk.links[0].url,'https://example.com/');assert.equal(t.writes,1);
});
test('concurrent stale edits cannot silently overwrite newer notes',async()=>{
 const t=setup(),save=notes=>t.a.receiveMessage({name:'RosavioWorkspace:Save',data:{revision:0,notes,links:[]}});
 const results=await Promise.allSettled([save('first'),save('second')]);
 assert.equal(results[0].status,'fulfilled');assert.equal(results[1].status,'rejected');assert.equal(t.disk.notes,'first');assert.equal(t.writes,1);
});
test('reading places survive concurrent additions, reject stale saves and deduplicate exact entries',async()=>{
 const t=setup(),entry=n=>({url:'https://example.org/article#:~:text='+n,quote:'Zitat '+n});
 const add=p=>t.a.constructor.addPlace({},p);
 await t.a.receiveMessage({name:'RosavioWorkspace:Save',data:{notes:'Existing note',revision:0,links:[]}});
 const stale=t.disk;
 await Promise.all([add(entry('a')),add(entry('b')),add(entry('a'))]);
 assert.equal(t.disk.notes,stale.notes);assert.equal(t.disk.places.length,2);assert.equal(t.disk.revision,3);
 await assert.rejects(t.a.receiveMessage({name:'RosavioWorkspace:Save',data:stale}));
});
test('private windows, unsafe addresses and a full list cannot overwrite saved reading places',async()=>{
 const t=setup(),add=url=>t.a.constructor.addPlace({},{url,quote:'Ein Absatz'});
 for(const url of ['file:///private#:~:text=a','javascript:test#:~:text=a','https://user:secret@example.org/#:~:text=x','https://example.org/no-fragment'])assert.throws(()=>add(url));
 for(let i=0;i<30;i++)await add('https://example.org/#:~:text='+i);
 const disk=t.disk;await assert.rejects(add('https://example.org/#:~:text=overflow'));assert.deepEqual(t.disk,disk);
 t.private();assert.throws(()=>add('https://example.org/#:~:text=private'));assert.deepEqual(t.disk,disk);
});
