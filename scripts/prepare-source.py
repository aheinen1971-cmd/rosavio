"""Apply the Rosavio overlay to an extracted Firefox 158.0 release source tree."""
import argparse
import json
import os
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
parser.add_argument('--platform', choices=('win64', 'linux-x64', 'macos-x64', 'macos-arm64'), default='win64')
args = parser.parse_args()
source = args.source.resolve()
if os.name == 'nt' and len(str(source)) > 62:
    raise SystemExit('Firefox on Windows requires a source path no longer than 62 characters; choose a shorter working directory')
config = json.loads((project / 'rosavio.config.json').read_text())
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
info_url = f'https://github.com/{args.github_repo}/releases' if args.github_repo else origin
project_url = f'https://github.com/{args.github_repo}' if args.github_repo else origin
cert = project / 'certificates/rosavio-update.der'
if not cert.exists():
    raise SystemExit('Create the Rosavio update signing identity first')

branding = source / 'browser/branding/rosavio'
if not branding.exists():
    shutil.copytree(source / 'browser/branding/unofficial', branding)
for name in ('configure.sh', 'branding.nsi', 'locales/en-US/brand.ftl', 'locales/en-US/brand.properties'):
    file = branding / name
    text = file.read_text()
    text = text.replace('Mozilla Developer Preview', 'Rosavio').replace('nightlyunofficial', 'rosavio.browser').replace('Nightly', 'Rosavio')
    text = text.replace('-brand-product-name = Firefox', '-brand-product-name = Rosavio').replace('-vendor-short-name = Mozilla', '-vendor-short-name = Rosavio')
    if name == 'branding.nsi':
        text = re.sub(r'(!define CompanyName\s+)"[^"]+"', r'\1"Rosavio"', text)
        text = re.sub(r'(!define Channel\s+)"[^"]+"', r'\1"rosavio-release"', text)
        for key, value in (('URLInfoAbout', project_url), ('HelpLink', project_url + '/issues'), ('URLManualDownload', info_url)):
            text = re.sub(r'(!define ' + key + r'\s+)"[^"]+"', lambda match: match.group(1) + '"' + value + '"', text)
    file.write_text(text, newline='\n')

# Keep the Firefox application ID for signed WebExtension compatibility.
# Process names, profile directories, vendor and MAR channel are independent.
browser_config = source / 'browser/moz.configure'
text = browser_config.read_text()
text = text.replace('imply_option("MOZ_APP_VENDOR", "Mozilla")', 'imply_option("MOZ_APP_VENDOR", "Rosavio")')
browser_config.write_text(text, newline='\n')

updater = source / 'toolkit/mozapps/update/updater'
build_file = updater / 'moz.build'
text = build_file.read_text()
needle = 'if CONFIG["MOZ_UPDATE_CHANNEL"] in ("beta", "release", "esr"):'
replacement = ('if CONFIG["MOZ_UPDATE_CHANNEL"] == "rosavio-release":\n'
               '    primary_cert.inputs += ["rosavio-update.der"]\n'
               '    secondary_cert.inputs += ["rosavio-update.der"]\n'
               'el' + needle)
if 'primary_cert.inputs += ["rosavio-update.der"]' not in text:
    if needle not in text:
        raise SystemExit('Upstream updater certificate selection changed; refusing unsafe patch')
    text = text.replace(needle, replacement, 1)
build_file.write_text(text, newline='\n')
shutil.copyfile(cert, updater / 'rosavio-update.der')

update_url = origin.rstrip('/') + '/update/1/%PRODUCT%/%VERSION%/%BUILD_ID%/%BUILD_TARGET%/%LOCALE%/%CHANNEL%/update.xml'
if args.github_repo:
    update_url = f'https://github.com/{args.github_repo}/releases/latest/download/rosavio-win64-update.xml'
    if args.platform != 'win64':
        update_url = f'https://github.com/{args.github_repo}/releases/download/rosavio-{args.platform}-latest/rosavio-{args.platform}-update.xml'
prefs = branding / 'pref/firefox-branding.js'
prefs.write_text('''/* Rosavio branding defaults. Based on MPL-2.0 Firefox source. */
pref("startup.homepage_override_url", "");
pref("startup.homepage_welcome_url", "");
pref("startup.homepage_welcome_url.additional", "");
pref("app.update.interval", 21600);
pref("app.update.auto", true);
pref("app.update.background.enabled", true);
pref("extensions.update.enabled", true);
pref("browser.translations.enable", true);
pref("browser.translations.select.enable", true);
pref("browser.translations.quickAction.enabled", true);
pref("browser.contentblocking.category", "strict");
pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
pref("browser.newtabpage.activity-stream.showSponsored", false);
''' + f'pref("app.update.url", {json.dumps(update_url)});\n'
    + f'pref("app.update.url.manual", {json.dumps(info_url)});\n'
    + f'pref("app.update.url.details", {json.dumps(info_url)});\n', newline='\n')

app_ini = source / 'build/application.ini.in'
text = app_ini.read_text()
text, count = re.subn(r'(?m)(\[AppUpdate\]\n)URL=[^\n]+', lambda match: match.group(1) + 'URL=' + update_url, text)
if count != 1:
    raise SystemExit('Native application update URL template changed; refusing an incomplete updater configuration')
app_ini.write_text(text, newline='\n')

# Full compilation is mandatory: artifact builds would retain upstream binaries.
mozconfig = '''mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-rose
mk_add_options MOZ_MAKE_FLAGS=-j8
ac_add_options --enable-application=browser
ac_add_options --with-branding=browser/branding/rosavio
ac_add_options --with-app-name=rosavio
ac_add_options --with-app-basename=Rosavio
ac_add_options --enable-update-channel=rosavio-release
ac_add_options --enable-updater
ac_add_options --disable-maintenance-service
ac_add_options --disable-crashreporter
ac_add_options --disable-tests
export MOZ_APP_REMOTINGNAME=rosavio
export MAR_CHANNEL_ID=rosavio-release
export ACCEPTED_MAR_CHANNEL_IDS=rosavio-release
'''
(source / 'mozconfig').write_text(mozconfig, newline='\n')
subprocess.run([sys.executable, str(project / 'scripts/create-icons.py'), str(branding)], check=True)
(source / 'rosavio-build.json').write_text(json.dumps({'name': 'Rosavio', 'upstreamVersion': version, 'updateOrigin': origin, 'updateUrl': update_url, 'githubRepo': args.github_repo, 'localTest': args.local_test, 'signedUpdatesRequired': True}, indent=2))
subprocess.run([sys.executable, str(project / 'scripts/prepare-extensions.py'), str(source)], check=True)
print(f'Rosavio overlay applied to Firefox {version}. Update origin: {origin}')
