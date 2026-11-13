'use strict';
// Portable data only. Import never opens URLs or writes the profile.
var RosavioTrailBackup = (() => {
 const limit=512*1024;
 function validate(value) {
  if(!value || value.format!=='rosavio-rose-trail' || value.version!==1 ||
     Object.keys(value).some(k=>!['format','version','trail'].includes(k)))throw Error('Invalid backup');
  const trail=value.trail;
  if(!trail || typeof trail.name!=='string' || trail.name.length>80 ||
     !Array.isArray(trail.steps) || !trail.steps.length || trail.steps.length>30 ||
     !Number.isInteger(trail.current) || trail.current<0 || trail.current>=trail.steps.length ||
     Object.keys(trail).some(k=>!['name','current','steps'].includes(k)))throw Error('Invalid trail');
  const steps=trail.steps.map(step=>{
   if(!step || Object.keys(step).some(k=>!['url','quote','note'].includes(k)) ||
      typeof step.url!=='string' || step.url.length>8192 ||
      typeof step.quote!=='string' || !step.quote.trim() || step.quote.length>1200 ||
      typeof step.note!=='string' || step.note.length>700)throw Error('Invalid step');
   const url=new URL(step.url);
   if(!['https:','http:'].includes(url.protocol) || url.username || url.password ||
      !url.hash.includes(':~:text='))throw Error('Invalid URL');
   return {url:url.href,quote:step.quote,note:step.note};
  });
  if(new Set(steps.map(s=>s.url)).size!==steps.length)throw Error('Duplicate step');
  return {name:trail.name.trim(),current:trail.current,steps};
 }
 function parse(text) {
  if(typeof text!=='string' || new TextEncoder().encode(text).length>limit)throw Error('Backup too large');
  return validate(JSON.parse(text));
 }
 function stringify(trail) {
  const value={format:'rosavio-rose-trail',version:1,trail};
  const text=JSON.stringify(value,null,2);
  parse(text);
  return text;
 }
 return {limit,parse,stringify};
})();
