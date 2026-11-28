"""Isolated Windows prototype. No browser configuration, cookies or native registration."""
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import signal
import tempfile
import unicodedata
import errno
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent
BIN_ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else ROOT
CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def safe_title(value):
    if not isinstance(value, str) or len(value) > 500:
        raise ValueError('Invalid filename title')
    name = unicodedata.normalize('NFC', value)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()[:90].strip('. ')
    # Keep each filename below the common 255-byte filesystem component limit.
    while len(name.encode('utf-8')) > 200:
        name = name[:-1]
    if re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', name, re.I):
        name = '_' + name
    return name or 'Video'


def publish_video(source, output, title):
    output.mkdir(parents=True, exist_ok=True)
    base = safe_title(title)
    partial = output / ('.video-finder-' + uuid.uuid4().hex + '.part')
    try:
        with source.open('rb') as src, partial.open('xb') as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        for number in range(10000):
            suffix = '' if number == 0 else f' ({number})'
            target = output / (base + suffix + source.suffix)
            try:
                # Atomic, same-volume publication; never replace an existing file.
                os.link(partial, target)
                return target
            except FileExistsError:
                continue
            except OSError as exc:
                if exc.errno not in (errno.EPERM, errno.EACCES, errno.ENOSYS, errno.EOPNOTSUPP):
                    raise
                # FAT/exFAT destinations may not support hard links. Exclusive
                # creation still guarantees that existing user files are safe.
                try:
                    destination = target.open('xb')
                except FileExistsError:
                    continue
                try:
                    with partial.open('rb') as src, destination as dst:
                        shutil.copyfileobj(src, dst)
                        dst.flush()
                        os.fsync(dst.fileno())
                    return target
                except BaseException:
                    target.unlink(missing_ok=True)
                    raise
        raise OSError('No free filename')
    finally:
        partial.unlink(missing_ok=True)


def downloads_folder():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        class GUID(ctypes.Structure):
            _fields_ = [('a', wintypes.DWORD), ('b', wintypes.WORD), ('c', wintypes.WORD), ('d', ctypes.c_ubyte * 8)]
        guid = GUID.from_buffer_copy(uuid.UUID('374de290-123f-4565-9164-39c4925e467b').bytes_le)
        pointer = ctypes.c_void_p()
        shell = ctypes.windll.shell32
        if shell.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(pointer)) != 0:
            raise OSError('Downloads folder unavailable')
        try:
            return Path(ctypes.wstring_at(pointer.value)) / 'Video Finder'
        finally:
            ctypes.windll.ole32.CoTaskMemFree(pointer)
    # XDG paths also match Flatpak's narrowly granted xdg-download directory.
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'user-dirs.dirs'
    if config.is_file():
        for line in config.read_text(encoding='utf-8').splitlines():
            match = re.fullmatch(r'XDG_DOWNLOAD_DIR="([^"\n]+)"', line.strip())
            if match:
                value = match[1].replace('$HOME', str(Path.home()))
                if '$' not in value and Path(value).is_absolute():
                    return Path(value) / 'Video Finder'
    return Path.home() / 'Downloads' / 'Video Finder'


def stop_process(p):
    if p.poll() is not None:
        return
    if os.name == 'nt':
        result = subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True, creationflags=CREATE_FLAGS, timeout=10)
        if result.returncode and p.poll() is None:
            raise OSError('Could not stop helper process')
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def normalize_url(value):
    p = urlsplit(value.strip())
    if p.scheme != 'https' or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Bitte eine HTTPS-Adresse eines einzelnen YouTube-Videos eingeben.')
    host = p.hostname
    if host == 'youtu.be':
        ident = p.path.strip('/')
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        ident = (parse_qs(p.query).get('v') or [''])[0] if p.path == '/watch' else ''
        if p.path.startswith(('/shorts/', '/live/')):
            ident = p.path.split('/')[2]
    else:
        ident = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', ident):
        raise ValueError('Keine gültige YouTube-Video-Adresse. Listen und andere Webseiten werden nicht unterstützt.')
    return 'https://www.youtube.com/watch?v=' + ident


def choices(info):
    if info.get('is_live') or info.get('_type') in ('playlist', 'multi_video'):
        raise ValueError('Laufende Livestreams und Wiedergabelisten werden im Prototyp nicht unterstützt.')
    result = []
    formats = info.get('formats') or []
    audio = [f for f in formats if f.get('acodec') not in (None, 'none') and f.get('vcodec') == 'none' and not f.get('has_drm')]
    for f in formats:
        fid = str(f.get('format_id', ''))
        if f.get('vcodec') in (None, 'none') or f.get('has_drm') or not re.fullmatch(r'[A-Za-z0-9_-]+', fid):
            continue
        separate = f.get('acodec') in (None, 'none')
        if separate and not audio:
            continue
        selector = fid + ('+bestaudio' if separate else '')
        height = f.get('height') or 0
        result.append({'selector': selector, 'height': height, 'label': f"{height or '?'}p · {'MKV' if separate else f.get('ext', '?').upper()} · {f.get('fps') or '?'} FPS · {'Bild + Ton zusammenführen' if separate else 'Bild und Ton'} · {fid}"})
    return sorted(result, key=lambda x: x['height'], reverse=True)


