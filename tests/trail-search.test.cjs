const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'../scripts/rosavio-pages'),words=JSON.parse(fs.readFileSync(path.join(root,'rosavio-workspace-locales.json'),'utf8'));
const js=fs.readFileSync(path.join(root,'rosavio-workspace.js'),'utf8');
test('all twenty locales filter quotes, URLs and notes without changing path data',()=>{
 for(const locale of Object.keys(words)){
  const data={trail:{current:7,steps:Array.from({length:30},(_,i)=>({quote:i===7?'Rose 日本語 العربية <script>':'Text '+i,url:'https://example.org/'+i,note:i===7?'Brücke merken':'note'}))}};
  const original=JSON.stringify(data),nodes={'trail-search':{value:''},'trail-search-status':{},'trail-steps':{children:data.trail.steps.map((_,i)=>({dataset:{index:String(i)},open:{hasAttribute:name=>name==='href'},querySelector(){return this.open;}}))}};
  const c=vm.createContext({data,l10n:{locale},t:k=>words[locale][k],$:id=>nodes[id]});
  vm.runInContext(js.slice(js.indexOf('function filterTrail(){'),js.indexOf("$('trail-search').addEventListener")),c);
  for(const [query,expected] of [['BRÜCKE',[7]],['日本語 العربية',[7]],['example.org/7',[7]],['<script>',[7]],['no-such-item',[]],['',Array.from({length:30},(_,i)=>i)]]){
   nodes['trail-search'].value=query;vm.runInContext('filterTrail()',c);
   assert.deepEqual(nodes['trail-steps'].children.filter(r=>!r.hidden).map(r=>+r.dataset.index),expected);
   assert.deepEqual(nodes['trail-steps'].children.filter(r=>!r.open.hidden).map(r=>+r.dataset.index),query?expected:[]);
   assert.equal(JSON.stringify(data),original);
  }
  assert.equal(nodes['trail-search-status'].textContent,words[locale]['Treffer: {n} von {total}'].replace('{n}','30').replace('{total}','30'));
 }
});
test('packaged labels match source catalogs and retain plain text CSP',()=>{
 const c=vm.createContext({});vm.runInContext(fs.readFileSync(path.join(root,'rosavio-workspace-l10n.js'),'utf8'),c);
 for(const locale of Object.keys(words))for(const key of ['Rosenpfad durchsuchen','Treffer: {n} von {total}'])assert.equal(c.RosavioWorkspaceL10n.forLocale(locale).text(key),words[locale][key]);
 const html=fs.readFileSync(path.join(root,'rosavio-workspace.html'),'utf8');assert.match(html,/connect-src 'none'/);assert.match(html,/type="search" maxlength="200"/);assert.doesNotMatch(js,/innerHTML|\bfetch\(/);
});
