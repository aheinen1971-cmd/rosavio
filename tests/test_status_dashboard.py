import importlib.util,pathlib,unittest,json,subprocess
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('dashboard',pathlib.Path(__file__).parents[1]/'scripts/build-status-dashboard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StatusTests(unittest.TestCase):
 def test_static_publication_only_data_branch(self):
  for head in [None,{'object':{'sha':'old'}}]:
   calls=[]
   def run(args,**kwargs):
    calls.append((args,kwargs))
    if len(calls)==1:
     return subprocess.CompletedProcess(args,0,json.dumps(head),'') if head else subprocess.CompletedProcess(args,1,'','gh: Not Found (HTTP 404)')
    return subprocess.CompletedProcess(args,0,json.dumps({'sha':'new'}),'')
   with patch.object(m.subprocess,'run',side_effect=run):m.publish_static({'schema':1,'rows':[]})
   tree=json.loads(calls[1][1]['input'])['tree']
   self.assertEqual([f['path'] for f in tree],['status.json'])
   self.assertEqual(json.loads(calls[2][1]['input'])['parents'],['old'] if head else [])
   final=json.loads(calls[-1][1]['input'])
   if head:self.assertIs(final['force'],False)
   else:self.assertEqual(final['ref'],'refs/heads/rosavio-status-data')
 def test_rate_limit_never_creates_or_overwrites_branch(self):
  with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','gh: API rate limit exceeded (HTTP 403)')) as run:
   with self.assertRaises(RuntimeError):m.publish_static({})
   self.assertEqual(run.call_count,1)
 def test_client_no_longer_uses_github_api(self):
  root=pathlib.Path(__file__).parents[1]/'docs/status'
  js=(root/'status.js').read_text(encoding='utf-8')
  self.assertNotIn('api.github.com',js)
  self.assertIn('rosavio-status-data/status.json',js)
  self.assertIn('connect-src https://raw.githubusercontent.com',(root/'index.html').read_text(encoding='utf-8'))
 def test_patch_version_beats_run_number(self):
  self.assertGreater(m.release_key({'tag_name':'v159.0.1-rosavio.2'}),m.release_key({'tag_name':'v159.0-rosavio.999999'}))
 def test_successful_skip_not_release(self):
  self.assertEqual(m.run_state({'status':'completed','conclusion':'success'},'159.0','159.0.1')[0],'yellow')
 def test_only_verified_current_is_green(self):
  self.assertEqual(m.run_state(None,'159.0.1','159.0.1')[0],'green')
 def test_active_does_not_mean_complete(self):
  self.assertEqual(m.run_state({'status':'in_progress'},'159.0.1','159.0.1')[0],'yellow')
 def test_failed_and_cancelled_visible(self):
  for conclusion in ['failure','timed_out','cancelled','action_required']:
   self.assertEqual(m.run_state({'status':'completed','conclusion':conclusion},'159.0','159.0.1')[0],'red')
 def test_page_uses_text_not_html(self):
  js=(pathlib.Path(__file__).parents[1]/'docs/status/status.js').read_text(encoding='utf-8')
  self.assertNotIn('innerHTML',js);self.assertIn('textContent',js)
if __name__=='__main__':unittest.main()
