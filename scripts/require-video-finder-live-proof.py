"""Require the completed real integrated Windows UI check before publication."""
import json,pathlib
p=json.loads((pathlib.Path(__file__).resolve().parents[1]/'tests/evidence/video-finder-integrated-20261126.json').read_text())
if p.get('qualifiedCommit')!='48bd22cd2a8a13ce6c32821b950b55c4bdf80af0' or p.get('buildID')!='20261126001102':raise SystemExit('Wrong live proof identity')
if p.get('diagnosticHelperReplacement') is not False:raise SystemExit('Original qualified helper required; diagnostic helper swaps cannot be published')
for key in ['passed','realSidebarDetection','realSidebarDownload','audioVideoStrictDecode','cancelCleaned','localizedRejection']:
 if p.get(key) is not True:raise SystemExit('Integrated proof missing: '+key)
if p.get('qualityCount',0)<2 or p.get('downloadedBytes',0)<1000000:raise SystemExit('Real media proof missing')
print('Actual packaged Video Finder YouTube detection, download, cancellation and decoded audio/video passed')
