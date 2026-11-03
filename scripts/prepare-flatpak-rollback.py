"""Preserve the current website and last verified public Flatpak repository."""
import json,pathlib,shutil,sys,tarfile,urllib.request,subprocess,re

def previous_release():
 result=subprocess.run(['gh','api','repos/aheinen1971-cmd/rosavio/releases/tags/rosavio-flatpak-repository'],capture_output=True,text=True)
 if result.returncode:
  if re.search(r'\(HTTP 404\)',result.stderr):return None
  raise RuntimeError('Authenticated GitHub rollback metadata request failed; deployment must stop')
 release=json.loads(result.stdout)
 if not isinstance(release,dict) or not isinstance(release.get('assets'),list):
  raise ValueError('Invalid rollback release metadata')
 return release

def main():
 release=previous_release()
 out=pathlib.Path(sys.argv[1]);shutil.copytree('docs',out);(out/'.nojekyll').touch()
 if release is None:
  print('No prior public Flatpak distribution; rollback preserves the existing website without Flatpak.')
  return
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

if __name__=='__main__':main()
