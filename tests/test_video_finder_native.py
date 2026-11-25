"""Native bridge checks, isolated from browser profiles and user downloads."""
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native/video_finder'))
import engine
import host

class NativeTests(unittest.TestCase):
    def run_fixture(self, output, mode='inspect'):
        with tempfile.TemporaryDirectory() as folder:
            script=Path(folder)/'worker.py'
            script.write_text("import sys,json,pathlib\nr=json.loads(pathlib.Path(sys.argv[1]).read_text())\nif r['mode']=='inspect':\n print(json.dumps({'type':'info','title':'fixture','choices':[{'selector':'18','height':360}]}),flush=True)\nelse:\n (pathlib.Path(r['folder'])/'fixture.mp4').write_bytes(b'fixture video')\n print(json.dumps({'type':'complete'}),flush=True)\n",encoding='utf-8')
            o=engine.Operation(output)
            with patch.object(engine,'ROOT',Path(folder)):
                o.start(mode,'https://youtu.be/aqz-KE-bpKQ','18' if mode=='download' else None)
                deadline=time.monotonic()+10
                while o.busy and time.monotonic()<deadline: time.sleep(.03)
            self.assertFalse(o.busy)
            events=[]
            while not o.events.empty(): events.append(o.events.get())
            return events

    def test_real_subprocess_inspection(self):
        with tempfile.TemporaryDirectory() as folder:
            events=self.run_fixture(folder)
            self.assertTrue(any(e['type']=='done' for e in events),events)

    def test_repeat_download_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            first=self.run_fixture(folder,'download')
            second=self.run_fixture(folder,'download')
            saved=[e['path'] for e in first+second if e['type']=='saved']
            self.assertEqual(len(saved),2,(first,second))
            self.assertNotEqual(saved[0],saved[1])
            self.assertEqual(len(list(Path(folder).iterdir())),2)

    def test_fragmented_native_input(self):
        data=json.dumps({'action':'cancel'}).encode()
        class Fragments(io.BytesIO):
            def read(self,n=-1): return super().read(min(n,2))
        self.assertEqual(host.read_message(Fragments(struct.pack('<I',len(data))+data)),{'action':'cancel'})

    def test_native_limits(self):
        for data in [b'\1', struct.pack('<I',0),struct.pack('<I',4097),struct.pack('<I',5)+b'{}',struct.pack('<I',2)+b'[]']:
            with self.assertRaises(ValueError): host.read_message(io.BytesIO(data))

    def test_temporary_folder_failure_releases_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            o=engine.Operation(folder)
            o.busy=True
            with patch.object(engine.tempfile,'mkdtemp',side_effect=PermissionError('fixture denied')):
                o._run('inspect','https://youtu.be/aqz-KE-bpKQ',None)
            self.assertFalse(o.busy)
            events=[]
            while not o.events.empty(): events.append(o.events.get())
            self.assertTrue(any(e['type']=='failed' for e in events))

    def test_reject_foreign_extension(self):
        with patch.object(sys,'argv',['host.exe','manifest.json','other@example.org']):
            with self.assertRaises(SystemExit): host.main()

    def test_reject_extra_native_fields(self):
        class Fake:
            busy=False
            events=__import__('queue').Queue()
            def start(self,*args): raise AssertionError('must not start')
            def cancel(self): return False
        data=json.dumps({'action':'inspect','url':'https://youtu.be/aqz-KE-bpKQ','output':'C:/arbitrary'}).encode()
        out=io.BytesIO()
        host.serve(io.BytesIO(struct.pack('<I',len(data))+data),out,Fake())
        out.seek(0)
        self.assertEqual(host.read_message(out)['type'],'ready')
        self.assertEqual(host.read_message(out)['code'],'youtubeRequestRejected')

if __name__=='__main__': unittest.main(verbosity=2)
