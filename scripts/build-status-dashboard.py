"""Read public evidence only; publish a small snapshot, never start browser builds."""
import datetime, importlib.util, json, os, pathlib, re, subprocess, urllib.request

REPO = 'aheinen1971-cmd/rosavio'
TAG = 'rosavio-status-dashboard'
ROOT = 'https://github.com/' + REPO
BASE = ROOT + '/releases/download/'

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Rosavio-status'}), timeout=30) as r:
        return json.load(r)

def api(route):
    if os.environ.get('GH_TOKEN'):
        return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/'+route], text=True))
    return get('https://api.github.com/repos/'+REPO+'/'+route)

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

def release_key(release):
    match=re.match(r'v(\d+(?:\.\d+)+)-',release['tag_name'])
    return tuple(map(int,match[1].split('.'))),int(release['tag_name'].split('.')[-1])

def run_state(job, current, target):
    if job and job['status']!='completed':
        return 'yellow', ('Wartet auf GitHub-Rechner' if job['status'] in ('queued','waiting','pending') else 'Bau / Prüfungen laufen')
    if job and job.get('conclusion') in ('failure','timed_out','cancelled','action_required'):
        return 'red', 'Letzter Auftrag: '+job['conclusion']+'; siehe Laufdetails'
    if current==target:return 'green','Öffentliches Update geprüft und veröffentlicht'
    return 'yellow','Neue Version noch nicht vollständig veröffentlicht'

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
        ('linux-x64','Linux','rosavio-linux-automatic.yml','release'),
        ('macos-x64','macOS Intel','rosavio-macos-automatic.yml','release (macos-x64)'),
        ('macos-arm64','macOS Apple Silicon','rosavio-macos-automatic.yml','release (macos-arm64)')]:
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
            rows.append(row(label,state,current+' → '+target if current!=target else current,detail,run['html_url'] if run else release['html_url']))
        except Exception as exc:
            rows.append(row(label,'gray','—','Prüfung derzeit nicht möglich'))
            data['errors'].append(label+': '+type(exc).__name__)
    try:
        proof=get(BASE+'rosavio-flatpak-repository/public-update-report.json')
        if not all(proof.get(k) is True for k in ('passed','publicUpdateTestPassed','gpgVerificationRequired','browserPagesAfterUpdatePassed')):raise ValueError('Incomplete Flatpak proof')
        if proof.get('desktopIconAndExtensionTestsPending') is not False:raise ValueError('Pending tests')
        version=guard.version_of(proof['newNativeRelease'])
        run=api('actions/workflows/rosavio-flatpak-automatic.yml/runs?branch=main&per_page=1')['workflow_runs'][0]
        state,detail=run_state(run,version,target)
        if state=='yellow' and run['status']=='completed':detail='Folgt auf ein neueres geprüftes Linux-Release'
        rows.append(row('Flatpak',state,version,detail,run['html_url']))
    except Exception as exc:
        rows.append(row('Flatpak','gray','—','Prüfung derzeit nicht möglich'));data['errors'].append('Flatpak: '+type(exc).__name__)
    try:
        count=0
        for lang in ['index','en','fr','es','nl','it','pt-PT','pl','cs','da','sv-SE','nb-NO','fi','tr','uk','el','ja','ko','ar','he']:
            with urllib.request.urlopen('https://aheinen1971-cmd.github.io/rosavio/'+lang+'.html',timeout=30) as response:html=response.read().decode('utf-8')
            for platform in ('linux-x64','macos-x64','macos-arm64'):
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
    assets=[a for r in regular for a in r['assets'] if a['name'] in ('Rosavio-Setup-Deutsch.exe','Rosavio-Linux-x64.tar.xz','Rosavio.dmg')]
    rows.append(row('Paketdownloads','neutral',str(sum(a['download_count'] for a in assets)),'GitHub-Abrufe inklusive Tests; keine Personen- oder Installationszahl. Ohne Flatpak und MAR-Updates.'))
    rows.append(row('Fehlerübersicht','red' if any(r['state']=='red' for r in rows) else 'neutral','—','Siehe rote Zeilen. Laufstatus und öffentliche Metadaten können nicht alle Browserfehler erkennen.'))
    order=['Windows','Linux','Flatpak','macOS Intel','macOS Apple Silicon']
    rows.sort(key=lambda r:order.index(r['label']) if r['label'] in order else len(order))
    return data

def main():
    snapshot=collect()
    pathlib.Path('status-snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    if '--publish' not in __import__('sys').argv:return
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!=REPO:raise SystemExit('Publication only on authorized runner')
    # Infrastructure prerelease never changes Latest or any product update feed.
    exists=subprocess.run(['gh','release','view',TAG,'--repo',REPO],capture_output=True).returncode==0
    args=['gh','release','edit' if exists else 'create',TAG,'--repo',REPO,'--title','Rosavio status data','--notes-file','status-snapshot.json','--prerelease','--latest=false']
    subprocess.run(args,check=True)

if __name__=='__main__':main()
