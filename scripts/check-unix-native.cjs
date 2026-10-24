const fs=require('fs'),path=require('path'),start=require('./native-session.cjs');
const [binary,root,platform]=process.argv.slice(2);
(async()=>{let b;try{
 b=await start(path.resolve(binary),path.resolve(root),2864);
 const r=await b.script(`return {name:Services.appinfo.name,version:Services.appinfo.version,buildID:Services.appinfo.appBuildID,os:Services.appinfo.OS,abi:Services.appinfo.XPCOMABI,locale:Services.locale.appLocaleAsBCP47,updateURL:Services.appinfo.updateURL,signatureVerificationDisabled:Services.prefs.getBoolPref('app.update.MARSignatureVerificationDisabled',false)};`);
 const url='https://github.com/aheinen1971-cmd/rosavio/releases/download/rosavio-'+platform+'-latest/rosavio-'+platform+'-update.xml';
 if(r.name!=='Rosavio'||r.locale!=='de'||r.updateURL!==url||r.signatureVerificationDisabled)throw Error(JSON.stringify(r));
 if(r.os!==(platform.startsWith('macos')?'Darwin':'Linux'))throw Error('Wrong native OS');
 fs.mkdirSync(root,{recursive:true});fs.writeFileSync(path.join(root,'report.json'),JSON.stringify({passed:true,...r},null,2));
}finally{if(b)await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
