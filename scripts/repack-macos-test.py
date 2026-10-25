"""Repackage existing native Mac builds; no browser compilation, no Apple notarization."""
import argparse,configparser,hashlib,json,os,pathlib,plistlib,platform,shlex,shutil,subprocess,sys,tarfile,tempfile,urllib.request,re
from macos_bundle_signing import seal_bundle
p=argparse.ArgumentParser();p.add_argument('candidate',type=pathlib.Path);p.add_argument('baseline',type=pathlib.Path);p.add_argument('platform',choices=['macos-arm64','macos-x64']);a=p.parse_args()
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio' or platform.system()!='Darwin' or platform.machine()!=('arm64' if a.platform=='macos-arm64' else 'x86_64'):raise SystemExit('Authorized matching native runner required')
key=os.environ.pop('ROSAVIO_UPDATE_KEY',None);password=os.environ.pop('ROSAVIO_SIGNING_PASSWORD',None)
if not key or not password:raise SystemExit('Existing MAR signing secrets required')
project=pathlib.Path.cwd();out=project/'macos-repack';out.mkdir();root=pathlib.Path(os.environ['RUNNER_TEMP'])/'rosavio-repack';root.mkdir()
def run(*args,**kw):subprocess.run([str(x) for x in args],check=True,**kw)
def readurl(url):
 with urllib.request.urlopen(url,timeout=120) as r:return r.read()
def copy_dmg(folder,dest):
 dmgs=list(folder.glob('*.dmg'))
 if len(dmgs)!=1:raise RuntimeError('Exactly one original DMG required')
 attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-readonly','-nobrowse','-plist',str(dmgs[0].resolve())]))
 mounts=[pathlib.Path(e['mount-point']) for e in attached['system-entities'] if 'mount-point' in e]
 try:
  apps=[f for mount in mounts for f in mount.glob('*.app')]
  if len(apps)!=1:raise RuntimeError('Exactly one app required')
  dest.parent.mkdir(parents=True,exist_ok=True);run('ditto',apps[0],dest)
 finally:
  for mount in reversed(mounts):run('hdiutil','detach',mount)
 info=plistlib.loads((dest/'Contents/Info.plist').read_bytes())
 if info.get('CFBundleName')!='Rosavio':raise RuntimeError('Wrong product')
 arches=subprocess.check_output(['lipo','-archs',str(dest/'Contents/MacOS/rosavio')],text=True).split()
 if ('arm64' if a.platform=='macos-arm64' else 'x86_64') not in arches:raise RuntimeError('Wrong architecture')
 ini=configparser.ConfigParser();ini.read(dest/'Contents/Resources/application.ini');return ini
candidate=root/'candidate/Rosavio.app';baseline=root/'baseline/Rosavio.app'
new=copy_dmg(a.candidate,candidate);old=copy_dmg(a.baseline,baseline)
reports=list(a.candidate.rglob('local-update-test.json'))
if len(reports)!=1:raise RuntimeError('Exactly one prior local update report required')
prior=json.loads(reports[0].read_text())
if not prior.get('passed') or prior.get('platform')!=a.platform or prior['after'].get('signatureDisabled',True) or prior['after']['buildID']!=new['App']['BuildID']:raise RuntimeError('Candidate must match signature-enforced native test')
if old['App']['BuildID']>=new['App']['BuildID']:raise RuntimeError('Genuine older baseline required')
version=new['App']['Version']
if not re.fullmatch(r'\d+\.\d+(\.\d+)?',version):raise RuntimeError('Stable version required')
for kind,app in [('baseline',baseline),('candidate',candidate)]:seal_bundle(app,out/(kind+'-app-signature.json'))
binary=candidate/'Contents/MacOS/rosavio'
for script,folder,args in [('check-unix-native.cjs','native-check',[a.platform]),('check-locales.cjs','locale-check',[]),('check-extensions.cjs','extensions-check',[]),('check-translations.cjs','translations-check',[])]:run('node',project/'scripts'/script,binary,out/folder,*args)
# Extract only the small upstream packaging tools from an officially hash-verified source archive.
base=f'https://archive.mozilla.org/pub/firefox/releases/{version}';name=f'source/firefox-{version}.source.tar.xz'
manifest=readurl(base+'/SHA512SUMS').decode();digest=next(line.split()[0] for line in manifest.splitlines() if line.split()[-1].lstrip('*')==name)
archive=root/'source.tar.xz';run('curl','--fail','--location','--retry','2','--max-time','900','--output',archive,base+'/'+name)
with archive.open('rb') as f:actual=hashlib.file_digest(f,'sha512').hexdigest()
if actual!=digest:raise RuntimeError('Upstream source SHA512 mismatch')
prefix=f'firefox-{version}/';allowed=('modules/libmar/','other-licenses/nsis/Contrib/CityHash/cityhash/','tools/update-packaging/')
with tarfile.open(archive) as tf:
 members=[m for m in tf.getmembers() if m.name.startswith(prefix) and m.name[len(prefix):].startswith(allowed)]
 tf.extractall(root,members=members,filter='data')
