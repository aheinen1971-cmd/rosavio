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

if __name__ == '__main__': unittest.main()
