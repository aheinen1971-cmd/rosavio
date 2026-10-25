"""Publish only a signed locally tested Linux artifact, then verify its public feed.

No private signing key is used by this workflow. Windows Latest is never changed.
"""
import configparser, hashlib, json, os, pathlib, re, subprocess, tarfile
from xml.sax.saxutils import quoteattr

if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
    raise SystemExit('Only the authorized public Rosavio runner may publish')
root=pathlib.Path.cwd();new=root/'linux-candidate';old=root/'linux-baseline';release=new/'release'
r=json.loads((release/'release.json').read_text());local=json.loads((release/'local-update-test.json').read_text())
if r.get('platform')!='linux-x64' or not r.get('signatureVerified') or not r.get('tamperNegativeTestPassed') or not local.get('passed'):
    raise SystemExit('Signed native local Linux test is mandatory')
if not re.fullmatch(r'\d+(?:\.\d+){1,3}',r['appVersion']) or not re.fullmatch(r'\d{14}',r['buildID']):raise SystemExit('Invalid version')
name=r['file']
if pathlib.Path(name).name!=name:raise SystemExit('Unsafe MAR path')
mar=release/name
with mar.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
if digest!=r['hashValue'] or mar.stat().st_size!=r['size']:raise SystemExit('Signed MAR hash mismatch')
package=release/'local-update/rosavio'
ini=configparser.ConfigParser();ini.read(package/'application.ini')
if ini.get('App','Name')!='Rosavio' or ini.get('App','BuildID')!=r['buildID']:raise SystemExit('Verified application missing')
def run(*args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
# Artifact ZIPs do not retain executable modes; restore only native launch tools.
for executable in ['rosavio','rosavio-bin','updater','glxtest','vaapitest','pingsender','crashhelper','minidump-analyzer']:
    file=package/executable
    if file.is_file():file.chmod(file.stat().st_mode|0o111)

archives=list(old.glob('*.tar.xz'))+list(old.glob('*.tar.bz2'))
if len(archives)!=1:raise SystemExit('Exactly one older baseline archive required')
extract=root/'baseline-app';extract.mkdir()
with tarfile.open(archives[0]) as tf:tf.extractall(extract,filter='data')
baselines=[x.parent for x in extract.rglob('rosavio') if x.is_file() and (x.parent/'application.ini').is_file()]
if len(baselines)!=1:raise SystemExit('Older native application missing')
baseline=baselines[0]
baseline_binary=baseline/'rosavio'
if not baseline_binary.is_file() or not os.access(baseline_binary,os.X_OK):raise SystemExit('Older baseline executable is missing or not executable')
run('node','scripts/check-unix-native.cjs',baseline_binary,root/'baseline-report','linux-x64')
b=json.loads((root/'baseline-report/report.json').read_text())
if b['buildID']>=r['buildID']:raise SystemExit('Public update needs an older genuine build')
run('node','scripts/check-locales.cjs',package,root/'candidate-languages')
run('node','scripts/check-extensions.cjs',package,root/'candidate-extensions')
run('node','scripts/check-translations.cjs',package,root/'candidate-translations')
archive=release/'Rosavio-Linux-x64.tar.xz'
run('tar','-cJf',archive,'-C',package.parent,package.name)
repo='aheinen1971-cmd/rosavio';stable='rosavio-linux-x64-latest'
tag=f'v{r["appVersion"]}-rosavio-linux-x64.{os.environ["GITHUB_RUN_ID"]}'
feedname='rosavio-linux-x64-update.xml';backup=root/'feed-backup';backup.mkdir()
env={**os.environ};latest_before=subprocess.check_output(['gh','api',f'repos/{repo}/releases/latest','--jq','.tag_name'],text=True).strip()
def gh(*args):return run('gh',*args)
def ensure_tag(t):
    exists=subprocess.run(['gh','api',f'repos/{repo}/git/ref/tags/{t}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if exists.returncode:gh('api',f'repos/{repo}/git/refs','-f',f'ref=refs/tags/{t}','-f','sha='+os.environ['GITHUB_SHA'])
ensure_tag(tag);ensure_tag(stable)
gh('release','create',tag,'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Rosavio Linux '+r['appVersion'],'--notes','Linux x64: signiertes Update mit aktivierter Signaturpruefung. Oeffentlicher nativer Update-Test laeuft noch.',mar,archive,release/'release.json',release/'local-update-test.json')
had_feed=subprocess.run(['gh','release','download',stable,'--repo',repo,'--pattern',feedname,'--dir',str(backup)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
if subprocess.run(['gh','release','view',stable,'--repo',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
    gh('release','create',stable,'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Rosavio Linux update feed','--notes','Plattformgetrennter signierter Linux-Updatekanal.')
attrs={'type':'minor','displayVersion':r['appVersion'],'appVersion':r['appVersion'],'platformVersion':r['appVersion'],'buildID':r['buildID']}
patch={'type':'complete','URL':f'https://github.com/{repo}/releases/download/{tag}/{name}','hashFunction':'SHA512','hashValue':digest,'size':str(r['size'])}
fmt=lambda d:' '.join(k+'='+quoteattr(v) for k,v in d.items())
feed=release/feedname;feed.write_text('<?xml version="1.0"?><updates><update '+fmt(attrs)+'><patch '+fmt(patch)+'/></update></updates>')
try:
    gh('release','upload',stable,feed,'--repo',repo,'--clobber')
    run('node','scripts/test-unix-update.cjs',baseline,release,'linux-x64',env={**os.environ,'ROSAVIO_PUBLIC_TEST':'1'})
    gh('release','upload',tag,release/'public-update-test.json','--repo',repo)
    # Keep as a prerelease until desktop launch/icon verification is also complete.
    gh('release','edit',tag,'--repo',repo,'--latest=false','--notes','Signiertes Linux-Autoupdate einschliesslich oeffentlichem Download, Installation und Neustart bestanden. Desktop-/Symbolpruefung noch ausstehend; Testversion.')
except BaseException:
    restore=backup/feedname
    if not had_feed:restore.write_text('<?xml version="1.0"?><updates/>')
    gh('release','upload',stable,restore,'--repo',repo,'--clobber')
    raise
finally:
    latest_after=subprocess.check_output(['gh','api',f'repos/{repo}/releases/latest','--jq','.tag_name'],text=True).strip()
    if latest_after!=latest_before:raise SystemExit('Windows Latest changed unexpectedly')
print('Public signed native Linux update passed; desktop/icon checks still required before final release.')
