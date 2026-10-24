"""Sign a native Unix complete MAR; never publish before native update tests."""
import argparse, configparser, hashlib, json, os, pathlib, subprocess

p=argparse.ArgumentParser()
p.add_argument('source', type=pathlib.Path)
p.add_argument('package', type=pathlib.Path)
p.add_argument('output', type=pathlib.Path)
p.add_argument('platform', choices=['linux-x64','macos-x64','macos-arm64'])
a=p.parse_args()
project=pathlib.Path(__file__).resolve().parent.parent
source=a.source.resolve(); package=a.package.resolve(); out=a.output.resolve()
out.mkdir(parents=True,exist_ok=True)
resources=package/'Contents/Resources' if a.platform.startswith('macos') else package
ini=configparser.ConfigParser();ini.read(resources/'application.ini')
if ini.get('App','Name')!='Rosavio':raise SystemExit('Wrong package identity')
version=ini.get('App','Version');build=ini.get('App','BuildID')
if not build.isdecimal() or len(build)!=14:raise SystemExit('Invalid native BuildID')
report=json.loads((out.parent/'native-check/report.json').read_text())
expected_abi={'linux-x64':'x86_64','macos-x64':'x86_64','macos-arm64':'aarch64'}[a.platform]
if not report.get('passed') or report['buildID']!=build or report['version']!=version or not report['abi'].startswith(expected_abi):
    raise SystemExit('Native identity/architecture report does not match package')
if report['signatureVerificationDisabled']:raise SystemExit('Signature verification must remain enabled')
def find_tool(name):
    for base in ['bin','host/bin']:
        candidate=source/'obj-rose/dist'/base/name
        if candidate.is_file():return candidate
    raise SystemExit('Native tool missing: '+name)
mar=find_tool('mar');signmar=find_tool('signmar')
signed=out/f'rosavio-{a.platform}-{build}.complete.mar'
unsigned=out/'unsigned.mar'
env={**os.environ,'MAR':str(mar),'MOZ_PRODUCT_VERSION':version,'MAR_CHANNEL_ID':'rosavio-release'}
subprocess.run(['bash',str(source/'tools/update-packaging/make_full_update.sh'),str(unsigned),str(package),'rosavio'],env=env,check=True,cwd=source)
key=os.environ.get('ROSAVIO_KEY_PATH')
if not key or not os.environ.get('ROSAVIO_SIGNING_PASSWORD'):raise SystemExit('Signing secrets missing')
subprocess.run([os.sys.executable,str(project/'scripts/sign-mar.py'),str(unsigned),str(signed),key,str(project/'certificates/rosavio-update.der'),'--platform',a.platform],check=True)
verify=[str(signmar),'-D',str(project/'certificates/rosavio-update.der'),'-v']
subprocess.run([*verify,str(signed)],check=True)
tampered=out/'tampered.mar'
try:
    import shutil
    shutil.copy2(signed,tampered)
    with tampered.open('r+b') as f:
        f.seek(-1,2);b=f.read(1);f.seek(-1,2);f.write(bytes([b[0]^1]))
    if subprocess.run([*verify,str(tampered)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        raise SystemExit('Tampered MAR unexpectedly verified')
finally:
    tampered.unlink(missing_ok=True);unsigned.unlink(missing_ok=True)
with signed.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
(out/'release.json').write_text(json.dumps({'product':'Rosavio','platform':a.platform,'appVersion':version,'buildID':build,'file':signed.name,'size':signed.stat().st_size,'hashValue':digest,'signatureVerified':True,'tamperNegativeTestPassed':True,'published':False},indent=2))
print('Native Unix MAR signature and tamper rejection passed; publication is still gated.')
