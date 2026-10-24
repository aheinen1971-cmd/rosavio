"""Install a sandboxed Rosavio catalogue page; installations stay on official AMO."""
from pathlib import Path
import sys

source=Path(sys.argv[1])
html='''<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' chrome:; style-src 'self' chrome:; connect-src https://addons.mozilla.org; base-uri 'none'; object-src 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Rosavio-Erweiterungen</title>
<link rel="stylesheet" href="chrome://browser/content/rosavio-addons.css"><script src="chrome://browser/content/rosavio-addons.js" defer></script></head>
<body><main><header><span class="rose" aria-hidden="true">🌹</span><h1>Rosavio-Erweiterungen</h1><p id="intro">Suche Erweiterungen aus dem offiziellen Mozilla-Katalog.</p></header>
<form id="search"><label for="query" id="query-label">Was möchtest du hinzufügen?</label><div class="searchrow"><input id="query" type="search" maxlength="100" required placeholder="Zum Beispiel: Übersetzer" autocomplete="off"><button id="search-button">Suchen</button></div></form>
<p id="notice">Zum Installieren öffnest du die offizielle Erweiterungsseite. Rosavio fragt vor der Installation nach deiner Zustimmung.</p>
<nav><a id="manage" href="about:addons">Installierte Erweiterungen verwalten</a> · <a id="catalog" href="https://addons.mozilla.org/firefox/" rel="noreferrer">Mozilla-Katalog öffnen</a></nav>
<p id="status" role="status" aria-live="polite"></p><section id="results" aria-label="Suchergebnisse"></section></main></body></html>'''
css='''html{font:16px system-ui,sans-serif;color:#402029;background:#fff5f5}body{margin:0}main{max-width:960px;margin:auto;padding:36px 24px}header{margin-bottom:28px}.rose{font-size:36px}h1{font-size:clamp(26px,5vw,40px);margin:12px 0}p{line-height:1.6}label{display:block;font-weight:600;margin-bottom:8px}.searchrow{display:flex;gap:10px}input{font:inherit;padding:13px;border:1px solid #b98d98;border-radius:10px;flex:1;min-width:0}button,.install{font:inherit;background:#ac193f;color:white;border:0;border-radius:10px;padding:13px 20px;cursor:pointer;text-decoration:none}a{color:#991536}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #477b48;outline-offset:3px}#notice{color:#72515a;font-size:14px}nav{line-height:1.8}#results{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}article{background:white;border:1px solid #ebcbd3;border-radius:16px;padding:22px;display:flex;flex-direction:column;align-items:start}h2{font-size:20px;margin:0}article p{flex:1}.install{font-size:14px}#status{min-height:24px}@media(max-width:500px){main{padding:24px 16px}.searchrow{flex-direction:column}}'''
js='''"use strict";
const en=!navigator.language.toLowerCase().startsWith('de');
const words=en?{title:'Rosavio Extensions',intro:'Find extensions in the official Mozilla catalogue.',label:'What would you like to add?',placeholder:'For example: translator',search:'Search',notice:'Open the official extension page to install. Rosavio will ask for your permission before installation.',manage:'Manage installed extensions',catalog:'Open Mozilla catalogue',loading:'Searching…',none:'No extensions found. Try a different search.',error:'The catalogue could not be loaded. You can use the Mozilla catalogue link above.',install:'Open installation page',results:'Search results'}:{title:'Rosavio-Erweiterungen',intro:'Suche Erweiterungen aus dem offiziellen Mozilla-Katalog.',label:'Was möchtest du hinzufügen?',placeholder:'Zum Beispiel: Übersetzer',search:'Suchen',notice:'Zum Installieren öffnest du die offizielle Erweiterungsseite. Rosavio fragt vor der Installation nach deiner Zustimmung.',manage:'Installierte Erweiterungen verwalten',catalog:'Mozilla-Katalog öffnen',loading:'Suche läuft…',none:'Keine Erweiterungen gefunden. Probiere einen anderen Suchbegriff.',error:'Der Katalog konnte nicht geladen werden. Du kannst oben den Mozilla-Katalog öffnen.',install:'Installationsseite öffnen',results:'Suchergebnisse'};
document.documentElement.lang=en?'en':'de';document.title=words.title;document.querySelector('h1').textContent=words.title;
for(const [id,key] of [['intro','intro'],['query-label','label'],['search-button','search'],['notice','notice'],['manage','manage'],['catalog','catalog']])document.getElementById(id).textContent=words[key];
document.getElementById('query').placeholder=words.placeholder;document.getElementById('results').setAttribute('aria-label',words.results);
const text=value=>typeof value==='string'?value:(value?.[navigator.language]||value?.['en-US']||Object.values(value||{}).find(v=>typeof v==='string')||'');
let controller;
document.getElementById('search').addEventListener('submit',async event=>{
 event.preventDefault();const query=document.getElementById('query').value.trim();if(!query)return;
 if(controller)controller.abort();controller=new AbortController();const signal=controller.signal;
 const status=document.getElementById('status'),results=document.getElementById('results');results.replaceChildren();status.textContent=words.loading;
 const url=new URL('https://addons.mozilla.org/api/v5/addons/search/');url.search=new URLSearchParams({q:query.slice(0,100),app:'firefox',type:'extension',page_size:'12',lang:navigator.language});
 document.getElementById('catalog').href='https://addons.mozilla.org/firefox/search/?'+new URLSearchParams({q:query,type:'extension'});
 try{
  const response=await fetch(url,{credentials:'omit',referrerPolicy:'no-referrer',signal});if(!response.ok)throw Error('Catalogue unavailable');const data=await response.json();if(!Array.isArray(data.results))throw Error('Invalid catalogue');
  for(const addon of data.results.slice(0,12)){
   let destination;try{destination=new URL(addon.url);}catch{continue;}
   if(destination.origin!=='https://addons.mozilla.org'||!/^\\/[^/]+\\/firefox\\/addon\\//.test(destination.pathname))continue;
   const card=document.createElement('article'),heading=document.createElement('h2'),description=document.createElement('p'),link=document.createElement('a');
   heading.textContent=text(addon.name);description.textContent=text(addon.summary);link.href=destination.href;link.rel='noreferrer';link.className='install';link.textContent=words.install;
   card.append(heading,description,link);results.append(card);
  }
  status.textContent=results.childElementCount?(en?results.childElementCount+' results':results.childElementCount+' Ergebnisse'):words.none;
 }catch(error){if(error.name!=='AbortError')status.textContent=words.error;}
});'''
menujs="""document.addEventListener('command',event=>{if(event.target.id==='appMenu-rosavio-extensions'){openTrustedLinkIn('about:rosavio-addons','tab');PanelUI.hide();}});"""
assets={'rosavio-addons.html':html,'rosavio-addons.css':css,'rosavio-addons.js':js,'rosavio-menu.js':menujs}
for name,content in assets.items():(source/'browser/base/content'/name).write_text(content,encoding='utf-8')
jar=source/'browser/base/jar.mn';s=jar.read_text(encoding='utf-8')
for name in assets:
 line=f'        content/browser/{name} (content/{name})'
 if line not in s:s+='\n'+line+'\n'
