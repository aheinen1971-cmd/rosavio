import copy
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('watchdog', pathlib.Path(__file__).parents[1] / 'scripts/build-watchdog.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
NOW = 10000

class Fake:
    def __init__(self):
        self.state = {'schema': 1, 'entries': {}}
        self.posts = []
        self.saved = []
        self.inv = ([], [], [])
        self.fail_save = False
        self.fail_post = False
    def read(self): return copy.deepcopy(self.state), 'sha'
    def inventory(self, *args): return self.inv
    def save(self, state, sha):
        if self.fail_save: raise RuntimeError('conflict')
        self.state = copy.deepcopy(state)
        self.saved.append(copy.deepcopy(state))
        return 'sha'
    def api(self, route, method, data):
        self.posts.append((route, data))
        assert self.state['entries']['161.0/' + ('Windows' if 'rosavio-build.yml' in route else 'Linux')]['dispatchAt'] == NOW
        if self.fail_post: raise TimeoutError('ambiguous')

class Tests(unittest.TestCase):
    def decision(self, runs=None, refs=None, releases=None, entry=None, platform='Windows'):
        return w.decide('161.0', platform, runs or [], refs or [], releases or [], entry or {'firstSeen': 0}, NOW)
    def test_new_version_waits(self):
        c=Fake(); self.assertEqual(w.check(c,'161.0',NOW,True),dict(Windows='grace-period',Linux='grace-period')); self.assertEqual(c.posts,[])
    def test_exact_grace(self):
        self.assertEqual(self.decision(entry={'firstSeen':NOW-w.GRACE+1}), 'grace-period')
        self.assertEqual(self.decision(entry={'firstSeen':NOW-w.GRACE}), 'dispatch')
    def test_active_states(self):
        for status in ['queued','in_progress','waiting','requested','pending']:
            self.assertEqual(self.decision(runs=[{'status':status}]),'active-run')
    def test_regular_publication_only(self):
        r={'draft':False,'prerelease':False,'tag_name':'v161.0-rosavio.42'}
        self.assertEqual(self.decision(releases=[r]),'published')
        self.assertEqual(self.decision(releases=[dict(r,draft=True)]),'dispatch')
        self.assertEqual(self.decision(releases=[dict(r,prerelease=True)]),'dispatch')
    def test_platform_and_version_isolation(self):
        for tag in ['v161.0-rosavio-linux-x64.42','v161.0.1-rosavio.42','v160.0.1-rosavio.42']:
            self.assertEqual(self.decision(refs=[{'ref':'refs/tags/'+tag}]),'dispatch')
    def test_failed_attempt_no_repeat(self):
        self.assertEqual(self.decision(runs=[{'id':42,'status':'completed','conclusion':'failure'}],refs=[{'ref':'refs/tags/v161.0-rosavio.42'}]),'attempt-needs-review')
    def test_unknown_reserved_attempt_stops(self):
        with self.assertRaises(ValueError): self.decision(refs=[{'ref':'refs/tags/v161.0-rosavio.42'}])
    def test_dispatch_discovery_deadline(self):
        self.assertEqual(self.decision(entry={'firstSeen':0,'dispatchAt':NOW-1199}),'awaiting-run')
        self.assertEqual(self.decision(entry={'firstSeen':0,'dispatchAt':NOW-1200}),'missing-dispatched-run')
    def test_completed_check_without_result(self):
        self.assertEqual(self.decision(runs=[{'status':'completed','created_at':'1970-01-01T02:46:40Z'}],entry={'firstSeen':0,'dispatchAt':NOW-30}),'completed-without-publication')
    def test_dry_run_cannot_write(self):
        c=Fake(); c.state['entries']={'161.0/Windows':{'firstSeen':0},'161.0/Linux':{'firstSeen':0}}
        self.assertEqual(w.check(c,'161.0',NOW),dict(Windows='dispatch',Linux='dispatch'));self.assertFalse(c.posts or c.saved)
    def test_claim_before_dispatch_and_repeat_suppressed(self):
        c=Fake(); c.state['entries']={'161.0/Windows':{'firstSeen':0},'161.0/Linux':{'firstSeen':0}}
        self.assertEqual(w.check(c,'161.0',NOW,True),dict(Windows='dispatched-once',Linux='dispatched-once'))
        self.assertEqual(len(c.posts),2)
        for route,payload in c.posts:
            self.assertNotIn('flatpak',route);self.assertEqual(payload,{'ref':'main','inputs':{'force':False}})
        w.check(c,'161.0',NOW+10,True);self.assertEqual(len(c.posts),2)
    def test_ambiguous_post_preserves_claim(self):
        c=Fake();c.state['entries']={'161.0/Windows':{'firstSeen':0}};c.fail_post=True
        with self.assertRaises(TimeoutError):w.check(c,'161.0',NOW,True)
        self.assertEqual(len(c.posts),1);c.fail_post=False
        w.check(c,'161.0',NOW+10,True);self.assertEqual(len(c.posts),1)
    def test_state_conflict_no_post(self):
        c=Fake();c.state['entries']={'161.0/Windows':{'firstSeen':0}};c.fail_save=True
        with self.assertRaises(RuntimeError):w.check(c,'161.0',NOW,True)
        self.assertFalse(c.posts)
    def test_race_active_before_claim(self):
        c=Fake();c.state['entries']={'161.0/Windows':{'firstSeen':0}}; n=0
        def inv(*args):
            nonlocal n
            n+=1;return ([],[],[]) if n==1 else ([{'status':'queued'}],[],[])
        c.inventory=inv;w.check(c,'161.0',NOW,True);self.assertFalse(c.posts)
    def test_inventory_error_no_write(self):
        c=Fake()
        def inv(*args):raise RuntimeError('API unavailable')
        c.inventory=inv
        with self.assertRaises(RuntimeError):w.check(c,'161.0',NOW,True)
        self.assertFalse(c.posts or c.saved)
    def test_invalid_version(self):
        with self.assertRaises(ValueError):w.check(Fake(),'161.0/evil',NOW,True)
    def test_invalid_saved_times_stop(self):
        for field,value in [('firstSeen',float('nan')),('firstSeen',NOW+1),('dispatchAt','invalid'),('dispatchAt',NOW+1)]:
            c=Fake();c.state['entries']={'161.0/Windows':{'firstSeen':0,field:value}}
            with self.assertRaises(ValueError):w.check(c,'161.0',NOW,True)
            self.assertFalse(c.posts or c.saved)
    def test_linux_reservation_blocks_retry(self):
        self.assertEqual(self.decision(platform='Linux',runs=[{'id':42,'status':'completed'}],refs=[{'ref':'refs/tags/v161.0-rosavio-linux-x64.42'}]),'attempt-needs-review')
    def test_linux_active_windows_missing(self):
        c=Fake();c.state['entries']={'161.0/Windows':{'firstSeen':0}}
        c.inventory=lambda version,platform:([{'status':'in_progress'}],[],[]) if platform=='Linux' else ([],[],[])
        result=w.check(c,'161.0',NOW,True)
        self.assertEqual(result,dict(Windows='dispatched-once',Linux='active-run'));self.assertEqual(len(c.posts),1)
    def test_status_job_keeps_narrow_permissions_and_event_guard(self):
        workflow=(pathlib.Path(__file__).parents[1]/'.github/workflows/rosavio-status.yml').read_text()
        self.assertIn('cancel-in-progress: false',workflow)
        job=workflow.split('  build-watchdog:')[1]
        self.assertIn("github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",job)
        self.assertIn('needs: status',job)
    def test_pagination(self):
        c=w.Client(); c.api=lambda path: {'workflow_runs':[{}]*100} if 'page=1'==path.split('&')[-1] else {'workflow_runs':[]}
        self.assertEqual(len(c.pages('actions/runs','workflow_runs')),100)
    def test_incomplete_pagination(self):
        c=w.Client();c.api=lambda path:[{}]*100
        with self.assertRaises(ValueError):c.pages('releases')

if __name__=='__main__':unittest.main()
