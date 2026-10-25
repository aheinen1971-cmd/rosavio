"""Prepare a public Flatpak repo/ref with a pinned public signing identity.

No private key is accepted, exported or uploaded by this helper. The public repo
must already have passed native installation/update tests before publication.
"""
import argparse,base64,configparser,json,pathlib,re,subprocess
APP='io.github.aheinen1971_cmd.Rosavio'
def prepare(repo,public_key,fingerprint,output,url):
    if not re.fullmatch(r'[0-9A-F]{40}',fingerprint):raise ValueError('Expected pinned OpenPGP fingerprint')
    if url!='https://aheinen1971-cmd.github.io/rosavio/flatpak/':raise ValueError('Unapproved distribution endpoint')
    if not (repo/'summary').is_file() or not (repo/'summary.sig').is_file():raise ValueError('Signed repository summary required')
    keys=subprocess.check_output(['gpg','--batch','--with-colons','--show-keys',str(public_key)],text=True)
    if not any(line.startswith('fpr:') and line.split(':')[9]==fingerprint for line in keys.splitlines()):raise ValueError('Wrong public signing key')
    ref=f'app/{APP}/x86_64/stable'
    subprocess.run(['flatpak','repo','--branches',str(repo)],check=True,stdout=subprocess.DEVNULL)
    commit=subprocess.check_output(['ostree','--repo='+str(repo),'rev-parse',ref],text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{64}',commit):raise ValueError('Missing stable app revision')
    key=base64.b64encode(public_key.read_bytes()).decode('ascii')
    output.mkdir(parents=True,exist_ok=True)
    config=configparser.ConfigParser(interpolation=None);config.optionxform=str
    config['Flatpak Repo']={'Title':'Rosavio Flatpak','Url':url,'Homepage':'https://aheinen1971-cmd.github.io/rosavio/','Comment':'Rosavio with twenty languages; updates managed by Flatpak','GPGKey':key,'DefaultBranch':'stable'}
    with (output/'Rosavio.flatpakrepo').open('w',encoding='utf-8') as f:config.write(f,space_around_delimiters=False)
    config=configparser.ConfigParser(interpolation=None);config.optionxform=str
    config['Flatpak Ref']={'Title':'Rosavio','Name':APP,'Branch':'stable','IsRuntime':'false','Url':url,'GPGKey':key,'SuggestRemoteName':'rosavio','RuntimeRepo':'https://flathub.org/repo/flathub.flatpakrepo'}
    with (output/'Rosavio.flatpakref').open('w',encoding='utf-8') as f:config.write(f,space_around_delimiters=False)
    (output/'distribution.json').write_text(json.dumps({'appID':APP,'architecture':'x86_64','branch':'stable','repository':url,'signingFingerprint':fingerprint,'commit':commit,'publicUpdateTestPassed':False,'productionReady':False},indent=2))
    return commit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('repository',type=pathlib.Path);p.add_argument('public_key',type=pathlib.Path);p.add_argument('fingerprint');p.add_argument('output',type=pathlib.Path)
    a=p.parse_args();prepare(a.repository,a.public_key,a.fingerprint,a.output,'https://aheinen1971-cmd.github.io/rosavio/flatpak/')
