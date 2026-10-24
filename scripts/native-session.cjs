const fs = require('fs'), net = require('net'), path = require('path');
const {spawn} = require('child_process');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
module.exports = async function start(binary, profile, port=2844) {
  fs.mkdirSync(profile,{recursive:true});
  fs.writeFileSync(path.join(profile,'user.js'), `user_pref("marionette.port", ${port});\nuser_pref("marionette.prefs.recommended", false);\nuser_pref("app.update.disabledForTesting", false);\nuser_pref("browser.shell.checkDefaultBrowser", false);\nuser_pref("app.update.background.enabled", false);\nuser_pref("app.update.log", true);\nuser_pref("app.update.staging.enabled", ${process.env.ROSAVIO_PRODUCTION_TEST === "1"});\n`);
  const browserEnv={...process.env};
  for(const key of ['ROSAVIO_SIGNING_PASSWORD','ROSAVIO_UPDATE_KEY','GH_TOKEN','GITHUB_TOKEN'])delete browserEnv[key];
  const proc=spawn(binary,['-headless','-no-remote','-profile',profile,'--marionette','--remote-allow-system-access'],{env:browserEnv,stdio:['ignore','ignore','pipe']});
  proc.stderr.on('data',data=>fs.appendFileSync(path.join(profile,'browser.log'),data));
  let socket, buffer=Buffer.alloc(0), sequence=0, queue=[], waiters=[];
  for(let i=0;i<200;i++){
    try{socket=await new Promise((resolve,reject)=>{const sock=net.connect(port,'127.0.0.1',()=>resolve(sock));sock.once('error',reject)});break;}
    catch{await pause(200);}
  }
  if(!socket){proc.kill();throw Error('Browser did not open automation port');}
  socket.on('data',data=>{buffer=Buffer.concat([buffer,data]);while(true){const colon=buffer.indexOf(58);if(colon<0)return;const length=Number(buffer.subarray(0,colon));if(buffer.length<colon+1+length)return;const message=JSON.parse(buffer.subarray(colon+1,colon+1+length));buffer=buffer.subarray(colon+1+length);if(waiters.length)waiters.shift()(message);else queue.push(message);}});
  const receive=()=>queue.length?Promise.resolve(queue.shift()):new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Automation command timed out')),60000);waiters.push(value=>{clearTimeout(timer);resolve(value)});});
  const command=async(name,args={})=>{const id=++sequence, body=JSON.stringify([0,id,name,args]);socket.write(Buffer.byteLength(body)+':'+body);const message=await receive();if(message[2])throw Error(JSON.stringify(message[2]));return message[3];};
  await receive();
  await command('WebDriver:NewSession',{capabilities:{alwaysMatch:{acceptInsecureCerts:false}}});
  await command('Marionette:SetContext',{value:'chrome'});
  return {proc,command,async script(script){return (await command('WebDriver:ExecuteAsyncScript',{script:`const done=arguments[arguments.length-1];(async()=>{${script}})().then(done,error=>done({error:String(error)}));`,args:[]})).value;},async close(){try{await command('Marionette:Quit',{flags:['eForceQuit']});}catch{}socket.destroy();if(proc.exitCode===null)await new Promise(resolve=>{const timer=setTimeout(()=>{if(proc.exitCode===null)proc.kill();resolve();},10000);proc.once('exit',()=>{clearTimeout(timer);resolve();});});}};
};
