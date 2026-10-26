"""Test platform-separated public macOS updates; no Apple notarization claim."""
import configparser,hashlib,json,os,pathlib,platform,plistlib,re,subprocess,tarfile,time,urllib.request,xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr
p=os.environ.get('ROSAVIO_MAC_PLATFORM')
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio' or p not in ('macos-arm64','macos-x64') or platform.system()!='Darwin' or platform.machine()!=('arm64' if p=='macos-arm64' else 'x86_64'):raise SystemExit('Authorized matching native Mac runner required')
root=pathlib.Path.cwd();candidate=root/'macos-candidate';release=candidate/'release';r=json.loads((release/'release.json').read_text());local=json.loads((release/'local-update-test.json').read_text());repack=json.loads((candidate/'repack-report.json').read_text())
if r.get('platform')!=p or not r.get('signatureVerified') or not r.get('tamperNegativeTestPassed') or not local.get('passed') or local.get('platform')!=p or local['after'].get('signatureDisabled',True) or not repack.get('passed') or not repack.get('resourceSealAfterUpdateVerified') or repack.get('platform')!=p:raise SystemExit('Sealed native signed local update test required')
if not re.fullmatch(r'\d+(?:\.\d+){1,3}',r['appVersion']) or not re.fullmatch(r'\d{14}',r['buildID']) or local['after']['buildID']!=r['buildID'] or repack['buildID']!=r['buildID']:raise SystemExit('Invalid or mismatched release identity')
name=r['file']
if pathlib.Path(name).name!=name:raise SystemExit('Unsafe MAR path')
mar=release/name
with mar.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
if digest!=r['hashValue'] or mar.stat().st_size!=r['size']:raise SystemExit('Signed package hash mismatch')
def run(*args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
dmgs=list(candidate.glob('*.dmg'))
if len(dmgs)!=1:raise SystemExit('One sealed candidate DMG required')
attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-readonly','-nobrowse','-plist',str(dmgs[0].resolve())]));mounts=[pathlib.Path(x['mount-point']) for x in attached['system-entities'] if 'mount-point' in x]
package=root/'candidate-app/Rosavio.app';package.parent.mkdir()
try:
 apps=[f for m in mounts for f in m.glob('*.app')]
 if len(apps)!=1:raise SystemExit('Exactly one sealed app required')
 run('ditto',apps[0],package)
finally:
 for m in reversed(mounts):run('hdiutil','detach',m)
ini=configparser.ConfigParser();ini.read(package/'Contents/Resources/application.ini')
if ini['App']['Name']!='Rosavio' or ini['App']['BuildID']!=r['buildID']:raise SystemExit('DMG identity mismatch')
run('codesign','--verify','--deep','--strict',package)
desktop_test=os.environ.get('ROSAVIO_MAC_DESKTOP_TEST')=='1'
if desktop_test:
 run(os.sys.executable,'scripts/check-macos-icons.py',package,root/'candidate-icons')
 with urllib.request.urlopen('https://addons.mozilla.org/api/v5/addons/addon/multi-account-containers/',timeout=60) as response:addon=json.load(response)
 if addon.get('guid')!='@testpilot-containers':raise SystemExit('Wrong official extension identity')
 xpi=addon['current_version']['file']['url']
 if not xpi.startswith('https://addons.mozilla.org/'):raise SystemExit('Official extension source required')
 os.environ['ROSAVIO_UPDATE_EXTENSION_XPI']=xpi
baseline_parent=root/'baseline-app';baseline_parent.mkdir()
with tarfile.open(candidate/'Rosavio-baseline.tar.xz') as tf:tf.extractall(baseline_parent,filter='data')
baseline=baseline_parent/'Rosavio.app';run('codesign','--verify','--deep','--strict',baseline)
for app,folder in [(baseline,'baseline-check'),(package,'candidate-check')]:run('node','scripts/check-unix-native.cjs',app/'Contents/MacOS/rosavio',root/folder,p)
b=json.loads((root/'baseline-check/report.json').read_text());c=json.loads((root/'candidate-check/report.json').read_text())
if b['buildID']>=r['buildID'] or c['buildID']!=r['buildID']:raise SystemExit('Genuine older baseline and matching candidate required')
run('node','scripts/check-locales.cjs',package/'Contents/MacOS/rosavio',root/'candidate-languages')
repo='aheinen1971-cmd/rosavio';stable=f'rosavio-{p}-latest';feedname=f'rosavio-{p}-update.xml';tag=f'v{r["appVersion"]}-rosavio-{p}.{os.environ["GITHUB_RUN_ID"]}'
def gh(*args):return run('gh',*args)
def tag_exists(t):
 if subprocess.run(['gh','api',f'repos/{repo}/git/ref/tags/{t}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:gh('api',f'repos/{repo}/git/refs','-f',f'ref=refs/tags/{t}','-f','sha='+os.environ['GITHUB_SHA'])
latest_before=subprocess.check_output(['gh','api',f'repos/{repo}/releases/latest','--jq','.tag_name'],text=True).strip()
backup=root/'feed-backup';backup.mkdir();tag_exists(tag);tag_exists(stable)
# Prerelease until public update and the remaining Mac UI/profile checks pass.
notes='macOS test package: not notarized by Apple; first launch may be blocked or require user approval. Own MAR signature verification remains mandatory. Public update and additional UI/profile checks are still pending.'
gh('release','create',tag,'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Rosavio '+p+' '+r['appVersion'],'--notes',notes,mar,dmgs[0],release/'release.json',release/'local-update-test.json',candidate/'repack-report.json')
had_feed=subprocess.run(['gh','release','download',stable,'--repo',repo,'--pattern',feedname,'--dir',str(backup)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
if had_feed:
 previous=ET.fromstring((backup/feedname).read_bytes()).find('update')
 if previous is not None:
  previous_build=previous.attrib['buildID'];previous_version=previous.attrib['appVersion']
  if not re.fullmatch(r'\d{14}',previous_build) or not re.fullmatch(r'\d+(?:\.\d+){1,3}',previous_version):raise SystemExit('Invalid previous feed identity')
  parts=lambda value:tuple((list(map(int,value.split('.')))+[0]*4)[:4])
  if previous_build>r['buildID'] or parts(previous_version)>parts(r['appVersion']):raise SystemExit('Public Mac feed downgrade rejected')
if subprocess.run(['gh','release','view',stable,'--repo',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:gh('release','create',stable,'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Rosavio '+p+' update feed','--notes','Separate macOS test update channel; unnotarized apps, own MAR signatures required.')
attrs={'type':'minor','displayVersion':r['appVersion'],'appVersion':r['appVersion'],'platformVersion':r['appVersion'],'buildID':r['buildID']};patch={'type':'complete','URL':f'https://github.com/{repo}/releases/download/{tag}/{name}','hashFunction':'SHA512','hashValue':digest,'size':str(r['size'])};fmt=lambda d:' '.join(k+'='+quoteattr(v) for k,v in d.items())
feed=release/feedname;feed.write_text('<?xml version="1.0"?><updates><update '+fmt(attrs)+'><patch '+fmt(patch)+'/></update></updates>')
try:
 gh('release','upload',stable,feed,'--repo',repo,'--clobber')
 # Check the exact new HTTPS feed and package before native browser testing.
 feed_url=f'https://github.com/{repo}/releases/download/{stable}/{feedname}'
 for attempt in range(12):
  try:
   with urllib.request.urlopen(urllib.request.Request(feed_url,headers={'Cache-Control':'no-cache'}),timeout=30) as response:published=ET.fromstring(response.read()).find('update')
   if published is not None and published.attrib.get('buildID')==r['buildID'] and published.find('patch').attrib==patch:break
  except Exception:
   if attempt==11:raise
  if attempt==11:raise SystemExit('New public Mac feed did not become visible')
  time.sleep(5)
 probe=release/'public-package-probe.mar'
 try:
  run('curl','--fail','--location','--retry','3','--retry-delay','3','--max-time','300','--output',probe,patch['URL'])
  with probe.open('rb') as f:remote_digest=hashlib.file_digest(f,'sha512').hexdigest()
  if remote_digest!=digest or probe.stat().st_size!=r['size']:raise SystemExit('Public Mac package hash/size mismatch')
 finally:probe.unlink(missing_ok=True)
 run('node','scripts/test-unix-update.cjs',baseline,release,p,env={**os.environ,'ROSAVIO_PUBLIC_TEST':'1','ROSAVIO_CHECK_BROWSER_PAGES':'1' if repack.get('browserPagesIncluded') else '0'})
 updated=release/'public-update/Rosavio.app';run('codesign','--verify','--deep','--strict',updated)
 public=json.loads((release/'public-update-test.json').read_text())
 if desktop_test:
  run(os.sys.executable,'scripts/check-macos-icons.py',updated,root/'updated-icons')
  if not public.get('macLaunchServicesStartPassed') or not public.get('preservationAfter',{}).get('extension',{}).get('containerTabLoaded'):raise SystemExit('Mac startup and container preservation must pass')
 public.update(resourceSealAfterPublicUpdateVerified=True,appleNotarized=False,distributionMode='free unnotarized',finderDockIconExtensionSecurityChecksPending=not desktop_test,releaseTag=tag)
 (release/'public-update-test.json').write_text(json.dumps(public,indent=2))
 gh('release','upload',tag,release/'public-update-test.json','--repo',repo)
 if desktop_test:gh('release','upload',tag,release/'macos-launchservices-toolbar.png',release/'macos-protection-settings.png',root/'updated-icons/report.json','--repo',repo)
 gh('release','edit',tag,'--repo',repo,'--latest=false','--notes','Unnotarized macOS test package. Public native signed update and restart, twenty languages and resource seal passed. Additional Finder/Dock, icon, extension and security UI checks remain pending. First launch may require user approval; Apple notarization is not provided.')
except BaseException:
 restore=backup/feedname
 if not had_feed:restore.write_text('<?xml version="1.0"?><updates/>')
 gh('release','upload',stable,restore,'--repo',repo,'--clobber');raise
finally:
 if subprocess.check_output(['gh','api',f'repos/{repo}/releases/latest','--jq','.tag_name'],text=True).strip()!=latest_before:raise SystemExit('Windows Latest changed unexpectedly')
print('Public native macOS update and seal passed; additional Mac UI/profile checks remain pending.')
