"""Delete only explicitly reviewed failed runs with a successful replacement."""
import datetime,json,os,pathlib,re,subprocess
REPO='aheinen1971-cmd/rosavio'
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise SystemExit('Authorized runner only')
config=json.loads(pathlib.Path('cleanup-approved-runs.json').read_text())
days=config.get('minimumAgeDays',7)
if not isinstance(days,int) or days<7:raise SystemExit('Minimum seven-day retention required')
dry=os.environ.get('DRY_RUN','true').lower()!='false'
def api(endpoint,method='GET'):
 r=subprocess.run(['gh','api','--method',method,f'repos/{REPO}/'+endpoint],capture_output=True,text=True)
 if r.returncode:
  if 'HTTP 404' in r.stderr:return None
  raise RuntimeError('GitHub API operation failed: '+endpoint)
 return json.loads(r.stdout) if r.stdout.strip() else {}
workflows='\n'.join(p.read_text() for p in pathlib.Path('.github/workflows').glob('*.yml'))
now=datetime.datetime.now(datetime.timezone.utc);report=[]
for item in config['runs']:
 old=str(item['id']);new=str(item['replacement'])
 if not old.isdecimal() or not new.isdecimal() or old==new or not item.get('reason','').strip():raise SystemExit('Invalid reviewed cleanup entry')
 if re.search(r'(?<!\d)'+re.escape(old)+r'(?!\d)',workflows):
  report.append({'id':old,'action':'kept','reason':'Workflow still references this run'});continue
 before=api('actions/runs/'+old);replacement=api('actions/runs/'+new)
 if before is None:report.append({'id':old,'action':'already absent'});continue
 if before['status']!='completed' or before['conclusion']!='failure':
  report.append({'id':old,'action':'kept','reason':'Only completed failures may be deleted'});continue
 created=datetime.datetime.fromisoformat(before['created_at'].replace('Z','+00:00'))
 if (now-created).days<days:
  report.append({'id':old,'action':'kept','reason':'Retention period not reached'});continue
 if not replacement or replacement['status']!='completed' or replacement['conclusion']!='success' or replacement['path']!=before['path'] or replacement['created_at']<=before['created_at']:
  report.append({'id':old,'action':'kept','reason':'Matching newer successful replacement required'});continue
 if not dry:
  # Recheck immediately before deletion; never touch a rerun which changed status.
  latest=api('actions/runs/'+old)
  if latest and (latest['status']!='completed' or latest['conclusion']!='failure'):raise SystemExit('Run changed state')
  if latest is not None:api('actions/runs/'+old,'DELETE')
  if api('actions/runs/'+old) is not None:raise SystemExit('Deletion not confirmed')
 report.append({'id':old,'replacement':new,'action':'would delete' if dry else 'deleted','reviewReason':item['reason']})
pathlib.Path('cleanup-report.json').write_text(json.dumps({'dryRun':dry,'retentionDays':days,'runs':report},indent=2))
print(json.dumps({'dryRun':dry,'reviewedEntries':len(config['runs']),'results':report}))
