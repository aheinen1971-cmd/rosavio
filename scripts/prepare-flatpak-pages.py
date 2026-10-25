"""Assemble current website and signed Flatpak objects without binary Git history."""
import argparse,json,pathlib,shutil,tarfile
p=argparse.ArgumentParser();p.add_argument('candidate',type=pathlib.Path);p.add_argument('revision',choices=['baseline','candidate']);p.add_argument('output',type=pathlib.Path);a=p.parse_args()
root=pathlib.Path.cwd();config=json.loads((root/'flatpak-signing.json').read_text());report=json.loads((a.candidate/'report.json').read_text())
if not report.get('passed') or not report.get('productionSigningConfigured') or report.get('signingFingerprint')!=config['fingerprint']:raise SystemExit('Verified production-signed candidate required')
if a.output.exists():raise SystemExit('Use a fresh Pages assembly directory')
shutil.copytree(root/'docs',a.output);repo=a.output/'flatpak';repo.mkdir()
with tarfile.open(a.candidate/('repository-'+a.revision+'.tar.xz')) as tf:tf.extractall(repo,filter='data')
for name in ['summary','summary.sig','config']:
 if not (repo/name).is_file():raise SystemExit('Incomplete signed repository')
for name in ['Rosavio.flatpakref','Rosavio.flatpakrepo']:shutil.copy2(a.candidate/'installation'/name,repo/name)
(a.output/'.nojekyll').touch()
size=sum(f.stat().st_size for f in a.output.rglob('*') if f.is_file())
if size>900*1024*1024:raise SystemExit('Pages payload exceeds safe size budget')
if len(list(a.output.glob('*.html')))!=20:raise SystemExit('All twenty website languages must remain')
print('Pages assembly verified:',a.revision,size,'bytes')
