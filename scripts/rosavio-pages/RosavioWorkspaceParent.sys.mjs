// Local workspace data: no URLs, paths or preference names are accepted as commands.
import { PrivateBrowsingUtils } from 'resource://gre/modules/PrivateBrowsingUtils.sys.mjs';

const LIMIT = 100000;
let pending = Promise.resolve();
function cleanPlace(place) {
  if (!place || typeof place.url !== 'string' || place.url.length > 8192 ||
      typeof place.quote !== 'string' || !place.quote.trim() || place.quote.length > 1200) {
    throw Error('Invalid reading place');
  }
  const url = new URL(place.url);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password ||
      !url.hash.includes(':~:text=')) throw Error('Invalid reading URL');
  return {url:url.href, quote:place.quote};
}
function enqueue(action) {
  const task = pending.then(action);
  pending = task.catch(() => {});
  return task;
}
async function write(file, data) {
  if (new TextEncoder().encode(JSON.stringify(data)).length > 1024 * 1024) throw Error('Workspace full');
  await IOUtils.writeJSON(file, data, {tmpPath:file+'.tmp', backupFile:file+'.bak'});
}
function clean(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data) ||
      Object.keys(data).some(k => !['revision', 'notes', 'links', 'places'].includes(k)) ||
      !Number.isSafeInteger(data.revision) || data.revision < 0 ||
      typeof data.notes !== 'string' || data.notes.length > LIMIT ||
      !Array.isArray(data.links) || data.links.length > 24) throw Error('Invalid workspace data');
  if (data.places !== undefined && (!Array.isArray(data.places) || data.places.length > 30)) throw Error('Invalid reading places');
  return { ...(data.places?.length ? {places:data.places.map(cleanPlace)} : {}), revision: data.revision, notes: data.notes, links: data.links.map(item => {
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
  static addPlace(win, place) {
    if (!win || PrivateBrowsingUtils.isWindowPrivate(win)) throw Error('Workspace unavailable in private windows');
    const entry = cleanPlace(place);
    const file = PathUtils.join(PathUtils.profileDir, 'rosavio-workspace.json');
    return enqueue(async () => {
      const data = await read(file);
      const places = data.places || [];
      if (places.some(item => item.url === entry.url && item.quote === entry.quote)) return;
      if (places.length >= 30) throw Error('Workspace full');
      data.places = [entry, ...places];
      data.revision++;
      await write(file, data);
    });
  }
  receiveMessage(message) {
    if (!['about:rosavio-notes','about:rosavio-home'].includes(this.manager.documentURI?.spec) ||
        this.browsingContext.parent || !['RosavioWorkspace:Read','RosavioWorkspace:Save'].includes(message.name)) {
      throw Error('Workspace request denied');
    }
    const win = this.browsingContext.top.embedderElement?.documentGlobal;
    if (!win || PrivateBrowsingUtils.isWindowPrivate(win)) throw Error('Workspace unavailable in private windows');
    const file = PathUtils.join(PathUtils.profileDir, 'rosavio-workspace.json');
    // Serialize reads/writes across tabs; reject stale edits instead of overwriting.
    return enqueue(async () => {
      const current = await read(file);
      if (message.name === 'RosavioWorkspace:Read') return current;
      const next = clean(message.data);
      if (next.revision !== current.revision) throw Error('Workspace changed in another tab');
      next.revision++;
      await write(file, next);
      return next;
    });
  }
}
