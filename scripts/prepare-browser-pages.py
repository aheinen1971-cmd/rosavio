"""Add read-only Rosavio information pages with a narrowly scoped IPC bridge."""
from pathlib import Path
import sys,re

source = Path(sys.argv[1])
assets = Path(__file__).with_name('rosavio-pages')
for name in ('rosavio-details.html', 'rosavio-details.css', 'rosavio-l10n.js', 'rosavio-details.js'):
    (source / 'browser/base/content' / name).write_text((assets / name).read_text(encoding='utf-8'), encoding='utf-8')
for name in ('RosavioDetailsParent.sys.mjs', 'RosavioDetailsChild.sys.mjs'):
    (source / 'browser/actors' / name).write_text((assets / name).read_text(encoding='utf-8'), encoding='utf-8')
    build = source / 'browser/actors/moz.build'
    s = build.read_text(encoding='utf-8')
    if '"' + name + '"' not in s:
        s += '\nFINAL_TARGET_FILES.actors += ["' + name + '"]\n'
        build.write_text(s, encoding='utf-8')

registry = source / 'browser/components/DesktopActorRegistry.sys.mjs'
s = registry.read_text(encoding='utf-8')
s = re.sub(r'\n  RosavioDetails: \{.*?\n  \},', '', s, flags=re.S)
if 'RosavioDetails:' not in s:
    anchor = 'let JSWINDOWACTORS = {'
    if anchor not in s:
        raise SystemExit('Desktop actor registry changed')
    s = s.replace(anchor, anchor + '''
  RosavioDetails: {
    parent: { esModuleURI: "resource:///actors/RosavioDetailsParent.sys.mjs" },
    child: {
      esModuleURI: "resource:///actors/RosavioDetailsChild.sys.mjs",
      events: {
        RosavioSummaryRequest: { wantUntrusted: true, capture: true },
        RosavioOpenPageRequest: { wantUntrusted: true, capture: true },
      },
    },
    matches: ["about:rosavio-privacy", "about:rosavio-updates"],
    allFrames: false,
    safeForUntrustedWebProcess: true,
  },''', 1)
    registry.write_text(s, encoding='utf-8')
redirect = source / 'browser/components/about/AboutRedirector.cpp'
s = redirect.read_text(encoding='utf-8')
conf = source / 'browser/components/about/components.conf'
c = conf.read_text(encoding='utf-8')
for page in ('rosavio-privacy', 'rosavio-updates'):
    if '{"' + page + '"' not in s:
        anchor = 'static const RedirEntry kRedirMap[] = {'
        if anchor not in s:
            raise SystemExit('About redirect map changed')
        s = s.replace(anchor, anchor + '''
    {"''' + page + '''", "chrome://browser/content/rosavio-details.html",
     nsIAboutModule::URI_SAFE_FOR_UNTRUSTED_CONTENT |
         nsIAboutModule::URI_MUST_LOAD_IN_CHILD | nsIAboutModule::ALLOW_SCRIPT},''', 1)
    if "'" + page + "'" not in c:
        if 'pages = [' not in c:
            raise SystemExit('About component registry changed')
        c = c.replace('pages = [', "pages = [\n    '" + page + "',", 1)
redirect.write_text(s, encoding='utf-8')
conf.write_text(c, encoding='utf-8')

menu = source / 'browser/base/content/appmenu-viewcache.inc.xhtml'
s = menu.read_text(encoding='utf-8')
if 'appMenu-rosavio-privacy' not in s:
    anchor = '<toolbarbutton id="appMenu-rosavio-extensions"'
    if anchor not in s:
        raise SystemExit('Prepare extension menu before browser information pages')
    s = s.replace(anchor, '''<toolbarbutton id="appMenu-rosavio-privacy" class="subviewbutton" label="Datenschutz im Überblick"/>
      <toolbarbutton id="appMenu-rosavio-updates" class="subviewbutton" label="Neues in Rosavio"/>
      ''' + anchor, 1)
    menu.write_text(s, encoding='utf-8')
menujs = '''document.addEventListener('command', event => {
  const pages = {'appMenu-rosavio-privacy':'about:rosavio-privacy','appMenu-rosavio-updates':'about:rosavio-updates'};
  if (Object.hasOwn(pages, event.target.id)) {openTrustedLinkIn(pages[event.target.id], 'tab'); PanelUI.hide();}
});
window.addEventListener('load', async () => {
  await PanelUI.ensureReady();
  const strings = {};
  Services.scriptloader.loadSubScript('chrome://browser/content/rosavio-l10n.js', strings, 'UTF-8');
  const l10n = strings.RosavioL10n.forLocale(Services.locale.appLocaleAsBCP47);
  for (const [id,key] of [['privacy','Privacy at a glance'],['updates','What’s new in Rosavio'],['extensions','Rosavio Extensions']]) {
    PanelUI.mainView.querySelector('#appMenu-rosavio-'+id).setAttribute('label', l10n.text(key));
  }
}, {once:true});'''
(source / 'browser/base/content/rosavio-details-menu.js').write_text(menujs, encoding='utf-8')
jar = source / 'browser/base/jar.mn'
s = jar.read_text(encoding='utf-8')
for name in ('rosavio-details.html', 'rosavio-details.css', 'rosavio-l10n.js', 'rosavio-details.js', 'rosavio-details-menu.js'):
    line = f'        content/browser/{name} (content/{name})'
    if line not in s:
        s += '\n' + line + '\n'
jar.write_text(s, encoding='utf-8')
browser = source / 'browser/base/content/browser.xhtml'
s = browser.read_text(encoding='utf-8')
if 'chrome://browser/content/rosavio-details-menu.js' not in s:
    anchor = '<script src="chrome://browser/content/browser-main.js"></script>'
    if anchor not in s:
        raise SystemExit('Browser script anchor changed')
    s = s.replace(anchor, anchor + '\n  <script src="chrome://browser/content/rosavio-details-menu.js"></script>', 1)
    browser.write_text(s, encoding='utf-8')
print('Read-only privacy overview and bundled release notes prepared (20 bundled interface languages).')

