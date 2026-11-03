'use strict';
const STATUS_LANGUAGE_NAMES={de:'Deutsch',en:'English',fr:'Français',es:'Español',nl:'Nederlands',it:'Italiano','pt-PT':'Português',pl:'Polski',cs:'Čeština',da:'Dansk','sv-SE':'Svenska','nb-NO':'Norsk bokmål',fi:'Suomi',tr:'Türkçe',uk:'Українська',el:'Ελληνικά',ja:'日本語',ko:'한국어',ar:'العربية',he:'עברית'};
const requestedLanguage=new URLSearchParams(location.search).get('lang')||'de';
const statusLanguage=Object.hasOwn(STATUS_LANGUAGE_NAMES,requestedLanguage)?requestedLanguage:'de';
const statusWords=Object.fromEntries(Object.entries(STATUS_LOCALES[statusLanguage]).map(([key,value])=>[key.trim(),value.trim()]));
function statusText(source){
 const value=String(source).trim();
 if(Object.hasOwn(statusWords,value))return statusWords[value];
 const phase=value.match(/^(\d+) von (\d+) Phasen abgeschlossen$/);
 if(phase){const result=statusWords['{done} von {total} Phasen abgeschlossen'].replace('{done}',phase[1]).replace('{total}',phase[2]);return ['ar','he'].includes(statusLanguage)?result.replace(/\d+\s*\/\s*\d+/g,number=>'\u2066'+number+'\u2069'):result;}
 const failure=value.match(/^Letzter Auftrag: (failure|timed_out|cancelled|action_required); siehe Laufdetails$/);
 if(failure)return statusWords['Letzter Auftrag: {result}; siehe Laufdetails'].replace('{result}',statusWords[failure[1]]);
 const icon=value.match(/^(🟢|🟡|🔴|⚪|ℹ️)\s+(.+)$/u);
 if(icon)return icon[1]+' '+statusText(icon[2]);
 return source;
}
document.documentElement.lang=statusLanguage;
document.documentElement.dir=['ar','he'].includes(statusLanguage)?'rtl':'ltr';
const walker=document.createTreeWalker(document.documentElement,NodeFilter.SHOW_TEXT);
const textNodes=[];while(walker.nextNode())if(!['SCRIPT','STYLE'].includes(walker.currentNode.parentElement?.tagName))textNodes.push(walker.currentNode);
for(const node of textNodes)if(node.textContent.trim())node.textContent=statusText(node.textContent);
const homeLink=document.querySelector('footer nav a');
homeLink.href=statusLanguage==='de'?'../':'../'+statusLanguage+'.html';
const languageNav=document.createElement('nav');languageNav.className='status-languages';languageNav.setAttribute('aria-label',statusText('Sprachen'));
for(const [code,name] of Object.entries(STATUS_LANGUAGE_NAMES)){
 const link=document.createElement('a');link.href='?lang='+encodeURIComponent(code);link.textContent=name;link.lang=code;link.hreflang=code;link.dir='auto';
 if(code===statusLanguage)link.setAttribute('aria-current','page');languageNav.append(link);
}
document.querySelector('header').after(languageNav);
