"""Update Flatpak only from a newer verified native Linux release, then test public delivery."""
import datetime,json,os,pathlib,re,subprocess,time,urllib.request,uuid,xml.etree.ElementTree as ET
REPO='aheinen1971-cmd/rosavio'
def ghjson(*args,input=None):
 r=subprocess.run(['gh',*args],input=json.dumps(input) if input is not None else None,text=True,capture_output=True,check=True)
 return json.loads(r.stdout) if r.stdout.strip() else None
def getjson(url):
 with urllib.request.urlopen(url,timeout=60) as f:return json.load(f)
def wait_run(runid):
 for attempt in range(300):
  r=ghjson('api',f'repos/{REPO}/actions/runs/{runid}')
  if r['status']=='completed':
   if r['conclusion']!='success':raise SystemExit('Downstream verification failed: '+r['html_url'])
   return r
  time.sleep(20)
 raise SystemExit('Downstream verification timed out')
def find_dispatched_run(workflow,prefix,identifier,attempts=120,interval=10):
 # GitHub may expose queued runs under a generic title for more than five
 # minutes. Keep the unique request ID mandatory; never select a recent run
 # merely because its workflow or queue position looks plausible.
 expected=prefix+identifier
 for attempt in range(attempts):
  runs=ghjson('api',f'repos/{REPO}/actions/workflows/{workflow}/runs?event=workflow_dispatch&branch=main&per_page=100')['workflow_runs']
  matching=[r for r in runs if r.get('display_title')==expected and r.get('path')=='.github/workflows/'+workflow and r.get('head_branch')=='main' and r.get('event')=='workflow_dispatch']
  if len(matching)>1:raise SystemExit('Ambiguous downstream dispatch: '+identifier)
  if matching:
   print(f"Located downstream request {identifier}: {matching[0]['id']}",flush=True)
   return matching[0]
  if attempt%6==0:print(f'Waiting for GitHub to resolve downstream request {identifier} ({attempt*interval}s); no duplicate dispatch.',flush=True)
  if attempt+1<attempts:time.sleep(interval)
 pathlib.Path('flatpak-dispatch-diagnostic.json').write_text(json.dumps({'workflow':workflow,'requestID':identifier,'expectedTitle':expected,'waitSeconds':(attempts-1)*interval,'redispatched':False,'lastVisibleRuns':[{'id':r.get('id'),'title':r.get('display_title'),'status':r.get('status')} for r in runs]},indent=2))
 raise SystemExit('Dispatched run title not resolved within 20 minutes; request '+identifier+' may still be queued. Inspect the existing request before dispatching again.')

def dispatch(workflow,prefix,inputs):
 identifier=uuid.uuid4().hex
 inputs={**inputs,'request_id':identifier}
 ghjson('api','--method','POST',f'repos/{REPO}/actions/workflows/{workflow}/dispatches','--input','-',input={'ref':'main','inputs':inputs})
 print('Dispatched one downstream request: '+identifier,flush=True)
 found=find_dispatched_run(workflow,prefix,identifier)
 return wait_run(found['id'])

def main():
 if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise SystemExit('Authorized runner only')
 reuse=os.environ.get('REUSE_PREPARATION','').strip()
 if reuse:
  if not reuse.isdecimal():raise SystemExit('Invalid production preparation run')
  prepared=wait_run(reuse)
  if prepared['path']!='.github/workflows/rosavio-flatpak-public.yml':raise SystemExit('Wrong preparation workflow')
 else:
  with urllib.request.urlopen(f'https://github.com/{REPO}/releases/download/rosavio-linux-x64-latest/rosavio-linux-x64-update.xml',timeout=60) as f:update=ET.fromstring(f.read()).find('update')
  if update is None:raise SystemExit('No verified native Linux update')
  build=update.attrib['buildID'];url=update.find('patch').attrib['URL']
  match=re.fullmatch(r'https://github.com/aheinen1971-cmd/rosavio/releases/download/(v\d+(?:\.\d+){1,3}-rosavio-linux-x64\.\d+)/[^/]+\.complete\.mar',url)
  if not match or not re.fullmatch(r'\d{14}',build):raise SystemExit('Invalid native Linux feed')
  latest=ghjson('api',f'repos/{REPO}/releases/tags/'+match[1])
  if latest['prerelease'] or latest['draft']:raise SystemExit('Native Linux release not fully published')
  current=getjson(f'https://github.com/{REPO}/releases/download/rosavio-flatpak-repository/public-update-report.json')
  if not current.get('passed') or current.get('desktopIconAndExtensionTestsPending',True):raise SystemExit('Complete first Flatpak verification before automatic updates')
  oldbuild=current['newBuildID'];oldtag=current['newNativeRelease']
  if not re.fullmatch(r'\d{14}',oldbuild) or not re.fullmatch(r'v\d+(?:\.\d+){1,3}-rosavio-linux-x64\.\d+',oldtag):raise SystemExit('Invalid prior verified Flatpak metadata')
  if build<=oldbuild:
   pathlib.Path('flatpak-automatic-report.json').write_text(json.dumps({'passed':True,'action':'no newer tested Linux build','currentBuildID':oldbuild,'nativeBuildID':build},indent=2));print('No newer verified Linux build; Flatpak unchanged.');raise SystemExit(0)
  prepared=dispatch('rosavio-flatpak-public.yml','Rosavio signed Flatpak preparation ',{'old_tag':oldtag,'new_tag':match[1]})
 published=dispatch('rosavio-flatpak-deploy.yml','Rosavio public Flatpak trial ',{'source_run':str(prepared['id'])})
 for attempt in range(30):
  report=getjson(f'https://github.com/{REPO}/releases/download/rosavio-flatpak-repository/public-update-report.json')
  if report.get('passed') and not report.get('desktopIconAndExtensionTestsPending',True) and report.get('extensionFunctionAndSettingsPreserved'):break
  time.sleep(10)
 else:raise SystemExit('Full public Flatpak verification required')
 pathlib.Path('flatpak-automatic-report.json').write_text(json.dumps({'passed':True,'preparationRun':prepared['id'],'publicVerificationRun':published['id'],'publicReport':report},indent=2))
 print('Flatpak automatic production signing, public update, desktop, icons and extension checks passed.')

if __name__=='__main__':main()
