import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const dir=new URL('../scripts/rosavio-pages/',import.meta.url);
const words=JSON.parse(fs.readFileSync(new URL('rosavio-locales.json',dir),'utf8'));
const source=fs.readFileSync(new URL('rosavio-l10n.js',dir),'utf8');
const context=vm.createContext({});vm.runInContext(source,context);
const api=context.RosavioL10n;
const locales=['de','en-US','fr','es-ES','nl','it','pt-PT','pl','cs','da','sv-SE','nb-NO','fi','tr','uk','el','ja','ko','ar','he'];
test('all twenty locales have every nonempty UI string and safe placeholders',()=>{
 assert.deepEqual(Object.keys(words).sort(),locales.slice().sort());
 for(const locale of locales){
  assert.deepEqual(Object.keys(words[locale]).sort(),Object.keys(words['en-US']).sort());
  for(const [key,value] of Object.entries(words[locale])){
   assert.equal(typeof value,'string');assert.ok(value.trim());
   assert.deepEqual(value.match(/\{[^}]+\}/g)||[],key.match(/\{[^}]+\}/g)||[],locale+': '+key);
   assert.ok(!/[<>\uFFFD]/.test(value),locale+': '+key);
   assert.equal(api.forLocale(locale).text(key),value);
  }
 }
});
test('regional aliases, unknown locales and right-to-left direction are deterministic',()=>{
 for(const [input,expected] of Object.entries({'fr-FR':'fr','es-MX':'es-ES','EN_us':'en-US','pt-BR':'pt-PT','sv':'sv-SE','no':'nb-NO','iw-IL':'he','ar-EG':'ar','zh':'en-US','constructor':'en-US'}))assert.equal(api.forLocale(input).locale,expected);
 for(const locale of locales)assert.equal(api.forLocale(locale).dir,['ar','he'].includes(locale)?'rtl':'ltr');
 assert.equal(api.forLocale('de').text('unknown'),'unknown');
});
test('bundled locale runtime has no network, HTML injection or preference access',()=>{
 assert.ok(!/\bfetch\s*\(|XMLHttpRequest|innerHTML|Services\.|eval\s*\(/.test(source));
 assert.ok(Object.isFrozen(api));
 for(const locale of locales)assert.ok(Object.isFrozen(api.forLocale(locale)));
});
