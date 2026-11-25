const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const patch=fs.readFileSync(path.join(__dirname,'../scripts/prepare-video-finder.py'),'utf8').match(/\nREPLACEMENT='''([\s\S]*?)'''/)[1];
test('reserved host accepts only the privileged built-in archive, never user hosts',async()=>{
 const canonical='jar:file:///fixture/browser/omni.ja!/chrome/browser/builtin-addons/rosavio-media/';
 let fallback=0,parsed=0;
 const context=vm.createContext({Services:{io:{getProtocolHandler:()=>({QueryInterface(){return this;},resolveURI:()=>canonical}),newURI:x=>x},dirsvc:{get:()=>({path:'/fixture'})}},Ci:{nsIResProtocolHandler:{},nsIFile:{}},PathUtils:{join:(...x)=>x.join('/')},AppConstants:{platform:'linux'},IOUtils:{exists:async()=>true}});
 const lookup=vm.runInContext('({'+patch+'})',context);
 lookup.init=async()=>{};lookup._lookup=()=>{fallback++;return 'normal';};lookup.parseManifest=async(type,path,name,ctx,data)=>{parsed++;return data;};
 const valid={extension:{id:'medien@rosavio.local',isPrivileged:true,rootURI:{spec:canonical}}};
 for(const extension of [{...valid.extension,id:'other'},{...valid.extension,isPrivileged:false},{...valid.extension,rootURI:{spec:'file:///foreign/'}},{...valid.extension,rootURI:{spec:'resource://builtin-addons/rosavio-media/'}}]){
  assert.equal(await lookup.lookupManifest('stdio','org.rosavio.video_finder',{extension}),null);
 }
 assert.equal(await lookup.lookupManifest('storage','org.rosavio.video_finder',valid),null);
 assert.equal(fallback,0);assert.equal(parsed,0);
 const accepted=await lookup.lookupManifest('stdio','org.rosavio.video_finder',valid);
 assert.equal(accepted.manifest.path,'/fixture/video-finder/video-finder-host');assert.equal(parsed,1);
 assert.equal(await lookup.lookupManifest('stdio','another_host',valid),'normal');assert.equal(fallback,1);
});
