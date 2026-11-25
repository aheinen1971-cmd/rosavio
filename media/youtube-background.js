/* Only extension pages can access this controller. No content-script command API. */
const youtubeControllers = new Map();
function videoFinderYouTubeURL(value) {
  try {
    const u = new URL(value);
    if (u.protocol !== 'https:' || u.username || u.password || (u.port && u.port !== '443')) return null;
    let id;
    if (u.hostname === 'youtu.be') id = u.pathname.slice(1);
    else if (['youtube.com', 'www.youtube.com', 'm.youtube.com'].includes(u.hostname)) {
      if (u.pathname === '/watch') id = u.searchParams.get('v');
      else id = /^\/(shorts|live)\/([\w-]{11})\/?$/.exec(u.pathname)?.[2];
    }
    return /^[\w-]{11}$/.test(id || '') ? `https://www.youtube.com/watch?v=${id}` : null;
  } catch { return null; }
}

function getYouTubeController(windowId) {
  if (youtubeControllers.has(windowId)) return youtubeControllers.get(windowId);
  let port = null;
  let closed = false;
  let state = {phase:'idle', busy:false, choices:[], title:'', url:'', percent:null, path:''};
  const listeners = new Set();
  const notify = () => { for (const listener of listeners) { try { listener({...state}); } catch {} } };
  function fail(code) {
    state = {...state, busy:false, phase:'error', code};
    notify();
  }
  function connect() {
    if (closed) throw new Error('Window closed');
    if (port) return port;
    const current = browser.runtime.connectNative('org.rosavio.video_finder');
    port = current;
    current.onMessage.addListener(message => {
      if (port !== current || closed || !message || typeof message.type !== 'string') return;
      switch (message.type) {
        case 'ready': return;
        case 'info':
          if (!Array.isArray(message.choices) || !message.choices.length) { fail('youtubeFailed'); return; }
          state = {...state, title:String(message.title), choices:message.choices, phase:'detected'}; break;
        case 'progress':
          state = {...state, phase:message.phase === 'finished' ? 'processing' : 'downloading',
            percent:Number.isFinite(message.percent) ? Math.max(0,Math.min(100,message.percent)) : null}; break;
        case 'saved': state = {...state, phase:'saved', path:String(message.path), percent:100}; break;
        case 'cancelled': state = {...state, phase:message.cleaned ? 'cancelled' : 'cleanup',percent:null}; break;
        case 'error': state = {...state, phase:'error',code:message.code || 'youtubeFailed'}; break;
        case 'failed': if (state.phase !== 'error') state = {...state,phase:'error',code:'youtubeFailed'}; break;
        case 'idle': state = {...state,busy:false}; break;
        case 'done': break;
        default: return;
      }
      notify();
    });
    current.onDisconnect.addListener(() => {
      if (port !== current) return;
      port = null;
      if (!closed) fail(current.error ? 'youtubeHelperUnavailable' : 'youtubeDisconnected');
    });
    return current;
  }
  const controller = {
    subscribe(listener) { listeners.add(listener); listener({...state}); return () => listeners.delete(listener); },
    inspect(value) {
      if (state.busy) return false;
      const url = videoFinderYouTubeURL(value);
      if (!url) { fail('youtubeRequestRejected'); return false; }
      state = {phase:'inspecting',busy:true,choices:[],title:'',url,percent:null,path:''};
      notify();
      try { connect().postMessage({action:'inspect',url}); } catch { fail('youtubeHelperUnavailable'); }
      return true;
    },
    download(selector) {
      if (state.busy || !state.choices.some(c => c.selector === selector)) return false;
      state = {...state,busy:true,phase:'downloading',percent:null,path:''}; notify();
      try { connect().postMessage({action:'download',url:state.url,selector}); } catch { fail('youtubeHelperUnavailable'); }
      return true;
    },
    cancel() {
      if (!state.busy || !port) return;
      // Keep the terminal saved status if cancellation arrives after commit.
      try { port.postMessage({action:'cancel'}); } catch { fail('youtubeDisconnected'); }
    },
    close() { closed=true; listeners.clear(); port?.disconnect(); port=null; youtubeControllers.delete(windowId); }
  };
  youtubeControllers.set(windowId,controller);
  return controller;
}
browser.windows.onRemoved.addListener(id => youtubeControllers.get(id)?.close());
