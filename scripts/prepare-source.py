"""Apply the Rose overlay to an extracted Firefox 158.0 release source tree."""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

project = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('source', type=pathlib.Path)
parser.add_argument('--update-origin')
parser.add_argument('--github-repo', help='OWNER/REPOSITORY for GitHub Releases hosting without a separate server')
parser.add_argument('--local-test', action='store_true')
args = parser.parse_args()
source = args.source.resolve()
config = json.loads((project / 'rose.config.json').read_text())
version = (source / 'browser/config/version.txt').read_text().strip()
if version != config['upstreamVersion']:
    raise SystemExit(f'Expected Firefox {config["upstreamVersion"]}, found {version}; review overlay before upgrading')
origin = args.update_origin or config['updateOrigin']
if args.github_repo:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+', args.github_repo):
        raise SystemExit('Invalid GitHub OWNER/REPOSITORY')
    if args.update_origin or args.local_test:
        raise SystemExit('Choose either GitHub Releases, a custom origin, or local-test mode')
    origin = 'https://github.com'
if not origin:
    if not args.local_test:
        raise SystemExit('No production update URL. Configure --update-origin https://your-host or use --local-test explicitly')
    origin = 'http://127.0.0.1:8877'
url = urlparse(origin)
if url.scheme != 'https' and not (args.local_test and url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost')):
    raise SystemExit('A production update origin must use HTTPS')
if url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
    raise SystemExit('Use a bare origin without credentials, query, fragment or subpath')
cert = project / 'certificates/rose-update.der'
if not cert.exists():
    raise SystemExit('Create the Rose update signing identity first')

branding = source / 'browser/branding/rose'
if not branding.exists():
    shutil.copytree(source / 'browser/branding/unofficial', branding)
for name in ('configure.sh', 'branding.nsi', 'locales/en-US/brand.ftl', 'locales/en-US/brand.properties'):
    file = branding / name
    text = file.read_text()
    text = text.replace('Mozilla Developer Preview', 'Rose').replace('nightlyunofficial', 'rose.browser').replace('Nightly', 'Rose')
    text = text.replace('-brand-product-name = Firefox', '-brand-product-name = Rose').replace('-vendor-short-name = Mozilla', '-vendor-short-name = Rose')
    if name == 'branding.nsi':
        text = re.sub(r'(!define CompanyName\s+)"[^"]+"', r'\1"Rose"', text)
        text = re.sub(r'(!define Channel\s+)"[^"]+"', r'\1"rose-release"', text)
    file.write_text(text, newline='\n')

# Keep the Firefox application ID for signed WebExtension compatibility.
# Process names, profile directories, vendor and MAR channel are independent.
browser_config = source / 'browser/moz.configure'
text = browser_config.read_text()
text = text.replace('imply_option("MOZ_APP_VENDOR", "Mozilla")', 'imply_option("MOZ_APP_VENDOR", "Rose")')
browser_config.write_text(text, newline='\n')

updater = source / 'toolkit/mozapps/update/updater'
build_file = updater / 'moz.build'
text = build_file.read_text()
needle = 'if CONFIG["MOZ_UPDATE_CHANNEL"] in ("beta", "release", "esr"):'
replacement = ('if CONFIG["MOZ_UPDATE_CHANNEL"] == "rose-release":\n'
               '    primary_cert.inputs += ["rose-update.der"]\n'
               '    secondary_cert.inputs += ["rose-update.der"]\n'
               'el' + needle)
if 'primary_cert.inputs += ["rose-update.der"]' not in text:
    if needle not in text:
        raise SystemExit('Upstream updater certificate selection changed; refusing unsafe patch')
    text = text.replace(needle, replacement, 1)
build_file.write_text(text, newline='\n')
shutil.copyfile(cert, updater / 'rose-update.der')

update_url = origin.rstrip('/') + '/update/1/%PRODUCT%/%VERSION%/%BUILD_ID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/update.xml'
if args.github_repo:
    update_url = f'https://github.com/{args.github_repo}/releases/latest/download/rose-win64-update.xml'
prefs = branding / 'pref/firefox-branding.js'
prefs.write_text('''/* Rose branding defaults. Based on MPL-2.0 Firefox source. */
pref("startup.homepage_override_url", "");
pref("startup.homepage_welcome_url", "");
pref("startup.homepage_welcome_url.additional", "");
pref("app.update.interval", 21600);
pref("app.update.auto", true);
pref("app.update.background.enabled", true);
pref("extensions.update.enabled", true);
pref("browser.contentblocking.category", "strict");
pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
pref("browser.newtabpage.activity-stream.showSponsored", false);
''' + f'pref("app.update.url", {json.dumps(update_url)});\n'
    + f'pref("app.update.url.manual", {json.dumps(origin)});\n'
    + f'pref("app.update.url.details", {json.dumps(origin)});\n', newline='\n')

# Full compilation is mandatory: artifact builds would retain upstream binaries.
mozconfig = '''mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-rose
mk_add_options MOZ_MAKE_FLAGS=-j8
ac_add_options --enable-application=browser
ac_add_options --with-branding=browser/branding/rose
ac_add_options --with-app-name=rose
ac_add_options --with-app-basename=Rose
ac_add_options --enable-update-channel=rose-release
ac_add_options --enable-updater
ac_add_options --disable-maintenance-service
ac_add_options --disable-crashreporter
ac_add_options --disable-tests
export MOZ_APP_REMOTINGNAME=rose
export MAR_CHANNEL_ID=rose-release
export ACCEPTED_MAR_CHANNEL_IDS=rose-release
'''
(source / 'mozconfig').write_text(mozconfig, newline='\n')
subprocess.run([sys.executable, str(project / 'scripts/create-icons.py'), str(branding)], check=True)
(source / 'rose-build.json').write_text(json.dumps({'name': 'Rose', 'upstreamVersion': version, 'updateOrigin': origin, 'updateUrl': update_url, 'githubRepo': args.github_repo, 'localTest': args.local_test, 'signedUpdatesRequired': True}, indent=2))
print(f'Rose overlay applied to Firefox {version}. Update origin: {origin}')
