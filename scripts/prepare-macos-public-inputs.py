"""Normalize a fresh sealed native build and use the previous public Mac app as baseline."""
import hashlib,json,os,pathlib,plistlib,re,shutil,subprocess,tarfile,urllib.request,xml.etree.ElementTree as ET
from urllib.parse import urlparse
p=os.environ['ROSAVIO_MAC_PLATFORM'];root=pathlib.Path.cwd();source=root/'unix-results'/p;out=root/'macos-candidate';out.mkdir()
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio' or p not in ('macos-arm64','macos-x64'):raise SystemExit('Authorized native Mac runner required')
r=json.loads((source/'release/release.json').read_text());local=json.loads((source/'release/local-update-test.json').read_text());seal=json.loads((source/'package-app-signature.json').read_text())
pages=json.loads((source/'browser-pages-check/report.json').read_text())
if not pages.get('passed'):raise SystemExit('Native browser information-page test required for fresh builds')
if not local.get('passed') or local['after'].get('signatureDisabled',True) or not seal.get('resourceSealVerified') or r.get('platform')!=p:raise SystemExit('Sealed signed local Mac update required')
subprocess.run(['codesign','--verify','--deep','--strict',str(source/'release/local-update/Rosavio.app')],check=True)
shutil.copytree(source/'release',out/'release',ignore=shutil.ignore_patterns('local-update'))
shutil.copy2(source/'Rosavio-sealed-test.dmg',out/'Rosavio.dmg')
feed=f'https://github.com/aheinen1971-cmd/rosavio/releases/download/rosavio-{p}-latest/rosavio-{p}-update.xml'
with urllib.request.urlopen(feed,timeout=60) as response:update=ET.fromstring(response.read()).find('update')
if update is None:raise SystemExit('Previous proven public Mac baseline required')
url=urlparse(update.find('patch').attrib['URL']);parts=url.path.split('/')
if url.scheme!='https' or url.netloc!='github.com' or len(parts)!=7 or parts[1:5]!=['aheinen1971-cmd','rosavio','releases','download'] or not re.fullmatch(r'v[0-9.]+-rosavio-'+p+r'\.[0-9]+',parts[5]):raise SystemExit('Unexpected platform feed')
tag=parts[5]
with urllib.request.urlopen(f'https://api.github.com/repos/aheinen1971-cmd/rosavio/releases/tags/{tag}',timeout=60) as response:release=json.load(response)
asset=next(x for x in release['assets'] if x['name']=='Rosavio.dmg')
if not re.fullmatch('sha256:[0-9a-f]{64}',asset.get('digest','')):raise SystemExit('Previous DMG hash missing')
old=root/'previous.dmg';subprocess.run(['curl','--fail','--location','--retry','2','--output',str(old),asset['browser_download_url']],check=True)
with old.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
if 'sha256:'+digest!=asset['digest']:raise SystemExit('Previous DMG hash mismatch')
attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-readonly','-nobrowse','-plist',str(old)]));mounts=[pathlib.Path(x['mount-point']) for x in attached['system-entities'] if 'mount-point' in x];dest=root/'previous-app/Rosavio.app';dest.parent.mkdir()
try:
 apps=[a for m in mounts for a in m.glob('*.app')]
 if len(apps)!=1:raise SystemExit('Previous app missing')
 subprocess.run(['ditto',str(apps[0]),str(dest)],check=True)
finally:
 for m in reversed(mounts):subprocess.run(['hdiutil','detach',str(m)],check=True)
subprocess.run(['codesign','--verify','--deep','--strict',str(dest)],check=True)
subprocess.run(['tar','-cJf',str(out/'Rosavio-baseline.tar.xz'),'-C',str(dest.parent),dest.name],check=True)
(out/'repack-report.json').write_text(json.dumps({'passed':True,'platform':p,'buildID':r['buildID'],'resourceSealAfterUpdateVerified':True,'browserPagesIncluded':True,'appleNotarized':False,'previousPublicTag':tag,'publicUpdateTestPassed':False,'published':False},indent=2))
