import http from 'node:http';
import { createReadStream } from 'node:fs';
import { readFile, stat } from 'node:fs/promises';
import { resolve, dirname, basename, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const empty = '<?xml version="1.0" encoding="UTF-8"?>\n<updates/>\n';
const escapeXml = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[c]);
const versionPattern = /^\d+(?:\.\d+){0,3}$/;
export function compareVersions(a, b) {
  if (!versionPattern.test(a) || !versionPattern.test(b)) throw Error('Only stable numeric versions are supported');
  const left = a.split('.').map(Number), right = b.split('.').map(Number);
  for (let i = 0; i < Math.max(left.length, right.length); i++) {
    if ((left[i] || 0) !== (right[i] || 0)) return (left[i] || 0) > (right[i] || 0) ? 1 : -1;
  }
  return 0;
}
export function validateRelease(release) {
  if (release.product !== 'Rose' || release.channel !== 'rose-release' || release.target !== 'WINNT_x86_64-msvc-x64') throw Error('Wrong product, channel or target');
  if (!versionPattern.test(release.appVersion) || !/^\d{14}$/.test(release.buildID)) throw Error('Invalid version or build ID');
  if (!['en-US', 'de'].includes(release.locale)) throw Error('Unsupported locale');
  if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*\.mar$/.test(release.file) || basename(release.file) !== release.file) throw Error('Unsafe MAR filename');
  if (!/^[a-f0-9]{128}$/.test(release.hashValue) || !Number.isSafeInteger(release.size) || release.size < 1) throw Error('Invalid SHA-512 or size');
  if (release.signatureVerified !== true) throw Error('Release was not verified by signmar');
  return release;
}
export function updateXml(release, request, origin, packageUrl) {
  validateRelease(release);
  if (request.product !== release.product || request.channel !== release.channel || request.target !== release.target || request.locale !== release.locale) return empty;
  const comparison = compareVersions(release.appVersion, request.version);
  if (comparison < 0 || (comparison === 0 && release.buildID <= request.buildID)) return empty;
  const marUrl = packageUrl || new URL('/files/' + encodeURIComponent(release.file), origin).href;
  const attrs = { type: 'minor', displayVersion: release.appVersion, appVersion: release.appVersion, platformVersion: release.appVersion, buildID: release.buildID };
  const patch = { type: 'complete', URL: marUrl, hashFunction: 'sha512', hashValue: release.hashValue, size: release.size };
  const attributes = obj => Object.entries(obj).map(([k, v]) => `${k}="${escapeXml(v)}"`).join(' ');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<updates><update ${attributes(attrs)}><patch ${attributes(patch)}/></update></updates>\n`;
}
export function createUpdateServer({ releaseDir, origin, allowLocalHttp = false }) {
  const parsedOrigin = new URL(origin);
  if (parsedOrigin.protocol !== 'https:' && !(allowLocalHttp && parsedOrigin.protocol === 'http:' && ['127.0.0.1', 'localhost'].includes(parsedOrigin.hostname))) throw Error('HTTPS is required outside explicit local tests');
  const root = resolve(releaseDir);
  return http.createServer(async (req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Cache-Control', 'no-store');
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405, { Allow: 'GET, HEAD' }).end(); return; }
    try {
      const url = new URL(req.url, origin);
      if (url.pathname === '/health') { res.writeHead(200, { 'Content-Type': 'application/json' }).end(req.method === 'HEAD' ? undefined : '{"service":"rose-updates","ok":true}'); return; }
      const match = /^\/update\/1\/([^/]+)\/([^/]+)\/(\d{14})\/([^/]+)\/([^/]+)\/([^/]+)\/update\.xml$/.exec(url.pathname);
      if (match) {
        const [, product, version, buildID, target, locale, channel] = match.map(decodeURIComponent);
        if (!versionPattern.test(version)) { res.writeHead(400).end(); return; }
        let body = empty;
        try {
          const release = validateRelease(JSON.parse(await readFile(resolve(root, 'release.json'), 'utf8')));
          const info = await stat(resolve(root, release.file));
          if (!info.isFile() || info.size !== release.size) throw Error('Release file size does not match metadata');
          body = updateXml(release, { product, version, buildID, target, locale, channel }, origin);
        } catch (error) { if (error.code !== 'ENOENT') throw error; }
        res.writeHead(200, { 'Content-Type': 'text/xml; charset=utf-8' }).end(req.method === 'HEAD' ? undefined : body);
        return;
      }
      if (url.pathname.startsWith('/files/')) {
        const file = decodeURIComponent(url.pathname.slice(7));
        const release = validateRelease(JSON.parse(await readFile(resolve(root, 'release.json'), 'utf8')));
        if (file !== release.file) { res.writeHead(404).end(); return; }
        const fullPath = resolve(root, file);
        if (!fullPath.startsWith(root + sep)) { res.writeHead(404).end(); return; }
        const info = await stat(fullPath);
        if (!info.isFile() || info.size !== release.size) throw Error('Release file changed');
        res.writeHead(200, { 'Content-Type': 'application/octet-stream', 'Content-Length': info.size });
        if (req.method === 'HEAD') res.end();
        else { const stream = createReadStream(fullPath); stream.on('error', () => res.destroy()); stream.pipe(res); }
        return;
      }
      res.writeHead(404).end();
    } catch (error) {
      console.error('Rose update request failed:', error.message);
      if (!res.headersSent) res.writeHead(error.code === 'ENOENT' ? 404 : 503).end();
      else res.destroy();
    }
  });
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const port = Number(process.env.PORT || 8877);
  const origin = process.env.ROSE_UPDATE_ORIGIN || `http://127.0.0.1:${port}`;
  const server = createUpdateServer({ releaseDir: process.env.ROSE_RELEASE_DIR || resolve(here, '../releases'), origin, allowLocalHttp: process.env.ROSE_LOCAL_TEST === '1' });
  server.listen(port, '127.0.0.1', () => console.log(`Rose update service: ${origin} (local listener; use an HTTPS reverse proxy for publication)`));
}
