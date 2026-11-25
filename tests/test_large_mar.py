import importlib.util
import lzma
from pathlib import Path
import tempfile
import unittest
import os
import shutil
import subprocess
import sys
from mardor.reader import MarReader

spec=importlib.util.spec_from_file_location('large_mar',Path(__file__).resolve().parents[1]/'scripts/write-large-mar.py')
large=importlib.util.module_from_spec(spec);spec.loader.exec_module(large)

class LargeMarTests(unittest.TestCase):
    def test_shell_handoff_keeps_spaces_and_many_names(self):
        bash=shutil.which('bash') or ('C:/mozilla-build/msys2/usr/bin/bash.exe' if Path('C:/mozilla-build/msys2/usr/bin/bash.exe').exists() else None)
        if not bash:self.skipTest('Bash unavailable')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);work=root/'compressed';work.mkdir()
            names=['updatev3.manifest']+[f'long folder/library number {i:04}.py' for i in range(1400)]
            for name in names:
                p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(lzma.compress(b'fixture'))
            script=root/'tools/update-packaging/make_full_update.sh';script.parent.mkdir(parents=True)
            script.write_text('set -euo pipefail\nworkdir="'+work.as_posix()+'"\ntargetfiles=\''+' '.join('"'+n+'"' for n in names)+'\'\nmar_command=false\neval "$mar_command $targetfiles"\n',encoding='utf8')
            large.patch(root)
            env={**os.environ,'ROSAVIO_MAR_WRITER':str(Path(large.__file__).resolve()),'ROSAVIO_PYTHON':sys.executable,'MOZ_PRODUCT_VERSION':'161.0','MAR_CHANNEL_ID':'rosavio-release'}
            subprocess.run([bash,script.as_posix()],env=env,check=True,timeout=60)
            with (work/'output.mar').open('rb') as f:
                self.assertEqual([e.name for e in MarReader(f).mardata.index.entries],names)

    def test_large_file_list_roundtrip_preserves_compression_and_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            names=['updatev3.manifest']+[f'video-finder/_internal/long-library-directory/library-{i:04}.py' for i in range(1400)]
            self.assertGreater(len('\0'.join(names)),32767)
            data=lzma.compress(b'fixture payload')
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            listing=root/'files';listing.write_bytes(('\0'.join(names)+'\0').encode())
            large.write(root,listing,'161.0','rosavio-release')
            with (root/'output.mar').open('rb') as f:
                reader=MarReader(f)
                self.assertEqual(reader.productinfo,('161.0','rosavio-release'))
                entries=reader.mardata.index.entries
                self.assertEqual([x.name for x in entries],names)
                for entry in entries:
                    self.assertEqual(b''.join(reader.extract_entry(entry,decompress=None)),data)
                    self.assertEqual(b''.join(reader.extract_entry(entry)),b'fixture payload')

    def test_reject_bad_lists_before_output(self):
        for content in [b'',b'updatev3.manifest',b'../escape\0',b'updatev3.manifest\0updatev3.manifest\0',b'/absolute\0',b'updatev3.manifest\0missing\0']:
            with self.subTest(content=content),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);(root/'updatev3.manifest').write_bytes(b'fixture')
                listing=root/'files';listing.write_bytes(content)
                with self.assertRaises(ValueError):large.write(root,listing,'161.0','rosavio-release')
                self.assertFalse((root/'output.mar').exists())

    def test_upstream_patch_is_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'tools/update-packaging/make_full_update.sh'
            p.parent.mkdir(parents=True);p.write_text('eval "$mar_command $targetfiles"\n')
            large.patch(root);first=p.read_text();large.patch(root)
            self.assertEqual(first,p.read_text())
            self.assertIn('|| exit 1',first)
            p.write_text('changed upstream')
            with self.assertRaises(ValueError):large.patch(root)

if __name__=='__main__':unittest.main()
