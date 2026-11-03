import importlib.util,pathlib,unittest
spec=importlib.util.spec_from_file_location('dashboard',pathlib.Path(__file__).parents[1]/'scripts/build-status-dashboard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StatusTests(unittest.TestCase):
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