def friendly_error(raw):
    low = raw.lower()
    if 'requested format' in low:
        return 'Die gewählte Qualität ist nicht mehr verfügbar. Bitte das Video erneut erkennen lassen.'
    if any(s in low for s in ('sign in', 'bot', 'login', 'private video', 'age-restricted')):
        return 'YouTube verlangt eine Anmeldung oder blockiert den Abruf. Es werden keine Browser-Anmeldedaten übernommen.'
    if any(s in low for s in ('unavailable', 'removed', 'not available')):
        return 'Dieses Video ist nicht verfügbar oder für diesen Abruf gesperrt.'
    if any(s in low for s in ('timed out', 'name resolution', 'connection', 'certificate')):
        return 'Die sichere Verbindung ist fehlgeschlagen. Verbindung prüfen und später erneut versuchen.'
    return 'Der Vorgang ist fehlgeschlagen. Technische Einzelheiten stehen unten.'


class Operation:
    def __init__(self, output=None):
        self.events = queue.Queue()
        self.lock = threading.Lock()
        self.process = None
        self.cancelled = False
        self.busy = False
        self.settled = False
        self.output = Path(output) if output else downloads_folder()

    def start(self, mode, url, selector=None, filename_title=None):
        url = normalize_url(url)
        if mode not in ('inspect', 'download'):
            raise ValueError('Unbekannter Vorgang.')
        if mode == 'download' and not re.fullmatch(r'[A-Za-z0-9_-]+(?:\+bestaudio)?', selector or ''):
            raise ValueError('Bitte zuerst eine verfügbare Qualität auswählen.')
        if filename_title is not None:
            filename_title = safe_title(filename_title)
        with self.lock:
            if self.busy:
                raise ValueError('Es läuft bereits ein Vorgang.')
            self.busy, self.cancelled = True, False
            self.settled = False
        threading.Thread(target=self._run, args=(mode, url, selector, filename_title), daemon=True).start()

    def cancel(self):
        with self.lock:
            if not self.busy or self.settled:
                return False
            self.cancelled = True
            p = self.process
            if p and p.poll() is None:
                # Only our own worker and its children (including FFmpeg), never browser processes.
                stop_process(p)
            return True

    def _run(self, mode, url, selector, filename_title=None):
        staging = None
        complete = False
        worker_error = False
        metadata = False
        try:
            staging = Path(tempfile.mkdtemp(prefix='rosavio-video-finder-'))
            request = {'mode': mode, 'url': url, 'selector': selector, 'folder': str(staging)}
            req = staging / 'request.json'
            req.write_text(json.dumps(request), encoding='utf-8')
            with self.lock:
                if self.cancelled:
                    return
                command = [sys.executable, '--worker', str(req)] if getattr(sys, 'frozen', False) else [sys.executable, str(ROOT / 'worker.py'), str(req)]
                # The worker reads its request file, never the browser's open
                # native-messaging input pipe. Inheriting that pipe can block
                # Windows worker startup and also exposes unrelated messages.
                self.process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=CREATE_FLAGS, start_new_session=os.name != 'nt')
                p = self.process
            for line in p.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    event = {'type': 'log', 'message': line.strip()}
                if not isinstance(event, dict) or not isinstance(event.get('type'), str):
                    raise ValueError('Ungültige Antwort des Download-Helfers.')
                if event['type'] == 'complete':
                    complete = True
                if event['type'] == 'error':
                    worker_error = True
                if event['type'] == 'info':
                    metadata = bool(event.get('title') and event.get('choices'))
                if event.get('type') != 'complete':
                    self.events.put(event)
            code = p.wait()
            with self.lock:
                if self.cancelled:
                    return
                self.settled = True
                if code or worker_error:
                    self.events.put({'type': 'failed'})
                elif mode == 'download':
                    if not complete:
                        raise ValueError('Der Download-Helfer hat keinen vollständigen Abschluss bestätigt.')
                    files = [x for x in staging.iterdir() if x.suffix.lower() in ('.mp4', '.mkv', '.webm')]
                    if len(files) != 1 or not files[0].stat().st_size:
                        raise ValueError('Kein vollständiges Video erzeugt.')
                    output = self.output
                    target = publish_video(files[0], output, filename_title or files[0].stem)
                    self.events.put({'type': 'saved', 'path': str(target)})
                else:
                    if not metadata:
                        raise ValueError('Der Download-Helfer hat keine Videoangaben geliefert.')
                    self.events.put({'type': 'done'})
        except Exception as exc:
            self.events.put({'type': 'error', 'message': str(exc)})
            self.events.put({'type': 'failed'})
        finally:
            with self.lock:
                p = self.process
                if p and p.poll() is None:
                    stop_process(p)
                    p.wait(timeout=10)
                if p and p.stdout:
                    p.stdout.close()
            try:
                if staging is not None and staging.exists():
                    shutil.rmtree(staging)
            except OSError:
                self.events.put({'type': 'log', 'message': 'Temporäre Dateien konnten nicht vollständig entfernt werden: ' + str(staging)})
            with self.lock:
                cancelled = self.cancelled
                self.process, self.busy = None, False
            if cancelled:
                self.events.put({'type': 'cancelled', 'cleaned': staging is None or not staging.exists()})
            self.events.put({'type': 'idle'})
