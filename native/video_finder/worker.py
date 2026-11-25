import json
import shutil
import sys
from pathlib import Path
from engine import ROOT, BIN_ROOT, choices
import yt_dlp

sys.stdout.reconfigure(encoding='utf-8')

def emit(kind, **data):
    print(json.dumps({'type': kind, **data}, ensure_ascii=True), flush=True)

class Logger:
    def debug(self, message):
        pass
    def warning(self, message):
        emit('log', message=message)
    def error(self, message):
        emit('error', message=message)

def options(folder):
    suffix = '.exe' if sys.platform == 'win32' else ''
    node = BIN_ROOT / ('node' + suffix)
    ffmpeg = BIN_ROOT / ('ffmpeg' + suffix)
    if not node.is_file() or not ffmpeg.is_file():
        raise FileNotFoundError('Bundled video tools are missing')
    return {'logger': Logger(), 'noplaylist': True, 'cachedir': False,
            'socket_timeout': 20, 'retries': 1, 'fragment_retries': 1,
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
            opts['format'] = req['selector']
            with yt_dlp.YoutubeDL(opts) as download:
                download.download([req['url']])
            emit('complete')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        emit('error', message=str(exc))
        sys.exit(1)
