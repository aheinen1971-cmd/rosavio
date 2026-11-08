const fs=require('fs'),path=require('path');const start=require('./native-session.cjs');
const binary=path.resolve(process.argv[2]);const root=path.resolve(process.argv[3]||'locale-check');
const expected={"de": "Über Rosavio", "en-US": "About Rosavio", "fr": "À propos de Rosavio", "es-ES": "Acerca de Rosavio", "nl": "Over Rosavio", "it": null, "pt-PT": null, "pl": null, "cs": null, "da": null, "sv-SE": null, "nb-NO": null, "fi": null, "tr": null, "uk": null, "el": null, "ja": null, "ko": null, "ar": null, "he": null};
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

async function verifyLocale(locale, label, profile) {
 let session;
 try {
  session = await start(binary, profile, 2859);
  const available = await session.script(`Services.locale.requestedLocales=[${JSON.stringify(locale)}];Services.prefs.savePrefFile(null);return Services.locale.availableLocales;`);
  if (!Array.isArray(available) || !Object.keys(expected).every(code => available.includes(code))) {
   throw Error('Missing packaged languages: ' + JSON.stringify(available));
  }
  await session.close();
  session = null;
  await pause(600);
  session = await start(binary, profile, 2859);
  const result = await session.script("await document.l10n.ready;return {name:Services.appinfo.name,locale:Services.locale.appLocaleAsBCP47,about:document.getElementById('aboutName').getAttribute('label'),available:Services.locale.availableLocales};");
  if (result.name !== 'Rosavio' || result.locale !== locale ||
      (label ? result.about !== label : (!result.about || !result.about.includes('Rosavio') || result.about === 'About Rosavio'))) {
   throw Error('Language verification failed for ' + locale + ': ' + JSON.stringify(result));
  }
  if (process.argv.includes('--rosavio-pages')) {
   result.rosavioPages = await require('./check-page-locales.cjs')(session, locale, path.join(root, 'pages'));
  }
  if (process.argv.includes('--workspace')) {
   result.workspace = await require('./check-workspace-locales.cjs')(session, locale);
  }
  return result;
 } finally {
  if (session) await session.close();
 }
}

function transientWindowsProcessFailure(error, profile) {
 const log = path.join(profile, 'browser.log');
 return process.platform === 'win32' &&
  String(error).includes('Browsing context has been discarded') &&
  fs.existsSync(log) &&
  fs.readFileSync(log, 'utf8').includes('SpawnTarget (Error:-2147024809)');
}

(async () => {
 const reports = [];
 for (const [locale, label] of Object.entries(expected)) {
  console.log('Checking native locale: ' + locale);
  const profile = path.join(root, locale);
  let firstFailure;
  try {
   let result;
   try {
    result = await verifyLocale(locale, label, profile);
   } catch (error) {
    if (!transientWindowsProcessFailure(error, profile)) throw error;
    firstFailure = String(error);
    console.warn('Windows could not start a browser child process. Retesting the full locale with a fresh profile: ' + locale);
    await pause(2500);
    result = await verifyLocale(locale, label, profile + '-retry');
   }
   if (firstFailure) result.firstAttempt = firstFailure;
   reports.push(result);
  } catch (error) {
   fs.mkdirSync(root, {recursive:true});
   fs.writeFileSync(path.join(root, 'failure.json'), JSON.stringify({
    passed:false, locale, completedLocales:reports.map(item => item.locale), firstFailure,
    error:String(error), stack:error.stack,
   }, null, 2));
   throw error;
  }
 }
 fs.writeFileSync(path.join(root, 'report.json'), JSON.stringify({passed:true,languages:reports}, null, 2));
 console.log('All twenty native Rosavio languages passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
