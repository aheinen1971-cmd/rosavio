"""Prepare freshly built Linux output and the last public Linux baseline."""
import json, os, pathlib, re, subprocess, urllib.request, urllib.error, xml.etree.ElementTree as ET
from urllib.parse import urlparse
root=pathlib.Path.cwd();candidate=root/'unix-results/linux-x64'
paths=json.loads((candidate/'paths.json').read_text())
if os.environ.get('GITHUB_ACTIONS')!='true':raise SystemExit('CI only')
(root/'linux-candidate').symlink_to(candidate,target_is_directory=True)
baseline=root/'linux-baseline';baseline.mkdir()
feed='https://github.com/aheinen1971-cmd/rosavio/releases/download/rosavio-linux-x64-latest/rosavio-linux-x64-update.xml'
try:
    with urllib.request.urlopen(feed,timeout=60) as response:xml=response.read()
except urllib.error.HTTPError as e:
    if e.code!=404:raise
    xml=b'<updates/>'
patch=ET.fromstring(xml).find('./update/patch')
if patch is not None:
    url=urlparse(patch.attrib['URL']);parts=url.path.split('/')
    if url.scheme!='https' or url.netloc!='github.com' or parts[1:5]!=['aheinen1971-cmd','rosavio','releases','download'] or len(parts)!=7 or not re.fullmatch(r'[A-Za-z0-9._-]+',parts[5]):
        raise SystemExit('Unexpected public Linux package URL')
    archive=f'https://github.com/aheinen1971-cmd/rosavio/releases/download/{parts[5]}/Rosavio-Linux-x64.tar.xz'
    subprocess.run(['curl','--fail','--location','--retry','2','--output',str(baseline/'previous.tar.xz'),archive],check=True)
else:
    package=pathlib.Path(paths['baseline'])
    subprocess.run(['tar','-cJf',str(baseline/'previous.tar.xz'),'-C',str(package.parent),package.name],check=True)
print('Fresh Linux candidate and genuine older public baseline prepared.')
