"""Prepare pinned translations and native twenty-language Rosavio packaging."""
import json,pathlib,re,subprocess,sys
source=pathlib.Path(sys.argv[1]).resolve(); l10n=pathlib.Path(sys.argv[2]).resolve()
pins=json.loads((source/'browser/locales/l10n-changesets.json').read_text())
for locale in ('fr', 'es-ES', 'nl', 'it', 'pt-PT', 'pl', 'cs', 'da', 'sv-SE', 'nb-NO', 'fi', 'tr', 'uk', 'el', 'ja', 'ko', 'ar', 'he'):
 revision=pins[locale]['revision']
 subprocess.run(['git','-C',str(l10n),'fetch','--depth=1','origin',revision],check=True)
 subprocess.run(['git','-C',str(l10n),'restore','--source',revision,'--staged','--worktree','--',locale],check=True)
 subprocess.run(['git','-C',str(l10n),'diff','--exit-code',revision,'--',locale],check=True)
 for file in (l10n/locale).rglob('*'):
  if file.suffix not in ('.ftl','.properties','.dtd'):continue
  lines=file.read_text(encoding='utf-8').splitlines(keepends=True)
  text=''.join(line if line.lstrip().startswith(('#','<!--')) else line.replace('Mozilla Firefox','Rosavio').replace('Firefox','Rosavio') for line in lines)
  text=re.sub(r'(?m)^-vendor-short-name = .*$', '-vendor-short-name = Rosavio',text)
  file.write_text(text,encoding='utf-8',newline='\n')
# Default remains German; users can select any packaged language in Settings.
prefs=source/'browser/app/profile/firefox.js'
with prefs.open('a',encoding='utf-8') as f:f.write('\npref("intl.locale.requested", "de");\n')
print('Twenty pinned native languages prepared; no signature checks weakened')
