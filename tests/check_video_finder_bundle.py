"""Executable smoke test with private fixtures; no network or browser profiles."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

bundle=Path(sys.argv[1]).resolve()
suffix='.exe' if sys.platform=='win32' else ''
binary=bundle/('video-finder-host'+suffix)
request=json.dumps({'action':'inspect','url':'https://example.org/not-youtube'}).encode()
result=subprocess.run([binary,'manifest.json','medien@rosavio.local'],input=struct.pack('<I',len(request))+request,capture_output=True,timeout=30)
if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace'))
messages=[]; data=result.stdout
while data:
    if len(data)<4: raise ValueError('truncated host reply')
    length,=struct.unpack('<I',data[:4]);payload=data[4:4+length];data=data[4+length:]
    messages.append(json.loads(payload))
assert any(x.get('type')=='ready' for x in messages),messages
assert any(x.get('code')=='youtubeRequestRejected' for x in messages),messages
foreign=subprocess.run([binary,'manifest.json','wrong@example.org'],capture_output=True,timeout=10)
assert foreign.returncode!=0 and not foreign.stdout
fixtures=Path(__file__).parent/'fixtures/video-finder'
with tempfile.TemporaryDirectory() as folder:
    output=Path(folder)/'combined.mkv'
    subprocess.run([bundle/('ffmpeg'+suffix),'-v','error','-i',fixtures/'video.mp4','-i',fixtures/'audio.m4a','-map','0:v:0','-map','1:a:0','-c','copy',output],check=True,timeout=30)
    probe=subprocess.run([bundle/('ffprobe'+suffix),'-v','error','-show_streams','-of','json',output],capture_output=True,text=True,check=True,timeout=30)
    streams=json.loads(probe.stdout)['streams']
    assert {x['codec_type'] for x in streams}=={'video','audio'},streams
print('Native framing, rejected foreign caller, remux and audio/video inspection passed.')

# YouTube HLS video fragments are MPEG-TS even when yt-dlp names them .mp4.
# Exercise the real container, not just the extension or capability listing.
with tempfile.TemporaryDirectory() as folder:
    output=Path(folder)/'hls-combined.mkv'
    subprocess.run([bundle/('ffmpeg'+suffix),'-v','error','-i',fixtures/'video.ts','-i',fixtures/'audio.m4a','-map','0:v:0','-map','1:a:0','-c','copy',output],check=True,timeout=30)
    probe=subprocess.run([bundle/('ffprobe'+suffix),'-v','error','-show_streams','-of','json',output],capture_output=True,text=True,check=True,timeout=30)
    streams=json.loads(probe.stdout)['streams']
    assert {x['codec_type'] for x in streams}=={'video','audio'},streams
print('MPEG-TS/HLS video and separate audio remux passed.')
