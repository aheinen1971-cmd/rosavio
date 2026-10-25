"""Repair resource seals on an isolated copy using explicit ad-hoc signing.

This creates no Developer ID identity and never changes Gatekeeper settings.
The result remains a test artifact until independent distribution gates pass.
"""
import argparse,configparser,json,os,pathlib,plistlib,subprocess
p=argparse.ArgumentParser();p.add_argument('artifact',type=pathlib.Path);p.add_argument('platform',choices=['macos-arm64','macos-x64']);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio' or os.uname().sysname!='Darwin':raise SystemExit('Authorized native macOS test runner required')
a.output.mkdir(parents=True,exist_ok=True)
dmgs=list(a.artifact.glob('*.dmg'))
if len(dmgs)!=1:raise SystemExit('Exactly one original DMG required')
attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-nobrowse','-readonly','-plist',str(dmgs[0].resolve())]))
mounts=[pathlib.Path(x['mount-point']) for x in attached['system-entities'] if 'mount-point' in x]
app=a.output/'Rosavio.app'
try:
 apps=[app for mount in mounts for app in mount.glob('*.app')]
 if len(apps)!=1:raise SystemExit('Exactly one native application required')
 subprocess.run(['ditto',str(apps[0]),str(app)],check=True)
finally:
 for mount in reversed(mounts):subprocess.run(['hdiutil','detach',str(mount)],check=True)
info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
if info.get('CFBundleName')!='Rosavio':raise SystemExit('Wrong product')
local=list(a.artifact.rglob('local-update-test.json'))
if len(local)!=1:raise SystemExit('Signed local update report required')
tested=json.loads(local[0].read_text())
ini=configparser.ConfigParser();ini.read(app/'Contents/Resources/application.ini')
if not tested.get('passed') or tested.get('platform')!=a.platform or tested.get('after',{}).get('signatureDisabled',True) or ini.get('App','BuildID')!=tested['after']['buildID']:raise SystemExit('DMG must match the signature-enforced tested build')
magic={bytes.fromhex(x) for x in ['feedface','cefaedfe','feedfacf','cffaedfe','cafebabe','bebafeca','cafebabf','bfbafeca']}
# Remove only codesign-forbidden Finder metadata from the isolated copy.
# Preserve quarantine, provenance and every other security-related attribute.
removed_metadata=[]
for item in [app,*app.rglob('*')]:
 if item.is_symlink():continue
 for attribute in subprocess.check_output(['/usr/bin/xattr',str(item)],text=True).splitlines():
  if attribute in ('com.apple.FinderInfo','com.apple.ResourceFork'):
   subprocess.run(['/usr/bin/xattr','-d',attribute,str(item)],check=True)
   removed_metadata.append({'path':str(item.relative_to(a.output)),'attribute':attribute})
(a.output/'removed-finder-metadata.json').write_text(json.dumps(removed_metadata,indent=2))
signed=[]
def sign(target):
 subprocess.run(['codesign','--force','--sign','-','--timestamp=none','--preserve-metadata=entitlements',str(target)],check=True)
 signed.append(str(target.relative_to(a.output)))
main_binary=app/'Contents/MacOS'/info['CFBundleExecutable']
# codesign recognizes the main executable as the outer bundle: dependencies first.
for file in sorted(app.rglob('*'),key=lambda x:(x!=main_binary,len(x.parts)),reverse=True):
 if file==main_binary or file.is_symlink() or not file.is_file():continue
 with file.open('rb') as f:header=f.read(4)
 if header in magic:sign(file)
for bundle in sorted([x for x in app.rglob('*') if x.is_dir() and not x.is_symlink() and x.suffix in ['.app','.framework','.xpc']],key=lambda x:len(x.parts),reverse=True):sign(bundle)
sign(app)
subprocess.run(['codesign','--verify','--deep','--strict','--verbose=2',str(app)],check=True)
binary=app/'Contents/MacOS'/info['CFBundleExecutable']
subprocess.run(['node','scripts/check-unix-native.cjs',str(binary.resolve()),str(a.output/'native-check'),a.platform],check=True)
subprocess.run(['node','scripts/check-locales.cjs',str(binary.resolve()),str(a.output/'locale-check')],check=True)
def inspect(*args):
 r=subprocess.run(args,text=True,capture_output=True)
 return {'passed':r.returncode==0,'exitCode':r.returncode,'output':(r.stdout+r.stderr)[-16000:]}
report={'resourceSealVerified':True,'nativeStartAndTwentyLanguagesPassed':True,'identity':'ad-hoc test signing; no Developer ID','signedObjects':signed,'gatekeeper':inspect('spctl','--assess','--type','execute','--verbose=4',str(app)),'notarization':inspect('xcrun','stapler','validate',str(app)),'publicUpdateStillRequired':True,'published':False}
report['appleDistributionApproved']=report['gatekeeper']['passed'] and report['notarization']['passed']
(a.output/'signing-report.json').write_text(json.dumps(report,indent=2))
subprocess.run(['tar','-cJf',str(a.output/'Rosavio-signed-test.tar.xz'),'-C',str(a.output),'Rosavio.app'],check=True)
print('Complete bundle seal and twenty native languages passed. Apple distribution acceptance: '+str(report['appleDistributionApproved']))