jar.write_text(s,encoding='utf-8')
redirect=source/'browser/components/about/AboutRedirector.cpp';s=redirect.read_text(encoding='utf-8')
if '{"rosavio-addons"' not in s:
 anchor='static const RedirEntry kRedirMap[] = {'
 if anchor not in s:raise SystemExit('About redirect map changed')
 s=s.replace(anchor,anchor+'''\n    {"rosavio-addons", "chrome://browser/content/rosavio-addons.html",
     nsIAboutModule::URI_SAFE_FOR_UNTRUSTED_CONTENT |
         nsIAboutModule::URI_MUST_LOAD_IN_CHILD | nsIAboutModule::ALLOW_SCRIPT},''',1)
 redirect.write_text(s,encoding='utf-8')
conf=source/'browser/components/about/components.conf';s=conf.read_text(encoding='utf-8')
if "'rosavio-addons'" not in s:
 if 'pages = [' not in s:raise SystemExit('About component registration changed')
 conf.write_text(s.replace('pages = [',"pages = [\n    'rosavio-addons',",1),encoding='utf-8')
menu=source/'browser/base/content/appmenu-viewcache.inc.xhtml';s=menu.read_text(encoding='utf-8')
if 'appMenu-rosavio-extensions' not in s:
 anchor='<toolbarbutton id="appMenu-extensions-themes-button"'
 if anchor not in s:raise SystemExit('Extensions menu anchor changed')
 entry='''<toolbarbutton id="appMenu-rosavio-extensions" class="subviewbutton" label="Rosavio-Erweiterungen"/>
      '''
 menu.write_text(s.replace(anchor,entry+anchor,1),encoding='utf-8')
browser=source/'browser/base/content/browser.xhtml';s=browser.read_text(encoding='utf-8')
if 'chrome://browser/content/rosavio-menu.js' not in s:
 anchor='<script src="chrome://browser/content/browser-main.js"></script>'
 if anchor not in s:raise SystemExit('Browser script anchor changed')
 browser.write_text(s.replace(anchor,anchor+'\n  <script src="chrome://browser/content/rosavio-menu.js"></script>',1),encoding='utf-8')
print('Sandboxed about:rosavio-addons catalogue and menu entry prepared; native installation remains on official AMO.')