archive.unlink();source=root/f'firefox-{version}';lib=source/'modules/libmar';city=source/'other-licenses/nsis/Contrib/CityHash/cityhash';bindir=source/'obj-rose/dist/bin';bindir.mkdir(parents=True)
nss=pathlib.Path(subprocess.check_output(['brew','--prefix','nss'],text=True).strip());nspr=pathlib.Path(subprocess.check_output(['brew','--prefix','nspr'],text=True).strip())
inc=[f'-I{lib/d}' for d in ['src','sign','verify']]+[f'-I{city}',f'-I{nss}/include/nss',f'-I{nspr}/include/nspr']
common=['-DXP_UNIX','-DXP_MACOSX=1','-DMAR_CHANNEL_ID="rosavio-release"',f'-DMOZ_APP_VERSION="{version}"',*inc]
objects=[]
files=[lib/'src'/n for n in ['mar_create.c','mar_extract.c','mar_read.c']]+[lib/'verify'/n for n in ['mar_verify.c','cryptox.c','MacVerifyCrypto.cpp']]+[lib/'sign'/n for n in ['mar_sign.c','nss_secutil.c']]+[city/'city.cpp',lib/'tool/mar.c']
for i,f in enumerate(files):
 obj=root/f'tool-{i}.o';cpp=f.suffix=='.cpp';flags=['-DMAR_NSS'] if f.parent.name=='sign' else []
 run('clang++' if cpp else 'clang','-std=c++17' if cpp else '-std=c11','-O2',*common,*flags,'-c',f,'-o',obj);objects.append(obj)
run('clang++',*objects,f'-L{nss}/lib',f'-L{nspr}/lib','-lnss3','-lsmime3','-lssl3','-lnspr4','-lplc4','-lplds4','-framework','Security','-framework','CoreFoundation','-o',bindir/'signmar')
shutil.copy2(bindir/'signmar',bindir/'mar')
fd,keyname=tempfile.mkstemp(dir=os.environ['RUNNER_TEMP'],prefix='rosavio-encrypted-mar-');keypath=pathlib.Path(keyname)
try:
 with os.fdopen(fd,'w') as f:f.write(key)
 key=None;os.chmod(keypath,0o600)
 env={**os.environ,'ROSAVIO_KEY_PATH':str(keypath),'ROSAVIO_SIGNING_PASSWORD':password}
 run(sys.executable,project/'scripts/package-unix-update.py',source,candidate,out/'release',a.platform,env=env)
finally:keypath.unlink(missing_ok=True);password=None;env=None
run('node',project/'scripts/test-unix-update.cjs',baseline,out/'release',a.platform)
run('codesign','--verify','--deep','--strict',out/'release/local-update/Rosavio.app')
run('hdiutil','create','-volname','Rosavio','-srcfolder',candidate,'-format','UDZO',out/'Rosavio.dmg')
run('tar','-cJf',out/'Rosavio-baseline.tar.xz','-C',baseline.parent,baseline.name)
(out/'repack-report.json').write_text(json.dumps({'passed':True,'platform':a.platform,'buildID':new['App']['BuildID'],'baselineBuildID':old['App']['BuildID'],'sourceSHA512':actual,'resourceSealAfterUpdateVerified':True,'appleNotarized':False,'distributionMode':'free unnotarized; user-managed macOS first-launch approval may be needed','publicUpdateTestPassed':False,'published':False},indent=2))
