"""Recheck saved sealed packages without compiling or loading signing secrets."""
import hashlib,json,os,pathlib,subprocess,tarfile,urllib.request
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
with urllib.request.urlopen('https://addons.mozilla.org/api/v5/addons/addon/multi-account-containers/',timeout=60) as response:addon=json.load(response)
xpi=addon['current_version']['file']['url']
if addon.get('guid')!='@testpilot-containers' or not xpi.startswith('https://addons.mozilla.org/'):raise SystemExit('Official signed extension source required')
os.environ['ROSAVIO_UPDATE_EXTENSION_XPI']=xpi
subprocess.run(['node','scripts/test-unix-update.cjs',str(app),str(out/'release'),platform],check=True)
subprocess.run(['codesign','--verify','--deep','--strict',str(out/'release/local-update/Rosavio.app')],check=True)
print('Saved native packages passed a new signature-enforced update and resource-seal check')
