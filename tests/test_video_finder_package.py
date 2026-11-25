import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_video', ROOT/'scripts/prepare-video-finder.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PackageTests(unittest.TestCase):
    def fixture(self, root):
        source, bundle = root/'source', root/'bundle'
        for name, value in {'toolkit/components/extensions/NativeManifests.sys.mjs':module.MARKER,
                            'browser/extensions/rosavio-media/moz.build':'# existing\n',
                            'browser/installer/package-manifest.in':'# existing\n'}.items():
            path=source/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value)
        bundle.mkdir(); (bundle/'video-finder-host').write_bytes(b'fixture')
        (bundle/'bundle.json').write_text(json.dumps({'schema':1,'qualified':True,'files':{
            'video-finder-host':hashlib.sha256(b'fixture').hexdigest()}}))
        return source,bundle

    def test_repeatable_package_and_reserved_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,bundle=self.fixture(Path(tmp))
            module.install(source,bundle); module.install(source,bundle)
            text=(source/'toolkit/components/extensions/NativeManifests.sys.mjs').read_text()
            self.assertEqual(text,module.REPLACEMENT)
            self.assertIn('!context.extension.isPrivileged',text)
            self.assertIn('resource://builtin-addons/rosavio-media/',text)
            self.assertEqual((source/'browser/installer/package-manifest.in').read_text().count('[video-finder]'),1)
            self.assertEqual((source/'browser/extensions/rosavio-media/native/video-finder-host').read_bytes(),b'fixture')

    def test_bad_hash_rejected_before_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,bundle=self.fixture(Path(tmp)); (bundle/'video-finder-host').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'checksum'): module.install(source,bundle)
            self.assertEqual((source/'toolkit/components/extensions/NativeManifests.sys.mjs').read_text(),module.MARKER)

    def test_changed_upstream_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,bundle=self.fixture(Path(tmp))
            (source/'toolkit/components/extensions/NativeManifests.sys.mjs').write_text('new upstream')
            with self.assertRaisesRegex(ValueError,'Upstream'): module.install(source,bundle)

if __name__=='__main__': unittest.main()
