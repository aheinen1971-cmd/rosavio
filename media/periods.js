// Join compatible fragmented MP4 periods by continuing each track's decode timeline.
function joinPeriods(periods) {
  if (periods.length < 2 || periods.some(p=>!p.init)) return null;
  const first = periods[0].init;
  if (!periods.every(p=>p.init.length===first.length && p.init.every((v,i)=>v===first[i]))) return null;
  const ends = new Map(), output = [first];
  function boxes(view, start, end) {
    const found = [];
    for (let i=start; i<end;) {
      const size=view.getUint32(i);
      if (size<8 || size>end-i) throw Error('box');
      const type=String.fromCharCode(...new Uint8Array(view.buffer,view.byteOffset+i+4,4));
      found.push({type,at:i+8,end:i+size});
      i+=size;
    }
    return found;
  }
  function children(v,b,type) {return boxes(v,b.at,b.end).filter(x=>x.type===type);}
  const view=b=>new DataView(b.buffer,b.byteOffset,b.byteLength);
  try {
    const init=view(first), moov=boxes(init,0,first.length).find(b=>b.type==='moov');
    const defaults=new Map();
    for (const mvex of children(init,moov,'mvex')) for (const b of children(init,mvex,'trex'))
      defaults.set(init.getUint32(b.at+4),init.getUint32(b.at+12));
    for (const [periodIndex,period] of periods.entries()) {
      const shifts=new Map();
      for (const original of period.media) {
        const bytes=original.slice(), v=view(bytes);
        const top=boxes(v,0,bytes.length);
        if (!top.some(b=>b.type==='moof') || !top.some(b=>b.type==='mdat')) return null;
        for (const moof of top.filter(b=>b.type==='moof')) for (const traf of children(v,moof,'traf')) {
          const [h]=children(v,traf,'tfhd'), [t]=children(v,traf,'tfdt');
          const flags=v.getUint32(h.at)&0xffffff, track=v.getUint32(h.at+4);
          if (flags&1 || !(flags&0x020000)) return null;
          let cursor=h.at+8+(flags&2?4:0);
          const def=flags&8?v.getUint32(cursor):defaults.get(track);
          const wide=v.getUint8(t.at)===1, pos=t.at+4;
          const time=wide?v.getBigUint64(pos):BigInt(v.getUint32(pos));
          if (!shifts.has(track)) shifts.set(track,periodIndex && ends.has(track)?ends.get(track)-time:0n);
          const adjusted=time+shifts.get(track);
          if (adjusted<0n || (!wide && adjusted>0xffffffffn)) return null;
          if(wide)v.setBigUint64(pos,adjusted);else v.setUint32(pos,Number(adjusted));
          let duration=0n;
          for (const r of children(v,traf,'trun')) {
            const f=v.getUint32(r.at)&0xffffff, count=v.getUint32(r.at+4);
            if(count>1000000)return null;
            let p=r.at+8+(f&1?4:0)+(f&4?4:0);
            const stride=[0x100,0x200,0x400,0x800].filter(bit=>f&bit).length*4;
            if(p+count*stride>r.end)return null;
            if(!(f&0x100)){if(!def)return null;duration+=BigInt(count)*BigInt(def);}
            else for(let i=0;i<count;i++,p+=stride)duration+=BigInt(v.getUint32(p));
          }
          if(!duration)return null;
          ends.set(track,adjusted+duration);
        }
        // Fragment indexes describe the old period offsets and durations.
        for(const b of top)if(!['sidx','mfra'].includes(b.type))output.push(bytes.subarray(b.at-8,b.end));
      }
    }
    return {blob:new Blob(output,{type:'video/mp4'}),ext:'mp4'};
  } catch {return null;}
}
