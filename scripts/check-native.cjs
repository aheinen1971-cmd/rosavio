const fs=require('fs'), path=require('path'), net=require('net'), {spawn}=require('child_process'), {pathToFileURL}=require('url');
if(!process.argv[2])throw Error('Usage: node scripts/check-native.cjs ROSAVIO_EXE [REPORT_DIRECTORY]');
const binary=path.resolve(process.argv[2]);
const base=path.resolve(process.argv[3]||'native-check'), profile=path.join(base,'profile');
fs.mkdirSync(profile,{recursive:true});
fs.writeFileSync(path.join(profile,'user.js'),[
 'user_pref("marionette.port", 2843);',
 'user_pref("browser.shell.checkDefaultBrowser", false);',
 'user_pref("app.update.background.enabled", false);',
 'user_pref("browser.startup.page", 0);'
].join('\n'));
const browserEnv={...process.env};
delete browserEnv.ROSAVIO_SIGNING_PASSWORD;
const proc=spawn(binary,['-headless','-no-remote','-profile',profile,'--marionette','--remote-allow-system-access'],{env:browserEnv,stdio:['ignore','ignore','pipe']});
let sock,buffer=Buffer.alloc(0),queue=[],waiters=[],sequence=0;
proc.stderr.on('data',data=>fs.appendFileSync(path.join(base,'native-smoke-browser.log'),data));
function parse(data){buffer=Buffer.concat([buffer,data]);while(true){const colon=buffer.indexOf(58);if(colon<0)return;const size=Number(buffer.subarray(0,colon).toString());if(buffer.length<colon+1+size)return;const message=JSON.parse(buffer.subarray(colon+1,colon+1+size));buffer=buffer.subarray(colon+1+size);if(waiters.length)waiters.shift()(message);else queue.push(message);}}
function receive(){if(queue.length)return Promise.resolve(queue.shift());return new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Marionette response timed out')),60000);waiters.push(value=>{clearTimeout(timer);resolve(value)})});}
async function command(name,args={}){const id=++sequence,body=JSON.stringify([0,id,name,args]);sock.write(Buffer.byteLength(body)+':'+body);const result=await receive();if(result[2])throw Error(name+': '+JSON.stringify(result[2]));return result[3];}
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{try{
 for(let attempt=0;attempt<200;attempt++){try{sock=await new Promise((resolve,reject)=>{const socket=net.connect(2843,'127.0.0.1',()=>resolve(socket));socket.once('error',reject)});break}catch{if(proc.exitCode!==null)throw Error('Rosavio exited before automation startup');await pause(200)}}
 if(!sock)throw Error('Rosavio automation port did not open');
 sock.on('data',parse); await receive();
 await command('WebDriver:NewSession',{capabilities:{alwaysMatch:{acceptInsecureCerts:false}}});
 await command('Marionette:SetContext',{value:'chrome'});
 const identity=(await command('WebDriver:ExecuteAsyncScript',{script:'const done=arguments[arguments.length-1]; document.l10n.ready.then(async()=>{const {UpdateUtils}=ChromeUtils.importESModule("resource://gre/modules/UpdateUtils.sys.mjs"); const items=[...document.querySelectorAll("[data-l10n-id*=about]")].map(el=>({id:el.id,label:el.getAttribute("label"),l10n:el.getAttribute("data-l10n-id")})); done({name:Services.appinfo.name,vendor:Services.appinfo.vendor,locale:Services.locale.appLocaleAsBCP47,version:Services.appinfo.version,buildID:Services.appinfo.appBuildID,platformVersion:Services.appinfo.platformVersion,updateUrl:await Cc["@mozilla.org/updates/update-checker;1"].getService(Ci.nsIUpdateChecker).wrappedJSObject.getUpdateURL(Ci.nsIUpdateChecker.BACKGROUND_CHECK),aboutItems:items});}).catch(error=>done({error:String(error)}));',args:[]})).value;
 if(identity.name!=='Rosavio'||identity.vendor!=='Rosavio')throw Error('Native Rosavio product identity is incorrect: '+JSON.stringify(identity));
 if(!/^https:\/\/github\.com\/aheinen1971-cmd\/(rose|rosavio)\/releases\/latest\/download\/rosavio-win64-update\.xml$/.test(identity.updateUrl))throw Error('Wrong native update destination');
 if(!identity.aboutItems.some(item=>item.label&&item.label.includes('Rosavio')))throw Error('Rosavio name not found in About menu');
 await command('Marionette:SetContext',{value:'content'});
 await command('WebDriver:Navigate',{url:'https://example.com/'});
 const title=(await command('WebDriver:GetTitle')).value;
 if(title!=='Example Domain')throw Error('HTTPS navigation failed: '+title);
 await command('WebDriver:Navigate',{url:'about:preferences'});
 const preferences=(await command('WebDriver:ExecuteScript',{script:'return {title:document.title,rosavioMentioned:document.body.textContent.includes("Rosavio")};',args:[]})).value;
 if(process.env.ROSAVIO_EXPECT_LOCALE === "de" && (identity.locale !== "de" || preferences.title !== "Einstellungen" || !identity.aboutItems.some(item=>item.label === "Über Rosavio")))throw Error("German interface check failed: "+JSON.stringify({identity,preferences}));
 if(!preferences.rosavioMentioned)throw Error('Settings still lack Rosavio branding');
 const report={...identity,httpsNavigation:title,preferences,passed:true};
 fs.writeFileSync(path.join(base,'report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 try{await command('Marionette:SetContext',{value:'chrome'});const screenshot=(await command('WebDriver:TakeScreenshot',{id:null,highlights:[],full:false})).value;fs.writeFileSync(path.join(base,'preview.png'),Buffer.from(screenshot,'base64'));}catch(error){console.log('Screenshot unavailable:',error.message)}
 await command('Marionette:Quit',{flags:['eForceQuit']});
}finally{if(sock)sock.destroy();if(proc.exitCode===null)proc.kill();}})().catch(error=>{console.error(error);process.exitCode=1});
