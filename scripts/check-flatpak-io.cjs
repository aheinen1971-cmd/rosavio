const fs=require('fs'),path=require('path'),http=require('http');
const exec=require('util').promisify(require('child_process').execFile);
module.exports=async function(b,root,mode){
 const input=process.env.ROSAVIO_FLATPAK_PICKER_FILE;
 if(!input)return null;
 const title='Rosavio Flatpak file test';
 const selected=b.script(`const picker=Cc['@mozilla.org/filepicker;1'].createInstance(Ci.nsIFilePicker);picker.init(window.browsingContext,${JSON.stringify(title)},Ci.nsIFilePicker.modeOpen);const result=await new Promise(resolve=>picker.open(resolve));if(result!==Ci.nsIFilePicker.returnOK)throw Error('File selection was not accepted');return {path:picker.file.path,text:await IOUtils.readUTF8(picker.file.path)};`);
 try{
  const {stdout}=await exec('xdotool',['search','--sync','--onlyvisible','--name',title],{timeout:30000});
  const windows=stdout.trim().split(/\s+/);if(windows.length!==1)throw Error('Ambiguous native chooser window');
  const id=windows[0];
  await exec('xdotool',['windowfocus','--sync',id],{timeout:10000});
  await exec('xdotool',['key','--window',id,'ctrl+l']);
  await exec('xdotool',['type','--window',id,'--clearmodifiers','--delay','10',input]);
  await exec('xdotool',['key','--window',id,'Return']);
  const read=await selected;
  if(read?.text!=='Rosavio portal test file')throw Error('Selected host file could not be read: '+JSON.stringify(read));
 }catch(e){selected.catch(()=>{});throw e;}
 const body='Rosavio real browser download '+mode;
 const server=http.createServer((req,res)=>{res.writeHead(200,{'Content-Type':'application/octet-stream','Content-Disposition':'attachment; filename="rosavio-flatpak-download.txt"'});res.end(body);});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const url='http://127.0.0.1:'+server.address().port+'/file';
  const result=await b.script(`const {Downloads}=ChromeUtils.importESModule('resource://gre/modules/Downloads.sys.mjs');const target=PathUtils.join(PathUtils.homeDir,'Downloads','rosavio-flatpak-${mode}.txt');const download=await Downloads.createDownload({source:${JSON.stringify(url)},target});const list=await Downloads.getList(Downloads.ALL);await list.add(download);await download.start();return {succeeded:download.succeeded,text:await IOUtils.readUTF8(target),target};`);
  if(!result?.succeeded||result.text!==body)throw Error('Real browser download failed: '+JSON.stringify(result));
  const host=path.join(require('os').homedir(),'Downloads','rosavio-flatpak-'+mode+'.txt');
  if(fs.readFileSync(host,'utf8')!==body)throw Error('Download did not reach the host Downloads directory');
  return {passed:true,nativeFilePickerAccepted:true,selectedFileReadable:true,realBrowserDownload:true,hostDownloadsVerified:true};
 }finally{await new Promise(resolve=>server.close(resolve));}
};
