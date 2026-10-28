import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {EventEmitter} from 'node:events';
import {pathToFileURL} from 'node:url';

const source=fs.readFileSync(new URL('../scripts/native-session.cjs',import.meta.url),'utf8');
test('standalone Windows checker isolates system-access opt-in and excludes signing credentials',()=>{
  const env={GH_TOKEN:'test-token',GITHUB_TOKEN:'test-token',ROSAVIO_UPDATE_KEY:'test-key',ROSAVIO_SIGNING_PASSWORD:'test-password',ROSAVIO_FLATPAK_SIGNING_KEY:'test-key',ROSAVIO_FLATPAK_SIGNING_PASSWORD:'test-password',ROSAVIO_KEY_PATH:'test-path'};
  let captured;
  const mocks={fs:{mkdirSync(){},writeFileSync(){}},path,net:{},url:{pathToFileURL},child_process:{spawn(binary,args,options){captured=options.env;throw Error('test stops before launching');}}};
  const code=fs.readFileSync(new URL('../scripts/check-native.cjs',import.meta.url),'utf8');
  assert.throws(()=>vm.runInNewContext(code,{require:n=>mocks[n],process:{argv:['node','check-native','test-browser','test-profile'],env}}),/test stops before launching/);
  assert.equal(captured.MOZ_REMOTE_ALLOW_SYSTEM_ACCESS,'1');
  assert.equal(env.MOZ_REMOTE_ALLOW_SYSTEM_ACCESS,undefined);
  for(const key of Object.keys(env))assert.equal(captured[key],undefined,key);
});
function harness(failContext=false){
  const env={GH_TOKEN:'test-token',ROSAVIO_SIGNING_PASSWORD:'test-password',KEEP:'yes'};
  const child=new EventEmitter();child.stderr=new EventEmitter();child.exitCode=null;
  child.kill=()=>{child.killed=true;setImmediate(()=>{child.exitCode=1;child.emit('exit',1);});};
  const socket=new EventEmitter();socket.destroy=()=>{socket.destroyed=true;};
  const commands=[];let spawnOptions;
  const send=value=>{const body=JSON.stringify(value);socket.emit('data',Buffer.from(Buffer.byteLength(body)+':'+body));};
  socket.write=data=>{const request=JSON.parse(data.slice(data.indexOf(':')+1));commands.push(request);
    setImmediate(()=>send([1,request[1],failContext&&request[2]==='Marionette:SetContext'?{error:'unsupported operation',message:'System access is required'}:null,{}]));};
  const mocks={fs:{mkdirSync(){},writeFileSync(){},appendFileSync(){}},path,
    net:{connect(port,host,connected){setImmediate(()=>{connected();setImmediate(()=>send({applicationType:'gecko',marionetteProtocol:3}));});return socket;}},
    child_process:{spawn(binary,args,options){spawnOptions=options;return child;}}};
  const context={module:{exports:{}},require:name=>mocks[name],process:{env,platform:'win32'},Buffer,setTimeout,clearTimeout};
  vm.runInNewContext(source,context);
  return {start:context.module.exports,env,child,socket,commands,get spawnOptions(){return spawnOptions;}};
}
test('isolated automation child opts in without exposing secrets or changing parent environment',async()=>{
  const h=harness();const session=await h.start('test-browser','test-profile');
  assert.equal(h.spawnOptions.env.MOZ_REMOTE_ALLOW_SYSTEM_ACCESS,'1');
  assert.equal(h.env.MOZ_REMOTE_ALLOW_SYSTEM_ACCESS,undefined);
  assert.equal(h.spawnOptions.env.GH_TOKEN,undefined);
  assert.equal(h.spawnOptions.env.ROSAVIO_SIGNING_PASSWORD,undefined);
  assert.equal(h.spawnOptions.env.KEEP,'yes');
  assert.equal(h.commands[0][3].capabilities.alwaysMatch.acceptInsecureCerts,false);
  h.child.exitCode=0;await session.close();assert.equal(h.socket.destroyed,true);
});
test('startup rejection closes its socket and child even before a session can be returned',async()=>{
  const h=harness(true);
  await assert.rejects(h.start('test-browser','test-profile'),/System access is required/);
  assert.equal(h.socket.destroyed,true);assert.equal(h.child.killed,true);assert.equal(h.child.exitCode,1);
});
