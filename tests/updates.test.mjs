import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { compareVersions, updateXml, validateRelease, createUpdateServer } from '../updates/server.mjs';
const release = { product: 'Rose', channel: 'rose-release', target: 'WINNT_x86_64-msvc-x64', locale: 'en-US', appVersion: '158.0', buildID: '20261017090000', file: 'rose-158.0.complete.mar', size: 3, hashValue: 'a'.repeat(128), signatureVerified: true };
const request = { product: 'Rose', channel: 'rose-release', target: 'WINNT_x86_64-msvc-x64', locale: 'en-US', version: '157.0', buildID: '20261010090000' };
test('offers newer versions and rebuilds, never repeats or downgrades', () => {
  assert.equal(compareVersions('158.10', '158.2'), 1);
  assert.match(updateXml(release, request, 'https://updates.example.org'), /<patch type="complete"/);
  assert.match(updateXml(release, { ...request, version: '158.0' }, 'https://updates.example.org'), /<patch/);
  for (const state of [{ version: '159.0' }, { version: '158.0', buildID: release.buildID }, { version: '158.0', buildID: '20261018000000' }]) assert.match(updateXml(release, { ...request, ...state }, 'https://updates.example.org'), /<updates\/>/);
});
test('does not cross product, locale, architecture or channel boundaries', () => {
  for (const changes of [{ product: 'Firefox' }, { channel: 'release' }, { target: 'WINNT_aarch64-msvc' }, { locale: 'de' }]) assert.match(updateXml(release, { ...request, ...changes }, 'https://updates.example.org'), /<updates\/>/);
});
test('rejects missing verification, unsafe paths, bad hashes and unencrypted remote origins', () => {
  for (const changes of [{ signatureVerified: false }, { file: '../evil.mar' }, { hashValue: '0' }, { size: -1 }]) assert.throws(() => validateRelease({ ...release, ...changes }));
  assert.throws(() => createUpdateServer({ releaseDir: '.', origin: 'http://updates.example.org', allowLocalHttp: true }));
});
test('serves update XML and package bytes; empty release state is safe', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'rose-update-'));
  const server = createUpdateServer({ releaseDir: dir, origin: 'http://127.0.0.1:8877', allowLocalHttp: true });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const url = base + '/update/1/Rose/157.0/20261010090000/WINNT_x86_64-msvc-x64/en-US/rose-release/update.xml';
  try {
    assert.match(await (await fetch(url)).text(), /<updates\/>/);
    const bytes = Buffer.from('MAR');
    await writeFile(join(dir, release.file), bytes);
    await writeFile(join(dir, 'release.json'), JSON.stringify({ ...release, hashValue: createHash('sha512').update(bytes).digest('hex') }));
    const response = await fetch(url);
    assert.equal(response.status, 200);
    assert.match(await response.text(), /hashFunction="sha512"/);
    assert.equal(await (await fetch(base + '/files/' + release.file)).text(), 'MAR');
    assert.equal((await fetch(base + '/files/not-a-release.mar')).status, 404);
    assert.equal((await fetch(url, { method: 'POST' })).status, 405);
    assert.equal((await fetch(url, { method: 'HEAD' })).status, 200);
  } finally { await new Promise(resolve => server.close(resolve)); await rm(dir, { recursive: true, force: true }); }
});
