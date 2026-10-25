"""Install/update from the actual public HTTPS Flatpak ref; retain only test data."""
import base64,configparser,hashlib,json,os,pathlib,shlex,subprocess,sys,time,urllib.request
ROOT=pathlib.Path.cwd();DATA=ROOT/'flatpak-public-profiles';DATA.mkdir(exist_ok=True)
APP='io.github.aheinen1971_cmd.Rosavio';mode=sys.argv[1];candidate=pathlib.Path(sys.argv[2]);r=json.loads((candidate/'report.json').read_text())
if mode not in ['seed','verify']:raise SystemExit('Invalid mode')
URL='https://aheinen1971-cmd.github.io/rosavio/flatpak/Rosavio.flatpakref'
def run(*args,**kw):return subprocess.run([str(x) for x in args],check=True,**kw)
def output(*args):return subprocess.check_output([str(x) for x in args],text=True).strip()
run('flatpak','remote-add','--user','--if-not-exists','flathub','https://flathub.org/repo/flathub.flatpakrepo')
if mode=='seed':
 config=json.loads((ROOT/'flatpak-signing.json').read_text())
 with urllib.request.urlopen(URL,timeout=60) as response:descriptor=response.read().decode('utf-8')
 ref=configparser.ConfigParser(interpolation=None);ref.read_string(descriptor)
 if ref['Flatpak Ref']['Url']!=config['repositoryURL'] or ref['Flatpak Ref']['Name']!=APP:raise SystemExit('Unexpected public installation descriptor')
 key=DATA/'pinned-public-key.gpg';key.write_bytes(base64.b64decode(ref['Flatpak Ref']['GPGKey'],validate=True))
 publickeys=output('gpg','--batch','--with-colons','--show-keys',key)
 if not any(line.startswith('fpr:') and line.split(':')[9]==config['fingerprint'] for line in publickeys.splitlines()):raise SystemExit('Public Flatpak signing identity mismatch')
 run('flatpak','install','--user','--noninteractive',URL)
else:
 for attempt in range(30):
  run('flatpak','update','--user','--noninteractive',APP)
  if output('flatpak','info','--user','--show-commit',APP)==r['newCommit']:break
  time.sleep(10)
 else:raise SystemExit('Public Flatpak candidate revision never arrived')
expected=r['oldCommit'] if mode=='seed' else r['newCommit']
if output('flatpak','info','--user','--show-commit',APP)!=expected:raise SystemExit('Wrong public Flatpak commit')
remotes=output('flatpak','remotes','--user','--show-details')
if 'https://aheinen1971-cmd.github.io/rosavio/flatpak/' not in remotes:raise SystemExit('Public repository was not used')
if any('aheinen1971-cmd.github.io/rosavio/flatpak/' in line and 'no-gpg-verify' in line for line in remotes.splitlines()):raise SystemExit('Public GPG verification disabled')
wrapper=ROOT/'flatpak-public-launcher';wrapper.write_text('#!/bin/sh\nexec flatpak run --user --filesystem="'+str(DATA)+'" '+APP+' "$@"\n');wrapper.chmod(0o755)
extra={}
if os.environ.get('ROSAVIO_FLATPAK_EXTRA_CHECKS')=='1':
 # Probe the installed sandbox without the test-only profile filesystem grant.
 sentinel=pathlib.Path.home()/'.rosavio-flatpak-private-probe'
 sentinel.write_text('isolated-test-data')
 try:
  run('flatpak','run','--user','--command=sh',APP,'-c','test -f /.flatpak-info && ! test -r "$1"','probe',sentinel)
 finally:sentinel.unlink(missing_ok=True)
 metadata=output('flatpak','info','--user','--show-permissions',APP)
 if 'filesystems=host' in metadata or 'filesystems=home' in metadata or 'session-bus;' in metadata:raise SystemExit('Unexpected broad Flatpak permission')
 portal=output('gdbus','introspect','--session','--dest','org.freedesktop.portal.Desktop','--object-path','/org/freedesktop/portal/desktop')
 if 'org.freedesktop.portal.FileChooser' not in portal:raise SystemExit('Native file chooser portal missing')
 (DATA/(mode+'-isolation-report.json')).write_text(json.dumps({'passed':True,'privateHostFileBlocked':True,'fileChooserPortalAvailable':True,'permissions':metadata},indent=2))
 location=pathlib.Path(output('flatpak','info','--user','--show-location',APP))
 native=location/'files/lib/rosavio'
 run(sys.executable,'scripts/check-linux-icons.py',native,DATA/(mode+'-icons'))
 exported=pathlib.Path.home()/'.local/share/flatpak/exports/share/applications'/ (APP+'.desktop')
 if not exported.is_file():raise SystemExit('Actual exported Flatpak desktop launcher missing')
 run('desktop-file-validate',exported)
 text=exported.read_text()
 if 'Icon='+APP not in text or APP not in text:raise SystemExit('Incorrect exported launcher identity')
 for size in [16,32,48,64,128]:
  icon=pathlib.Path.home()/f'.local/share/flatpak/exports/share/icons/hicolor/{size}x{size}/apps'/ (APP+'.png')
  original=native/f'browser/chrome/icons/default/default{size}.png'
  if not icon.is_file() or icon.read_bytes()!=original.read_bytes():raise SystemExit('Exported icon mismatch: '+str(size))
 # Use the exported desktop file as the template, adding test-only profile args.
 desktop=ROOT/('Rosavio-Flatpak-'+mode+'.desktop')
 command=shlex.quote(str(wrapper))+' -no-remote -profile '+shlex.quote(str(DATA/'preserved-profile'))+' --marionette --remote-allow-system-access'
 desktop.write_text('\n'.join('Exec='+command if line.startswith('Exec=') else line for line in text.splitlines())+'\n')
 run('desktop-file-validate',desktop)
 with urllib.request.urlopen('https://addons.mozilla.org/api/v5/addons/addon/multi-account-containers/',timeout=60) as response:addon=json.load(response)
 xpi=addon['current_version']['file']['url']
 if not xpi.startswith('https://addons.mozilla.org/firefox/downloads/file/') or not xpi.endswith('.xpi'):raise SystemExit('Official signed extension download required')
 extra={'ROSAVIO_FLATPAK_DESKTOP_ENTRY':str(desktop),'ROSAVIO_FLATPAK_EXTENSION_XPI':xpi}
run('node','scripts/check-flatpak.cjs',wrapper,DATA,mode,r['oldBuildID'] if mode=='seed' else r['newBuildID'],env={**os.environ,**extra})
if mode=='verify':
 run('node','scripts/check-locales.cjs',wrapper,DATA/'locales')
 verified=json.loads((DATA/'verify-report.json').read_text())
 extras=bool(extra) and bool(verified.get('desktopTest',{}).get('passed')) and bool(verified.get('extensionTest',{}).get('passed'))
 (DATA/'public-update-report.json').write_text(json.dumps({'passed':True,'publicInstallationPassed':True,'publicUpdateTestPassed':True,'gpgVerificationRequired':True,'oldCommit':r['oldCommit'],'newCommit':r['newCommit'],'oldBuildID':r['oldBuildID'],'newBuildID':r['newBuildID'],'newNativeRelease':r.get('newNativeRelease','v158.0.1-rosavio-linux-x64.40179413346'),'signingFingerprint':r['signingFingerprint'],'languages':20,'profilePreservationPassed':True,'desktopIconAndExtensionTestsPending':not extras,'ownDesktopTestBasedOnExportedLauncher':bool(extra),'extensionFunctionAndSettingsPreserved':extras},indent=2))
