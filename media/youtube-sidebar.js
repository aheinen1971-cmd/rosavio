/* User explicitly starts YouTube extraction; scanning alone sends no native request. */
(async () => {
  const background = await browser.runtime.getBackgroundPage();
  const currentWindow = await browser.windows.getCurrent();
  const controller = background.getYouTubeController(currentWindow.id);
  const section = document.querySelector('#youtube');
  const detect = document.querySelector('#youtube-detect');
  const select = document.querySelector('#youtube-quality');
  const save = document.querySelector('#youtube-save');
  const cancel = document.querySelector('#youtube-cancel');
  const status = document.querySelector('#youtube-status');
  const progress = document.querySelector('#youtube-progress');
  const title = document.querySelector('#youtube-title');
  const name = document.querySelector('#youtube-filename');
  let currentURL = null;
  let state = {phase:'idle',busy:false,choices:[]};
  let choicesKey = '';
  const errors = new Set(['youtubeLogin','youtubeQualityChanged','youtubeUnavailable','youtubeNetwork',
    'youtubeFailed','youtubeRequestRejected','youtubeHelperUnavailable','youtubeDisconnected']);
  function render() {
    section.hidden = !currentURL && state.phase === 'idle';
    detect.disabled = state.busy || !currentURL;
    save.disabled = state.busy || !state.choices.length;
    cancel.disabled = !state.busy;
    select.disabled = state.busy || !state.choices.length;
    title.textContent = state.title || '';
    name.value = state.filenameTitle ?? state.title ?? '';
    name.disabled = state.busy || !state.choices.length;
    const key = JSON.stringify(state.choices);
    if (key !== choicesKey) {
      choicesKey = key;
      select.replaceChildren(...state.choices.map(choice => {
        const option = document.createElement('option');
        option.value = choice.selector;
        option.textContent = `${choice.height || '?'}p · ${mediaText(choice.merged ? 'youtubeMerge' : 'youtubeCombined')}`;
        return option;
      }));
      const combined = state.choices.find(c => !c.merged);
      if (combined) select.value = combined.selector;
    }
    progress.hidden = !state.busy;
    if (Number.isFinite(state.percent)) progress.value = state.percent;
    else progress.removeAttribute('value');
    const phaseKeys = {idle:'youtubeHint',inspecting:'youtubeInspecting',detected:'youtubeDetected',
      downloading:'youtubeDownloading',processing:'youtubeProcessing',saved:'youtubeSaved',
      cancelled:'youtubeCancelled',cleanup:'youtubeCleanup'};
    status.textContent = state.phase === 'error' ? mediaText(errors.has(state.code) ? state.code : 'youtubeFailed') :
      mediaText(phaseKeys[state.phase] || 'youtubeHint', {path:state.path || ''});
    if (state.phase === 'downloading' && Number.isFinite(state.percent)) {
      status.textContent += ` ${mediaNumber(state.percent,{maximumFractionDigits:0})} %`;
    }
  }
  async function tabChanged() {
    try {
      const [tab] = await browser.tabs.query({active:true,windowId:currentWindow.id});
      currentURL = background.videoFinderYouTubeURL(tab?.url || '');
    } catch { currentURL = null; }
    render();
  }
  detect.onclick = () => currentURL && controller.inspect(currentURL);
  name.oninput = () => controller.setFilenameTitle(name.value);
  save.onclick = () => controller.download(select.value);
  cancel.onclick = () => controller.cancel();
  const unsubscribe = controller.subscribe(value => { state=value; render(); });
  const activated = info => { if(info.windowId===currentWindow.id) tabChanged(); };
  const updated = (id, change, tab) => { if(tab.active && tab.windowId===currentWindow.id && (change.url || change.status==='complete')) tabChanged(); };
  browser.tabs.onActivated.addListener(activated);
  browser.tabs.onUpdated.addListener(updated);
  // A toolbar click can newly grant activeTab while the sidebar is already open.
  browser.browserAction.onClicked.addListener(tabChanged);
  document.querySelector('#scan').addEventListener('click', tabChanged);
  window.addEventListener('pagehide', () => {
    unsubscribe(); browser.tabs.onActivated.removeListener(activated); browser.tabs.onUpdated.removeListener(updated);
    browser.browserAction.onClicked.removeListener(tabChanged);
    document.querySelector('#scan').removeEventListener('click', tabChanged);
  },{once:true});
  await tabChanged();
})();
