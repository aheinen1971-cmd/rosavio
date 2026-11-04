'use strict';
const endpoint='https://raw.githubusercontent.com/aheinen1971-cmd/rosavio/rosavio-status-data/status.json';
const labels={green:'🟢 Bestätigt',yellow:'🟡 In Arbeit / wartet',red:'🔴 Problem',gray:'⚪ Nicht bestätigt',neutral:'ℹ️ Information'};
let busy=false,last=null;
function ageNotice(){
 if(!last)return;
 const stale=Date.now()-Date.parse(last.checkedAt)>90*60*1000;
 const el=document.getElementById('notice');
 el.textContent=statusText(stale?'Dieser Prüfstand ist über 90 Minuten alt. Aktuelle Ergebnisse sind noch nicht bestätigt.':'Gespeicherter GitHub-Prüfstand. Nächster Datenabruf dieser Seite automatisch in fünf Minuten.');
 el.className=stale?'warning':'';
}
function render(data){
 if(data.schema!==1||!Array.isArray(data.rows)||data.rows.length>30||!Number.isFinite(Date.parse(data.checkedAt)))throw Error('Ungültige Statusdaten');
 const expanded=new Set(Array.from(document.querySelectorAll('.package-box[open]'),box=>box.closest('tr').dataset.platform));
 const fragment=document.createDocumentFragment();
 for(const row of data.rows){
  if(!Object.hasOwn(labels,row.state)||!['label','version','detail'].every(k=>typeof row[k]==='string'))throw Error('Ungültige Statuszeile');
  const tr=document.createElement('tr');tr.dataset.platform=row.label;
  for(const key of ['label','version','state','detail']){
   const td=document.createElement('td');
   if(key==='state'){
    const badge=document.createElement('span');
    badge.className='badge '+row.state;
    const active=row.state==='yellow'&&Array.isArray(row.progress?.steps)&&row.progress.steps.includes('in_progress');
    if(active){
     const ring=document.createElement('span');ring.className='activity-ring';ring.setAttribute('aria-hidden','true');
     badge.append(ring,statusText('Bau / Prüfungen laufen'));
    }else badge.textContent=statusText(labels[row.state]);
    td.append(badge);
   }
   else if(key==='detail'&&Object.hasOwn(packageLabels,row.label))showRelease(td,row,data.checkedAt);
   else td.textContent=statusText(row[key]);
   if(key==='version'&&/^\d+(?:\.\d+)*(?: → \d+(?:\.\d+)*)?$/.test(row.version))td.dir='ltr';
   if(key==='label'&&['Windows','Linux','Flatpak'].includes(row.label)){
    const p=row.progress, percent=p?.percent;
    const valid=Number.isInteger(percent)&&percent>=0&&percent<=100&&(percent!==100||row.state==='green');
    const box=document.createElement('div');box.className='phase-progress';
    const text=document.createElement('span');text.dir='ltr';text.textContent=valid?percent+' %':'— %';box.append(text);
    if(valid){const bar=document.createElement('progress');bar.max=100;bar.value=percent;bar.setAttribute('aria-label',row.label+' – '+statusText('abgeschlossene Updatephasen'));bar.className='phase-'+row.state;box.append(bar);}
    const note=document.createElement('small');note.textContent=statusText(valid&&typeof p.note==='string'?p.note:'Fortschritt nicht überprüfbar');box.append(note);td.append(box);
   }
   if(key==='detail'){const box=packageBox(row,expanded.has(row.label));if(box)td.append(box);}
   if(key==='detail'&&row.url){
    const url=new URL(row.url);
    if(url.protocol==='https:'&&['github.com','aheinen1971-cmd.github.io','addons.mozilla.org'].includes(url.hostname)){
     const a=document.createElement('a');a.href=url.href;a.textContent=statusText('Details ansehen ↗');a.target='_blank';a.rel='noopener noreferrer';a.className='details-link';td.append(a);
    }
   }
   tr.append(td);
  }
  fragment.append(tr);
 }
 document.getElementById('rows').replaceChildren(fragment);
 document.getElementById('upstream').textContent=data.upstream||'—';
 document.getElementById('checked').textContent=new Intl.DateTimeFormat(statusLanguage,{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Berlin'}).format(new Date(data.checkedAt));
 last=data;ageNotice();roseCard(data);
}
async function refresh(){
 if(busy)return;busy=true;document.getElementById('refresh').disabled=true;
 try{const response=await fetch(endpoint,{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);render(await response.json());}
 catch(error){const el=document.getElementById('notice');el.className='warning';el.textContent=statusText('Aktueller Abruf nicht möglich. ')+' '+statusText(last?'Die Tabelle zeigt den letzten abgerufenen Stand.':'Bitte später erneut abrufen.');}
 finally{busy=false;document.getElementById('refresh').disabled=false;}
}
document.getElementById('refresh').addEventListener('click',refresh);
refresh();setInterval(refresh,300000);
