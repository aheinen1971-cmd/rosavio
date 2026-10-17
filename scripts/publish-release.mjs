import { readFile, writeFile, rename, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, dirname, basename } from 'node:path';
import { execFileSync } from 'node:child_process';
import { validateRelease } from '../updates/server.mjs';
const [marArg, iniArg, signmarArg, certArg, locale = 'en-US'] = process.argv.slice(2);
if (![marArg, iniArg, signmarArg, certArg].every(Boolean)) throw Error('Usage: node scripts/publish-release.mjs SIGNED_MAR APPLICATION_INI SIGNMAR PUBLIC_CERT');
const mar = resolve(marArg);
execFileSync(resolve(signmarArg), ['-D', resolve(certArg), '-v', mar], { stdio: 'inherit' });
const ini = await readFile(resolve(iniArg), 'utf8');
let section = '', values = {};
for (const line of ini.split(/\r?\n/)) {
  const header = /^\[([^\]]+)\]$/.exec(line.trim());
  if (header) section = header[1];
  const pair = /^([^=]+)=(.*)$/.exec(line);
  if (pair && section === 'App') values[pair[1].trim()] = pair[2].trim();
}
if (values.Name !== 'Rosavio') throw Error('Refusing to publish a non-Rosavio application');
const hash = createHash('sha512');
for await (const chunk of createReadStream(mar)) hash.update(chunk);
const release = validateRelease({ product: 'Rosavio', channel: 'rosavio-release', target: 'WINNT_x86_64-msvc-x64', locale, appVersion: values.Version, buildID: values.BuildID, file: basename(mar), hashValue: hash.digest('hex'), size: (await stat(mar)).size, signatureVerified: true });
const output = resolve(dirname(mar), 'release.json');
const temp = output + '.tmp';
await writeFile(temp, JSON.stringify(release, null, 2) + '\n');
await rename(temp, output);
console.log('Published metadata after native MAR signature verification:', release.appVersion, release.buildID);
