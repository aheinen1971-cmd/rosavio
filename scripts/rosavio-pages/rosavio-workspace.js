 'use strict';
const l10n=RosavioWorkspaceL10n.forLocale(navigator.language),t=l10n.text;
document.documentElement.lang=l10n.locale;document.documentElement.dir=l10n.dir;
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
while(walker.nextNode()){const node=walker.currentNode;if(!['SCRIPT','STYLE'].includes(node.parentElement?.tagName)){const original=node.textContent.trim();if(original)node.textContent=node.textContent.replace(original,t(original));}}
const urlLabel=document.querySelector('label[for="link-url"]');
urlLabel.textContent=t('Webadresse (https://…)').replace(/\s*[（(].*?[）)]/g,'')+' ';
const urlExample=document.createElement('bdi');urlExample.dir='ltr';urlExample.textContent='https://…';urlLabel.append(urlExample);

const $ = id => document.getElementById(id);
let data=null, dirty=false, busy=false;
const isNotes=location.href==='about:rosavio-notes';
$('title').textContent=document.title=isNotes?t("Meine Notizen · Rosavio"):t("Meine Startseite · Rosavio");
$(isNotes?'notes-panel':'home-panel').hidden=false;
function controls(enabled){for(const id of ['notes','link-title','link-url','add','save','reload'])$(id).disabled=!enabled;for(const button of $('links').querySelectorAll('button'))button.disabled=!enabled;}
function changed(){dirty=true;$('status').textContent=t("Noch nicht gespeichert");}
function render(){
 $('notes').value=data.notes;$('links').replaceChildren();
 data.links.forEach((link,index)=>{
  const li=document.createElement('li'),a=document.createElement('a'),button=document.createElement('button');
  a.textContent=link.title;a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';
  button.textContent=t("Entfernen");button.addEventListener('click',()=>{data.links.splice(index,1);render();changed();});
  li.append(a,button);$('links').append(li);
 });
}
document.addEventListener('RosavioWorkspaceResult',event=>{data=event.detail;dirty=false;busy=false;render();controls(true);$('status').textContent=t("Gespeicherter Stand geladen");});
document.addEventListener('RosavioWorkspaceError',()=>{busy=false;controls(!!data);$('reload').disabled=false;$('status').textContent=t("Nicht gespeichert: In privaten Fenstern nicht verfügbar oder Daten inzwischen geändert. Kopiere neue Notizen vor dem erneuten Laden.");});
$('notes').addEventListener('input',()=>{data.notes=$('notes').value;changed();});
$('add').addEventListener('click',()=>{
 try{const u=new URL($('link-url').value);const title=$('link-title').value.trim();
 if(!title||!['https:','http:'].includes(u.protocol)||u.username||u.password||data.links.length>=24)throw Error();
 data.links.push({title,url:u.href});$('link-title').value='';$('link-url').value='';render();changed();
 }catch{$('status').textContent=t("Bitte Name und gültige HTTP-/HTTPS-Adresse eingeben (höchstens 24 Webseiten).");}
});
$('save').addEventListener('click',()=>{if(busy||!data)return;busy=true;controls(false);document.dispatchEvent(new CustomEvent('RosavioWorkspaceSave',{detail:data}));});
$('reload').addEventListener('click',()=>{if(dirty&&!confirm(t("Ungespeicherte Änderungen verwerfen?")))return;controls(false);document.dispatchEvent(new CustomEvent('RosavioWorkspaceRead'));});
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
document.dispatchEvent(new CustomEvent('RosavioWorkspaceRead'));
