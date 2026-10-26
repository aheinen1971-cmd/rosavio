"""Use existing repository secrets only during signing, and erase the key afterwards."""
import json, os, pathlib, subprocess, sys, tempfile, urllib.request
platform=sys.argv[1]
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
    raise SystemExit('Only the authorized Rosavio cloud runner may sign')
if platform not in ['linux-x64','macos-x64','macos-arm64']:raise SystemExit('Invalid platform')
project=pathlib.Path.cwd();out=project/'unix-results'/platform
paths=json.loads((out/'paths.json').read_text())
key=os.environ.pop('ROSAVIO_UPDATE_KEY',None)
password=os.environ.pop('ROSAVIO_SIGNING_PASSWORD',None)
if not key or not password:raise SystemExit('Existing signing secrets missing')
if platform.startswith('macos'):
    from macos_bundle_signing import seal_bundle
    # Seal both genuine builds before constructing the update archive.
    # The original pre-sealing DMG must never masquerade as this candidate.
    for kind in ('baseline','package'):
        seal_bundle(paths[kind],out/(kind+'-app-signature.json'))
    subprocess.run(['node',str(project/'scripts/check-locales.cjs'),str(pathlib.Path(paths['package'])/'Contents/MacOS/rosavio'),str(out/'sealed-locale-check')],check=True)
    for dmg in out.glob('*.dmg'):
        dmg.rename(dmg.with_suffix('.dmg.unsealed-not-for-distribution'))
    subprocess.run(['hdiutil','create','-volname','Rosavio','-srcfolder',paths['package'],'-format','UDZO',str(out/'Rosavio-sealed-test.dmg')],check=True)
    subprocess.run(['tar','-cJf',str(out/'Rosavio-sealed-baseline.tar.xz'),'-C',str(pathlib.Path(paths['baseline']).parent),pathlib.Path(paths['baseline']).name],check=True)
handle,name=tempfile.mkstemp(prefix='rosavio-encrypted-key-',dir=os.environ['RUNNER_TEMP'])
keypath=pathlib.Path(name)
try:
    with os.fdopen(handle,'w') as f:f.write(key)
    key=None;os.chmod(keypath,0o600)
    env={**os.environ,'ROSAVIO_KEY_PATH':str(keypath),'ROSAVIO_SIGNING_PASSWORD':password}
    subprocess.run([sys.executable,str(project/'scripts/package-unix-update.py'),paths['source'],paths['package'],str(out/'release'),platform],env=env,check=True)
finally:
    keypath.unlink(missing_ok=True);password=None;env=None
if os.environ.get('ROSAVIO_MAC_DESKTOP_TEST')=='1' or os.environ.get('ROSAVIO_DESKTOP_TEST')=='1':
    # Local preservation tests need the same official signed extension as public tests.
    with urllib.request.urlopen('https://addons.mozilla.org/api/v5/addons/addon/multi-account-containers/',timeout=60) as response:
        addon=json.load(response)
    xpi=addon['current_version']['file']['url']
    if addon.get('guid')!='@testpilot-containers' or not xpi.startswith('https://addons.mozilla.org/'):
        raise SystemExit('Official Containers identity and HTTPS source required')
    os.environ['ROSAVIO_UPDATE_EXTENSION_XPI']=xpi
subprocess.run(['node',str(project/'scripts/test-unix-update.cjs'),paths['baseline'],str(out/'release'),platform],check=True)
report=json.loads((out/'build.json').read_text())
report.update(signedLocalUpdateTestPassed=True,nativeAutoupdateTestPassed=False,published=False,state='signed local update passed; public native update test and release still required')
(out/'build.json').write_text(json.dumps(report,indent=2))
