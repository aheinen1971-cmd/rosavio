// Local workspace data: no URLs, paths or preference names are accepted as commands.
import { PrivateBrowsingUtils } from 'resource://gre/modules/PrivateBrowsingUtils.sys.mjs';

const LIMIT = 100000;
let pending = Promise.resolve();
function clean(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).some(k => !['revision', 'notes', 'links'].includes(k)) ||
      !Number.isSafeInteger(data.revision) || data.revision < 0 ||
      typeof data.notes !== 'string' || data.notes.length > LIMIT ||
      !Array.isArray(data.links) || data.links.length > 24) throw Error('Invalid workspace data');
  return { revision: data.revision, notes: data.notes, links: data.links.map(item => {
    if (!item || Object.keys(item).some(k => !['title','url'].includes(k)) ||
        typeof item.title !== 'string' || !item.title.trim() || item.title.length > 100 ||
        typeof item.url !== 'string' || item.url.length > 4096) throw Error('Invalid shortcut');
    const url = new URL(item.url);
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) throw Error('Invalid shortcut URL');
    return {title:item.title.trim(), url:url.href};
  })};
}
async function read(file) {
  if (!await IOUtils.exists(file)) return {revision:0, notes:'', links:[]};
  const info = await IOUtils.stat(file);
  if (info.size > 1024 * 1024) throw Error('Workspace file too large');
  return clean(await IOUtils.readJSON(file));
}
export class RosavioWorkspaceParent extends JSWindowActorParent {
  receiveMessage(message) {
    if (!['about:rosavio-notes','about:rosavio-home'].includes(this.manager.documentURI?.spec) ||
        this.browsingContext.parent || !['RosavioWorkspace:Read','RosavioWorkspace:Save'].includes(message.name)) {
      throw Error('Workspace request denied');
    }
    const win = this.browsingContext.top.embedderElement?.documentGlobal;
    if (!win || PrivateBrowsingUtils.isWindowPrivate(win)) throw Error('Workspace unavailable in private windows');
    const file = PathUtils.join(PathUtils.profileDir, 'rosavio-workspace.json');
    // Serialize reads/writes across tabs; reject stale edits instead of overwriting.
    const task = pending.then(async () => {
      const current = await read(file);
      if (message.name === 'RosavioWorkspace:Read') return current;
      const next = clean(message.data);
      if (next.revision !== current.revision) throw Error('Workspace changed in another tab');
      next.revision++;
      await IOUtils.writeJSON(file, next, {tmpPath:file+'.tmp', backupFile:file+'.bak'});
      return next;
    });
    pending = task.catch(() => {});
    return task;
  }
}
