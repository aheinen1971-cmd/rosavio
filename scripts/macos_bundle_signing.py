"""Seal a native Rosavio bundle without claiming Developer ID or notarization."""
import json, os, pathlib, plistlib, subprocess, sys

def seal_bundle(app, report_path):
 app=pathlib.Path(app).resolve()
 if sys.platform!='darwin' or os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
  raise RuntimeError('Authorized native macOS runner required')
 if app.suffix!='.app' or app.is_symlink():raise RuntimeError('Real app bundle required')
 info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
 if info.get('CFBundleName')!='Rosavio':raise RuntimeError('Wrong product')
 removed=[];signed=[]
 for item in [app,*app.rglob('*')]:
  if item.is_symlink():continue
  for attribute in subprocess.check_output(['/usr/bin/xattr',str(item)],text=True).splitlines():
   if attribute in ('com.apple.FinderInfo','com.apple.ResourceFork'):
    subprocess.run(['/usr/bin/xattr','-d',attribute,str(item)],check=True)
    removed.append({'path':str(item.relative_to(app)),'attribute':attribute})
 def sign(item):
  subprocess.run(['codesign','--force','--sign','-','--timestamp=none','--preserve-metadata=entitlements',str(item)],check=True)
  signed.append(str(item.relative_to(app)))
 magic={bytes.fromhex(x) for x in ['feedface','cefaedfe','feedfacf','cffaedfe','cafebabe','bebafeca','cafebabf','bfbafeca']}
 # Little-endian Mach-O 64-bit.
 magic.add(bytes.fromhex('cffaedfe'))
 for item in sorted(app.rglob('*'),key=lambda p:len(p.parts),reverse=True):
  if item.is_symlink() or not item.is_file():continue
  with item.open('rb') as f:header=f.read(4)
  if header in magic:sign(item)
 for item in sorted([p for p in app.rglob('*') if p.is_dir() and not p.is_symlink() and p.suffix in ('.app','.framework','.xpc')],key=lambda p:len(p.parts),reverse=True):sign(item)
 sign(app)
 subprocess.run(['codesign','--verify','--deep','--strict','--verbose=2',str(app)],check=True)
 def inspect(args):
  r=subprocess.run(args,text=True,capture_output=True)
  return {'passed':r.returncode==0,'exitCode':r.returncode,'output':(r.stdout+r.stderr)[-16000:]}
 report={'resourceSealVerified':True,'identity':'ad-hoc; no Developer ID','removedFinderMetadata':removed,'signedObjects':signed,'gatekeeper':inspect(['spctl','--assess','--type','execute','--verbose=4',str(app)]),'notarization':inspect(['xcrun','stapler','validate',str(app)]),'published':False}
 report['appleDistributionApproved']=report['gatekeeper']['passed'] and report['notarization']['passed']
 pathlib.Path(report_path).write_text(json.dumps(report,indent=2))
 return report

