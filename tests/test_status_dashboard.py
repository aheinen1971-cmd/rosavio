import sys
import importlib.util,pathlib,unittest,json,subprocess
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"scripts"))
spec=importlib.util.spec_from_file_location('dashboard',pathlib.Path(__file__).parents[1]/'scripts/build-status-dashboard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class StatusTests(unittest.TestCase):
 def test_phase_progress_not_time_estimate(self):
  for label in m.PHASES:
   steps=[{'name':name,'conclusion':'success' if i==0 else None} for i,name in enumerate(m.PHASES[label])]
   result=m.with_progress(m.row(label,'yellow','old','running'),{'steps':steps})
   self.assertEqual(result['progress']['percent'],int(100/len(steps)))
 def test_only_verified_publication_can_reach_100(self):
  job={'steps':[{'name':name,'conclusion':'success'} for name in m.PHASES['Windows']]}
  for state in ['yellow','red']:
   self.assertEqual(m.with_progress(m.row('Windows',state,'old',''),job)['progress']['percent'],99)
  self.assertEqual(m.with_progress(m.row('Windows','green','new',''))['progress']['percent'],100)
 def test_missing_and_failed_steps_are_not_success(self):
  self.assertIsNone(m.with_progress(m.row('Linux','gray','?',''))['progress']['percent'])
  self.assertIsNone(m.with_progress(m.row('Linux','yellow','?',''),{'steps':[{'name':'unexpected','conclusion':'success'}]})['progress']['percent'])
  steps=[{'name':name,'conclusion':'skipped' if i else 'failure'} for i,name in enumerate(m.PHASES['Windows'])]
  self.assertEqual(m.with_progress(m.row('Windows','red','old',''),{'steps':steps})['progress']['percent'],0)
 def test_flatpak_wait_uses_release_identity_even_for_same_firefox_version(self):
  linux={'state':'yellow'}
  self.assertEqual(m.flatpak_wait(linux,'v159.0.1.2','v159.0.1.2','green'),'linux')
  self.assertEqual(m.flatpak_wait(linux,'v159.0.1.3','v159.0.1.2','green'),'flatpak')
  self.assertIsNone(m.flatpak_wait({'state':'green'},'same','same','green'))
  self.assertIsNone(m.flatpak_wait(linux,None,'old','green'))
  self.assertIsNone(m.flatpak_wait(linux,'new','old','red'))
 def test_duration_uses_only_active_phase_start(self):
  steps=[{'name':n,'status':'in_progress' if i==1 else 'completed','started_at':str(i)} for i,n in enumerate(m.PHASES['Windows'])]
  result=m.with_progress(m.row('Windows','yellow','159.0.1',''),{'steps':steps})
  self.assertEqual(result['progress']['startedAt'],'1')
 def test_feature_evidence_requires_post_update_test_and_matching_report(self):
  proof={'passed':True,'workspaceAfterUpdatePassed':True,'workspaceAfter':{'passed':True,'readingPlaceExistedBeforeUpdate':False}}
  old=m.feature_evidence(proof,'v1.2','Windows')
  self.assertEqual(old,{'reading':True,'rose':False})
  proof['workspaceAfter']['rosePathExistedBeforeUpdate']=False
  self.assertTrue(m.feature_evidence(proof,'v1.3','Linux')['download'].endswith('v1.3/Rosavio-Linux-x64.tar.xz'))
  proof['workspaceAfterUpdatePassed']=False
  self.assertFalse(m.feature_evidence(proof,'v1.3','Linux'))
 def test_change_time_persists_across_checks(self):
  import copy
  current={'checkedAt':'2026-11-04T12:00:00Z','rows':[{'label':'Linux','state':'yellow','detail':'running','progress':{'steps':['in_progress'],'startedAt':'2026-11-04T11:00:00Z'}}]}
  m.feature_changes(current,{})
  previous=copy.deepcopy(current)
  current['checkedAt']='2026-11-04T13:00:00Z'
  m.feature_changes(current,previous)
  self.assertEqual(current['rows'][0]['roseChange']['at'],'2026-11-04T11:00:00Z')
  current['rows'][0]['progress']={'steps':['success']}
  m.feature_changes(current,previous)
  self.assertEqual(current['rows'][0]['roseChange']['at'],current['checkedAt'])
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
