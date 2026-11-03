"""Prepare isolated Rosavio workspace pages and native browser tool entry points."""
from pathlib import Path
import sys,re

source=Path(sys.argv[1]);assets=Path(__file__).with_name('rosavio-pages')
files=['rosavio-workspace-l10n.js','rosavio-workspace.html','rosavio-workspace.css','rosavio-workspace.js','rosavio-tools-menu.js']
for name in files:
    (source/'browser/base/content'/name).write_text((assets/name).read_text(encoding='utf-8'),encoding='utf-8')
for name in ['RosavioWorkspaceParent.sys.mjs','RosavioWorkspaceChild.sys.mjs']:
    (source/'browser/actors'/name).write_text((assets/name).read_text(encoding='utf-8'),encoding='utf-8')
    p=source/'browser/actors/moz.build';s=p.read_text(encoding='utf-8')
    line='FINAL_TARGET_FILES.actors += ["'+name+'"]'
    if line not in s:p.write_text(s+'\n'+line+'\n',encoding='utf-8')
p=source/'browser/components/DesktopActorRegistry.sys.mjs';s=p.read_text(encoding='utf-8')
s=re.sub(r'\n  RosavioWorkspace: \{.*?\n  \},','',s,flags=re.S)
if 'RosavioWorkspace:' not in s:
    anchor='let JSWINDOWACTORS = {'
    if anchor not in s:raise SystemExit('Actor registry changed')
    s=s.replace(anchor,anchor+'''
  RosavioWorkspace: {
    parent: {esModuleURI: "resource:///actors/RosavioWorkspaceParent.sys.mjs"},
    child: {esModuleURI: "resource:///actors/RosavioWorkspaceChild.sys.mjs", events: {
      RosavioWorkspaceRead: {wantUntrusted: true, capture: true},
      RosavioWorkspaceSave: {wantUntrusted: true, capture: true},
    }},
    matches: ["about:rosavio-notes", "about:rosavio-home"],
    allFrames: false, safeForUntrustedWebProcess: true,
  },''',1);p.write_text(s,encoding='utf-8')
for page in ['rosavio-notes','rosavio-home']:
    p=source/'browser/components/about/AboutRedirector.cpp';s=p.read_text(encoding='utf-8')
    if '{"'+page+'"' not in s:
        anchor='static const RedirEntry kRedirMap[] = {'
        if anchor not in s:raise SystemExit('About registry changed')
        s=s.replace(anchor,anchor+'\n    {"'+page+'", "chrome://browser/content/rosavio-workspace.html", nsIAboutModule::URI_SAFE_FOR_UNTRUSTED_CONTENT | nsIAboutModule::URI_MUST_LOAD_IN_CHILD | nsIAboutModule::ALLOW_SCRIPT},',1)
        p.write_text(s,encoding='utf-8')
    p=source/'browser/components/about/components.conf';s=p.read_text(encoding='utf-8')
    if "'"+page+"'" not in s:
        if 'pages = [' not in s:raise SystemExit('About components changed')
        p.write_text(s.replace('pages = [',"pages = [\n    '"+page+"',",1),encoding='utf-8')
p=source/'browser/base/content/appmenu-viewcache.inc.xhtml';s=p.read_text(encoding='utf-8')
if 'id="appMenu-rosavio-qr"' not in s:
    anchor='<toolbarbutton id="appMenu-rosavio-privacy"'
    if anchor not in s:raise SystemExit('Prepare information pages before workspace')
    buttons='\n'.join('<toolbarbutton id="appMenu-rosavio-'+id+'" class="subviewbutton" label="'+label+'"/>' for id,label in [('qr','Webseite als QR-Code'),('notes','Meine Notizen'),('home','Meine Startseite'),('reader','Lesemodus ein/aus'),('split','Zwei Webseiten nebeneinander')])
    p.write_text(s.replace(anchor,buttons+'\n'+anchor,1),encoding='utf-8')
p=source/'browser/base/jar.mn';s=p.read_text(encoding='utf-8')
for name in files:
    line=f'        content/browser/{name} (content/{name})'
    if line not in s:s+='\n'+line+'\n'
p.write_text(s,encoding='utf-8')
p=source/'browser/base/content/browser.xhtml';s=p.read_text(encoding='utf-8')
if 'chrome://browser/content/rosavio-tools-menu.js' not in s:
    anchor='<script src="chrome://browser/content/browser-main.js"></script>'
    if anchor not in s:raise SystemExit('Browser script anchor changed')
    p.write_text(s.replace(anchor,anchor+'\n<script src="chrome://browser/content/rosavio-tools-menu.js"></script>',1),encoding='utf-8')
print('Workspace prototype prepared; native and packaged qualification still required.')
