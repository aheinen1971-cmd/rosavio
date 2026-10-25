"""Inspect the delivered DMG without installing it or weakening Gatekeeper."""
import argparse,json,os,pathlib,plistlib,subprocess
p=argparse.ArgumentParser();p.add_argument('artifact',type=pathlib.Path);p.add_argument('platform',choices=['macos-arm64','macos-x64']);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':raise SystemExit('Authorized isolated macOS runner required')
if os.uname().sysname!='Darwin':raise SystemExit('Native macOS required')
local=list(a.artifact.rglob('local-update-test.json'))
if len(local)!=1:raise SystemExit('Exactly one signed local update report required')
tested=json.loads(local[0].read_text())
if not tested.get('passed') or tested.get('platform')!=a.platform or tested.get('after',{}).get('signatureDisabled',True):raise SystemExit('Successful signature-enforced native update required')
dmgs=list(a.artifact.glob('*.dmg'))
if len(dmgs)!=1:raise SystemExit('Exactly one original native DMG required')
attached=plistlib.loads(subprocess.check_output(['hdiutil','attach','-nobrowse','-readonly','-plist',str(dmgs[0].resolve())]))
mounts=[pathlib.Path(x['mount-point']) for x in attached['system-entities'] if 'mount-point' in x]
def inspect(*cmd):
 r=subprocess.run(cmd,text=True,capture_output=True)
 return {'passed':r.returncode==0,'exitCode':r.returncode,'output':(r.stdout+r.stderr)[-16000:]}
try:
 apps=[app for mount in mounts for app in mount.glob('*.app')]
 if len(apps)!=1:raise SystemExit('Exactly one application in read-only DMG required')
 app=apps[0];info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
 executable=app/'Contents/MacOS'/info['CFBundleExecutable']
 arches=subprocess.check_output(['lipo','-archs',str(executable)],text=True).strip().split()
 expected={'macos-arm64':'arm64','macos-x64':'x86_64'}[a.platform]
 if expected not in arches or info.get('CFBundleName')!='Rosavio':raise SystemExit('Wrong native product or architecture')
 report={'platform':a.platform,'product':'Rosavio','architectures':arches,'nativeUpdateBuildID':tested['after']['buildID'],'readOnlyDMGInspected':True,'signature':inspect('codesign','--verify','--deep','--strict','--verbose=2',str(app)),'signatureIdentity':inspect('codesign','-d','--verbose=4',str(app)),'gatekeeper':inspect('spctl','--assess','--type','execute','--verbose=4',str(app)),'stapledNotarization':inspect('xcrun','stapler','validate',str(app))}
 report['appleDistributionApproved']=report['signature']['passed'] and report['gatekeeper']['passed']
 report['publicUpdateTestStillRequired']=True
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2))
 print('macOS distribution inspection recorded. Apple acceptance: '+str(report['appleDistributionApproved']))
finally:
 for mount in reversed(mounts):subprocess.run(['hdiutil','detach',str(mount)],check=True)
