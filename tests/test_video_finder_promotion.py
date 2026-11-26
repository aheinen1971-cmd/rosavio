import hashlib,json,pathlib,subprocess,sys,tempfile,unittest,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
class PromotionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
  self.write('locale-check/report.json',{'passed':True,'languages':list(range(20))})
  self.write('workspace-check/report.json',{'passed':True})
  self.ext={'passed':True,'media':{'builtIn':True,'active':True,'version':'2.2.0'},'nativeBridge':{'passed':True,'foreignURLRejected':True},'nativeGuard':{'passed':True}}
  self.write('extensions-check/report.json',self.ext)
  self.write('local-update-test.json',{'passed':True,'workspaceAfterUpdatePassed':True})
  (self.root/'signed.mar').write_bytes(b'exact signed test fixture')
  self.release={'signatureVerified':True,'appVersion':'161.0','buildID':'20261126145619','file':'signed.mar','hashValue':hashlib.sha512(b'exact signed test fixture').hexdigest(),'size':25}
  self.write('release.json',self.release)
  with zipfile.ZipFile(self.root/'Rosavio-Deutsch-Windows.zip','w') as z:
   for name in ['source/ffmpeg-9.1.tar.xz','source/mutagen-source.json','licenses/Python-LICENSE.txt']:z.writestr('rosavio/video-finder/'+name,'fixture')
   z.writestr('rosavio/video-finder/source/ffmpeg-configure.json',json.dumps(['--enable-demuxer=mov,matroska,mpegts']))
  digest=hashlib.sha256((self.root/'Rosavio-Deutsch-Windows.zip').read_bytes()).hexdigest()
  (self.root/'Rosavio-SHA256SUMS.txt').write_text(digest+'  Rosavio-Deutsch-Windows.zip\n')
 def tearDown(self):self.tmp.cleanup()
 def write(self,name,value):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value))
 def check(self):return subprocess.run([sys.executable,ROOT/'scripts/verify-video-finder-candidate.py',self.root,'windows'],capture_output=True,text=True)
 def test_valid(self):self.assertEqual(self.check().returncode,0,self.check().stderr)
 def test_wrong_build_rejected(self):
  self.release['buildID']='20261125204035';self.write('release.json',self.release);self.assertNotEqual(self.check().returncode,0)
 def test_bridge_failure_rejected(self):
  self.ext['nativeBridge']['passed']=False;self.write('extensions-check/report.json',self.ext);self.assertNotEqual(self.check().returncode,0)
 def test_changed_mar_rejected(self):
  (self.root/'signed.mar').write_bytes(b'altered');self.assertNotEqual(self.check().returncode,0)
 def test_changed_installer_zip_rejected(self):
  with (self.root/'Rosavio-Deutsch-Windows.zip').open('ab') as f:f.write(b'altered')
  self.assertNotEqual(self.check().returncode,0)
 def test_missing_language_rejected(self):
  self.write('locale-check/report.json',{'passed':True,'languages':list(range(19))});self.assertNotEqual(self.check().returncode,0)
 def test_missing_ts_support_rejected_even_with_correct_package_hash(self):
  target=self.root/'Rosavio-Deutsch-Windows.zip'
  with zipfile.ZipFile(target) as z:entries={n:z.read(n) for n in z.namelist()}
  entries['rosavio/video-finder/source/ffmpeg-configure.json']=json.dumps(['--enable-demuxer=mov,matroska']).encode()
  with zipfile.ZipFile(target,'w') as z:
   for name,data in entries.items():z.writestr(name,data)
  digest=hashlib.sha256(target.read_bytes()).hexdigest()
  (self.root/'Rosavio-SHA256SUMS.txt').write_text(digest+'  Rosavio-Deutsch-Windows.zip\n')
  result=self.check()
  self.assertNotEqual(result.returncode,0)
  self.assertIn('MPEG-TS input support is missing',result.stderr)
if __name__=='__main__':unittest.main()
