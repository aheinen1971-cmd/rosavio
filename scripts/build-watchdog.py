"""Conservative recovery checks driven by the existing status clock.

State is committed BEFORE dispatch. Ambiguous POSTs are never retried.
This module cannot dispatch Flatpak, force builds, reruns or cancellations.
"""
import base64
import datetime as dt
import json
import math
import os
import re
import urllib.request
import urllib.error

REPO = 'aheinen1971-cmd/rosavio'
BRANCH = 'rosavio-build-watchdog-state'
PLATFORMS = {'Windows': ('rosavio-build.yml', ''),
             'Linux': ('rosavio-linux-automatic.yml', '-linux-x64')}
GRACE = 3600
DISCOVERY = 1200

def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp needs timezone')
    return parsed.timestamp()

def decide(version, platform, runs, refs, releases, entry, now):
    suffix = PLATFORMS[platform][1]
    pattern = re.compile(r'^v' + re.escape(version + '-rosavio' + suffix) + r'\.(\d+)$')
    if any(not r['draft'] and not r['prerelease'] and pattern.fullmatch(r['tag_name']) for r in releases):
        return 'published'
    if any(r['status'] != 'completed' for r in runs):
        return 'active-run'
    attempts = {int(m[1]) for ref in refs if (m := pattern.fullmatch(ref['ref'].removeprefix('refs/tags/')))}
    if attempts:
        matching = [r for r in runs if r['id'] in attempts]
        if not matching:
            raise ValueError('Reserved attempt not found')
        return 'attempt-needs-review'
    if entry.get('dispatchAt') is not None:
        after = [r for r in runs if timestamp(r['created_at']) >= entry['dispatchAt'] - 60]
        if after:
            return 'completed-without-publication'
        return 'awaiting-run' if now - entry['dispatchAt'] < DISCOVERY else 'missing-dispatched-run'
    return 'grace-period' if now - entry['firstSeen'] < GRACE else 'dispatch'

class Client:
    def api(self, path, method='GET', data=None, missing=False):
        request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + path,
            method=method, headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
            'Accept': 'application/vnd.github+json', 'User-Agent': 'rosavio-build-watchdog',
            'Content-Type': 'application/json'},
            data=json.dumps(data).encode() if data is not None else None)
        # GitHub API routes used here do not redirect. Never forward credentials.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs): return None
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if missing and error.code == 404: return None
            raise RuntimeError('GitHub API HTTP ' + str(error.code)) from None

    def pages(self, route, key=None):
        result = []
        for page in range(1, 101):
            data = self.api(route + ('&' if '?' in route else '?') + f'per_page=100&page={page}')
            batch = data[key] if key else data
            if not isinstance(batch, list): raise ValueError('Invalid page')
            result.extend(batch)
            if len(batch) < 100: return result
        raise ValueError('Incomplete pagination')

    def read(self):
        file = self.api('contents/state.json?ref=' + BRANCH, missing=True)
        if file is None:
            if self.api('git/ref/heads/' + BRANCH, missing=True) is not None:
                raise ValueError('State branch exists but state missing')
            return {'schema': 1, 'entries': {}}, None
        state = json.loads(base64.b64decode(file['content'], validate=False))
        if state.get('schema') != 1 or not isinstance(state.get('entries'), dict):
            raise ValueError('Invalid watchdog state')
        return state, file['sha']

    def save(self, state, sha):
        raw = json.dumps(state, indent=2)
        if sha is None:
            tree = self.api('git/trees', 'POST', {'tree': [{'path': 'state.json', 'mode': '100644', 'type': 'blob', 'content': raw}]})
            commit = self.api('git/commits', 'POST', {'message': 'Initialize build watchdog observations', 'tree': tree['sha'], 'parents': []})
            self.api('git/refs', 'POST', {'ref': 'refs/heads/' + BRANCH, 'sha': commit['sha']})
        else:
            self.api('contents/state.json', 'PUT', {'branch': BRANCH, 'sha': sha,
                'message': 'Record build watchdog decision', 'content': base64.b64encode(raw.encode()).decode()})
        return self.read()[1]

    def inventory(self, version, platform):
        workflow = PLATFORMS[platform][0]
        return (self.pages('actions/workflows/' + workflow + '/runs', 'workflow_runs'),
                self.pages('git/matching-refs/tags/v' + version + '-rosavio'),
                self.pages('releases'))

def check(client, version, now, apply=False):
    if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', version): raise ValueError('Invalid stable version')
    state, sha = client.read()
    results = {}
    for platform, (workflow, _) in PLATFORMS.items():
        key = version + '/' + platform
        entry = state['entries'].setdefault(key, {'firstSeen': now})
        for field in ['firstSeen', 'dispatchAt']:
            if field == 'dispatchAt' and field not in entry: continue
            value = entry.get(field)
            if not isinstance(value, (float, int)) or not math.isfinite(value) or value > now:
                raise ValueError('Invalid observation time')
        inventory = client.inventory(version, platform)
        result = decide(version, platform, *inventory, entry, now)
        if result == 'dispatch' and apply:
            # Re-read immediately before the durable claim. Existing workflow
            # concurrency and ordinary version checks cover a schedule race.
            result = decide(version, platform, *client.inventory(version, platform), entry, now)
            if result == 'dispatch':
                entry['dispatchAt'] = now
                entry['sourceStatusRun'] = os.environ.get('GITHUB_RUN_ID')
                sha = client.save(state, sha)
                client.api('actions/workflows/' + workflow + '/dispatches', 'POST',
                           {'ref': 'main', 'inputs': {'force': False}})
                result = 'dispatched-once'
        results[platform] = result
    if apply: client.save(state, sha)
    return results

def main():
    apply = '--apply' in __import__('sys').argv
    if apply and (os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REPOSITORY') != REPO):
        raise RuntimeError('Writes only on authorized repository runner')
    with urllib.request.urlopen('https://product-details.mozilla.org/1.0/firefox_versions.json', timeout=30) as response:
        version = json.load(response)['LATEST_FIREFOX_VERSION']
    results = check(Client(), version, dt.datetime.now(dt.timezone.utc).timestamp(), apply)
    report = f'Stable Firefox {version}: ' + json.dumps(results)
    print(report)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as output: output.write(report + '\n')
    if any(value in ('attempt-needs-review', 'completed-without-publication', 'missing-dispatched-run') for value in results.values()):
        raise RuntimeError('Build recovery needs review; no automatic repeat')

if __name__ == '__main__': main()
