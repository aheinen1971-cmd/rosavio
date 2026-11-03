import importlib.util,unittest,json,tempfile,pathlib,io,tarfile,sys,os
from unittest.mock import patch
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('rollback',pathlib.Path(__file__).resolve().parents[1]/'scripts/prepare-flatpak-rollback.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def result(self,code=0,out='{"assets":[]}',err=''):return SimpleNamespace(returncode=code,stdout=out,stderr=err)
 def test_all_rollback_workflow_callers_supply_scoped_auth(self):
  root=pathlib.Path(__file__).resolve().parents[1]/'.github/workflows'
  found=[]
  for f in root.glob('*.yml'):
   for step in f.read_text(encoding='utf8').split('      - '):
    if 'scripts/prepare-flatpak-rollback.py' in step:
     found.append(f.name);self.assertIn('GH_TOKEN: ${{ github.token }}',step,f.name)
  self.assertEqual(set(found),{'rosavio-pages.yml','rosavio-flatpak-deploy.yml'})
 def test_authenticated_api(self):
  with patch.object(m.subprocess,'run',return_value=self.result()) as p:
   self.assertEqual(m.previous_release(),{'assets':[]});self.assertEqual(p.call_args.args[0],['gh','api','repos/aheinen1971-cmd/rosavio/releases/tags/rosavio-flatpak-repository'])
 def test_missing_only_404(self):
  with patch.object(m.subprocess,'run',return_value=self.result(1,err='gh: Not Found (HTTP 404)')):self.assertIsNone(m.previous_release())
 def test_other_errors_stop(self):
  for err in ['gh: rate limit (HTTP 403)','gh: Unauthorized (HTTP 401)','network unavailable']:
   with patch.object(m.subprocess,'run',return_value=self.result(1,err=err)),self.assertRaises(RuntimeError):m.previous_release()
 def test_invalid_metadata_stop(self):
  for value in ['bad','{}','[]','{"assets":{}}']:
   with patch.object(m.subprocess,'run',return_value=self.result(out=value)),self.assertRaises(ValueError):m.previous_release()
 def test_preserves_existing_repo(self):
  archive=io.BytesIO()
  with tarfile.open(fileobj=archive,mode='w:xz') as tf:
   info=tarfile.TarInfo('summary.sig');info.size=3;tf.addfile(info,io.BytesIO(b'sig'))
  names=['repository-candidate.tar.xz','Rosavio.flatpakref','Rosavio.flatpakrepo'];release={'assets':[{'name':n,'browser_download_url':'https://example.invalid/'+n} for n in names]}
  with tempfile.TemporaryDirectory() as d:
   old=os.getcwd();os.chdir(d)
   try:
    pathlib.Path('docs').mkdir();pathlib.Path('docs/index.html').write_text('site')
    with patch.object(m,'previous_release',return_value=release),patch.object(sys,'argv',['test','restore']),patch.object(m.urllib.request,'urlopen',side_effect=lambda url,**kw:io.BytesIO(archive.getvalue() if url.endswith('.xz') else b'descriptor')):m.main()
    self.assertEqual(pathlib.Path('restore/index.html').read_text(),'site');self.assertEqual(pathlib.Path('restore/flatpak/summary.sig').read_bytes(),b'sig');self.assertEqual(pathlib.Path('restore/flatpak/Rosavio.flatpakref').read_bytes(),b'descriptor')
   finally:os.chdir(old)
 def test_failure_before_site_copy(self):
  with patch.object(m,'previous_release',side_effect=RuntimeError('403')),patch.object(m.shutil,'copytree') as copy,self.assertRaises(RuntimeError):
   m.main()
  copy.assert_not_called()
if __name__=='__main__':unittest.main()
