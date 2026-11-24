const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const dir = process.env.VIDEO_FINDER_SOURCE || path.join(__dirname,'../media');
const base = 'https://video.example/a/';
function context(files, extra={}) {
  const ctx = vm.createContext({URL,Blob,Uint8Array,DataView,AbortController, mediaText:(key)=>JSON.parse(fs.readFileSync(path.join(dir,'_locales/de/messages.json'),'utf8'))[key].message, mediaError:(key,values={})=>new Error(JSON.parse(fs.readFileSync(path.join(dir,'_locales/de/messages.json'),'utf8'))[key].message.replace(/\{([a-z]+)\}/g,(t,k)=>values[k]??t)), ...extra});
  for (const file of files) vm.runInContext(fs.readFileSync(path.join(dir,file+'.js'),'utf8'),ctx,{filename:file+'.js'});
  return ctx;
}
const core=context(['time','hls','parts','periods']);
const master='#EXTM3U\n#EXT-X-STREAM-INF:RESOLUTION=1920x1080,BANDWIDTH=9000000\nlow.m3u8\n#EXT-X-STREAM-INF:CODECS="a,b",BANDWIDTH=8000000,RESOLUTION=3840x2160\nhigh.m3u8';
const list=(text)=>({base,lines:text.split('\n').filter(Boolean)});
test('master: relative URLs, quoted commas, 4K before 1080p despite lower bitrate',()=>{
  const v=core.variantsOf(list(master)); assert.equal(v.length,2);assert.equal(v[0].height,2160);assert.equal(v[0].url,base+'high.m3u8');assert.equal(v[1].rate,9000000);
});
test('unknown resolution uses bitrate; separate audio ignored',()=>{
  const v=core.variantsOf(list('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\na\n#EXT-X-STREAM-INF:BANDWIDTH=2\nb\n#EXT-X-STREAM-INF:AUDIO="ext",BANDWIDTH=20\nc'));
  assert.equal(v.length,2);assert.equal(v[0].url,base+'b');assert.equal(v[0].height,0);
});
const media=(duration)=>'#EXTM3U\n#EXTINF:'+duration+',\na.ts\n#EXT-X-ENDLIST';
test('fractional durations, 8-second clip, hour-long video, missing duration',()=>{
  assert.equal(core.formatDuration(core.mediaPlan(list(media('7.75'))).seconds),'0:08');
  assert.equal(core.formatDuration(3601),'1:00:01');assert.equal(core.formatDuration(754),'12:34');
  assert.ok(Number.isNaN(core.mediaPlan(list(media('invalid'))).seconds));
});
for (const [name, text, message] of [
 ['live',media(8).replace('#EXT-X-ENDLIST',''),/Ende/],
 ['encrypted',media(8)+'\n#EXT-X-KEY:METHOD=AES-128',/Verschlüsselte/],
 ['gap',media(8)+'\n#EXT-X-GAP',/fehlend/],
 ['preview',media(8)+'\n#EXT-X-I-FRAMES-ONLY',/Vorschaubilder/],
 ['missing segment',media(8).replace('a.ts',''),/Unvollständig/],
 ['nested master',master,/Verschachtelte/]
])test(name+' fails before downloading',()=>assert.throws(()=>core.mediaPlan(list(text)),message));
test('manifest errors and final redirected URL',async()=>{
  await assert.rejects(core.readList(base,async()=>new Response('',{status:404})),/404/);
  await assert.rejects(core.readList(base,async()=>new Response('html')),/HLS/);
  const m=await core.readList(base,async()=>({ok:true,url:base+'sub/list',text:async()=>master}));
  assert.equal(core.variantsOf(m)[0].url,base+'sub/high.m3u8');
});
function event(){ const set=new Set();return {addListener:f=>set.add(f),removeListener:f=>set.delete(f),emit:(...a)=>[...set].map(f=>f(...a))};}

test('three retries for a network error, no retry for 403, same byte range on each attempt',async()=>{
  const parts=context(['parts'],{setTimeout:fn=>setImmediate(fn),clearTimeout:clearImmediate});
  const part={url:base+'data',start:5,end:8};
  let count=0;
  await assert.rejects(parts.readPart(part,async(url,opts)=>{
    count++;assert.equal(opts.headers.Range,'bytes=5-8');throw new TypeError('offline');
  }),/offline/);
  assert.equal(count,4); count=0;
  await assert.rejects(parts.readPart(part,async()=>{count++;return new Response('',{status:403});}),/403/);
  assert.equal(count,1);
});
test('cancel during retry delay prevents another request',async()=>{
  const parts=context(['parts'],{setTimeout,clearTimeout});
  const c=new AbortController();let count=0;
  const task=parts.readPart({url:base},async()=>{count++;setImmediate(()=>c.abort());throw new TypeError('offline');},c.signal);
  await assert.rejects(task,{name:'AbortError'});assert.equal(count,1);
});
test('safe filenames retain actual quality and multipart suffix',()=>{
  const names=context(['filename']);
  assert.equal(names.videoFilename('Mein Video',2160,'','mp4'),'Mein Video – 2160p.mp4');
  assert.equal(names.videoFilename(' ../CON ',0,'-Teil-02','ts'),'_CON-Teil-02.ts');
  assert.equal(names.videoFilename('',0,'','mp4'),'Video.mp4');
});
