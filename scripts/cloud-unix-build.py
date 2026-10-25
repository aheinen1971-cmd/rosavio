"""Native Linux/macOS builds and isolated update baselines; no publication here."""
import argparse, datetime, hashlib, json, os, pathlib, platform, shutil, subprocess, tarfile, urllib.request

p=argparse.ArgumentParser();p.add_argument('--platform',choices=['linux-x64','macos-x64','macos-arm64'],required=True);a=p.parse_args()
if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_REPOSITORY')!='aheinen1971-cmd/rosavio':
    raise SystemExit('Only run on the public Rosavio GitHub runner')
expected={'linux-x64':('Linux','x86_64'),'macos-x64':('Darwin','x86_64'),'macos-arm64':('Darwin','arm64')}
if (platform.system(),platform.machine())!=expected[a.platform]:raise SystemExit('Runner architecture does not match package')
project=pathlib.Path.cwd();root=pathlib.Path(os.environ['RUNNER_TEMP'])/'rosavio-native';root.mkdir(exist_ok=True)
os.environ['MOZBUILD_STATE_PATH']=str(root/'state')
os.environ['MOZ_BUILD_DATE']=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
os.environ['CARGO_BUILD_JOBS']='2'
build_jobs=2
if a.platform=='macos-x64':
    cpus=int(subprocess.check_output(['sysctl','-n','hw.logicalcpu'],text=True))
    memory=int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True))
    # Reserve 2 GiB for the OS; budget 3 GiB per native compilation worker.
    # Use the existing standard runner, never a larger paid runner.
    build_jobs=max(1,min(4,cpus,(memory-2*1024**3)//(3*1024**3)))
    os.environ['CARGO_BUILD_JOBS']=str(min(2,build_jobs))
    print(json.dumps({'platform':a.platform,'logicalCPUs':cpus,'memoryBytes':memory,'nativeBuildJobs':build_jobs,'rustBuildJobs':os.environ['CARGO_BUILD_JOBS']}),flush=True)
def run(*args,cwd=None):
    print(datetime.datetime.now(datetime.timezone.utc).isoformat()+' RUN '+str(args[0])+' '+' '.join(str(x) for x in args[1:]),flush=True)
    subprocess.run([str(x) for x in args],cwd=cwd or project,check=True)
def get(url):
    with urllib.request.urlopen(url,timeout=120) as response:return response.read()
version=json.loads(get('https://product-details.mozilla.org/1.0/firefox_versions.json'))['LATEST_FIREFOX_VERSION']
if not __import__('re').fullmatch(r'\d+\.\d+(\.\d+)?',version):raise SystemExit('Invalid upstream stable version')
base=f'https://archive.mozilla.org/pub/firefox/releases/{version}'
filename=f'source/firefox-{version}.source.tar.xz'
manifest=get(base+'/SHA512SUMS').decode()
expected_hash=next(line.split()[0] for line in manifest.splitlines() if line.split()[-1].lstrip('*')==filename)
archive=root/'source.tar.xz';run('curl','--fail','--location','--retry','2','--max-time','900','--output',archive,base+'/'+filename)
with archive.open('rb') as f:actual=hashlib.file_digest(f,'sha512').hexdigest()
if actual!=expected_hash:raise SystemExit('Mozilla source SHA512 mismatch')
with tarfile.open(archive) as tf:tf.extractall(root,filter='data')
archive.unlink();source=root/f'firefox-{version}'
if not (source/'mach').is_file():raise SystemExit('Unexpected source archive')
config_file=project/'rosavio.config.json';config=json.loads(config_file.read_text());config['upstreamVersion']=version;config_file.write_text(json.dumps(config))
python=__import__('sys').executable
run(python,project/'scripts/prepare-source.py',source,'--github-repo','aheinen1971-cmd/rosavio','--platform',a.platform)
mozconfig=source/'mozconfig';s=mozconfig.read_text().replace('MOZ_MAKE_FLAGS=-j8',f'MOZ_MAKE_FLAGS=-j{build_jobs}').replace('ac_add_options --disable-maintenance-service\n','')
s+='\nac_add_options --enable-bootstrap\nac_add_options --disable-debug-symbols\n'
mozconfig.write_text(s)
run('git','init','--quiet',cwd=source)
if a.platform=='macos-x64':
    # Source archive bytes are already hash-verified; avoid inherited global
    # line-ending conversion while indexing this large temporary source tree.
    run('git','config','core.autocrlf','false',cwd=source)
run('git','add','--all',cwd=source)
run('git','-c','user.name=Rosavio','-c','user.email=build@rosavio.invalid','commit','--quiet','-m','Verified Mozilla source with Rosavio platform overlay',cwd=source)
l10n=root/'l10n';pins=json.loads((source/'browser/locales/l10n-changesets.json').read_text())
locales=json.loads((project/'scripts/requested-languages.json').read_text())['locales'];translations=[x for x in locales if x!='en-US']
run('git','clone','--filter=blob:none','--no-checkout','https://github.com/mozilla-l10n/firefox-l10n',l10n)
run('git','sparse-checkout','set',*translations,cwd=l10n);run('git','checkout','--detach',pins['de']['revision'],cwd=l10n)
run(python,project/'scripts/prepare-german.py',source,l10n);run(python,project/'scripts/prepare-multilocale.py',source,l10n)
run(python,'mach','--no-interactive','bootstrap','--application-choice','browser','--no-system-changes',cwd=source)
for command in ['configure','build','package']:run(python,'mach','--no-interactive',command,cwd=source)
run(python,'mach','--no-interactive','package-multi-locale','--locales',*translations,cwd=source)
dist=source/'obj-rose/dist';out=project/'unix-results'/a.platform;out.mkdir(parents=True,exist_ok=True)
if a.platform.startswith('macos'):
    apps=list((dist/'rosavio').glob('*.app')) or list(dist.glob('*.app'))
    if len(apps)!=1:raise SystemExit('Expected exactly one native app bundle')
    package=apps[0];binary=package/'Contents/MacOS/rosavio'
else:package=dist/'rosavio';binary=package/'rosavio'
if not binary.is_file():raise SystemExit(f'Native binary missing: {binary}')
run('node',project/'scripts/check-locales.cjs',binary,out/'locale-check')
run('node',project/'scripts/check-unix-native.cjs',binary,out/'native-check',a.platform)
run('node',project/'scripts/check-extensions.cjs',binary,out/'extensions-check')
run('node',project/'scripts/check-translations.cjs',binary,out/'translations-check')
# Keep a genuine older application in a separate writable test installation.
baseline=root/'baseline'/package.name
baseline.parent.mkdir(parents=True,exist_ok=True)
shutil.copytree(package,baseline,symlinks=True)
old_build=os.environ['MOZ_BUILD_DATE']
new_build=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
if new_build<=old_build:raise SystemExit('Second genuine build needs a later BuildID')
os.environ['MOZ_BUILD_DATE']=new_build
for command in ['configure','build','package']:run(python,'mach','--no-interactive',command,cwd=source)
run(python,'mach','--no-interactive','package-multi-locale','--locales',*translations,cwd=source)
run('node',project/'scripts/check-locales.cjs',binary,out/'updated-locale-check')
run('node',project/'scripts/check-unix-native.cjs',binary,out/'native-check',a.platform)
(out/'paths.json').write_text(json.dumps({'source':str(source),'package':str(package),'baseline':str(baseline),'platform':a.platform},indent=2))

for pattern in ('*.dmg','*.tar.xz','*.tar.bz2'):
    for file in dist.glob(pattern):shutil.copy2(file,out/file.name)
if not any(x.suffix in ('.dmg','.xz','.bz2') for x in out.iterdir()):
    run('tar','-cJf',out/f'Rosavio-{a.platform}-test.tar.xz','-C',package.parent,package.name)
(out/'build.json').write_text(json.dumps({'platform':a.platform,'version':version,'buildID':os.environ['MOZ_BUILD_DATE'],'sourceSHA512':actual,'nativeStartAndTwentyLanguagesPassed':True,'nativeAutoupdateTestPassed':False,'published':False,'state':'native bring-up only; signed local and public update tests still required'},indent=2))
print('Native platform package and language/start reports ready. Autoupdate not yet certified.')
