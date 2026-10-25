"""Install/update from the actual public HTTPS Flatpak ref; retain only test data."""
import base64,configparser,json,pathlib,subprocess,sys,time,urllib.request
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
run('node','scripts/check-flatpak.cjs',wrapper,DATA,mode,r['oldBuildID'] if mode=='seed' else r['newBuildID'])
if mode=='verify':
 run('node','scripts/check-locales.cjs',wrapper,DATA/'locales')
 (DATA/'public-update-report.json').write_text(json.dumps({'passed':True,'publicInstallationPassed':True,'publicUpdateTestPassed':True,'gpgVerificationRequired':True,'oldCommit':r['oldCommit'],'newCommit':r['newCommit'],'signingFingerprint':r['signingFingerprint'],'languages':20,'profilePreservationPassed':True,'desktopIconAndExtensionTestsPending':True},indent=2))
