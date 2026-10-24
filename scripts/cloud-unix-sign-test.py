"""Use existing repository secrets only during signing, and erase the key afterwards."""
import json, os, pathlib, subprocess, sys, tempfile
platform=sys.argv[1]
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
    raise SystemExit('Only the authorized Rosavio cloud runner may sign')
if platform not in ['linux-x64','macos-x64','macos-arm64']:raise SystemExit('Invalid platform')
project=pathlib.Path.cwd();out=project/'unix-results'/platform
paths=json.loads((out/'paths.json').read_text())
key=os.environ.pop('ROSAVIO_UPDATE_KEY',None)
if not key or not os.environ.get('ROSAVIO_SIGNING_PASSWORD'):raise SystemExit('Existing signing secrets missing')
handle,name=tempfile.mkstemp(prefix='rosavio-encrypted-key-',dir=os.environ['RUNNER_TEMP'])
keypath=pathlib.Path(name)
try:
    with os.fdopen(handle,'w') as f:f.write(key)
    key=None;os.chmod(keypath,0o600)
    env={**os.environ,'ROSAVIO_KEY_PATH':str(keypath)}
    subprocess.run([sys.executable,str(project/'scripts/package-unix-update.py'),paths['source'],paths['package'],str(out/'release'),platform],env=env,check=True)
finally:
    keypath.unlink(missing_ok=True);os.environ.pop('ROSAVIO_SIGNING_PASSWORD',None)
subprocess.run(['node',str(project/'scripts/test-unix-update.cjs'),paths['baseline'],str(out/'release'),platform],check=True)
report=json.loads((out/'build.json').read_text())
report.update(signedLocalUpdateTestPassed=True,nativeAutoupdateTestPassed=False,published=False,state='signed local update passed; public native update test and release still required')
(out/'build.json').write_text(json.dumps(report,indent=2))
