import hashlib
import ast
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
    def test_helper_target_matches_runtime_and_installer_without_moving_addon(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,bundle=self.fixture(Path(tmp))
            module.install(source,bundle); module.install(source,bundle)
            addon=source/'browser/extensions/rosavio-media'
            parent=(addon/'moz.build').read_text()
            self.assertNotIn('DIST_SUBDIR =',parent)
            self.assertEqual(parent.count('DIRS += ["native"]'),1)
            native=(addon/'native/moz.build').read_text()
            # The browser parent exports DIST_SUBDIR="browser". Only the helper
            # child must reset it; changing the add-on would move its JAR too.
            scope={'DIST_SUBDIR':'browser'}
            tree=ast.parse(native)
            for statement in tree.body:
                if isinstance(statement,ast.Assign):
                    scope[statement.targets[0].id]=ast.literal_eval(statement.value)
            self.assertEqual(scope['DIST_SUBDIR'],'')
            for statement in tree.body:
                if isinstance(statement,ast.AugAssign):
                    for relative in ast.literal_eval(statement.value):
                        self.assertTrue((addon/'native'/relative).is_file())
            self.assertIn('@BINPATH@/video-finder/**', (source/'browser/installer/package-manifest.in').read_text())

    def test_native_libraries_use_mozbuild_case_insensitive_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,bundle=self.fixture(Path(tmp))
            inventory=json.loads((bundle/'bundle.json').read_text())
            for extension in ('.pyd','.abi3.so'):
                for name in ('_ARC4','_Salsa20','_chacha20','_raw_aes'):
                    relative='_internal/Cryptodome/Cipher/'+name+extension
                    path=bundle/relative;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(b'fixture')
                    inventory['files'][relative]=hashlib.sha256(b'fixture').hexdigest()
            (bundle/'bundle.json').write_text(json.dumps(inventory))
            module.install(source,bundle)
            tree=ast.parse((source/'browser/extensions/rosavio-media/native/moz.build').read_text())
            for statement in tree.body:
                if isinstance(statement,ast.AugAssign):
                    values=ast.literal_eval(statement.value)
                    self.assertEqual(values,sorted(values,key=str.lower))

    def fixture(self, root):
        source, bundle = root/'source', root/'bundle'
        for name, value in {'toolkit/components/extensions/NativeManifests.sys.mjs':module.MARKER,
                            'python/mozbuild/mozpack/files.py':module.PACKAGER_MARKER,
                            'toolkit/components/extensions/NativeMessaging.sys.mjs':module.PORTAL_MARKER,
                            'browser/extensions/rosavio-media/moz.build':'# existing\n',
                            'browser/installer/package-manifest.in':'# existing\n'}.items():
            path=source/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value)
        bundle.mkdir(); (bundle/'video-finder-host').write_bytes(b'fixture')
        (bundle/'bundle.json').write_text(json.dumps({'schema':1,'qualified':True,'files':{
            'video-finder-host':hashlib.sha256(b'fixture').hexdigest()}}))
        return source,bundle

    def test_only_bundled_helper_bypasses_executable_transformation(self):
        import textwrap
        from types import SimpleNamespace
        code='def choose(self,path,srcpath):\n'+textwrap.indent(textwrap.dedent(module.PACKAGER_REPLACEMENT),'    ')+'\n    return File(srcpath)\n'
        scope={'File':lambda p:('copy',p),'ExecutableFile':lambda p:('transform',p),'is_executable':lambda p:True}
        exec(code,scope)
        for path in ['video-finder/video-finder-host','bin/video-finder/_internal/libpython.so','bin\\video-finder\\node']:
            self.assertEqual(scope['choose'](SimpleNamespace(find_executables=True),path,path)[0],'copy')
        for path in ['bin/rosavio','bin/libxul.so','bin/video-finder-other/host']:
            self.assertEqual(scope['choose'](SimpleNamespace(find_executables=True),path,path)[0],'transform')

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
