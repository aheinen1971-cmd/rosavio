const jobs = new Map();
let tail = Promise.resolve();

function enqueue(signal, download) {
  const task = tail.then(() => {
    if (!signal.aborted) return download();
  });
  tail = task.catch(() => {});
  return task;
}

function addDownload(mediaURL, videoTitle) {
  let row = jobs.get(mediaURL);
  if (row) {
    row.focus();
    return;
  }
  row = document.querySelector('template').content.firstElementChild.cloneNode(true);
  row.querySelector('h2').textContent = videoTitle || new URL(mediaURL).pathname.split('/').pop() || mediaText('video');
  jobs.set(mediaURL, row);
  document.querySelector('main').append(row);
  setupDownload(row, mediaURL, videoTitle);
}

function waitForFile(id) {
  return new Promise((resolve,reject) => {
    function finish(state) {
      if (state !== 'complete' && state !== 'interrupted') return;
      browser.downloads.onChanged.removeListener(changed);
      if (state === 'complete') resolve();
      else reject(mediaError('interrupted'));
    }
    function changed(delta) {
      if (delta.id === id) finish(delta.state?.current);
    }
    browser.downloads.onChanged.addListener(changed);
    browser.downloads.search({id}).then(([file]) => finish(file?.state ?? 'interrupted'), () => finish('interrupted'));
  });
}

