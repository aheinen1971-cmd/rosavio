import { readFile } from 'node:fs/promises';
import { parseAppIni, validateNativeIdentity } from '../updates/native-identity.mjs';
const [ini, report, locale] = process.argv.slice(2);
if (!ini || !report || !locale) throw Error('Usage: node scripts/check-package-identity.mjs APPLICATION_INI NATIVE_REPORT LOCALE');
const values = validateNativeIdentity(parseAppIni(await readFile(ini, 'utf8')), JSON.parse(await readFile(report, 'utf8')), locale);
console.log('Package matches the running native Rosavio:', values.Version, values.BuildID, locale);
