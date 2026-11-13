const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'../scripts/rosavio-pages');
const ctx={URL,TextEncoder};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'rosavio-trail-backup.js'),'utf8'),ctx);
const backup=ctx.RosavioTrailBackup;
const step={url:'https://example.org/#:~:text=rose',quote:'🌹 日本語 العربية <script>plain text</script>',note:'Reminder'};
const trail={name:'My 🌹 trail',current:1,steps:[step,{...step,url:'https://example.org/second#:~:text=rose'}]};
const plain=x=>JSON.parse(JSON.stringify(x));
test('portable round trip preserves order, current passage, notes and Unicode',()=>{
 assert.deepEqual(plain(backup.parse(backup.stringify(trail))),trail);
 assert.deepEqual(Object.keys(JSON.parse(backup.stringify(trail))).sort(),['format','trail','version']);
});
test('reject malformed, oversized, future and unsafe imports without mutating caller',()=>{
 const source=backup.stringify(trail);
 for(const input of ['', '{', source+'x', ' '.repeat(backup.limit+1),JSON.stringify({format:'rosavio-rose-trail',version:2,trail}),JSON.stringify({format:'rosavio-rose-trail',version:1,trail,notes:'unrelated'})])assert.throws(()=>backup.parse(input));
 for(const bad of [{...trail,current:-1},{...trail,current:2},{...trail,current:0.5},{...trail,steps:[]},{...trail,steps:Array(31).fill(step)},{...trail,steps:[step,step]},{...trail,name:'x'.repeat(81)}])assert.throws(()=>backup.stringify(bad));
 for(const url of ['javascript:alert(1)#:~:text=x','file:///secret#:~:text=x','https://user:secret@example.org/#:~:text=x','https://example.org/'])assert.throws(()=>backup.stringify({...trail,current:0,steps:[{...step,url}]}));
 for(const bad of [{...step,note:'x'.repeat(701)},{...step,quote:''},{...step,extra:'secret'}])assert.throws(()=>backup.stringify({...trail,current:0,steps:[bad]}));
 assert.equal(backup.stringify(trail),source);
});
test('maximum bounded trail fits portable limit and survives round trip',()=>{
 const max={name:'n'.repeat(80),current:29,steps:Array.from({length:30},(_,i)=>({url:'https://example.org/'+i+'#:~:text='+ 'x'.repeat(800),quote:'🌹'.repeat(600),note:'文'.repeat(700)}))};
 assert.deepEqual(plain(backup.parse(backup.stringify(max))),max);
});
test('all twenty locales contain all backup labels and matching runtime translations',()=>{
 const words=JSON.parse(fs.readFileSync(path.join(root,'rosavio-workspace-locales.json'),'utf8'));
 const c={};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(root,'rosavio-workspace-l10n.js'),'utf8'),c);
 assert.equal(Object.keys(words).length,20);
 for(const [locale,texts] of Object.entries(words))for(const key of ['Rosenpfad sichern','Sicherung öffnen','Die Datei enthält deinen gespeicherten Rosenpfad mit Zitaten und Notizen. Bewahre sie privat auf.','Sicherung konnte nicht verarbeitet werden.','Rosenpfad im Entwurf ersetzen? Erst „Speichern“ übernimmt die Sicherung.','Sicherung geladen. Prüfe den Rosenpfad und klicke auf „Speichern“.']){
  assert.ok(texts[key],locale+': '+key);assert.equal(c.RosavioWorkspaceL10n.forLocale(locale).text(key),texts[key]);
 }
});
