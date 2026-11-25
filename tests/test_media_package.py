import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_media', ROOT / 'scripts/prepare-media.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MediaPackageTests(unittest.TestCase):
    def test_package_is_complete_and_repeatable(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)
            base = source / 'browser/extensions'
            base.mkdir(parents=True)
            (base / 'moz.build').write_text('# existing extensions\n', encoding='utf8')
            module.install(source)
            module.install(source)
            self.assertEqual((base / 'moz.build').read_text().count('DIRS += ["rosavio-media"]'), 1)
            jar = (base / 'rosavio-media/jar.mn').read_text()
            for asset in (ROOT / 'media').rglob('*'):
                if asset.is_file():
                    relative = asset.relative_to(ROOT / 'media')
                    self.assertEqual(asset.read_bytes(), (base / 'rosavio-media' / relative).read_bytes())
                    self.assertIn('builtin-addons/rosavio-media/' + relative.as_posix(), jar)

    def test_permissions_and_entrypoints(self):
        manifest = json.loads((ROOT / 'media/manifest.json').read_text())
        self.assertEqual(manifest['version'], '2.2.0')
        self.assertEqual(manifest['browser_specific_settings']['gecko']['id'], 'medien@rosavio.local')
        self.assertEqual(set(manifest['permissions']), {'activeTab', 'scripting', 'downloads', 'nativeMessaging'})
        for entry in [manifest['background']['page'], manifest['sidebar_action']['default_panel'], manifest['browser_action']['default_icon']]:
            self.assertTrue((ROOT / 'media' / entry).is_file())
        self.assertNotIn('update_url', manifest['browser_specific_settings']['gecko'])

if __name__ == '__main__':
    unittest.main()
