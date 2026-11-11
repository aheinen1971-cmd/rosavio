import sys,re
import importlib.util,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"scripts"))
s=importlib.util.spec_from_file_location('website',pathlib.Path(__file__).parents[1]/'scripts/update-website-downloads.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class WebsiteTests(unittest.TestCase):
 def proof(self):return {'platform':'linux-x64','passed':True,'publicUpdateTestPassed':True,'browserPagesAfterUpdatePassed':True,'desktopLaunchTestPassed':True,'after':{'signatureDisabled':False,'buildID':'20261028000404'}}
 def test_failed_or_unsigned_release_rejected(self):
  for key in ['passed','publicUpdateTestPassed','browserPagesAfterUpdatePassed','desktopLaunchTestPassed']:
   p=self.proof();p[key]=False
   with self.assertRaises(ValueError):m.verified({},p,'linux-x64')
  p=self.proof();p['after']['signatureDisabled']=True
  with self.assertRaises(ValueError):m.verified({},p,'linux-x64')
 def test_prerelease_and_wrong_platform_rejected(self):
  with self.assertRaises(ValueError):m.verified({'prerelease':True},self.proof(),'linux-x64')
  with self.assertRaises(ValueError):m.verified({},self.proof(),'macos-arm64')
 def test_only_link_changes_and_idempotent(self):
  tag='v158.0.1-rosavio-linux-x64.1';old=m.BASE+tag+'/Rosavio-Linux-x64.tar.xz';new=m.BASE+'v159.0-rosavio-linux-x64.2/Rosavio-Linux-x64.tar.xz'
  source='<html dir="rtl">🌹<a target="_blank" href="'+old+'">تحميل</a>keep Flatpak and Windows</html>'
  t={'linux-x64':{'build':'20261028000000','url':new}};b={tag:'20261027000000','v159.0-rosavio-linux-x64.2':'20261028000000'}
  result=m.rewrite(source,t,b);self.assertEqual(result,source.replace(old,new));self.assertEqual(m.rewrite(result,t,b),result)
  t['linux-x64']['build']='20261026000000'
  with self.assertRaises(ValueError):m.rewrite(source,t,b)
 def test_version_display_all_languages_idempotent_and_mixed(self):
  for lang in m.LABELS:
   source=f'<html lang="{lang}" dir="rtl"><h1>Rosavio</h1><p>Keep roses and links</p></html>'
   same={'Windows':'159.0','Linux':'159.0','Flatpak':'159.0'}
   result=m.show_versions(source,same)
   self.assertIn('Rosavio 159.0',result);self.assertEqual(m.show_versions(result,same),result)
   changed=m.show_versions(result,dict(same,Windows='159.0.1'))
   self.assertIn('Windows · Rosavio 159.0.1',changed);self.assertIn('Linux · Rosavio 159.0',changed)
   self.assertEqual(m.VERSION_BLOCK.sub('',changed),source)
 def test_windows_display_requires_public_proof(self):
  r={'tag_name':'v159.0-rosavio.123','assets':[{'name':'Rosavio-Setup-Deutsch.exe'}]}
  p={'passed':True,'browserPagesAfterUpdatePassed':True,'signatureVerificationDisabled':False,'after':{'version':'159.0'}}
  self.assertEqual(m.windows_version(r,p),'159.0')
  p['signatureVerificationDisabled']=True
  with self.assertRaises(ValueError):m.windows_version(r,p)
 def test_news_all_pages_preserves_pdf_and_everything_else(self):
  pages=list((pathlib.Path(__file__).parents[1]/'docs').glob('*.html'))
  self.assertEqual(len(pages),20)
  for page in pages:
   source=page.read_text(encoding='utf-8-sig')
   heading=re.search(r'<h3><bdi>(?:Windows · )?Rosavio \d.*?</h3>',source)[0]
   versions={'Windows':'161.0','Linux':'161.0','Flatpak':'161.0'}
   changed=m.show_news_version(source,versions)
   self.assertEqual(changed,source.replace(heading,'<h3><bdi>Rosavio 161.0</bdi></h3>',1))
   self.assertEqual(m.show_news_version(changed,versions),changed)
   mixed=m.show_news_version(changed,dict(versions,Flatpak='160.0'))
   self.assertIn('Flatpak · Rosavio 160.0',mixed)
   self.assertIn('Windows · Rosavio 161.0',mixed)
   self.assertEqual(m.show_news_version(mixed,versions),changed)
 def test_news_missing_or_ambiguous_fails_closed(self):
  versions={'Windows':'160.0'}
  with self.assertRaises(ValueError):m.show_news_version('<h3>Rosavio 159.0</h3>',versions)
  with self.assertRaises(ValueError):m.show_news_version('<section id="rosavio-news"><h3>Rosavio 1.0</h3><h3>Rosavio 2.0</h3></section>',versions)
if __name__=='__main__':unittest.main()
