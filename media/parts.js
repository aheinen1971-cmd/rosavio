function parsePart(line, rawRange, base, previous) {
  const url = httpUrl(line, base);
  if (rawRange === null) return {url};
  const match = /^(\d+)(?:@(\d+))?$/.exec(rawRange);
  if (!match) throw mediaError('rangeInvalid');
  const length = Number(match[1]);
  const start = match[2] === undefined
    ? (previous?.url === url && previous.end !== undefined ? previous.end + 1 : NaN)
    : Number(match[2]);
  const end = start + length - 1;
  if (length < 1 || !Number.isSafeInteger(start) || start < 0 || !Number.isSafeInteger(end))
    throw mediaError('rangeStart');
  return {url,start,end};
}

function parseMedia(lines, base) {
  if (lines.includes('#EXT-X-I-FRAMES-ONLY')) throw mediaError('preview');
  if (lines.includes('#EXT-X-GAP')) throw mediaError('gap');
  const sections = [];
  let section, init = null, range = null, previous, previousMap, pending = false;
  for (const line of lines) {
    if (line === '#EXT-X-DISCONTINUITY') section = null;
    else if (line.startsWith('#EXT-X-MAP:')) {
      const uri = line.match(/[:,]URI="([^"]+)"/);
      if (!uri) throw mediaError('noInit');
      const spec = line.match(/,BYTERANGE="([^"]+)"/);
      const next = parsePart(uri[1], spec?.[1] ?? null, base, previousMap);
      if (JSON.stringify(next) !== JSON.stringify(init)) section = null;
      previousMap = init = next;
    } else if (line.startsWith('#EXT-X-BYTERANGE:')) range = line.slice(line.indexOf(':')+1);
    else if (line.startsWith('#EXTINF:')) {
      if (pending) throw mediaError('incomplete');
      pending = true;
    } else if (!line.startsWith('#')) {
      if (!pending) throw mediaError('noTime');
      if (!section) { section = {init,media:[]}; sections.push(section); }
      previous = parsePart(line,range,base,previous);
      section.media.push(previous);
      range = null;
      pending = false;
    }
  }
  if (pending || range !== null || !sections.length) throw mediaError('incomplete');
  return sections;
}

async function readPartOnce(part, load) {
  const ranged = part.start !== undefined;
  const res = await load(part.url, ranged ? {headers:{Range:'bytes='+part.start+'-'+part.end}} : {});
  if (!res.ok) {
    const error = mediaError('serverHttp', {status:res.status});
    error.retryable = [408,429,500,502,503,504].includes(res.status);
    await res.body?.cancel();
    throw error;
  }
  let bytes = new Uint8Array(await res.arrayBuffer());
  if (ranged) {
    if (res.status === 200) {
      if (bytes.length <= part.end) throw mediaError('rangeIncomplete');
      bytes = bytes.slice(part.start,part.end+1);
    } else {
      const hdr = res.headers.get('content-range');
      const match = hdr?.match(/^bytes (\d+)-(\d+)\/(?:\d+|\*)$/i);
      if (res.status !== 206 || (hdr && (!match || Number(match[1]) !== part.start || Number(match[2]) !== part.end)) || bytes.length !== part.end-part.start+1)
        throw mediaError('rangeMismatch');
    }
  }
  return bytes;
}

function retryDelay(ms, signal) {
  return new Promise((resolve,reject) => {
    signal?.throwIfAborted();
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', abort);
      resolve();
    },ms);
    function abort() {
      clearTimeout(timer);
      reject(signal.reason);
    }
    signal?.addEventListener('abort', abort, {once:true});
  });
}

async function readPart(part, load, signal) {
  for (let attempt = 0; ; attempt++) {
    signal?.throwIfAborted();
    try {
      return await readPartOnce(part, load);
    } catch (error) {
      const transient = error.retryable || error.name === 'TypeError' || error.name === 'NetworkError';
      if (!transient || attempt >= 3 || signal?.aborted) throw error;
      await retryDelay(500 * 2 ** attempt, signal);
    }
  }
}

async function assembleSections(sections, progress, load, signal) {
  const total = sections.reduce((sum,s)=>sum+s.media.length+(s.init ? 1 : 0),0);
  let index = 0, loadedBytes = 0;
  const files = []; const periods = [];
  for (const section of sections) {
    const buffers = [];
    const parts = section.init ? [section.init,...section.media] : section.media;
    for (const [i,part] of parts.entries()) {
      progress(index,total,loadedBytes);
      const bytes = await readPart(part,load,signal);
      const tag = String.fromCharCode(...bytes.subarray(4,8));
      const valid = section.init ? (i === 0 ? ['ftyp','moov'] : ['moof','styp','sidx','emsg','prft','free']).includes(tag) : bytes[0] === 0x47;
      if (!valid) throw mediaError('format');
      buffers.push(bytes);
      loadedBytes += bytes.byteLength;
      progress(++index,total,loadedBytes);
    }
    if (sections.length>1) periods.push({init:section.init ? buffers[0] : null,media:buffers.slice(1)});
    files.push({blob:new Blob(buffers,{type:section.init?'video/mp4':'video/mp2t'}),ext:section.init?'mp4':'ts'});
  }
  const joined=joinPeriods(periods);
  return joined ? [joined] : files;
}
