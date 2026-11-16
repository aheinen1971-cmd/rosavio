const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'../scripts/rosavio-pages'),source=fs.readFileSync(path.join(root,'rosavio-workspace.js'),'utf8');
const locales=Object.keys(JSON.parse(fs.readFileSync(path.join(root,'rosavio-workspace-locales.json'),'utf8')));
class Node{constructor(tag,text=''){this.tag=tag;this.value=text;this.children=[];}append(...nodes){this.children.push(...nodes);}replaceChildren(){this.children=[];this.value='';}set textContent(value){this.value=value;this.children=[];}get textContent(){return this.value+this.children.map(n=>n.textContent).join('');}}
test('original Unicode text survives overlapping, repeated, HTML-looking and empty queries in all locales',()=>{
 for(const locale of locales){
  const c=vm.createContext({l10n:{locale},document:{createTextNode:text=>new Node('#text',text),createElement:tag=>new Node(tag)}});
  vm.runInContext(source.slice(source.indexOf('function highlightTrailText('),source.indexOf('function filterTrail(){')),c);
  for(const [text,tokens] of [['Rose rose <script>日本語 العربية 😀',['rose','ros','<script>','日本語','العربية','😀']],['İSTANBUL Straße ΟΣ',['i','straße','ος']],['not changed',[]]]){
   const node=new Node('span');c.node=node;c.text=text;c.tokens=tokens;
   vm.runInContext('highlightTrailText(node,text,tokens)',c);
   assert.equal(node.textContent,text);
   assert(node.children.every(n=>n.tag==='#text'||n.tag==='mark'));
   const count=node.children.filter(n=>n.tag==='mark').length;
   if(tokens.length)assert(count>0);else assert.equal(count,0);
   c.tokens=[];vm.runInContext('highlightTrailText(node,text,tokens)',c);
   assert.equal(node.textContent,text);assert(!node.children.some(n=>n.tag==='mark'));
  }
 }
});
