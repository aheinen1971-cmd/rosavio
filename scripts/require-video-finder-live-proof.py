"""Require the completed real integrated Windows UI check before publication."""
import json,pathlib
p=json.loads((pathlib.Path(__file__).resolve().parents[1]/'tests/evidence/video-finder-integrated-20261126.json').read_text())
if p.get('qualifiedCommit')!='4955df9801b9cb9de578e68ee5afe9855ddd9d65' or p.get('buildID')!='20261126145619':raise SystemExit('Wrong live proof identity')
if p.get('diagnosticHelperReplacement') is not False:raise SystemExit('Original qualified helper required; diagnostic helper swaps cannot be published')
for key in ['passed','realSidebarDetection','realSidebarDownload','audioVideoStrictDecode','cancelCleaned','localizedRejection']:
 if p.get(key) is not True:raise SystemExit('Integrated proof missing: '+key)
if p.get('qualityCount',0)<2 or p.get('downloadedBytes',0)<1000000:raise SystemExit('Real media proof missing')
if not any(d.get('selector')=='312+bestaudio' and d.get('width')==1920 and d.get('height')==1080 and d.get('exitCode')==0 for d in p.get('decodes',[])):raise SystemExit('Actual 1080p image and audio decode required')
print('Actual packaged Video Finder YouTube detection, download, cancellation and decoded audio/video passed')
