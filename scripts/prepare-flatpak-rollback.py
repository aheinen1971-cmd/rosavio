"""Preserve the current website and any last verified public Flatpak repository."""
import json,pathlib,shutil,sys,tarfile,urllib.request,urllib.error
out=pathlib.Path(sys.argv[1]);shutil.copytree('docs',out);(out/'.nojekyll').touch()
try:
 with urllib.request.urlopen('https://api.github.com/repos/aheinen1971-cmd/rosavio/releases/tags/rosavio-flatpak-repository',timeout=60) as f:release=json.load(f)
except urllib.error.HTTPError as e:
 if e.code!=404:raise
 print('No prior public Flatpak distribution; rollback preserves the existing website without Flatpak.')
else:
 assets={x['name']:x for x in release['assets']}
 for name in ['repository-candidate.tar.xz','Rosavio.flatpakref','Rosavio.flatpakrepo']:
  if name not in assets:raise SystemExit('Incomplete prior Flatpak rollback assets')
 repo=out/'flatpak';repo.mkdir()
 archive=out.parent/'prior-flatpak-repository.tar.xz'
 with urllib.request.urlopen(assets['repository-candidate.tar.xz']['browser_download_url'],timeout=120) as f,archive.open('wb') as d:shutil.copyfileobj(f,d)
 with tarfile.open(archive) as tf:tf.extractall(repo,filter='data')
 for name in ['Rosavio.flatpakref','Rosavio.flatpakrepo']:
  with urllib.request.urlopen(assets[name]['browser_download_url'],timeout=60) as f:(repo/name).write_bytes(f.read())
 print('Prior public Flatpak repository preserved for rollback.')
