"""Bounded retries for transient HTTP failures in website/status maintenance."""
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

RETRY_STATUS = {500, 502, 503, 504}
DELAYS = (3, 10)

def http_status(result):
    match = re.search(r'\bHTTP(?: Error)?[ :]+(\d{3})\b', result.stderr or '')
    return int(match[1]) if match else None

def read_url(url, timeout=30):
    """Retry the complete read; certificate and permanent HTTP errors still fail."""
    for attempt in range(len(DELAYS) + 1):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Rosavio-maintenance'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            retryable = exc.code in RETRY_STATUS
            exc.close()
            if not retryable or attempt == len(DELAYS):
                raise
            print(f'Temporary HTTP {exc.code}; retrying read ({attempt + 1}/{len(DELAYS)}).', file=sys.stderr)
            time.sleep(DELAYS[attempt])

def run_gh(args, *, input=None, check=True):
    """Use only for reads or idempotent metadata writes; never dispatch builds."""
    for attempt in range(len(DELAYS) + 1):
        result = subprocess.run(args, input=input, capture_output=True, text=True)
        status = http_status(result)
        if result.returncode == 0 or status not in RETRY_STATUS or attempt == len(DELAYS):
            break
        print(f'Temporary HTTP {status}; retrying metadata request ({attempt + 1}/{len(DELAYS)}).', file=sys.stderr)
        time.sleep(DELAYS[attempt])
    if check and result.returncode:
        raise RuntimeError(f'GitHub metadata request failed (HTTP {status or "unknown"}, exit {result.returncode}).')
    return result
