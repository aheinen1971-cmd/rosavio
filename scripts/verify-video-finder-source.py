"""Allow release plumbing and documentation changes, never untested product bytes."""
import subprocess,sys
qualified=sys.argv[1]
allowed={'.github/workflows/video-finder-publish.yml','scripts/cloud-publish.ps1',
 'scripts/publish-linux-test.py','scripts/verify-video-finder-candidate.py',
 'scripts/require-video-finder-live-proof.py','scripts/verify-video-finder-source.py',
 'tests/test_video_finder_promotion.py','tests/evidence/video-finder-integrated-20261126.json'}
changed=subprocess.check_output(['git','diff','--name-only',qualified,'HEAD'],text=True).splitlines()
unexpected=[p for p in changed if p not in allowed and not p.startswith('docs/')]
if unexpected:raise SystemExit('Untested source changes: '+', '.join(unexpected))
print('All product source matches the qualified commit; only release checks/docs differ')
