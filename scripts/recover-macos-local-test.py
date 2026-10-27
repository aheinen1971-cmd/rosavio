"""Recheck saved sealed packages without compiling or loading signing secrets."""
import hashlib,json,os,pathlib,subprocess,tarfile,plistlib,configparser
platform=os.environ['ROSAVIO_MAC_PLATFORM']
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio' or platform not in ('macos-arm64','macos-x64'):
    raise SystemExit('Authorized native recovery runner required')
os.environ.pop('GH_TOKEN',None)
root=pathlib.Path.cwd();out=root/'unix-results'/platform
r=json.loads((out/'release/release.json').read_text())
prior=json.loads((out/'release/local-update-test.json').read_text())
pages=json.loads((out/'browser-pages-check/report.json').read_text())
seal=json.loads((out/'package-app-signature.json').read_text())
if not (r.get('platform')==platform and r.get('signatureVerified') and r.get('tamperNegativeTestPassed') and prior.get('passed') and prior['after']['buildID']==r['buildID'] and not prior['after'].get('signatureDisabled',True) and pages.get('passed') and seal.get('resourceSealVerified')):
    raise SystemExit('Saved signed native evidence incomplete')
mar=out/'release'/r['file']
if pathlib.Path(r['file']).name!=r['file']:raise SystemExit('Unsafe MAR path')
with mar.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
if digest!=r['hashValue'] or mar.stat().st_size!=r['size']:raise SystemExit('Saved signed MAR mismatch')
baseline=root/'recovery-baseline';baseline.mkdir()
with tarfile.open(out/'Rosavio-sealed-baseline.tar.xz') as archive:archive.extractall(baseline,filter='data')
app=baseline/'Rosavio.app'
subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
# Reuse the already-passed genuine local update, and verify its exact candidate.
# The public test below will independently repeat update/restart/profile/seal gates.
dmg=out/'Rosavio-sealed-test.dmg'
attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-readonly','-nobrowse','-plist',str(dmg.resolve())]))
mounts=[pathlib.Path(e['mount-point']) for e in attached['system-entities'] if 'mount-point' in e]
dest=out/'release/local-update/Rosavio.app';dest.parent.mkdir(parents=True)
try:
    apps=[a for m in mounts for a in m.glob('*.app')]
    if len(apps)!=1:raise SystemExit('Exactly one saved candidate required')
    subprocess.run(['ditto',str(apps[0]),str(dest)],check=True)
finally:
    for mount in reversed(mounts):subprocess.run(['hdiutil','detach',str(mount)],check=True)
ini=configparser.ConfigParser();ini.read(dest/'Contents/Resources/application.ini')
if ini['App']['Name']!='Rosavio' or ini['App']['BuildID']!=r['buildID']:raise SystemExit('Saved DMG identity mismatch')
subprocess.run(['codesign','--verify','--deep','--strict',str(dest)],check=True)
partial=root/'macos-candidate'
if partial.exists():partial.rename(root/'saved-incomplete-candidate')
print('Saved signed local-update evidence and exact sealed candidate verified; new public update still required')
