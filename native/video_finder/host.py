"""Length-framed native messaging, reserved for Rosavio's built-in Video Finder."""
import json
import struct
import sys
import threading
import time
from engine import Operation

MAX_MESSAGE = 4096
EXTENSION_ID = 'medien@rosavio.local'

def read_exact(stream, length):
    chunks = bytearray()
    while len(chunks) < length:
        part = stream.read(length-len(chunks))
        if not part:
            break
        chunks.extend(part)
    return bytes(chunks)

def read_message(stream):
    header = read_exact(stream, 4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError('Incomplete native header')
    length, = struct.unpack('<I', header)
    if length == 0 or length > MAX_MESSAGE:
        raise ValueError('Native message size rejected')
    payload = read_exact(stream, length)
    if len(payload) != length:
        raise ValueError('Incomplete native message')
    message = json.loads(payload)
    if not isinstance(message, dict):
        raise ValueError('Object required')
    return message

def error_code(message):
    text = str(message).lower()
    if any(x in text for x in ('sign in', 'bot', 'login', 'private', 'age-restricted')):
        return 'youtubeLogin'
    if 'requested format' in text:
        return 'youtubeQualityChanged'
    if any(x in text for x in ('unavailable', 'removed', 'not available')):
        return 'youtubeUnavailable'
    if any(x in text for x in ('connection', 'certificate', 'timed out', 'name resolution')):
        return 'youtubeNetwork'
    return 'youtubeFailed'

def serve(input_stream, output_stream, operation=None):
    operation = operation or Operation()
    lock = threading.Lock()
    active = threading.Event()
    active.set()
    def send(message):
        data = json.dumps(message, ensure_ascii=True).encode('utf-8')
        if len(data) > 512000:
            raise ValueError('Native reply too large')
        with lock:
            output_stream.write(struct.pack('<I', len(data)) + data)
            output_stream.flush()

    def pump():
        last_progress = 0
        while active.is_set() or operation.busy or not operation.events.empty():
            try:
                event = operation.events.get(timeout=.1)
            except __import__('queue').Empty:
                continue
            kind = event.get('type')
            if kind == 'log':
                continue
            if kind == 'error':
                event = {'type': 'error', 'code': error_code(event.get('message', ''))}
            if kind == 'info':
                event = {'type':'info', 'title':str(event.get('title', ''))[:500], 'choices':[
                    {'selector': x['selector'], 'height': x['height'], 'merged': '+bestaudio' in x['selector']}
                    for x in event['choices'][:100]]}
            if kind == 'progress':
                now = time.monotonic()
                if now-last_progress < .2 and event.get('phase') != 'finished':
                    continue
                last_progress = now
            try:
                send(event)
            except (BrokenPipeError, OSError):
                operation.cancel()
                return
    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    try:
        send({'type':'ready', 'version':1})
        while active.is_set():
            message = read_message(input_stream)
            if message is None:
                break
            action = message.get('action')
            if action not in ('inspect','download','cancel') or set(message)-{'action','url','selector'}:
                send({'type':'error','code':'youtubeRequestRejected'})
                continue
            try:
                if action == 'cancel':
                    operation.cancel()
                else:
                    operation.start(action, message.get('url',''), message.get('selector'))
            except (ValueError, OSError, TypeError, AttributeError):
                send({'type':'error','code':'youtubeRequestRejected'})
                if not operation.busy:
                    send({'type':'idle'})
    finally:
        active.clear()
        operation.cancel()
        thread.join(timeout=15)

def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        from worker import main as worker_main, emit
        sys.argv = [sys.argv[0], sys.argv[2]]
        try:
            worker_main()
        except Exception as exc:
            emit('error', message=str(exc))
            raise SystemExit(1)
        return
    if not sys.argv or sys.argv[-1] != EXTENSION_ID:
        raise SystemExit('Only the built-in Video Finder may connect')
    if sys.platform == 'win32':
        import msvcrt, os
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    serve(sys.stdin.buffer, sys.stdout.buffer)

if __name__ == '__main__':
    main()
