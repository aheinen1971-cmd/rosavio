const statusLine = document.querySelector('#status');
const list = document.querySelector('#list');
const more = document.querySelector('#more');
const alternatives = document.querySelector('#alternatives');
const scanButton = document.querySelector('#scan');

function findVideos() {
  const found = new Map();
  let playingWithoutSource = false;
  const pattern = /\.(mp4|m4v|webm|mov|ogv)$/i;
  function add(raw, playerSource, playing = false, seconds, title, height) {
    if (!raw) return;
    let url;
    try { url = new URL(raw, document.baseURI); } catch { return; }
    if (!['http:', 'https:'].includes(url.protocol)) return;
    const playlist = /\.m3u8$/i.test(url.pathname);
    const fragment = /(?:_h26[45]_init_|^mrg_.*_h26[45]_\d+_)/i.test(url.pathname.split('/').pop());
    if (/\.(mpd|m4s|ts)$/i.test(url.pathname)) return;
    if (!playerSource && !playlist && !pattern.test(url.pathname)) return;
    const previous = found.get(url.href);
    found.set(url.href, {
      url: url.href, playlist, fragment,
      title: title || previous?.title || document.title,
      height: height || previous?.height,
      seconds: Number.isFinite(seconds) && seconds > 0 ? seconds : previous?.seconds,
      name: url.pathname.split('/').pop() || 'Video',
      playing: playing || Boolean(previous?.playing)
    });
  }
  for (const video of document.querySelectorAll('video')) {
    const rect = video.getBoundingClientRect();
    const visible = Math.min(rect.right, innerWidth) > Math.max(rect.left, 0)
      && Math.min(rect.bottom, innerHeight) > Math.max(rect.top, 0);
    const active = visible && !video.paused && !video.ended && video.readyState >= 2;
    if (active && !/^https?:/i.test(video.currentSrc)) playingWithoutSource = true;
    add(video.currentSrc, true, active, video.duration, video.title, video.videoHeight);
    add(video.src, true);
    for (const source of video.querySelectorAll('source[src]')) {
      if (!/dash\+xml/i.test(source.type)) add(source.src, true);
    }
  }
  for (const link of document.querySelectorAll('a[href]')) add(link.href, false);
  for (const entry of performance.getEntriesByType('resource')) add(entry.name, false);
  return {videos:[...found.values()], playingWithoutSource};
}

function requestServer(origin) {
  const server = new URL(origin);
  const permission = {origins:[server.protocol + '//' + server.hostname + '/*']};
  // Request during the click. Firefox may already grant access through a site permission.
  return browser.permissions.request(permission).catch(() => browser.permissions.contains(permission));
}

function renderRow(video, container) {
  const row = document.createElement('li');
  const displayName = video.name === 'Video' ? mediaText('video') : video.name;
  row.textContent = video.playlist ? mediaText('playlist', {name:displayName}) : displayName;
  if (video.seconds) row.append(' · ' + formatDuration(video.seconds));
  if (video.height) row.append(' · ' + video.height + 'p');
  const save = document.createElement('button');
  save.textContent = mediaText('save');
  if (video.playlist) save.textContent = mediaText('details');
  save.onclick = async () => {
    if (save.disabled) return;

    save.disabled = true;
    if (video.playlist) {
      const origin = new URL(video.url).origin + '/*';
      try {
        const granted = await requestServer(origin);
        if (!granted) { statusLine.textContent = mediaText('videoAccess'); return; }
        (await queueReady).addDownload(video.url, video.title);
      } catch { statusLine.textContent = mediaText('queueError'); }
      finally { save.disabled = false; }
      return;
    }
    try {
      const ext = /\.(mp4|m4v|mov|ogv|webm)$/i.exec(video.name)?.[1];
      const filename = ext && video.title ? videoFilename(video.title, video.height, "", ext) : undefined;
      const queue = await queueReady;
      const id = await browser.downloads.download({url:video.url, filename, saveAs:false, conflictAction:"uniquify"});
      queue.trackDirect(id, video.title || video.name);
    } catch { statusLine.textContent = mediaText('directError'); }
    finally { save.disabled = false; }
  };
  row.append(save);
  container.append(row);
}

