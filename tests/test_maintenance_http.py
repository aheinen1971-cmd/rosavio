import importlib.util
import io
import pathlib
import ssl
import subprocess
import sys
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'scripts'))
import maintenance_http as http

class RetryTests(unittest.TestCase):
    def error(self, status):
        return urllib.error.HTTPError('https://example.test/report', status, 'test', {}, io.BytesIO())

    def test_read_recovers_after_504(self):
        with patch.object(http.urllib.request, 'urlopen', side_effect=[self.error(504), io.BytesIO(b'{"passed":true}')]) as read, patch.object(http.time, 'sleep') as sleep:
            self.assertEqual(http.read_url('https://example.test/report'), b'{"passed":true}')
            self.assertEqual(read.call_count, 2)
            sleep.assert_called_once_with(3)

    def test_read_stops_after_three_server_failures(self):
        with patch.object(http.urllib.request, 'urlopen', side_effect=[self.error(503) for _ in range(3)]) as read, patch.object(http.time, 'sleep') as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                http.read_url('https://example.test/report')
            self.assertEqual(read.call_count, 3)
            self.assertEqual([c.args[0] for c in sleep.call_args_list], [3, 10])

    def test_certificate_auth_missing_and_conflict_errors_are_not_retried(self):
        errors=[self.error(code) for code in (401,403,404,409,422,429)]
        errors.append(urllib.error.URLError(ssl.SSLCertVerificationError('invalid certificate')))
        for error in errors:
            with self.subTest(error=error), patch.object(http.urllib.request, 'urlopen', side_effect=error) as read, patch.object(http.time, 'sleep') as sleep:
                with self.assertRaises(urllib.error.URLError):
                    http.read_url('https://example.test/report')
                self.assertEqual(read.call_count, 1)
                sleep.assert_not_called()

    def test_gh_patch_retry_keeps_identical_nonforce_payload(self):
        args=['gh','api','--method','PATCH','repos/example/repo/git/refs/heads/status']
        payload='{"sha":"tested","force":false}'
        with patch.object(http.subprocess, 'run', side_effect=[subprocess.CompletedProcess(args,1,'','HTTP 500 (https://api.github.com/example)'),subprocess.CompletedProcess(args,0,'{}','')]) as run, patch.object(http.time,'sleep'):
            self.assertEqual(http.run_gh(args,input=payload).returncode,0)
            self.assertEqual(run.call_args_list[0],run.call_args_list[1])
            self.assertEqual(run.call_args.kwargs['input'],payload)

    def test_gh_permanent_error_and_retry_exhaustion_remain_failures(self):
        for code,attempts in ((403,1),(404,1),(409,1),(422,1),(500,3),(502,3),(503,3),(504,3)):
            with self.subTest(code=code),patch.object(http.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'',f'gh: Error (HTTP {code})')) as run,patch.object(http.time,'sleep'):
                with self.assertRaisesRegex(RuntimeError,f'HTTP {code}'):
                    http.run_gh(['gh','api','example'])
                self.assertEqual(run.call_count,attempts)

    def test_unknown_error_is_not_retried_or_echoed(self):
        with patch.object(http.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','private diagnostic')) as run:
            with self.assertRaisesRegex(RuntimeError,'HTTP unknown') as caught:
                http.run_gh(['gh','api','example'])
            self.assertNotIn('private diagnostic',str(caught.exception))
            self.assertEqual(run.call_count,1)

if __name__=='__main__':
    unittest.main()
