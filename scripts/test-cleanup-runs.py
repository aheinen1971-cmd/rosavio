import datetime,json,os,pathlib,runpy,subprocess,tempfile,unittest
from unittest.mock import patch
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'scripts/cleanup-resolved-runs.py'
class CleanupSafety(unittest.TestCase):
 def exercise(self,old_status='completed',old_result='failure',age=10,same_workflow=True,referenced=False,dry=False):
  now=datetime.datetime.now(datetime.timezone.utc)
  old={'status':old_status,'conclusion':old_result,'path':'.github/workflows/browser.yml','created_at':(now-datetime.timedelta(days=age)).isoformat()}
  new={'status':'completed','conclusion':'success','path':old['path'] if same_workflow else '.github/workflows/other.yml','created_at':now.isoformat()}
  deleted=[]
  def fake(args,**kw):
   identifier=args[-1].rsplit('/',1)[1]
   if args[3]=='DELETE':deleted.append(identifier);return subprocess.CompletedProcess(args,0,'','')
   value=new if identifier=='200' else None if deleted else old
   return subprocess.CompletedProcess(args,0,json.dumps(value),'') if value else subprocess.CompletedProcess(args,1,'','HTTP 404')
  with tempfile.TemporaryDirectory() as temp:
   previous=pathlib.Path.cwd();os.chdir(temp)
   try:
    pathlib.Path('.github/workflows').mkdir(parents=True)
    pathlib.Path('.github/workflows/browser.yml').write_text('run-id: 100' if referenced else 'name: browser')
    pathlib.Path('cleanup-approved-runs.json').write_text(json.dumps({'minimumAgeDays':7,'runs':[{'id':100,'replacement':200,'reason':'Resolved and retested'}]}))
    with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'aheinen1971-cmd/rosavio','DRY_RUN':str(dry).lower()}),patch('subprocess.run',side_effect=fake):runpy.run_path(str(SCRIPT),run_name='__main__')
    report=json.loads(pathlib.Path('cleanup-report.json').read_text())
   finally:os.chdir(previous)
  return deleted,report
 def test_reviewed_old_failure_deleted(self):self.assertEqual(self.exercise()[0],['100'])
 def test_success_never_deleted(self):self.assertEqual(self.exercise(old_result='success')[0],[])
 def test_running_never_deleted(self):self.assertEqual(self.exercise(old_status='in_progress')[0],[])
 def test_retention_enforced(self):self.assertEqual(self.exercise(age=1)[0],[])
 def test_wrong_replacement_kept(self):self.assertEqual(self.exercise(same_workflow=False)[0],[])
 def test_referenced_artifact_kept(self):self.assertEqual(self.exercise(referenced=True)[0],[])
 def test_preview_never_deletes(self):self.assertEqual(self.exercise(dry=True)[0],[])
if __name__=='__main__':unittest.main()
