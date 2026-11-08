"""Read public evidence only; publish a small snapshot, never start browser builds."""
from maintenance_http import read_url, run_gh, http_status
import datetime, importlib.util, json, os, pathlib, re, subprocess, urllib.request

REPO = 'aheinen1971-cmd/rosavio'
TAG = 'rosavio-status-dashboard'
ROOT = 'https://github.com/' + REPO
BASE = ROOT + '/releases/download/'

def get(url):
    return json.loads(read_url(url))

def api(route, repo=REPO):
    if os.environ.get('GH_TOKEN'):
        return json.loads(run_gh(['gh','api','repos/'+repo+'/'+route]).stdout)
    return get('https://api.github.com/repos/'+repo+'/'+route)

def paginate(route, key=None):
    result=[]
    for page in range(1,101):
        data=api(route+('&' if '?' in route else '?')+f'per_page=100&page={page}')
        batch=data[key] if key else data
        result.extend(batch)
        if len(batch)<100:return result
    raise ValueError('Pagination incomplete')

def row(label, state, version, detail, url=''):
    return dict(label=label,state=state,version=version,detail=detail,url=url)

def pdf_rows():
    """Public Windows release metadata only; no package downloads or build dispatch."""
    repo='aheinen1971-cmd/pdf-digital'
    root='https://github.com/'+repo
    releases=[]
    for page in range(1,101):
        batch=api(f'releases?per_page=100&page={page}',repo)
        releases.extend(r for r in batch if not r['draft'] and not r['prerelease'])
        if len(batch)<100:break
    else:raise ValueError('Incomplete PDF pagination')
    latest=max(releases,key=lambda r:r['published_at'])
    version=latest['tag_name'].removeprefix('v')
    names={a['name'] for a in latest['assets']}
    if not {f'PDF-Werkbank-{version}-Windows.zip',f'PDF-Werkbank-{version}-Signatur.json'}<=names:
        raise ValueError('Missing Windows package or project signature')
    count=sum(a['download_count'] for r in releases for a in r['assets'] if a['name'].endswith('-Windows.zip'))
    return [row('PDF Digital · Windows','green',version,'Windows-Veröffentlichung und Projektsignatur vorhanden; kein neuer Funktionstest.',latest['html_url']),
            row('PDF Digital · Downloads','neutral',str(count),'Windows-Paketabrufe aller Versionen inklusive Tests; keine Nutzerzahl.',root+'/releases')]

def release_key(release):
    match=re.match(r'v(\d+(?:\.\d+)+)-',release['tag_name'])
    return tuple(map(int,match[1].split('.'))),int(release['tag_name'].split('.')[-1])

PHASES={
 'Windows':['Reserve release tag before the long build','Build German Rosavio from verified stable Firefox source','Verify, sign and test native update','Publish and test public update with rollback on failure'],
 'Linux':['Reserve release tag before the long build','Prepare standard Linux runner','Build two genuine Linux versions and verify all twenty languages','Sign and test the local native update','Prepare the previous public Linux baseline','Verify public update, actual desktop launch and colored icons'],
 'Flatpak':['Verify delayed dispatch discovery and correlation safeguards','Build only newer tested Linux versions and verify full public Flatpak delivery'],
}

def with_progress(item, job=None):
    """Equal completed phases, not elapsed time; 100 requires verified publication."""
    if item['label'] not in PHASES:return item
    phases=PHASES[item['label']]
    steps={s['name']:s for s in (job or {}).get('steps',[])}
    if item['state']=='green':percent=100; note='Geprüft und veröffentlicht'
    elif item['state']=='gray':percent=None; note='Fortschritt nicht überprüfbar'
    elif not steps:percent=0 if item['state']=='yellow' else None; note='Noch keine abgeschlossene Phase bestätigt'
    elif not all(name in steps for name in phases):percent=None; note='Fortschritt nicht überprüfbar'
    else:
        complete=sum(steps[name].get('conclusion')=='success' for name in phases)
        percent=min(99,int(complete*100/len(phases)))
        note=f'{complete} von {len(phases)} Phasen abgeschlossen'
    item['progress']={'percent':percent,'note':note}
    if steps and any(name in steps for name in phases):
        item['progress']['steps']=[steps.get(name,{}).get('conclusion') or steps.get(name,{}).get('status','unknown') for name in phases]
        active=next((steps[n] for n in phases if n in steps and steps[n].get('status')=='in_progress'),{})
        if active.get('started_at'):item['progress']['startedAt']=active['started_at']
    return item

