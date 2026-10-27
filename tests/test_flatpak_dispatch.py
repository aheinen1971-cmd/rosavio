import importlib.util,pathlib,tempfile,unittest,os
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('automatic',pathlib.Path(__file__).parents[1]/'scripts/flatpak-automatic.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
W='rosavio-flatpak-deploy.yml';P='Rosavio public Flatpak trial ';ID='unique-test-request'
def run(**kw):return {'id':123,'display_title':P+ID,'path':'.github/workflows/'+W,'head_branch':'main','event':'workflow_dispatch','status':'queued',**kw}
class DiscoveryTests(unittest.TestCase):
 def test_title_resolves_after_old_five_minute_limit(self):
  generic=run(display_title='Rosavio public Flatpak installation and update trial')
  with patch.object(m,'ghjson',side_effect=[{'workflow_runs':[generic]}]*70+[{'workflow_runs':[run()]}]) as api,patch.object(m.time,'sleep') as sleep,patch('builtins.print'):
   self.assertEqual(m.find_dispatched_run(W,P,ID)['id'],123);self.assertEqual(api.call_count,71);self.assertEqual(sleep.call_count,70)
 def test_unrelated_and_wrong_source_are_never_selected(self):
  bad=[run(display_title=P+'other'),run(path='.github/workflows/other.yml'),run(head_branch='other'),run(event='push')]
  with patch.object(m,'ghjson',side_effect=[{'workflow_runs':bad},{'workflow_runs':[run()]}]),patch.object(m.time,'sleep'),patch('builtins.print'):
   self.assertEqual(m.find_dispatched_run(W,P,ID)['id'],123)
 def test_ambiguous_request_fails_closed(self):
  with patch.object(m,'ghjson',return_value={'workflow_runs':[run(),run(id=124)]}):
   with self.assertRaisesRegex(SystemExit,'Ambiguous'):m.find_dispatched_run(W,P,ID)
 def test_timeout_records_request_and_never_posts(self):
  cwd=os.getcwd()
  with tempfile.TemporaryDirectory() as d:
   try:
    os.chdir(d)
    with patch.object(m,'ghjson',return_value={'workflow_runs':[run(display_title='generic')]} ) as api,patch.object(m.time,'sleep'),patch('builtins.print'):
     with self.assertRaisesRegex(SystemExit,'may still be queued'):m.find_dispatched_run(W,P,ID,attempts=3,interval=10)
     self.assertEqual(api.call_count,3);self.assertTrue(pathlib.Path('flatpak-dispatch-diagnostic.json').is_file());self.assertTrue(all('--method' not in c.args for c in api.call_args_list))
   finally:os.chdir(cwd)
 def test_dispatch_posts_once_and_waits_for_exact_run(self):
  with patch.object(m,'ghjson') as api,patch.object(m,'find_dispatched_run',return_value=run()) as find,patch.object(m,'wait_run',return_value={'passed':True}) as wait,patch('builtins.print'):
   self.assertTrue(m.dispatch(W,P,{'source_run':'456'})['passed']);self.assertEqual(api.call_count,1);wait.assert_called_once_with(123);self.assertEqual(api.call_args.kwargs['input']['inputs']['request_id'],find.call_args.args[2])
 def test_matching_failed_run_still_requires_success(self):
  with patch.object(m,'ghjson',return_value={'status':'completed','conclusion':'failure','html_url':'https://github.com/example'}):
   with self.assertRaisesRegex(SystemExit,'Downstream verification failed'):m.wait_run(123)
if __name__=='__main__':unittest.main()
