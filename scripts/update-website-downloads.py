"""Refresh only existing package links from regular, publicly tested releases."""
import json,pathlib,re,subprocess,urllib.request

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
    pages=list(pathlib.Path('docs').glob('*.html'))
    if len(pages)!=20:raise ValueError('Exactly twenty language pages required')
    pending=[]
    for page in pages:
        source=page.read_text(encoding='utf-8-sig')
        for m in PATTERN.finditer(source):
            if m[1] not in builds:
                release=api('releases/tags/'+m[1]);platform=next(p for p in targets if f'-rosavio-{p}.' in m[1])
                builds[m[1]]=verified(release,report(m[1]),platform)
        updated=rewrite(source,targets,builds)
        if source!=updated:pending.append((page,updated))
    # Validate every page before writing any; all other content remains intact.
    for page,updated in pending:page.write_text(updated,encoding='utf-8')
    print(f'Updated {len(pending)} language pages; unchanged releases require no commit.')

if __name__=='__main__':main()
