"""Require unchanged qualified helper bytes and a working packaged host."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
package=Path(sys.argv[1])/'video-finder'
inventory=json.loads((root/'build/video-finder/bundle.json').read_text(encoding='utf8'))
for name,digest in inventory['files'].items():
    path=package/name
    with path.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
            raise ValueError('Packaging changed qualified helper file: '+name)
subprocess.run([sys.executable,root/'tests/check_video_finder_bundle.py',package],check=True)
print('Packaged helper: every qualified file unchanged; native protocol and remux passed.')
