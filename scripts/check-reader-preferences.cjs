const assert=require('node:assert/strict'),select=require('./select-test-content.cjs');
module.exports=async function checkReaderPreferences(s){
 const pause=ms=>new Promise(r=>setTimeout(r,ms));
 async function click(css){const e=await s.command('WebDriver:FindElement',{using:'css selector',value:css});await s.command('WebDriver:ElementClick',{id:(e.value||e)['element-6066-11e4-a52e-4f735466cecf']});}
 const prefScript="return {font:Services.prefs.getIntPref('reader.font_size'),line:Services.prefs.getIntPref('reader.line_height'),color:Services.prefs.getCharPref('reader.color_scheme')};";
 await s.command('Marionette:SetContext',{value:'chrome'});const original=await s.script(prefScript);
 await select(s);
 for(let i=0;i<80;i++){if(await s.script("return !!document.querySelector('#line-spacing-slider moz-slider');"))break;await pause(100);}
 await click('.text-layout-button');await click('.text-size-plus-button');
 await s.script("document.querySelector('#line-spacing-slider moz-slider').dispatchEvent(new CustomEvent('slider-changed',{detail:7}));return true;");
 await click('.colors-button');await click('label.dark-button');
 await pause(300);await s.command('Marionette:SetContext',{value:'chrome'});
 const saved=await s.script(prefScript);assert.equal(saved.font,original.font+1);assert.equal(saved.line,7);assert.equal(saved.color,'dark');
 await select(s);await s.command('WebDriver:Refresh');
 let actual;
 for(let i=0;i<100;i++){
  actual=await s.script("return {font:document.body.style.getPropertyValue('--font-size'),line:document.querySelector('#moz-reader-content')?.style.getPropertyValue('--line-height'),dark:document.body.classList.contains('dark')};");
  if(actual.dark && actual.font)break;await pause(100);
 }
 assert.equal(actual.font,(10+2*saved.font)+'px');assert.equal(actual.dark,true);
 assert.equal(await s.script("return document.querySelector('#line-spacing-slider moz-slider').getAttribute('value');"),'7');
 await s.command('Marionette:SetContext',{value:'chrome'});
 await s.script(`Services.prefs.setIntPref('reader.font_size',${original.font});Services.prefs.setIntPref('reader.line_height',${original.line});Services.prefs.setCharPref('reader.color_scheme',${JSON.stringify(original.color)});return true;`);
 return {passed:true,fontSizeSaved:true,lineSpacingSaved:true,backgroundSaved:true,reloadPreserved:true};
};
