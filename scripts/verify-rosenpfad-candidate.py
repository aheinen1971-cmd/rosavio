"""Fail closed before promoting the already qualified Rosenpfad artifacts."""
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);platform=sys.argv[2]
def read(name):return json.loads((root/name).read_text(encoding='utf-8-sig'))
def require(value,label):
 if value is not True:raise SystemExit('Candidate proof missing: '+label)
for name in ['locale-check/report.json','workspace-check/report.json','local-workspace-check/report.json' if platform=='windows' else 'release/local-workspace-check/report.json']:
 d=read(name);require(d.get('passed'),name)
 if 'workspace' in name:
  if d.get('runtimeOverlayOnly') is not False:raise SystemExit('Packaged native proof required')
  b=d['readingPlaces']['rosePath']['backup']
  for key in ['passed','realFileExport','explicitRestoreConfirmation','cancelPreservedState','stagedUntilSave','unrelatedDraftPreserved','invalidFileRejected']:require(b.get(key),key)
  for key in ['swapPassed','resizePassed']:require(d['splitControls'].get(key),key)
  for key in ['passed','fontSizeSaved','lineSpacingSaved','backgroundSaved','reloadPreserved']:require(d['readerEnterAndExit'].get(key),key)
 else:
  if len(d['languages'])!=20:raise SystemExit('All twenty languages required')
release=root if platform=='windows' else root/'release'
r=json.loads((release/'release.json').read_text(encoding='utf-8-sig'))
local=json.loads((release/'local-update-test.json').read_text(encoding='utf-8-sig'))
require(local.get('passed'),'signed local update')
require(local.get('workspaceAfterUpdatePassed'),'workspace after update')
require(r.get('signatureVerified'),'MAR signature')
if platform!='windows':
 require(r.get('signatureVerified'),'MAR signature')
 require(r.get('tamperNegativeTestPassed'),'tamper rejection')
mar=release/r['file']
if pathlib.Path(r['file']).name!=r['file']:raise SystemExit('Unsafe MAR path')
with mar.open('rb') as f:digest=hashlib.file_digest(f,'sha512').hexdigest()
if digest!=r['hashValue'] or mar.stat().st_size!=r['size']:raise SystemExit('MAR digest mismatch')
if r['appVersion']!='160.0':raise SystemExit('Unexpected candidate version')
print('Native Rosenpfad, reader, split view, twenty languages and update proof verified:',platform,r['buildID'])