def flatpak_wait(linux, linux_tag, flatpak_tag, state):
    if state in ('red','gray') or not linux_tag:return None
    if linux_tag!=flatpak_tag:return 'flatpak'
    if linux and linux['state'] in ('yellow','red'):return 'linux'
    return None

def run_state(job, current, target):
    if job and job['status']!='completed':
        return 'yellow', ('Wartet auf GitHub-Rechner' if job['status'] in ('queued','waiting','pending') else 'Bau / Prüfungen laufen')
    if job and job.get('conclusion') in ('failure','timed_out','cancelled','action_required'):
        return 'red', 'Letzter Auftrag: '+job['conclusion']+'; siehe Laufdetails'
    if current==target:return 'green','Öffentliches Update geprüft und veröffentlicht'
    return 'yellow','Neue Version noch nicht vollständig veröffentlicht'

def feature_evidence(proof, tag, platform):
    preservation=proof.get('workspaceAfter') or proof.get('workspacePreservation') or {}
    if not (proof.get('passed') is True and proof.get('workspaceAfterUpdatePassed') is True
            and preservation.get('passed') is True):
        return {}
    # These report fields were introduced by the corresponding post-update UI tests.
    # A false value describes the OLD profile and is valid for a newly added feature.
    features={'reading':isinstance(preservation.get('readingPlaceExistedBeforeUpdate'),bool),
              'rose':isinstance(preservation.get('rosePathExistedBeforeUpdate'),bool)}
    if features['rose']:
        names={'Windows':'Rosavio-Setup-Deutsch.exe','Linux':'Rosavio-Linux-x64.tar.xz'}
        features['download']=BASE+tag+'/'+names[platform] if platform in names else 'https://aheinen1971-cmd.github.io/rosavio/flatpak/Rosavio.flatpakref'
    return features

def feature_changes(snapshot, previous):
    earlier={r['label']:r for r in previous.get('rows',[])}
    for item in snapshot['rows']:
        if item['label'] not in PHASES:continue
        progress=item.get('progress',{})
        key=[item.get('features',{}).get('rose'),item['state'],item['detail'],item.get('awaiting'),
             progress.get('steps'),item.get('available',{}).get('build')]
        if item.get('awaiting')=='linux':
            linux=next((r for r in snapshot['rows'] if r['label']=='Linux'),{})
            key.append(linux.get('progress',{}).get('steps'))
        prior=earlier.get(item['label'],{}).get('roseChange',{})
        if prior.get('key')==key:
            when=prior.get('at')
        else:
            when=progress.get('startedAt')
            if item.get('awaiting')=='linux':when=linux.get('progress',{}).get('startedAt')
            if not when or (prior.get('at') and when < prior['at']):
                when=snapshot['checkedAt'] if prior else None
        item['roseChange']={'key':key,'at':when}

