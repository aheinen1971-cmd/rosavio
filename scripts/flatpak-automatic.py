"""Update Flatpak only from a newer verified native Linux release, then test public delivery."""
import datetime,json,os,pathlib,re,subprocess,time,urllib.request,uuid,xml.etree.ElementTree as ET
REPO='aheinen1971-cmd/rosavio'
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise SystemExit('Authorized runner only')
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
def dispatch(workflow,prefix,inputs):
 identifier=uuid.uuid4().hex
 inputs={**inputs,'request_id':identifier}
 ghjson('api','--method','POST',f'repos/{REPO}/actions/workflows/{workflow}/dispatches','--input','-',input={'ref':'main','inputs':inputs})
 for attempt in range(60):
  runs=ghjson('api',f'repos/{REPO}/actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=20')['workflow_runs']
  matching=[r for r in runs if r['display_title']==prefix+identifier]
  if len(matching)==1:return wait_run(matching[0]['id'])
  if len(matching)>1:raise SystemExit('Ambiguous downstream dispatch')
  time.sleep(5)
 raise SystemExit('Dispatched run not found')
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
 latest=getjson(f'https://api.github.com/repos/{REPO}/releases/tags/'+match[1])
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
