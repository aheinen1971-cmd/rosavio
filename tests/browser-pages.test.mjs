import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../scripts/rosavio-pages/RosavioDetailsParent.sys.mjs',import.meta.url),'utf8');
function actor(uri='about:rosavio-privacy',parent=null){
 const prefs={getBoolPref:()=>true,getStringPref:()=> 'strict',getIntPref:()=>5};
 const context={AppConstants:{MOZ_TELEMETRY_REPORTING:false},JSWindowActorParent:class{},Services:{prefs,appinfo:{version:'158.0.1',appBuildID:'20261026000000'},locale:{appLocaleAsBCP47:'de'},policies:{isAllowed:()=>true}}};
 vm.createContext(context);vm.runInContext(source.replace(/^import .*;$/m,'').replace('export class RosavioDetailsParent','this.RosavioDetailsParent = class'),context);
 const instance=new context.RosavioDetailsParent();instance.manager={documentURI:{spec:uri}};instance.browsingContext={parent};return instance;
}
test('read-only bridge returns a fixed summary without sensitive profile data',()=>{
 const result=actor().receiveMessage({name:'Rosavio:Summary',data:{pref:'arbitrary.secret'}});
 assert.deepEqual(Object.keys(result).sort(),['version','buildID','locale','trackingCategory','tracking','trackingPrivate','cookies','malware','phishing','downloads','unwanted','uncommon','telemetry','settingsRedesign','sponsored','updateAllowed'].sort());
 assert.equal(result.telemetry,false);
 assert.equal(result.cookies,5);assert.equal(result.malware,true);
});
test('other origins, subframes, fragments and messages cannot use the bridge',()=>{
 for(const uri of ['https://example.org/','about:blank','about:rosavio-privacy#fake','about:rosavio-addons'])assert.throws(()=>actor(uri).receiveMessage({name:'Rosavio:Summary'}),/denied/);
 assert.throws(()=>actor('about:rosavio-privacy',{}).receiveMessage({name:'Rosavio:Summary'}),/denied/);
 for(const name of ['SetPref','OpenURL','Rosavio:Write'])assert.throws(()=>actor().receiveMessage({name}),/denied/);
});
test('packaged content has no network connections, HTML injection or preference writer',()=>{
 const root=new URL('../scripts/rosavio-pages/',import.meta.url);
 const html=fs.readFileSync(new URL('rosavio-details.html',root),'utf8');
 const js=fs.readFileSync(new URL('rosavio-details.js',root),'utf8');
 assert.match(html,/connect-src 'none'/);assert.match(html,/object-src 'none'/);
 assert.doesNotMatch(js,/innerHTML|outerHTML|\bfetch\(|XMLHttpRequest|\.set\w*Pref\(/);
 assert.doesNotMatch(source,/\.set\w*Pref\(/);
});
test('settings navigation uses only fixed internal destinations, ignoring supplied URLs',()=>{
 const a=actor();const opened=[];
 a.browsingContext.top={embedderElement:{documentGlobal:{openTrustedLinkIn:(...args)=>opened.push(args)}}};
 a.receiveMessage({name:'Rosavio:OpenPrivacy',data:{url:'https://attacker.invalid/'}});
 a.receiveMessage({name:'Rosavio:OpenSecurity',data:{url:'file:///secret'}});
 a.receiveMessage({name:'Rosavio:OpenAddons'});
 assert.deepEqual(opened,[['about:preferences#privacy','current'],['about:preferences#connectionSecurity','current'],['about:addons','current']]);
 assert.throws(()=>actor('https://example.org/').receiveMessage({name:'Rosavio:OpenPrivacy'}),/denied/);
});
