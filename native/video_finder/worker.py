import json
import shutil
import sys
import tempfile
from pathlib import Path
from engine import ROOT, BIN_ROOT, choices
import yt_dlp

sys.stdout.reconfigure(encoding='utf-8')

def emit(kind, **data):
    print(json.dumps({'type': kind, **data}, ensure_ascii=True), flush=True)

class Logger:
    def __init__(self):
        self.failed = False
        self.errors = []
    def debug(self, message):
        pass
    def warning(self, message):
        emit('log', message=message)
    def error(self, message):
        self.failed = True
        self.errors.append(str(message))
        # A recoverable attempt is not yet the final result of the operation.
        emit('log', message=message)


def equivalent_selectors(info, selected):
    formats = info.get('formats') or []
    original = next((f for f in formats if str(f.get('format_id')) == selected.split('+')[0]), None)
    if not original or any(not original.get(k) for k in ('width', 'height', 'fps')):
        return []
    allowed = {c['selector'] for c in choices(info)}
    candidates = []
    for f in formats:
        selector = str(f.get('format_id')) + ('+bestaudio' if f.get('acodec') in (None, 'none') else '')
        if selector == selected or selector not in allowed or f.get('has_drm'):
            continue
        if any(f.get(k) != original.get(k) for k in ('width', 'height', 'fps', 'dynamic_range')):
            continue
        candidates.append((f.get('protocol') == original.get('protocol'),
                           f.get('vcodec', '').split('.')[0] != original.get('vcodec', '').split('.')[0], selector))
    return [item[2] for item in sorted(candidates)[:2]]


def incomplete_transfer(message):
    text = str(message).lower()
    return ('bytes read' in text or 'incomplete read' in text or 'connection reset' in text
            or 'timed out' in text)


def download_complete(req, info):
    selectors = [req['selector']] + equivalent_selectors(info, req['selector'])
    for index, selector in enumerate(selectors):
        # Never merge files or partial fragments from different attempts.
        with tempfile.TemporaryDirectory(prefix='attempt-', dir=req['folder']) as folder:
            opts = options(folder)
            opts['format'] = selector
            failure = None
            try:
                with yt_dlp.YoutubeDL(opts) as download:
                    result = download.download([req['url']])
                if result or opts['logger'].failed:
                    raise RuntimeError('; '.join(opts['logger'].errors) or 'Video download did not finish completely')
            except Exception as exc:
                failure = exc
            if failure is not None:
                if index + 1 < len(selectors) and incomplete_transfer(failure):
                    emit('log', message='Interrupted transfer; retrying an equivalent resolution and frame rate')
                    continue
                raise failure
            files = [p for p in Path(folder).iterdir() if p.suffix.lower() in ('.mp4', '.mkv', '.webm')]
            if len(files) != 1 or not files[0].stat().st_size:
                raise RuntimeError('No complete media output')
            shutil.move(str(files[0]), str(Path(req['folder']) / files[0].name))
            emit('complete')
            return

def options(folder):
    suffix = '.exe' if sys.platform == 'win32' else ''
    node = BIN_ROOT / ('node' + suffix)
    ffmpeg = BIN_ROOT / ('ffmpeg' + suffix)
    if not node.is_file() or not ffmpeg.is_file():
        raise FileNotFoundError('Bundled video tools are missing')
    return {'logger': Logger(), 'noplaylist': True, 'cachedir': False,
            'socket_timeout': 20, 'retries': 3, 'fragment_retries': 3,
            # Restart interrupted fragments rather than reusing partial bytes.
            # A missing fragment must never become a successful, damaged video.
            'continuedl': False, 'skip_unavailable_fragments': False,
            'js_runtimes': {'node': {'path': str(node)}},
            'remote_components': set(), 'ffmpeg_location': str(ffmpeg),
            'outtmpl': str(Path(folder) / '%(id)s.%(ext)s'),
            'overwrites': False, 'windowsfilenames': True, 'merge_output_format': 'mkv',
            'progress_hooks': [progress]}

def progress(data):
    total = data.get('total_bytes') or data.get('total_bytes_estimate')
    percent = min(100, data.get('downloaded_bytes', 0) / total * 100) if total else None
    emit('progress', percent=percent, phase=data.get('status'), bytes=data.get('downloaded_bytes', 0))

def main():
    req = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    opts = options(req['folder'])
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(req['url'], download=False)
        available = choices(info)
        if not available:
            raise ValueError('Keine herunterladbare Qualität mit Bild und Ton erkannt.')
        if req['mode'] == 'inspect':
            emit('info', title=info.get('title'), choices=available)
        else:
            if req['selector'] not in [x['selector'] for x in available]:
                raise ValueError('Requested format is no longer available')
            download_complete(req, info)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit('error', message=str(exc))
        sys.exit(1)