function setupDownload(row, mediaURL, videoTitle) {
  const name = row.querySelector('.filename-title');
  name.value = videoTitle || mediaText('video');
  let downloadTitle = name.value;
  const statusLine=row.querySelector('.status');
  const bar=row.querySelector('progress');
  const files=row.querySelector('.files');
  const cancel = row.querySelector('.cancel');
  const controller = new AbortController();
  cancel.onclick = () => {
    cancel.disabled = true;
    controller.abort();
  };
  const quality = row.querySelector('.quality');
  const choices = row.querySelector('.choices');
  const save = row.querySelector('.save');
  const restart = row.querySelector('.restart');
  const manualURLs = [];
  restart.onclick = () => {
    controller.abort();
    for (const url of manualURLs) URL.revokeObjectURL(url);
    jobs.delete(mediaURL);
    row.remove();
    addDownload(mediaURL, name.value.trim() || videoTitle);
  };
  let plan, selection = 0;
  const heights = new Map();

  const load = (url, options) => fetch(url, {...options, signal:controller.signal});

  function failed(error) {
    restart.hidden = false;
    statusLine.textContent = controller.signal.aborted ? mediaText('cancelled') : mediaText('failed', {error:mediaErrorText(error)});
  }
  controller.signal.addEventListener('abort', () => {
    selection++;
    plan = null;
    save.hidden = cancel.hidden = choices.hidden = true;
    restart.hidden = false;
    statusLine.textContent = mediaText('cancelled');
  });
  async function showPlan(getList, audioURL) {
    const current = ++selection;
    restart.hidden = true;
    plan = null;
    save.disabled = true;
    save.hidden = true;
    statusLine.textContent = mediaText('durationLoading');
    try {
      const next = mediaPlan(await getList());
      if (audioURL) next.audioURL = audioURL;
      if (current !== selection) return;
      plan = next;
      save.dataset.audioOrigin = audioURL && new URL(audioURL).origin !== new URL(mediaURL).origin ? new URL(audioURL).origin : '';
      statusLine.textContent = Number.isFinite(plan.seconds) ? mediaText('duration', {duration:formatDuration(plan.seconds)}) : mediaText('durationUnknown');
      save.hidden = save.disabled = false;
    } catch (error) { if (current === selection) failed(error); }
  }
  async function prepare() {
    try {
      const first = await readList(mediaURL, load);
      if (controller.signal.aborted) return;
      const variants = variantsOf(first);
      if (!variants.length) return showPlan(() => first);
      for (const [index,v] of variants.entries()) {
        const size = v.height ? v.height+'p'+(v.height === 2160 ? ' (4K)' : '') : mediaText('resolutionUnknown');
        const rate = v.rate ? ' · '+mediaNumber(v.rate/1000000)+' Mbit/s' : '';
        heights.set(v.url,v.height);
        quality.add(new Option((index === 0 ? mediaText('best') : '') + size + rate, v.url));
      }
      choices.hidden = false;
      quality.onchange = () => {
        const variant = variants[quality.selectedIndex];
        return showPlan(() => readList(variant.url,load), variant.audioURL);
      };
      await quality.onchange();
    } catch (error) { failed(error); }
  }
  save.onclick = async () => {
    if (!plan || save.disabled || controller.signal.aborted) return;
    save.disabled = save.hidden = true;
    downloadTitle = name.value.trim() || videoTitle || mediaText('video');
    name.disabled = true;
    quality.disabled = true;
    statusLine.textContent = mediaText('waiting');
    return enqueue(controller.signal, download);
  };
  async function download() {
    try {
      const audioPlan = plan.audioURL ? mediaPlan(await readList(plan.audioURL,load)) : null;
      function progress(done,total,bytes) {
        bar.hidden = false;
        bar.max = total;
        bar.value = done;
        const percent = Math.floor(100*done/total);
        const size = mediaNumber(bytes/1000000,{maximumFractionDigits:1});
        statusLine.textContent = mediaText('progress', {percent:mediaNumber(percent),done:mediaNumber(done),total:mediaNumber(total),size});
      }
      let result = await assembleSections(plan.sections, progress, load, controller.signal);
      if (audioPlan) {
        const sound = await assembleSections(audioPlan.sections, progress, load, controller.signal);
        if (result.length !== 1 || sound.length !== 1) throw mediaError('trackFormat');
        statusLine.textContent = mediaText('merging');
        const {mergeTracks} = await import('./merge.mjs');
        result = [await mergeTracks(result[0].blob, sound[0].blob, controller.signal)];
      }
      cancel.hidden = true;
      bar.hidden = true;
      let submitted = 0;
      for (const [index,file] of result.entries()) {
        const url = URL.createObjectURL(file.blob);
        const suffix = result.length > 1 ? '-'+mediaText('part')+'-'+String(index+1).padStart(2,'0') : '';
        const filename = videoFilename(downloadTitle, heights.get(quality.value), suffix, file.ext);
        try {
          const id = await browser.downloads.download({url,filename,saveAs:false,conflictAction:'uniquify'});
          await waitForFile(id);
          submitted++;
          URL.revokeObjectURL(url);
        } catch {
          manualURLs.push(url);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          link.textContent = mediaText('manual', {name:filename});
          const row = document.createElement('p');
          row.append(link);
          files.append(row);
        }
      }
      if (submitted === result.length) {
        statusLine.textContent = submitted === 1 ? mediaText('saved') : mediaText('partsSaved', {count:mediaNumber(submitted)});
      } else {
        statusLine.textContent = mediaText('partialSaved', {done:mediaNumber(submitted),total:mediaNumber(result.length)});
      }
    }catch(error){statusLine.textContent=controller.signal.aborted ? mediaText('cancelled') : mediaText('failed', {error:mediaErrorText(error)});}
    finally{bar.hidden=true; cancel.hidden=true; restart.hidden=false;}
  }
  prepare();
}

async function trackDirect(id, title) {
  const row = document.createElement('section');
  const heading = document.createElement('h2');
  const progress = document.createElement('progress');
  const status = document.createElement('p');
  heading.textContent = title;
  row.append(heading, progress, status);
  document.querySelector('main').append(row);
  for (;;) {
    const [file] = await browser.downloads.search({id});
    if (!file || file.state !== 'in_progress') {
      progress.hidden = true;
      status.textContent = file?.state === 'complete' ? mediaText('saved') : mediaText('interrupted');
      return;
    }
    if (file.totalBytes > 0) {
      progress.max = file.totalBytes;
      progress.value = file.bytesReceived;
    }
    status.textContent = mediaText('loaded', {size:mediaNumber(file.bytesReceived/1000000,{minimumFractionDigits:1,maximumFractionDigits:1})});
    await new Promise(resolve => setTimeout(resolve, 500));
  }
}
