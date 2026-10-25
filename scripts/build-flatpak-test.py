"""Build and verify a Flatpak candidate; no public release or persistent key upload.

The disposable CI signing identity is used only for this isolated test repository.
It is never published as Rosavio's production trust root.
"""
import configparser, hashlib, json, os, pathlib, shutil, subprocess, tarfile, tempfile, urllib.request

if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
    raise SystemExit('Only the authorized Rosavio test runner may run this script')
ROOT=pathlib.Path.cwd(); OUT=ROOT/'flatpak-results'; OUT.mkdir(exist_ok=True)
APP='io.github.aheinen1971_cmd.Rosavio'; BRANCH='stable'; RUNTIME='25.08'
REPO=ROOT/'flatpak-test-repo'; PROFILE=ROOT/'flatpak-profile-tests'; PROFILE.mkdir()
PRODUCTION=os.environ.get('ROSAVIO_FLATPAK_PRODUCTION')=='1'
private_identity=os.environ.pop('ROSAVIO_FLATPAK_SIGNING_KEY','')
identity_password=os.environ.pop('ROSAVIO_FLATPAK_SIGNING_PASSWORD','')
if PRODUCTION and (not private_identity or not identity_password):raise SystemExit('Approved production signing secrets required')
def run(*args,**kw):return subprocess.run([str(a) for a in args],check=True,**kw)
def output(*args):return subprocess.check_output([str(a) for a in args],text=True).strip()
def getjson(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Rosavio-Flatpak-Test'}),timeout=60) as f:return json.load(f)
def source(tag,label):
    release=getjson('https://api.github.com/repos/aheinen1971-cmd/rosavio/releases/tags/'+tag)
    if release['prerelease']:raise SystemExit('Only verified regular Linux releases can be packaged')
    asset=next(x for x in release['assets'] if x['name']=='Rosavio-Linux-x64.tar.xz')
    digest=asset.get('digest','')
    if not digest.startswith('sha256:'):raise SystemExit('Missing GitHub asset digest')
    archive=ROOT/(label+'.tar.xz')
    with urllib.request.urlopen(asset['browser_download_url'],timeout=120) as src,archive.open('wb') as dst:shutil.copyfileobj(src,dst)
    with archive.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if 'sha256:'+actual!=digest or archive.stat().st_size!=asset['size']:raise SystemExit('Linux source archive mismatch')
    folder=ROOT/label;folder.mkdir()
    with tarfile.open(archive) as tf:tf.extractall(folder,filter='data')
    candidates=[p.parent for p in folder.rglob('application.ini') if (p.parent/'rosavio').is_file()]
    if len(candidates)!=1:raise SystemExit('Ambiguous native package')
    app=candidates[0];ini=configparser.ConfigParser();ini.read(app/'application.ini')
    if ini.get('App','Name')!='Rosavio':raise SystemExit('Wrong native identity')
    return app,ini.get('App','BuildID'),actual

run('flatpak','remote-add','--user','--if-not-exists','flathub','https://flathub.org/repo/flathub.flatpakrepo')
run('flatpak','install','--user','--noninteractive','flathub','org.freedesktop.Platform//'+RUNTIME,'org.freedesktop.Sdk//'+RUNTIME)
baseline,oldid,oldhash=source('v158.0.1-rosavio-linux-x64.40178990988','flatpak-old-native')
candidate,newid,newhash=source('v158.0.1-rosavio-linux-x64.40179413346','flatpak-new-native')
if oldid>=newid:raise SystemExit('Two distinct genuine builds are required')

with tempfile.TemporaryDirectory(prefix='rosavio-flatpak-test-key-') as keydir:
    os.chmod(keydir,0o700)
    if PRODUCTION:
        config=json.loads((ROOT/'flatpak-signing.json').read_text())
        run('gpg','--homedir',keydir,'--batch','--import',input=private_identity.encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        private_identity=''
        (pathlib.Path(keydir)/'gpg-agent.conf').write_text('default-cache-ttl 3600\nmax-cache-ttl 3600\n')
    else:
        run('gpg','--homedir',keydir,'--batch','--passphrase','','--quick-generate-key','Rosavio disposable CI test key','rsa3072','sign','1d',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    fingerprint=next(line.split(':')[9] for line in output('gpg','--homedir',keydir,'--with-colons','--list-keys').splitlines() if line.startswith('fpr:'))
    if PRODUCTION:
        if fingerprint!=config['fingerprint']:raise SystemExit('Production signing fingerprint mismatch')
        probe=pathlib.Path(keydir)/'probe.txt';probe.write_text('Rosavio production Flatpak signing verification')
        run('gpg','--homedir',keydir,'--batch','--yes','--pinentry-mode','loopback','--passphrase-fd','0','--local-user',fingerprint,'--detach-sign',probe,input=(identity_password+'\n').encode(),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        identity_password=''
    public=OUT/'test-repository-public-key.gpg'
    with public.open('wb') as f:run('gpg','--homedir',keydir,'--export',fingerprint,stdout=f)
    def package(native,label):
        build=ROOT/label
        run('flatpak','build-init',build,APP,'org.freedesktop.Sdk','org.freedesktop.Platform',RUNTIME)
        files=build/'files';dest=files/'lib/rosavio';dest.parent.mkdir(parents=True)
        shutil.copytree(native,dest,symlinks=True)
        distribution=dest/'distribution';distribution.mkdir(exist_ok=True)
        policy=distribution/'policies.json'
        existing=json.loads(policy.read_text()) if policy.exists() else {'policies':{}}
        existing.setdefault('policies',{})['DisableAppUpdate']=True
        policy.write_text(json.dumps(existing))
        bins=files/'bin';bins.mkdir()
        launcher=bins/'rosavio';launcher.write_text('#!/bin/sh\nexport MOZ_ENABLE_WAYLAND=1\nexec /app/lib/rosavio/rosavio "$@"\n');launcher.chmod(0o755)
        apps=files/'share/applications';apps.mkdir(parents=True)
        (apps/(APP+'.desktop')).write_text('[Desktop Entry]\nType=Application\nName=Rosavio\nComment=Independent browser based on Firefox\nExec=rosavio %u\nIcon='+APP+'\nTerminal=false\nCategories=Network;WebBrowser;\nMimeType=text/html;x-scheme-handler/http;x-scheme-handler/https;\nStartupNotify=true\n')
        for size in [16,32,48,64,128]:
            icon=files/f'share/icons/hicolor/{size}x{size}/apps';icon.mkdir(parents=True)
            shutil.copy2(dest/f'browser/chrome/icons/default/default{size}.png',icon/(APP+'.png'))
        meta=files/'share/metainfo';meta.mkdir(parents=True)
        (meta/(APP+'.metainfo.xml')).write_text('<?xml version="1.0" encoding="UTF-8"?><component type="desktop-application"><id>'+APP+'</id><name>Rosavio</name><summary>Independent browser based on Firefox</summary><metadata_license>CC0-1.0</metadata_license><project_license>MPL-2.0</project_license><description><p>A browser with twenty interface languages. Updates to this package are managed by Flatpak.</p></description><launchable type="desktop-id">'+APP+'.desktop</launchable><url type="homepage">https://aheinen1971-cmd.github.io/rosavio/</url></component>')
        run('desktop-file-validate',apps/(APP+'.desktop'))
        permissions=['--share=network','--share=ipc','--socket=wayland','--socket=fallback-x11','--socket=pulseaudio','--device=dri','--filesystem=xdg-download','--talk-name=org.freedesktop.Notifications']
        run('flatpak','build-finish','--command=rosavio',*permissions,build)
        run('flatpak','build-export','--gpg-homedir='+keydir,'--gpg-sign='+fingerprint,REPO,build,BRANCH)
        run('flatpak','build-update-repo','--gpg-homedir='+keydir,'--gpg-sign='+fingerprint,REPO)
    package(baseline,'flatpak-old-build')
    if PRODUCTION:
        run('tar','-cJf',OUT/'repository-baseline.tar.xz','-C',REPO,'.')
    run('flatpak','remote-add','--user','--gpg-import='+str(public),'rosavio-isolated-test',REPO.as_uri())
    run('flatpak','install','--user','--noninteractive','rosavio-isolated-test',APP)
    # This CI-only wrapper exposes only the isolated profile-test folder for automation.
    wrapper=ROOT/'flatpak-test-launcher';wrapper.write_text('#!/bin/sh\nexec flatpak run --user --filesystem="'+str(PROFILE)+'" '+APP+' "$@"\n');wrapper.chmod(0o755)
    run('node','scripts/check-flatpak.cjs',wrapper,PROFILE,'seed',oldid)
    oldcommit=output('flatpak','info','--user','--show-commit',APP)
    package(candidate,'flatpak-new-build')
    run('flatpak','update','--user','--noninteractive',APP)
    newcommit=output('flatpak','info','--user','--show-commit',APP)
    if oldcommit==newcommit:raise SystemExit('Flatpak revision did not change')
    run('node','scripts/check-flatpak.cjs',wrapper,PROFILE,'verify',newid)
    run('node','scripts/check-locales.cjs',wrapper,PROFILE/'locales')
    run('flatpak','build-bundle',REPO,OUT/'Rosavio-Linux-x64-Test.flatpak',APP,BRANCH)
    if PRODUCTION:
        run('tar','-cJf',OUT/'repository-candidate.tar.xz','-C',REPO,'.')
        run(os.sys.executable,'scripts/prepare-flatpak-distribution.py',REPO,public,fingerprint,OUT/'installation')
    # Never export private test keys, test profiles or an untrusted production installer.
    (OUT/'report.json').write_text(json.dumps({'passed':True,'candidateOnly':True,'publicRepositoryTestPassed':False,'productionSigningConfigured':PRODUCTION,'signingFingerprint':fingerprint,'appID':APP,'languages':20,'oldBuildID':oldid,'newBuildID':newid,'oldCommit':oldcommit,'newCommit':newcommit,'sourcesSHA256':[oldhash,newhash],'signedLocalFlatpakUpdatePassed':True,'permissions':output('flatpak','info','--user','--show-permissions',APP)},indent=2))
print('Isolated signed Flatpak installation/update and twenty languages passed; public distribution remains gated.')
