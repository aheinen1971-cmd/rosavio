const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
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
