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
  row.querySelector('h2').textContent = videoTitle || new URL(mediaURL).pathname.split('/').pop() || 'Video';
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
      else reject(new Error('Speichern unterbrochen.'));
    }
    function changed(delta) {
      if (delta.id === id) finish(delta.state?.current);
    }
    browser.downloads.onChanged.addListener(changed);
    browser.downloads.search({id}).then(([file]) => finish(file?.state ?? 'interrupted'), () => finish('interrupted'));
  });
}

function setupDownload(row, mediaURL, videoTitle) {
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
    addDownload(mediaURL, videoTitle);
  };
  let plan, selection = 0;
  const heights = new Map();

  const load = (url, options) => fetch(url, {...options, signal:controller.signal});

  function failed(error) {
    restart.hidden = false;
    statusLine.textContent = controller.signal.aborted ? 'Download abgebrochen.' : 'Download nicht möglich. '+error.message;
  }
  controller.signal.addEventListener('abort', () => {
    selection++;
    plan = null;
    save.hidden = cancel.hidden = choices.hidden = true;
    restart.hidden = false;
    statusLine.textContent = 'Download abgebrochen.';
  });
  async function showPlan(getList, audioURL) {
    const current = ++selection;
    restart.hidden = true;
    plan = null;
    save.disabled = true;
    save.hidden = true;
    statusLine.textContent = 'Dauer wird ermittelt …';
    try {
      const next = mediaPlan(await getList());
      if (audioURL) next.audioURL = audioURL;
      if (current !== selection) return;
      plan = next;
      save.dataset.audioOrigin = audioURL && new URL(audioURL).origin !== new URL(mediaURL).origin ? new URL(audioURL).origin : '';
      statusLine.textContent = Number.isFinite(plan.seconds) ? 'Videolänge: '+formatDuration(plan.seconds) : 'Videolänge unbekannt.';
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
        const size = v.height ? v.height+'p'+(v.height === 2160 ? ' (4K)' : '') : 'Auflösung unbekannt';
        const rate = v.rate ? ' · '+(v.rate/1000000).toLocaleString('de-DE')+' Mbit/s' : '';
        heights.set(v.url,v.height);
        quality.add(new Option((index === 0 ? 'Beste verfügbare · ' : '') + size + rate, v.url));
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
    quality.disabled = true;
    statusLine.textContent = 'Wartet auf Download …';
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
        const size = (bytes/1000000).toLocaleString('de-DE',{maximumFractionDigits:1});
        statusLine.textContent = percent+' % · '+done+' von '+total+' Abschnitten · '+size+' MB geladen';
      }
      let result = await assembleSections(plan.sections, progress, load, controller.signal);
      if (audioPlan) {
        const sound = await assembleSections(audioPlan.sections, progress, load, controller.signal);
        if (result.length !== 1 || sound.length !== 1) throw Error('Die getrennten Spuren enthalten inkompatible Formatwechsel.');
        statusLine.textContent = 'Bild und Ton werden zusammengefügt.';
        const {mergeTracks} = await import('./merge.mjs');
        result = [await mergeTracks(result[0].blob, sound[0].blob, controller.signal)];
      }
      cancel.hidden = true;
      bar.hidden = true;
      let submitted = 0;
      for (const [index,file] of result.entries()) {
        const url = URL.createObjectURL(file.blob);
        const suffix = result.length > 1 ? '-Teil-'+String(index+1).padStart(2,'0') : '';
        const filename = videoFilename(videoTitle, heights.get(quality.value), suffix, file.ext);
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
          link.textContent = filename+' manuell speichern';
          const row = document.createElement('p');
          row.append(link);
          files.append(row);
        }
      }
      if (submitted === result.length) {
        statusLine.textContent = submitted === 1 ? 'Video im Downloadordner gespeichert.' : submitted+' Teile im Downloadordner gespeichert.';
      } else {
        statusLine.textContent = submitted+' von '+result.length+' Dateien gespeichert. Für die übrigen Dateien findest du hier einen Speicherlink.';
      }
    }catch(error){statusLine.textContent=controller.signal.aborted ? 'Download abgebrochen.' : 'Download nicht möglich. '+error.message;}
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
      status.textContent = file?.state === 'complete' ? 'Im Downloadordner gespeichert.' : 'Download unterbrochen.';
      return;
    }
    if (file.totalBytes > 0) {
      progress.max = file.totalBytes;
      progress.value = file.bytesReceived;
    }
    status.textContent = (file.bytesReceived / 1000000).toFixed(1) + ' MB geladen';
    await new Promise(resolve => setTimeout(resolve, 500));
  }
}
