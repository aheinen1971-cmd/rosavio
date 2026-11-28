import sys, tempfile, unittest, errno
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native/video_finder'))
import engine

class FilenameTests(unittest.TestCase):
    def test_untrusted_names_and_languages(self):
        for title in ['../../bad:name?','CON','NUL.txt','...','\u202eabc','日本語'*150,'العربية','עברית','Übung 🌹']:
            name=engine.safe_title(title)
            self.assertNotIn('/',name);self.assertNotIn('\\',name)
            self.assertLessEqual(len(name.encode('utf8')),201)
            self.assertFalse(name.endswith('.'))
        self.assertEqual(engine.safe_title('CON'),'_CON')
        for invalid in [None,{},['bad'],'x'*501]:
            with self.assertRaises(ValueError):engine.safe_title(invalid)

    def test_real_neutral_video_and_concurrent_collisions(self):
        source=Path(__file__).parent/'fixtures/video-finder/video.mp4'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with ThreadPoolExecutor(max_workers=6) as pool:
                targets=list(pool.map(lambda _:engine.publish_video(source,root,'Mein Testvideo'),range(12)))
            self.assertEqual(len(set(targets)),12)
            self.assertIn(root/'Mein Testvideo.mp4',targets)
            self.assertIn(root/'Mein Testvideo (11).mp4',targets)
            for target in targets:self.assertEqual(target.read_bytes(),source.read_bytes())
            self.assertFalse(list(root.glob('*.part')))

    def test_no_hardlinks_and_disk_full_cleanup(self):
        source=Path(__file__).parent/'fixtures/video-finder/video.mp4'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'Test.mp4').write_bytes(b'keep')
            with patch.object(engine.os,'link',side_effect=OSError(errno.EOPNOTSUPP,'fixture')):
                target=engine.publish_video(source,root,'Test')
                self.assertEqual(target.name,'Test (1).mp4')
                self.assertEqual(target.read_bytes(),source.read_bytes())
                original=engine.shutil.copyfileobj
                calls=0
                def fail_second(src,dst):
                    nonlocal calls
                    calls+=1
                    if calls==2:dst.write(b'partial');raise OSError('full')
                    return original(src,dst)
                with patch.object(engine.shutil,'copyfileobj',fail_second):
                    with self.assertRaises(OSError):engine.publish_video(source,root,'Broken')
            self.assertEqual((root/'Test.mp4').read_bytes(),b'keep')
            self.assertFalse((root/'Broken.mp4').exists())
            self.assertFalse(list(root.glob('*.part')))

if __name__=='__main__':unittest.main()
