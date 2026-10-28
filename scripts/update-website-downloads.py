"""Refresh only existing package links from regular, publicly tested releases."""
import json,pathlib,re,subprocess,urllib.request

LABELS=dict(zip('de en fr es nl it pt-PT pl cs da sv-SE nb-NO fi tr uk el ja ko ar he'.split(),['Aktuelle Version','Current version','Version actuelle','Versión actual','Huidige versie','Versione attuale','Versão atual','Aktualna wersja','Aktuální verze','Aktuel version','Aktuell version','Gjeldende versjon','Nykyinen versio','Güncel sürüm','Поточна версія','Τρέχουσα έκδοση','現在のバージョン','현재 버전','الإصدار الحالي','הגרסה הנוכחית']))
VERSION_BLOCK=re.compile(r'<!-- rosavio-versions -->.*?<!-- /rosavio-versions -->',re.S)

def version_of(tag):
    match=re.fullmatch(r'v(\d+(?:\.\d+)+)-rosavio(?:-(?:linux-x64|macos-arm64|macos-x64))?\.\d+',tag)
    if not match:raise ValueError('Invalid release version')
    return match[1]

def windows_version(release,proof):
    version=version_of(release['tag_name'])
    if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v[0-9.]+-rosavio\.\d+',release['tag_name']):raise ValueError('Regular Windows release required')
    if proof.get('passed') is not True or proof.get('browserPagesAfterUpdatePassed') is not True or proof.get('signatureVerificationDisabled') is not False:raise ValueError('Verified Windows update required')
    if proof['after']['version']!=version:raise ValueError('Version mismatch')
    if not any(a['name']=='Rosavio-Setup-Deutsch.exe' for a in release['assets']):raise ValueError('Windows installer missing')
    return version

def show_versions(source,versions):
    lang=re.search(r'<html\b[^>]*\blang="([^"]+)"',source)[1]
    label=LABELS[lang]
    if not versions or any(not re.fullmatch(r'\d+(?:\.\d+)+',v) for v in versions.values()):raise ValueError('Invalid displayed version')
    if len(set(versions.values()))==1:
        text='<bdi>Rosavio '+next(iter(versions.values()))+'</bdi>'
    else:
        text='<br>'.join('<bdi>'+p+' · Rosavio '+v+'</bdi>' for p,v in versions.items())
    block='<!-- rosavio-versions --><p id="rosavio-versions" style="font-size:16px;font-weight:700;color:#7c1935;line-height:1.7">'+label+': '+text+'</p><!-- /rosavio-versions -->'
    if VERSION_BLOCK.search(source):return VERSION_BLOCK.sub(lambda _:block,source)
    if source.count('</h1>')!=1:raise ValueError('Unique page heading required')
    return source.replace('</h1>','</h1>'+block,1)

REPO='aheinen1971-cmd/rosavio'
BASE=f'https://github.com/{REPO}/releases/download/'
PATTERN=re.compile(re.escape(BASE)+r'(v[^/"\s<>]+)/(Rosavio-Linux-x64\.tar\.xz|Rosavio\.dmg)')

def verified(release,report,platform):
    if release.get('draft') or release.get('prerelease'):raise ValueError('Regular release required')
    if report.get('platform')!=platform:raise ValueError('Wrong platform')
    if not all(report.get(k) is True for k in ('passed','publicUpdateTestPassed','browserPagesAfterUpdatePassed')):raise ValueError('Public tests required')
    after=report['after']
    if after.get('signatureDisabled') is not False:raise ValueError('Signature verification required')
    if not re.fullmatch(r'\d{14}',after['buildID']):raise ValueError('Invalid BuildID')
    if platform.startswith('macos'):
        if not all(report.get(k) is True for k in ('resourceSealAfterPublicUpdateVerified','macLaunchServicesStartPassed')):raise ValueError('Mac integrity/start checks required')
        if report.get('finderDockIconExtensionSecurityChecksPending') is not False:raise ValueError('Incomplete Mac checks')
    elif report.get('desktopLaunchTestPassed') is not True:raise ValueError('Linux desktop check required')
    return after['buildID']

def rewrite(source,targets,builds):
    def replace(m):
        platform=next((p for p in targets if f'-rosavio-{p}.' in m[1]),None)
        if platform is None:raise ValueError('Unrecognized package link')
        old=builds[m[1]];new=targets[platform]
        if new['build']<old:raise ValueError('Refusing website downgrade')
        return new['url'] if new['build']>old else m[0]
    return PATTERN.sub(replace,source)

def main():
    def api(route):return json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}/'+route],text=True))
    def report(tag):
        with urllib.request.urlopen(BASE+tag+'/public-update-test.json',timeout=60) as r:return json.load(r)
    releases=api('releases?per_page=100');targets={};builds={}
    win=api('releases/latest')
    versions={'Windows':windows_version(win,report(win['tag_name']))}
    with urllib.request.urlopen(BASE+'rosavio-flatpak-repository/public-update-report.json',timeout=60) as response:flatpak=json.load(response)
    if not all(flatpak.get(k) is True for k in ('passed','publicUpdateTestPassed','gpgVerificationRequired','browserPagesAfterUpdatePassed')):raise ValueError('Verified Flatpak release required')
    versions['Flatpak']=version_of(flatpak['newNativeRelease'])
    for platform,filename in [('linux-x64','Rosavio-Linux-x64.tar.xz'),('macos-arm64','Rosavio.dmg'),('macos-x64','Rosavio.dmg')]:
        candidates=[r for r in releases if re.fullmatch(r'v[0-9.]+-rosavio-'+platform+r'\.\d+',r['tag_name']) and not r['draft'] and not r['prerelease']]
        if not candidates:raise ValueError('Missing regular release: '+platform)
        # Publication order can differ from build order; use verified BuildIDs.
        for release in candidates:
            tag=release['tag_name'];proof=report(tag)
            try:build=verified(release,proof,platform)
            except ValueError:continue
            url=BASE+tag+'/'+filename
            if not any(a['name']==filename and a['browser_download_url']==url for a in release['assets']):raise ValueError('Package asset missing')
            builds[tag]=build
            if platform not in targets or build>targets[platform]['build']:targets[platform]={'build':build,'url':url}
        if platform not in targets:raise ValueError('No fully tested release: '+platform)
        versions[{'linux-x64':'Linux','macos-arm64':'macOS Apple Silicon','macos-x64':'macOS Intel'}[platform]]=version_of(targets[platform]['url'][len(BASE):].split('/')[0])
    pages=list(pathlib.Path('docs').glob('*.html'))
    if len(pages)!=20:raise ValueError('Exactly twenty language pages required')
    pending=[]
    for page in pages:
        source=page.read_text(encoding='utf-8-sig')
        for m in PATTERN.finditer(source):
            if m[1] not in builds:
                release=api('releases/tags/'+m[1]);platform=next(p for p in targets if f'-rosavio-{p}.' in m[1])
                builds[m[1]]=verified(release,report(m[1]),platform)
        updated=show_versions(rewrite(source,targets,builds),versions)
        if source!=updated:pending.append((page,updated))
    # Validate every page before writing any; all other content remains intact.
    for page,updated in pending:page.write_text(updated,encoding='utf-8')
    print(f'Updated {len(pending)} language pages; unchanged releases require no commit.')

if __name__=='__main__':main()
