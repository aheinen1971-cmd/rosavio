export function parseAppIni(text) {
  let section = '';
  const values = {};
  for (const line of text.split(/\r?\n/)) {
    const header = /^\[([^\]]+)\]$/.exec(line.trim());
    if (header) section = header[1];
    const pair = /^([^=]+)=(.*)$/.exec(line);
    if (pair && section === 'App') values[pair[1].trim()] = pair[2].trim();
  }
  return values;
}

export function validateNativeIdentity(values, report, locale) {
  if (report.passed !== true || report.name !== 'Rosavio' || report.vendor !== 'Rosavio') throw Error('Native Rosavio start verification is missing');
  if (values.Name !== report.name || values.Version !== report.version || values.BuildID !== report.buildID) throw Error('Package application.ini disagrees with the running native executable');
  if (report.locale !== locale) throw Error('Package locale disagrees with the running native executable');
  if (!/^https:\/\/github\.com\/aheinen1971-cmd\/(rose|rosavio)\/releases\/latest\/download\/rosavio-win64-update\.xml$/.test(report.updateUrl || '')) throw Error('Native Rosavio updater is not using its own public update address');
  return values;
}
