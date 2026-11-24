const queues = new Map();
browser.browserAction.onClicked.addListener(() => browser.sidebarAction.open());

function getQueue(windowId) {
  if (!queues.has(windowId)) {
    const frame = document.createElement('iframe');
    const ready = new Promise(resolve => frame.addEventListener('load', () => resolve(frame.contentWindow), {once:true}));
    queues.set(windowId, {frame, ready});
    frame.src = 'queue.html';
    document.body.append(frame);
  }
  return queues.get(windowId).ready;
}
browser.windows.onRemoved.addListener(id => {
  queues.get(id)?.frame.remove();
  queues.delete(id);
});
