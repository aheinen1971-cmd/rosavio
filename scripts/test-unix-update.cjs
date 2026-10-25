const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const start=require('./native-session.cjs');
const [oldPackageArg,releaseArg,platform]=process.argv.slice(2);
if(!['linux-x64','macos-x64','macos-arm64'].includes(platform))throw Error('Invalid platform');
const production=process.env.ROSAVIO_PUBLIC_TEST==='1';
const releaseDir=path.resolve(releaseArg),r=JSON.parse(fs.readFileSync(path.join(releaseDir,'release.json')));
if(r.platform!==platform||!r.signatureVerified||!r.tamperNegativeTestPassed)throw Error('Unsigned or wrong-platform update');
const mar=path.join(releaseDir,r.file);
if(path.basename(r.file)!==r.file||fs.statSync(mar).size!==r.size||crypto.createHash('sha512').update(fs.readFileSync(mar)).digest('hex')!==r.hashValue)throw Error('MAR metadata mismatch');
const root=path.join(releaseDir,production?'public-update':'local-update'),pkg=path.join(root,platform.startsWith('macos')?'Rosavio.app':'rosavio');
if(fs.existsSync(root))throw Error('Use a fresh isolated update directory');
fs.mkdirSync(root,{recursive:true});fs.cpSync(path.resolve(oldPackageArg),pkg,{recursive:true});
const resources=platform.startsWith('macos')?path.join(pkg,'Contents/Resources'):pkg;
const binary=platform.startsWith('macos')?path.join(pkg,'Contents/MacOS/rosavio'):path.join(pkg,'rosavio');
const profile=path.join(root,'profile'),pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const expectedURL=`https://github.com/aheinen1971-cmd/rosavio/releases/download/rosavio-${platform}-latest/rosavio-${platform}-update.xml`;
let session,server;
(async()=>{try{
 server=http.createServer((req,res)=>{
   if(req.url==='/update.xml'){
     res.setHeader('Content-Type','text/xml');res.end(`<?xml version="1.0"?><updates><update type="minor" displayVersion="${r.appVersion}" appVersion="${r.appVersion}" platformVersion="${r.appVersion}" buildID="${r.buildID}"><patch type="complete" URL="http://127.0.0.1:8878/package.mar" hashFunction="SHA512" hashValue="${r.hashValue}" size="${r.size}"/></update></updates>`);
   }else if(req.url==='/package.mar'){res.setHeader('Content-Length',r.size);fs.createReadStream(mar).pipe(res);}
   else{res.writeHead(404);res.end();}
 });await new Promise(resolve=>server.listen(8878,'127.0.0.1',resolve));
 session=await start(binary,profile,2865);
 const before=await session.script('return {name:Services.appinfo.name,buildID:Services.appinfo.appBuildID,updateURL:Services.appinfo.updateURL,updateRoot:Services.dirsvc.get("UpdRootD",Ci.nsIFile).path};');
 if(before.name!=='Rosavio'||before.buildID>=r.buildID||before.updateURL!==expectedURL)throw Error('Invalid baseline: '+JSON.stringify(before));
 const seed=await session.script(`const {PlacesUtils}=ChromeUtils.importESModule('resource://gre/modules/PlacesUtils.sys.mjs');Services.prefs.setBoolPref('remote.prefs.recommended',false);Services.prefs.setBoolPref('media.hardware-video-decoding.enabled',false);Services.prefs.setCharPref('browser.toolbars.bookmarks.visibility','always');await PlacesUtils.bookmarks.insert({parentGuid:PlacesUtils.bookmarks.toolbarGuid,title:'Rosavio update test',url:'https://example.com/rosavio'});const folder=await PlacesUtils.bookmarks.insert({parentGuid:PlacesUtils.bookmarks.toolbarGuid,title:'Preserved folder',type:PlacesUtils.bookmarks.TYPE_FOLDER});await PlacesUtils.bookmarks.insert({parentGuid:folder.guid,title:'Child bookmark',url:'https://example.org/rosavio'});Services.prefs.savePrefFile(null);return await PlacesUtils.promiseBookmarksTree(PlacesUtils.bookmarks.toolbarGuid);`);
 await session.close();session=null;
 if(!production){
  fs.mkdirSync(path.join(resources,'distribution'),{recursive:true});
  fs.writeFileSync(path.join(resources,'distribution/policies.json'),JSON.stringify({policies:{AppUpdateURL:'http://127.0.0.1:8878/update.xml',AppAutoUpdate:true}}));
 }else if(fs.existsSync(path.join(resources,'distribution/policies.json')))throw Error('Public test must not override update URL');
 session=await start(binary,profile,2865);
 const check=await session.script(`if(Services.prefs.getBoolPref('app.update.MARSignatureVerificationDisabled',false))throw Error('Signature verification disabled');const checker=Cc['@mozilla.org/updates/update-checker;1'].getService(Ci.nsIUpdateChecker);const url=await checker.wrappedJSObject.getUpdateURL(checker.BACKGROUND_CHECK);Services.ww.openWindow(null,'chrome://browser/content/aboutDialog.xhtml','RosavioUpdateTest','chrome,dialog=no',null);return {url};`);
 if(check.url!==(production?expectedURL:'http://127.0.0.1:8878/update.xml'))throw Error('Local policy not applied');
 let status='';for(let i=0;i<300;i++){const file=path.join(before.updateRoot,'updates/0/update.status');if(fs.existsSync(file))status=fs.readFileSync(file,'utf8').trim();if(status.startsWith('failed'))throw Error(status);if(['pending','applied'].includes(status))break;await pause(1000);}
 if(!['pending','applied'].includes(status))throw Error('Native download timed out: '+status);
 await session.close();session=null;await pause(1500);
 session=await start(binary,profile,2865);
 const after=await session.script(`const {PlacesUtils}=ChromeUtils.importESModule('resource://gre/modules/PlacesUtils.sys.mjs');return {name:Services.appinfo.name,version:Services.appinfo.version,buildID:Services.appinfo.appBuildID,locale:Services.locale.appLocaleAsBCP47,updateURL:Services.appinfo.updateURL,signatureDisabled:Services.prefs.getBoolPref('app.update.MARSignatureVerificationDisabled',false),video:Services.prefs.getBoolPref('media.hardware-video-decoding.enabled'),toolbar:Services.prefs.getCharPref('browser.toolbars.bookmarks.visibility'),bookmarks:await PlacesUtils.promiseBookmarksTree(PlacesUtils.bookmarks.toolbarGuid)};`);
 const stable=tree=>JSON.stringify(tree,(k,v)=>['dateAdded','lastModified'].includes(k)?undefined:v);
 if(after.name!=='Rosavio'||after.buildID!==r.buildID||after.version!==r.appVersion||after.locale!=='de'||after.updateURL!==expectedURL||after.signatureDisabled||after.video!==false||after.toolbar!=='always'||stable(seed)!==stable(after.bookmarks))throw Error('Updated identity/profile verification failed: '+JSON.stringify(after));
 await session.close();session=null;
 if(!production)fs.unlinkSync(path.join(resources,'distribution/policies.json'));
 fs.writeFileSync(path.join(releaseDir,production?'public-update-test.json':'local-update-test.json'),JSON.stringify({passed:true,platform,testedAt:new Date().toISOString(),before,after,status,publicUpdateTestPassed:production},null,2));
 console.log('Signed native Unix update, restart and bookmarks preserved. Public test still required.');
}finally{if(session)await session.close();if(server)await new Promise(resolve=>server.close(resolve));}})().catch(e=>{console.error(e);process.exitCode=1});
