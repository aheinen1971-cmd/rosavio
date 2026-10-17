"""Prepare the pinned German localization for Rosavio repackaging."""
import argparse
import json
import pathlib
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('source', type=pathlib.Path)
parser.add_argument('localizations', type=pathlib.Path)
args = parser.parse_args()
source = args.source.resolve()
localizations = args.localizations.resolve()
revision = json.loads((source / 'browser/locales/l10n-changesets.json').read_text())['de']['revision']
actual = subprocess.check_output(['git', '-C', str(localizations), 'rev-parse', 'HEAD'], text=True).strip()
if actual != revision:
    raise SystemExit(f'Expected German translations at {revision}, found {actual}')
for file in (localizations / 'de').rglob('*'):
    if file.suffix not in ('.ftl', '.properties', '.dtd'):
        continue
    lines = file.read_text(encoding='utf-8').splitlines(keepends=True)
    text = ''.join(line if line.lstrip().startswith(('#', '<!--')) else line.replace('Mozilla Firefox', 'Rosavio').replace('Firefox', 'Rosavio') for line in lines)
    file.write_text(text, encoding='utf-8', newline='\n')
branding = localizations / 'de/browser/branding/official'
for name in ('brand.ftl', 'brand.properties'):
    file = branding / name
    text = file.read_text(encoding='utf-8').replace('Mozilla Firefox', 'Rosavio').replace('Firefox', 'Rosavio')
    text = re.sub(r'(?m)^-vendor-short-name = .*$', '-vendor-short-name = Rosavio', text)
    text = re.sub(r'(?m)^trademarkInfo\s*=.*$', 'trademarkInfo = { " " }' if name.endswith('.ftl') else 'trademarkInfo=', text)
    file.write_text(text, encoding='utf-8', newline='\n')
mozconfig = source / 'mozconfig'
text = mozconfig.read_text()
text = re.sub(r'(?m)^ac_add_options --with-l10n-base=.*\n?', '', text)
text += f'ac_add_options --with-l10n-base={localizations.as_posix()}\n'
mozconfig.write_text(text, newline='\n')
print(f'German translations pinned to {revision}; Rosavio branding prepared')
