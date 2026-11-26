"""Fail closed when promoting the exact retained Video Finder qualification."""
import hashlib,json,pathlib,sys,zipfile
root=pathlib.Path(sys.argv[1]);platform=sys.argv[2]
def read(name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
def require(value,label):
 if value is not True:raise SystemExit('Missing candidate proof: '+label)
for name in ['locale-check/report.json','workspace-check/report.json','extensions-check/report.json']:
 d=read(name);require(d.get('passed'),name)
 if name.startswith('locale') and len(d.get('languages',[]))!=20:raise SystemExit('Twenty native languages required')
 if name.startswith('extensions'):
  require(d['media']['builtIn'],'built-in media');require(d['media']['active'],'active media')
  if d['media']['version']!='2.2.0':raise SystemExit('Wrong media version')
  for section in ['nativeBridge','nativeGuard']:require(d[section]['passed'],section)
  require(d['nativeBridge']['foreignURLRejected'],'foreign URL rejection')
release=root if platform=='windows' else root/'release'
r=json.loads((release/'release.json').read_text(encoding='utf-8-sig'))
local=json.loads((release/'local-update-test.json').read_text(encoding='utf-8-sig'))
for key in ['passed','workspaceAfterUpdatePassed']:require(local.get(key),key)
require(r.get('signatureVerified'),'MAR signature')
if platform!='windows':require(r.get('tamperNegativeTestPassed'),'tamper rejection')
expected='20261126001102' if platform=='windows' else '20261126015716'
if r['appVersion']!='161.0' or r['buildID']!=expected:raise SystemExit('Wrong qualified build')
if pathlib.Path(r['file']).name!=r['file']:raise SystemExit('Unsafe MAR filename')
mar=release/r['file']
with mar.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
if digest!=r['hashValue'] or mar.stat().st_size!=r['size']:raise SystemExit('MAR digest mismatch')
if platform=='windows':
 for line in (release/'Rosavio-SHA256SUMS.txt').read_text(encoding='utf-8-sig').splitlines():
  expected,name=line.split(None,1);name=name.strip()
  if pathlib.Path(name).name!=name:raise SystemExit('Unsafe checksum filename')
  with (release/name).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  if actual!=expected.lower():raise SystemExit('Package checksum mismatch: '+name)
 with zipfile.ZipFile(release/'Rosavio-Deutsch-Windows.zip') as z:
  names=z.namelist()
  for suffix in ['/video-finder/source/ffmpeg-9.1.tar.xz','/video-finder/source/mutagen-source.json','/video-finder/licenses/Python-LICENSE.txt']:
   if not any(n.endswith(suffix) for n in names):raise SystemExit('Missing redistributed sources/license: '+suffix)
else:
 package=release/'local-update/rosavio/video-finder'
 for name in ['source/ffmpeg-9.1.tar.xz','source/mutagen-source.json','licenses/Python-LICENSE.txt']:
  if not (package/name).is_file():raise SystemExit('Missing redistributed sources/license: '+name)
print('Exact Video Finder package, native bridge, twenty languages and signed update verified:',platform,expected)