function display(frames) {
  const unique = new Map();
  const results = frames.map(frame => frame.result).filter(Boolean);
  const unknownPlayer = results.some(result => result.playingWithoutSource);
  for (const video of results.flatMap(result => result.videos)) {
    const previous = unique.get(video.url);
    if (!previous || video.playing || (!previous.playing && !previous.seconds && video.seconds)) unique.set(video.url, video);
  }
  const all = [...unique.values()];
  const videos = all.filter(video => !video.fragment);
  const playing = videos.filter(video => video.playing);
  const main = !unknownPlayer && playing.length === 1 ? playing[0] : null;
  if (main) {
    statusLine.textContent = mediaText('playing');
    renderRow(main, list);
  } else {
    statusLine.textContent = videos.length ? mediaText('noSingle') : (all.length ? mediaText('fragments') : mediaText('noVideo'));
  }
  const rest = videos.filter(video => video !== main);
  if (rest.length) {
    more.querySelector('summary').textContent = mediaText('moreCount', {count:mediaNumber(rest.length)});
    for (const video of rest) renderRow(video, main ? alternatives : list);
    more.hidden = !main;
  }
}

let scanNumber = 0;
async function scan() {
  const request = ++scanNumber;
  scanButton.disabled = true;
  list.replaceChildren();
  alternatives.replaceChildren();
  more.open = false;
  more.hidden = true;
  statusLine.textContent = mediaText('searching');
  try {
    const [tab] = await browser.tabs.query({active:true, windowId:await windowId});
    const frames = await browser.scripting.executeScript({target:{tabId:tab.id, allFrames:true}, func:findVideos});
    if (request === scanNumber) display(frames);
  } catch { if (request === scanNumber) statusLine.textContent = mediaText('scanHelp'); }
  finally { if (request === scanNumber) scanButton.disabled = false; }
}
scanButton.onclick = scan;
document.querySelector('#folder').onclick = () => browser.downloads.showDefaultFolder();

const windowId = browser.windows.getCurrent().then(win => win.id);
const queueReady = Promise.all([browser.runtime.getBackgroundPage(), windowId])
  .then(([background, id]) => background.getQueue(id));

async function attachQueue() {
  const queue = await queueReady;
  const source = queue.document.querySelector('main');
  const target = document.querySelector('main');
  // Keep the actual controls alive while a download continues with the sidebar closed.
  const controls = new WeakMap();
  function sync() {
    const active = document.activeElement;
    const focused = controls.get(active);
    const copy = document.importNode(source, true);
    const selectors = 'button, select, progress, a';
    const originals = source.querySelectorAll(selectors);
    copy.querySelectorAll(selectors).forEach((element, i) => {
      const original = originals[i];
      controls.set(element, original);
      if (element.tagName === 'SELECT') {
        element.selectedIndex = original.selectedIndex;
        element.onchange = () => {
          original.selectedIndex = element.selectedIndex;
          original.dispatchEvent(new Event('change'));
        };
      } else if (element.tagName === 'BUTTON') {
        element.onclick = async () => {
          const origin = original.dataset.audioOrigin;
          if (origin && !await requestServer(origin+'/*')) {
            statusLine.textContent = mediaText('audioAccess');
            return;
          }
          original.click();
        };
      }
    });
    target.replaceChildren(...copy.childNodes);
    if (focused) [...target.querySelectorAll(selectors)].find(el=>controls.get(el)===focused)?.focus({preventScroll:true});
  }
  const observer = new MutationObserver(sync);
  observer.observe(source, {subtree:true, childList:true, attributes:true, characterData:true});
  window.addEventListener('pagehide', () => observer.disconnect(), {once:true});
  sync();
}
attachQueue();
browser.tabs.onActivated.addListener(async info => { if (info.windowId === await windowId) scan(); });
browser.tabs.onUpdated.addListener(async (id, change, tab) => {
  if (tab.active && tab.windowId === await windowId && (change.url || change.status === 'complete')) scan();
});
browser.browserAction.onClicked.addListener(scan);
scan();