def collect():
    spec=importlib.util.spec_from_file_location('download_guards',pathlib.Path(__file__).with_name('update-website-downloads.py'))
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    data={'schema':1,'checkedAt':now,'rows':[],'errors':[]}
    rows=data['rows']
    target=get('https://product-details.mozilla.org/1.0/firefox_versions.json')['LATEST_FIREFOX_VERSION']
    if not re.fullmatch(r'\d+(\.\d+)+',target):raise ValueError('Invalid upstream version')
    data['upstream']=target
    releases=paginate('releases'); regular=[r for r in releases if not r['draft'] and not r['prerelease']]
    published={}
    for platform,label,workflow,jobname in [
        ('windows','Windows','rosavio-build.yml','release'),
        ('linux-x64','Linux','rosavio-linux-automatic.yml','release')]:
        try:
            pattern=r'v[0-9.]+-rosavio'+('' if platform=='windows' else '-'+platform)+r'\.\d+'
            candidates=[r for r in regular if re.fullmatch(pattern,r['tag_name'])]
            release=max(candidates,key=release_key)
            proof=get(BASE+release['tag_name']+'/public-update-test.json')
            current=guard.version_of(release['tag_name'])
            if platform=='windows':guard.windows_version(release,proof)
            else:guard.verified(release,proof,platform)
            published[platform]=release
            runs=api('actions/workflows/'+workflow+'/runs?branch=main&per_page=10')['workflow_runs']
            # A check-only or skipped run must not hide the last actual platform attempt.
            selected=None; run=None
            for candidate in runs:
                # Attempts older than the published package are already superseded.
                if candidate['id'] < int(release['tag_name'].split('.')[-1]):break
                jobs=api(f"actions/runs/{candidate['id']}/jobs?per_page=100")['jobs']
                matching=[j for j in jobs if j['name']==jobname and j.get('conclusion')!='skipped']
                if matching:selected=matching[0];run=candidate;break
            state,detail=run_state(selected,current,target)
            if state=='red' and selected and not selected.get('steps'):
                annotations=api(f"check-runs/{selected['id']}/annotations")
                if any('capacity constraints' in a.get('message','') for a in annotations):
                    detail='GitHub hatte keinen freien Mac-Rechner; vor Baubeginn abgebrochen'
            rows.append(with_progress(row(label,state,current+' → '+target if current!=target else current,detail,run['html_url'] if run else release['html_url']),selected))
            rows[-1]['available']={'version':current,'build':release['tag_name'].split('.')[-1]}
            rows[-1]['features']=feature_evidence(proof,release['tag_name'],label)
        except Exception as exc:
            rows.append(row(label,'gray','—','Prüfung derzeit nicht möglich'))
            if platform in published:
                rows[-1]['available']={'version':current,'build':release['tag_name'].split('.')[-1]}
            data['errors'].append(label+': '+type(exc).__name__)
    flatpak_available=None
    try:
        proof=get(BASE+'rosavio-flatpak-repository/public-update-report.json')
        if not all(proof.get(k) is True for k in ('passed','publicUpdateTestPassed','gpgVerificationRequired','browserPagesAfterUpdatePassed')):raise ValueError('Incomplete Flatpak proof')
        if proof.get('desktopIconAndExtensionTestsPending') is not False:raise ValueError('Pending tests')
        version=guard.version_of(proof['newNativeRelease'])
        flatpak_available={'version':version,'build':proof['newNativeRelease'].split('.')[-1]}
        run=api('actions/workflows/rosavio-flatpak-automatic.yml/runs?branch=main&per_page=1')['workflow_runs'][0]
        state,detail=run_state(run,version,target)
        if state=='yellow' and run['status']=='completed':detail='Folgt auf ein neueres geprüftes Linux-Release'
        linux_tag=published.get('linux-x64',{}).get('tag_name')
        waiting=flatpak_wait(next((r for r in rows if r['label']=='Linux'),None),linux_tag,proof['newNativeRelease'],state)
        progress_job=None
        if state!='green':
            jobs=api(f"actions/runs/{run['id']}/jobs?per_page=100")['jobs']
            progress_job=next((j for j in jobs if j['name']=='update'),None)
        if waiting and state=='green':
            state,detail='yellow','Folgt auf ein neueres geprüftes Linux-Release'
        if waiting and run['status']=='completed':progress_job=None
        item=with_progress(row('Flatpak',state,version,detail,run['html_url']),progress_job)
        item['available']=flatpak_available
        item['features']=feature_evidence(proof,proof['newNativeRelease'],'Flatpak')
        if waiting and run['status']=='completed':item['awaiting']=waiting
        rows.append(item)
    except Exception as exc:
        rows.append(row('Flatpak','gray','—','Prüfung derzeit nicht möglich'));data['errors'].append('Flatpak: '+type(exc).__name__)
        if flatpak_available:rows[-1]['available']=flatpak_available
    try:
        count=0
        for lang in ['index','en','fr','es','nl','it','pt-PT','pl','cs','da','sv-SE','nb-NO','fi','tr','uk','el','ja','ko','ar','he']:
            html=read_url('https://aheinen1971-cmd.github.io/rosavio/'+lang+'.html').decode('utf-8')
            for platform in ('linux-x64',):
                if platform not in published or published[platform]['tag_name'] not in html:raise ValueError('Download links not current')
            count+=1
        rows.append(row('Webseite · 20 Sprachen','green','20 Seiten','Erreichbar; Links entsprechen den geprüften Unix-Releases','https://aheinen1971-cmd.github.io/rosavio/'))
    except Exception:
        rows.append(row('Webseite · 20 Sprachen','gray','—','Seiten oder aktuelle Downloadlinks nicht vollständig bestätigt','https://aheinen1971-cmd.github.io/rosavio/'))
    try:
        feed=get(BASE+'rosavio-weitersehen-updates/updates.json')
        update=feed['addons']['rosavio-weitersehen@local.invalid']['updates'][-1]
        rows.append(row('Weitersehen · GitHub','green',update['version'],'Öffentlicher Updatekanal erreichbar (kein neuer Funktionstest)',ROOT+'/releases/tag/rosavio-weitersehen-updates'))
    except Exception:
        rows.append(row('Weitersehen · GitHub','gray','—','Updatekanal nicht überprüfbar'))
    try:
        amo=get('https://addons.mozilla.org/api/v5/addons/addon/rosavio-weitersehen/')
        version=amo['current_version']; file=version['file']
        if amo['guid']!='rosavio-weitersehen@local.invalid' or not file['url'].startswith('https://addons.mozilla.org/'):raise ValueError('Wrong AMO identity')
        rows.append(row('Weitersehen · Mozilla-Katalog','green',version['version'],'Öffentlicher Katalog und offizieller Download vorhanden','https://addons.mozilla.org/de/firefox/addon/rosavio-weitersehen/'))
    except Exception:
        rows.append(row('Weitersehen · Mozilla-Katalog','gray','0.1.2 eingereicht','Öffentliche Freigabe nicht bestätigt. Interner Prüfstatus ist ohne Anmeldung nicht abrufbar.'))
    rows.append(row('macOS','neutral','Pflege eingestellt','Seit 03.11.2026 keine weitere Pflege oder Sicherheitsupdates. Bereits laufende Altaufträge dürfen enden; keine Wiederaufnahme.'))
    assets=[a for r in regular for a in r['assets'] if a['name'] in ('Rosavio-Setup-Deutsch.exe','Rosavio-Linux-x64.tar.xz','Rosavio.dmg')]
    rows.append(row('Paketdownloads','neutral',str(sum(a['download_count'] for a in assets)),'GitHub-Abrufe inklusive Tests; keine Personen- oder Installationszahl. Ohne Flatpak und MAR-Updates.'))
    try:
        rows.extend(pdf_rows())
    except Exception as exc:
        rows.append(row('PDF Digital · Windows','gray','—','Prüfung derzeit nicht möglich','https://github.com/aheinen1971-cmd/pdf-digital/releases'))
        data['errors'].append('PDF Digital: '+type(exc).__name__)
    rows.append(row('Fehlerübersicht','red' if any(r['state']=='red' for r in rows) else 'neutral','—','Siehe rote Zeilen. Laufstatus und öffentliche Metadaten können nicht alle Browserfehler erkennen.'))
    order=['Windows','Linux','Flatpak','macOS']
    rows.sort(key=lambda r:order.index(r['label']) if r['label'] in order else len(order))
    return data

