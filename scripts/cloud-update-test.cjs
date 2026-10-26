const fs=require('fs'),path=require('path'),{spawnSync}=require('child_process');
const start=require('./native-session.cjs');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const root=path.resolve(process.env.ROSAVIO_RELEASE_DIR,'../update-test');
const release=JSON.parse(fs.readFileSync(path.join(process.env.ROSAVIO_RELEASE_DIR,'release.json')));
const production=process.env.ROSAVIO_PUBLIC_TEST==='1';
const install=path.join(root,production?'public-install':'local-install');
const profile=path.join(root,production?'public-profile':'local-profile');
fs.mkdirSync(root,{recursive:true});
fs.cpSync(path.dirname(process.env.ROSAVIO_PREVIOUS_BINARY),install,{recursive:true});
const binary=path.join(install,'rosavio.exe');
(async()=>{
  let session,server;
  try {
    if(!production){
      const {createUpdateServer}=await import('../updates/server.mjs');
      server=createUpdateServer({releaseDir:process.env.ROSAVIO_RELEASE_DIR,origin:'http://127.0.0.1:8877',allowLocalHttp:true});
      await new Promise(resolve=>server.listen(8877,'127.0.0.1',resolve));
    }
    session=await start(binary,profile);
    const before=await session.script('return {version:Services.appinfo.version,buildID:Services.appinfo.appBuildID,locale:Services.locale.appLocaleAsBCP47,updateRoot:Services.dirsvc.get("UpdRootD",Ci.nsIFile).path,nativeUpdateURL:Services.appinfo.updateURL};');
    if(before.error||before.buildID>=release.buildID)throw Error('Expected older native browser: '+JSON.stringify(before));
    await session.close();session=null;
    if(!production){
      fs.mkdirSync(path.join(install,'distribution'),{recursive:true});
      fs.writeFileSync(path.join(install,'distribution/policies.json'),JSON.stringify({policies:{AppUpdateURL:`http://127.0.0.1:8877/update/1/Rosavio/${before.version}/${before.buildID}/WINNT_x86_64-msvc-x64/de/rosavio-release/update.xml`,AppAutoUpdate:true}}));
    }else if(fs.existsSync(path.join(install,'distribution/policies.json'))){throw Error('Public test must not override URL');}
    session=await start(binary,profile);
    const check=await session.script('Services.prefs.setBoolPref("media.hardware-video-decoding.enabled",false); const checker=Cc["@mozilla.org/updates/update-checker;1"].getService(Ci.nsIUpdateChecker);const url=await checker.wrappedJSObject.getUpdateURL(checker.BACKGROUND_CHECK);Services.ww.openWindow(null,"chrome://browser/content/aboutDialog.xhtml","RosavioUpdateTest","chrome,dialog=no",null);return {url};');
    if(production&&!/^https:\/\/github.com\/aheinen1971-cmd\/(rose|rosavio)\/releases\/latest\/download\/rosavio-win64-update.xml$/.test(check.url))throw Error('Unexpected production URL');
    let status='';
    for(let attempt=0;attempt<300;attempt++){
      const statusPath=path.join(before.updateRoot,'updates/0/update.status');
      if(fs.existsSync(statusPath))status=fs.readFileSync(statusPath,'utf8').trim();
      if(status.startsWith('failed'))throw Error('Native updater '+status);
      if(['pending','applied','pending-service','applied-service'].includes(status))break;
      await pause(1000);
    }
    if(!['pending','applied','pending-service','applied-service'].includes(status))throw Error('Update timed out: '+status);
    await session.close();session=null;
    await pause(1500);
    session=await start(binary,profile);
    const after=await session.script('return {name:Services.appinfo.name,version:Services.appinfo.version,buildID:Services.appinfo.appBuildID,locale:Services.locale.appLocaleAsBCP47,updateURL:Services.appinfo.updateURL,videoSetting:Services.prefs.getBoolPref("media.hardware-video-decoding.enabled")};');
    if(after.name!=='Rosavio'||after.version!==release.appVersion||after.buildID!==release.buildID||after.locale!=='de'||after.videoSetting!==false)throw Error('Updated browser identity or settings incorrect: '+JSON.stringify(after));
    if(after.updateURL!=='https://github.com/aheinen1971-cmd/rosavio/releases/latest/download/rosavio-win64-update.xml')throw Error('New update URL lost');
    await require('./check-browser-pages.cjs')(session,path.join(process.env.ROSAVIO_RELEASE_DIR,production?'public-browser-pages-check':'local-browser-pages-check'));
    await session.close();session=null;
    if(!production){
      const tampered=path.join(root,'tampered.mar');
      fs.copyFileSync(path.join(process.env.ROSAVIO_RELEASE_DIR,release.file),tampered);
      const fd=fs.openSync(tampered,'r+'),last=Buffer.alloc(1),size=fs.statSync(tampered).size;
      fs.readSync(fd,last,0,1,size-1);last[0]^=1;fs.writeSync(fd,last,0,1,size-1);fs.closeSync(fd);
      const verifier=spawnSync(path.join(process.env.ROSAVIO_SOURCE,'obj-rose/dist/bin/signmar.exe'),['-D',path.resolve('certificates/rosavio-update.der'),'-v',tampered],{encoding:'utf8'});
      if(verifier.error||verifier.status===0)throw Error('Tampered MAR negative test failed');
      fs.unlinkSync(tampered);
    }
    fs.writeFileSync(path.join(process.env.ROSAVIO_RELEASE_DIR,production?'public-update-test.json':'local-update-test.json'),JSON.stringify({passed:true,testedAt:new Date().toISOString(),before,check,after,status,signatureVerificationDisabled:false,browserPagesAfterUpdatePassed:true},null,2));
    console.log('Native '+(production?'public':'local')+' update, restart and preference preservation passed.');
  }finally{if(session)await session.close();if(server)await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1});
