 'use strict';
const l10n=RosavioWorkspaceL10n.forLocale(navigator.language),t=l10n.text;
document.documentElement.lang=l10n.locale;document.documentElement.dir=l10n.dir;
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
while(walker.nextNode()){const node=walker.currentNode;if(!['SCRIPT','STYLE'].includes(node.parentElement?.tagName)){const original=node.textContent.trim();if(original)node.textContent=node.textContent.replace(original,t(original));}}
const urlLabel=document.querySelector('label[for="link-url"]');
urlLabel.textContent=t('Webadresse (https://…)').replace(/\s*[（(].*?[）)]/g,'')+' ';
const urlExample=document.createElement('bdi');urlExample.dir='ltr';urlExample.textContent='https://…';urlLabel.append(urlExample);

const $ = id => document.getElementById(id);
let data=null, savedData=null, pendingTrailDraft=null, dirty=false, busy=false;
const trailDirty=()=>JSON.stringify(data?.trail)!==JSON.stringify(savedData?.trail);
const isNotes=location.href==='about:rosavio-notes';
$('title').textContent=document.title=isNotes?t("Meine Notizen · Rosavio"):t("Meine Startseite · Rosavio");
$(isNotes?'notes-panel':'home-panel').hidden=false;
function controls(enabled){for(const id of ['notes','link-title','link-url','add','save','reload'])$(id).disabled=!enabled;for(const button of document.querySelectorAll('#links button,#reading-places button,#rose-path button,#rose-path input,#rose-path textarea'))button.disabled=!enabled || button.dataset.unavailable==='true';$('trail-save').disabled=!enabled||!trailDirty();}
function changed(){dirty=true;$('trail-save').disabled=busy||!trailDirty();renderNavigation();$('status').textContent=t("Noch nicht gespeichert");}
function render(){
 $('notes').value=data.notes;$('links').replaceChildren();
 const list=$('reading-places');
 list.replaceChildren();
 (data.places || []).forEach((place,index)=>{
   const row=document.createElement('li'), link=document.createElement('a'), remove=document.createElement('button');
   link.href=place.url;link.target='_blank';link.rel='noopener noreferrer';link.dir='auto';
   link.textContent=place.quote+' · '+new URL(place.url).host;
   remove.textContent=t('Entfernen');
   remove.addEventListener('click',()=>{data.places.splice(index,1);render();changed();});
   const add=trailButton('Zum Rosenpfad',()=>addToTrail(place),data.trail?.steps.some(s=>s.url===place.url) || data.trail?.steps.length>=30);
   row.append(link,remove,add);list.append(row);
 });
 renderTrail();
 data.links.forEach((link,index)=>{
  const li=document.createElement('li'),a=document.createElement('a'),button=document.createElement('button');
  a.textContent=link.title;a.href=link.url;a.target='_blank';a.rel='noopener noreferrer';
  button.textContent=t("Entfernen");button.addEventListener('click',()=>{data.links.splice(index,1);render();changed();});
  li.append(a,button);$('links').append(li);
 });
}
function trailButton(label,run,disabled=false) {
 const b=document.createElement('button');
 b.textContent=t(label);b.disabled=disabled;b.dataset.unavailable=String(disabled);
 b.addEventListener('click',run);return b;
}
function addToTrail(place) {
 const trail=data.trail ||= {name:t('Rosenpfad'),current:0,steps:[]};
 if(trail.steps.length>=30 || trail.steps.some(s=>s.url===place.url))return;
 trail.steps.push({...place,note:''});render();changed();
}
function editStep(index, direction) {
 const trail=data.trail, active=trail.steps[trail.current];
 if(direction===0)trail.steps.splice(index,1);
 else {
  const other=index+direction;
  if(other<0 || other>=trail.steps.length)return;
  [trail.steps[index],trail.steps[other]]=[trail.steps[other],trail.steps[index]];
 }
 if(!trail.steps.length)delete data.trail;
 else trail.current=trail.steps.includes(active)?trail.steps.indexOf(active):Math.min(index,trail.steps.length-1);
 render();changed();
}
function renderNavigation() {
 const area=$('trail-navigation');area.replaceChildren();
 const trail=data?.trail;if(!trail)return;
 if(trailDirty() || busy){area.textContent=t('Änderungen werden erst mit „Speichern“ dauerhaft gesichert.');return;}
 for(const [index,label] of [[trail.current-1,'Zurück'],[trail.current,'Weiterlesen'],[trail.current+1,'Nächste Lesestelle']]){
  if(!trail.steps[index])continue;
  const a=document.createElement('a');a.href=trail.steps[index].url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=t(label);
  a.addEventListener('click',()=>{if(index!==trail.current){trail.current=index;changed();saveTrail();}});
  area.append(a);
 }
}
function renderTrail(){
 const trail=data.trail;$('trail-editor').hidden=!trail;
 if(!trail)return;
 $('trail-name').disabled=busy;$('trail-note').disabled=busy;
 $('trail-name').value=trail.name;$('trail-note').value=trail.steps[trail.current].note;
 $('trail-progress').textContent=t('Stelle {n} von {total}').replace('{n}',trail.current+1).replace('{total}',trail.steps.length);
 $('trail-quote').textContent=trail.steps[trail.current].quote;
 const list=$('trail-steps');list.replaceChildren();
 trail.steps.forEach((step,i)=>{
  const row=document.createElement('li');row.dataset.index=i;
  if(i===trail.current)row.setAttribute('aria-current','step');
  const label=document.createElement('span');label.dir='auto';label.textContent=step.quote+' · '+new URL(step.url).host;
  row.append(label,trailButton('↑',()=>editStep(i,-1),i===0),trailButton('↓',()=>editStep(i,1),i===trail.steps.length-1),trailButton('Entfernen',()=>editStep(i,0)));
  row.children[1].setAttribute('aria-label',t('Nach oben'));row.children[2].setAttribute('aria-label',t('Nach unten'));
  list.append(row);
 });
 renderNavigation();
}
function saveTrail(){
 if(busy || !data || !trailDirty())return;
 pendingTrailDraft=data;
 const payload=structuredClone(savedData);
 if(data.trail)payload.trail=structuredClone(data.trail);
 else delete payload.trail;
 busy=true;controls(false);renderNavigation();
 document.dispatchEvent(new CustomEvent('RosavioWorkspaceSave',{detail:payload}));
}
$('trail-save').addEventListener('click',saveTrail);
$('trail-name').addEventListener('input',()=>{data.trail.name=$('trail-name').value;changed();});
$('trail-note').addEventListener('input',()=>{data.trail.steps[data.trail.current].note=$('trail-note').value;changed();});
document.addEventListener('RosavioWorkspaceResult',event=>{
 savedData=structuredClone(event.detail);
 data=event.detail;
 if(pendingTrailDraft){
   for(const key of ['notes','links','places']){
     if(key in pendingTrailDraft)data[key]=pendingTrailDraft[key];
     else delete data[key];
   }
 }
 pendingTrailDraft=null;
 dirty=['notes','links','places'].some(key=>JSON.stringify(data[key])!==JSON.stringify(savedData[key]));
 busy=false;render();controls(true);
 $('status').textContent=t(dirty?'Noch nicht gespeichert':'Gespeicherter Stand geladen');
});
document.addEventListener('RosavioWorkspaceError',()=>{pendingTrailDraft=null;busy=false;controls(!!data);renderNavigation();$('reload').disabled=false;$('status').textContent=t("Nicht gespeichert: In privaten Fenstern nicht verfügbar oder Daten inzwischen geändert. Kopiere neue Notizen vor dem erneuten Laden.");});
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