def publish_static(snapshot):
    """Publish only public JSON on a separate data branch, never main or a feed."""
    branch='rosavio-status-data'
    def request(route, method='GET', payload=None, missing=False):
        args=['gh','api','--method',method,'repos/'+REPO+'/'+route]
        if payload is not None: args+=['--input','-']
        result=run_gh(args,input=json.dumps(payload) if payload is not None else None,check=False)
        if result.returncode:
            if missing and '(HTTP 404)' in result.stderr:return None
            raise RuntimeError(f'Status data publication failed: {route} (HTTP {http_status(result) or "unknown"}, exit {result.returncode}).')
        return json.loads(result.stdout)
    head=request('git/ref/heads/'+branch,missing=True)
    tree=request('git/trees','POST',{'tree':[{'path':'status.json','mode':'100644','type':'blob','content':json.dumps(snapshot,ensure_ascii=False,indent=2)}]})
    commit=request('git/commits','POST',{'message':'Refresh public Rosavio status','tree':tree['sha'],'parents':[head['object']['sha']] if head else []})
    if head:
        request('git/refs/heads/'+branch,'PATCH',{'sha':commit['sha'],'force':False})
    else:
        request('git/refs','POST',{'ref':'refs/heads/'+branch,'sha':commit['sha']})

def main():
    snapshot=collect()
    import base64
    saved=api('contents/status.json?ref=rosavio-status-data')
    feature_changes(snapshot,json.loads(base64.b64decode(saved['content'])))
    pathlib.Path('status-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    if '--publish' not in __import__('sys').argv:return
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise SystemExit('Publication only on authorized runner')
    # Infrastructure prerelease never changes Latest or any product update feed.
    lookup=run_gh(['gh','api','repos/'+REPO+'/releases/tags/'+TAG],check=False)
    if lookup.returncode and http_status(lookup)!=404:raise RuntimeError(f'Status release lookup failed (HTTP {http_status(lookup) or "unknown"}).')
    exists=lookup.returncode==0
    args=['gh','release','edit' if exists else 'create',TAG,'--repo',REPO,'--title','Rosavio status data','--notes-file','status-snapshot.json','--prerelease','--latest=false']
    if exists:run_gh(args)
    else:subprocess.run(args,check=True)
    publish_static(snapshot)

if __name__=='__main__':main()
