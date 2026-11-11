import copy,json,pathlib,re,sys,unittest
from unittest.mock import Mock
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/'scripts'))
import pdf_website_release as m

class PdfNewsTests(unittest.TestCase):
 def setUp(self):
  self.fixture=json.loads(pathlib.Path(__file__).with_name('pdf_release_fixture.json').read_text(encoding='utf-8'))
 def verify(self,release=None,signature=None):
  read=Mock(return_value=json.dumps(signature or self.fixture['signature']).encode())
  result=m.verified_pdf(release or self.fixture['release'],read)
  self.assertEqual(read.call_count,1)
  self.assertTrue(read.call_args.args[0].endswith('-Signatur.json'))
  return result
 def test_real_public_signature_without_package_download(self):
  self.assertEqual(self.verify(),'1.58.0')
 def test_draft_prerelease_and_tampering_rejected(self):
  for flag in ['draft','prerelease']:
   release=copy.deepcopy(self.fixture['release']);release[flag]=True
   with self.assertRaises(ValueError):self.verify(release)
  for field,value in [('digest','sha256:'+'0'*64),('size',1),('browser_download_url','https://example.com/package.zip')]:
   release=copy.deepcopy(self.fixture['release'])
   next(a for a in release['assets'] if a['name'].endswith('-Windows.zip'))[field]=value
   with self.assertRaises(ValueError):self.verify(release)
  sig=copy.deepcopy(self.fixture['signature']);sig['payload']='eA=='
  with self.assertRaises(Exception):self.verify(signature=sig)
 def test_all_twenty_pages_only_pdf_news_changes(self):
  pages=list((pathlib.Path(__file__).parents[1]/'docs').glob('*.html'))
  self.assertEqual(len(pages),20)
  languages=set()
  for page in pages:
   source=page.read_text(encoding='utf-8-sig')
   old=re.search(r'<h3><bdi>PDF Digital (\d+\.\d+\.\d+)',source)[1]
   new=str(int(old.split('.')[0])+1)+'.0.0'
   lang=re.search(r'<html\b[^>]*\blang="([^"]+)"',source)[1];languages.add(lang)
   self.assertEqual(m.rewrite_pdf_news(source,old),source)
   changed=m.rewrite_pdf_news(source,new)
   expected=re.sub(r'(<h3><bdi>PDF Digital )'+re.escape(old)+r'([^<]*</bdi></h3>)<p>.*?</p>',lambda x:x[1]+new+x[2]+'<p>'+m.TEXT[lang]+'</p>',source,flags=re.S)
   expected=expected.replace(m.ROOT+'/tag/v'+old,m.ROOT+'/tag/v'+new)
   self.assertEqual(changed,expected)
   self.assertEqual(m.rewrite_pdf_news(changed,new),changed)
   with self.assertRaises(ValueError):m.rewrite_pdf_news(changed,old)
  self.assertEqual(languages,set(m.TEXT))
 def test_missing_or_ambiguous_news_rejected(self):
  source=(pathlib.Path(__file__).parents[1]/'docs/index.html').read_text(encoding='utf-8-sig')
  for invalid in ['',source+source]:
   with self.assertRaises(ValueError):m.rewrite_pdf_news(invalid,'999.0.0')

if __name__=='__main__':unittest.main()
