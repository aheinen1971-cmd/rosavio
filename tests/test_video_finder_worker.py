"""A failed media transfer must never produce a successful completion."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native/video_finder'))
# Tests exercise the worker contract without downloading dependencies or media.
with patch.dict(sys.modules, {'yt_dlp': types.SimpleNamespace(YoutubeDL=None)}):
    spec = importlib.util.spec_from_file_location('tested_worker', Path(sys.path[0]) / 'worker.py')
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)


class WorkerTests(unittest.TestCase):
    def test_bounded_retries_restart_and_require_every_fragment(self):
        with patch.object(Path, 'is_file', return_value=True):
            options = worker.options('unused')
        self.assertEqual(options['retries'], 3)
        self.assertEqual(options['fragment_retries'], 3)
        self.assertFalse(options['continuedl'])
        self.assertFalse(options['skip_unavailable_fragments'])

    def run_download(self, result=0, logged_error=False, exception=False):
        events = []
        class Downloader:
            def __init__(self, options): self.options = options
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def extract_info(self, *args, **kwargs): return {'title': 'Neutral fixture'}
            def download(self, urls):
                if logged_error: self.options['logger'].error('Incomplete fragment')
                if exception: raise OSError('Connection interrupted')
                Path(self.options['outtmpl']).parent.joinpath('fixture.mkv').write_bytes(b'fixture')
                return result
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / 'request.json'
            request.write_text(json.dumps({'mode': 'download', 'folder': directory,
                'url': 'https://www.youtube.com/watch?v=aqz-KE-bpKQ', 'selector': '312+bestaudio'}))
            with patch.object(sys, 'argv', ['worker', str(request)]), \
                 patch.object(Path, 'is_file', return_value=True), \
                 patch.object(worker.yt_dlp, 'YoutubeDL', Downloader), \
                 patch.object(worker, 'choices', return_value=[{'selector': '312+bestaudio'}]), \
                 patch.object(worker, 'emit', side_effect=lambda kind, **data: events.append(kind)):
                if result or logged_error or exception:
                    with self.assertRaises((RuntimeError, OSError)): worker.main()
                    self.assertNotIn('complete', events)
                else:
                    worker.main()
                    self.assertEqual(events, ['complete'])

    def test_nonzero_result_is_failure(self): self.run_download(result=1)
    def test_logged_error_with_zero_exit_is_failure(self): self.run_download(logged_error=True)
    def test_interrupted_transfer_is_failure(self): self.run_download(exception=True)
    def test_complete_transfer_succeeds(self): self.run_download()

    def test_equivalent_format_never_downgrades_or_changes_fps_or_hdr(self):
        base = dict(width=1920,height=1080,fps=60,dynamic_range='SDR',vcodec='avc1.64002a',acodec='none',protocol='m3u8_native')
        formats = [dict(base,format_id='312'),dict(base,format_id='299',protocol='https'),
                   dict(base,format_id='low',height=720),dict(base,format_id='slow',fps=30),
                   dict(base,format_id='hdr',dynamic_range='HDR'),dict(base,format_id='drm',has_drm=True),
                   dict(format_id='audio',vcodec='none',acodec='aac')]
        self.assertEqual(worker.equivalent_selectors({'formats':formats},'312+bestaudio'),['299+bestaudio'])
        self.assertEqual(worker.equivalent_selectors({'formats':[]},'312+bestaudio'),[])

    def test_fallback_clean_output_and_bounded_failure(self):
        for errors in [('Incomplete read',None),('Incomplete read','Incomplete read'),('Sign in required',None)]:
            calls=[];events=[]
            class Downloader:
                def __init__(self,opts): self.opts=opts
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def download(self,urls):
                    folder=Path(self.opts['outtmpl']).parent
                    self_test.assertEqual(list(folder.iterdir()),[])
                    failure=errors[len(calls)];calls.append(self.opts['format'])
                    (folder/'fixture.mkv').write_bytes(b'bad' if failure else b'complete')
                    if failure: raise RuntimeError(failure)
                    return 0
            self_test=self
            with tempfile.TemporaryDirectory() as directory, \
                 patch.object(Path,'is_file',return_value=True), \
                 patch.object(worker.yt_dlp,'YoutubeDL',Downloader), \
                 patch.object(worker,'equivalent_selectors',return_value=['299+bestaudio']), \
                 patch.object(worker,'emit',side_effect=lambda kind,**data:events.append(kind)):
                req=dict(folder=directory,selector='312+bestaudio',url='https://www.youtube.com/watch?v=aqz-KE-bpKQ')
                if errors==('Incomplete read',None):
                    worker.download_complete(req,{})
                    self.assertEqual((Path(directory)/'fixture.mkv').read_bytes(),b'complete')
                    self.assertEqual(events.count('complete'),1)
                else:
                    with self.assertRaises(RuntimeError):worker.download_complete(req,{})
                    self.assertNotIn('complete',events)
                    self.assertEqual(list(Path(directory).iterdir()),[])
                self.assertEqual(len(calls),1 if errors[0]=='Sign in required' else 2)

if __name__ == '__main__': unittest.main()
