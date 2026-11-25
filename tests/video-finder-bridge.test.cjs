const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
for(const locale of require('../scripts/requested-languages.json').locales)test('YouTube sidebar states in '+locale,async()=>{
 const messages=JSON.parse(fs.readFileSync(path.join(__dirname,'../media/_locales',locale.replaceAll('-','_'),'messages.json'),'utf8'));
 const nodes=new Map();
 const node=()=>({hidden:false,disabled:false,textContent:'',value:'',removeAttribute(k){delete this[k];},replaceChildren(...children){this.children=children;}});
 const document={querySelector(id){if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);},createElement:node};
 let update;const calls=[];
 const controller={subscribe(fn){update=fn;fn({phase:'idle',busy:false,choices:[]});return()=>{};},inspect(url){calls.push(url);},download(){},cancel(){}};
 const events={addListener(){},removeListener(){}};
 const browser={runtime:{async getBackgroundPage(){return {getYouTubeController:()=>controller,videoFinderYouTubeURL:()=> 'https://www.youtube.com/watch?v=aqz-KE-bpKQ'};}},windows:{async getCurrent(){return {id:1};}},tabs:{async query(){return [{url:'https://youtu.be/aqz-KE-bpKQ'}];},onActivated:events,onUpdated:events}};
 const ctx=vm.createContext({browser,document,window:{addEventListener(){}},mediaNumber:v=>new Intl.NumberFormat(locale).format(v),mediaText:(key,args={})=>{
  assert.ok(messages[key],key);return messages[key].message.replace(/\{(\w+)\}/g,(_,k)=>args[k]||'');
 }});
 await vm.runInContext(fs.readFileSync(path.join(__dirname,'../media/youtube-sidebar.js'),'utf8'),ctx);
 assert.equal(calls.length,0);nodes.get('#youtube-detect').onclick();assert.equal(calls.length,1);
 for(const [phase,key] of Object.entries({inspecting:'youtubeInspecting',detected:'youtubeDetected',processing:'youtubeProcessing',cancelled:'youtubeCancelled',cleanup:'youtubeCleanup'})){
  update({phase,busy:phase==='inspecting',choices:[]});assert.equal(nodes.get('#youtube-status').textContent,messages[key].message);
 }
 update({phase:'saved',busy:false,choices:[],path:'<unsafe&name>.mkv'});
 assert.ok(nodes.get('#youtube-status').textContent.includes('<unsafe&name>.mkv'));
 update({phase:'error',busy:false,choices:[],code:'unknown'});
 assert.equal(nodes.get('#youtube-status').textContent,messages.youtubeFailed.message);
});
function fixture(){
 const ports=[];let removed;
 const browser={windows:{onRemoved:{addListener(fn){removed=fn;}}},runtime:{connectNative(name){
  assert.equal(name,'org.rosavio.video_finder');
  const p={sent:[],onMessage:{addListener(fn){p.receive=fn;}},onDisconnect:{addListener(fn){p.disconnected=fn;}},
   postMessage(m){p.sent.push(m);},disconnect(){p.closed=true;p.disconnected();}};
  ports.push(p);return p;
 }}};
 const ctx=vm.createContext({browser,URL});
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../media/youtube-background.js'),'utf8'),ctx);
 return {ctx,ports,remove:id=>removed(id)};
}
test('only exact HTTPS YouTube video URLs; no credentials or foreign origins',()=>{
 const {ctx}=fixture();
 for(const url of ['http://youtube.com/watch?v=aqz-KE-bpKQ','https://youtube.com.evil/watch?v=aqz-KE-bpKQ','https://x@youtube.com/watch?v=aqz-KE-bpKQ','https://youtube.com/playlist?list=x'])assert.equal(ctx.videoFinderYouTubeURL(url),null);
 assert.equal(ctx.videoFinderYouTubeURL('https://youtu.be/aqz-KE-bpKQ'),'https://www.youtube.com/watch?v=aqz-KE-bpKQ');
});
test('no automatic native connection; explicit detection, quality allowlist and duplicate guard',()=>{
 const {ctx,ports}=fixture();const c=ctx.getYouTubeController(1);let state;c.subscribe(s=>state=s);
 assert.equal(ports.length,0);c.inspect('https://youtu.be/aqz-KE-bpKQ');assert.equal(ports.length,1);
 assert.equal(c.inspect('https://youtu.be/aqz-KE-bpKQ'),false);
 ports[0].receive({type:'info',title:'<script>not HTML</script>',choices:[{selector:'18',height:360,merged:false}]});
 ports[0].receive({type:'idle'});assert.equal(state.title,'<script>not HTML</script>');
 assert.equal(c.download('--exec'),false);assert.equal(c.download('18'),true);
 assert.equal(ports[0].sent.at(-1).selector,'18');assert.equal(c.download('18'),false);
 c.cancel();assert.equal(ports[0].sent.at(-1).action,'cancel');
});
test('sidebar reopening preserves job, window close disconnects only its own helper',()=>{
 const {ctx,ports,remove}=fixture();const a=ctx.getYouTubeController(1),b=ctx.getYouTubeController(2);
 a.inspect('https://youtu.be/aqz-KE-bpKQ');b.inspect('https://youtu.be/aqz-KE-bpKQ');
 assert.equal(ctx.getYouTubeController(1),a);let updates=0;const off=a.subscribe(()=>updates++);off();
 ports[0].receive({type:'progress',percent:15,phase:'downloading'});assert.equal(updates,1);
 remove(1);assert.ok(ports[0].closed);assert.ok(!ports[1].closed);
});
test('lost helper clears busy, late success is not replaced by cancel-request status',()=>{
 const {ctx,ports}=fixture();const c=ctx.getYouTubeController(1);let state;c.subscribe(s=>state=s);
 c.inspect('https://youtu.be/aqz-KE-bpKQ');ports[0].receive({type:'saved',path:'fixture'});c.cancel();assert.equal(state.phase,'saved');
 ports[0].error={message:'missing'};ports[0].disconnected();assert.equal(state.busy,false);assert.equal(state.code,'youtubeHelperUnavailable');
});
