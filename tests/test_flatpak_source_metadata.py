import importlib.util,pathlib,unittest,json,os
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('metadata',pathlib.Path(__file__).resolve().parents[1]/'scripts/flatpak_release_metadata.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
TAG='v159.0.1-rosavio-linux-x64.41652717409'
class Tests(unittest.TestCase):
 def test_token_scoped_to_authenticated_subprocess(self):
  with patch.dict(os.environ,{'KEEP':'yes'},clear=True),patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps({'tag_name':TAG,'assets':[]}))) as call:
   self.assertEqual(m.get_release(TAG,'test-only-token')['tag_name'],TAG)
   self.assertNotIn('GH_TOKEN',os.environ);self.assertEqual(call.call_args.kwargs['env']['GH_TOKEN'],'test-only-token');self.assertEqual(call.call_args.args[0][:2],['gh','api'])
 def test_bad_tag_or_missing_token_no_request(self):
  with patch.object(m.subprocess,'run') as call:
   for tag,token in [('https://evil.invalid','x'),(TAG,'')]:
    with self.assertRaises(ValueError):m.get_release(tag,token)
   call.assert_not_called()
 def test_failure_does_not_fallback(self):
  with patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='')) as call,self.assertRaises(RuntimeError):m.get_release(TAG,'test')
  self.assertEqual(call.call_count,1)
 def test_wrong_release_or_invalid_json_rejected(self):
  for data in ['invalid','{}',json.dumps({'tag_name':'wrong','assets':[]})]:
   with patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=data)),self.assertRaises(ValueError):m.get_release(TAG,'test')
if __name__=='__main__':unittest.main()
