"""Write the already-compressed upstream MAR inputs without an argv size limit."""
import argparse
from pathlib import Path, PurePosixPath
import os
import re
from mardor.writer import MarWriter


def write(work, listing, version, channel):
    work = Path(work).resolve()
    if channel != 'rosavio-release' or not re.fullmatch(r'\d+(?:\.\d+){0,3}', version):
        raise ValueError('Invalid update identity')
    raw = Path(listing).read_bytes()
    if not raw.endswith(b'\0'):
        raise ValueError('Unterminated MAR file list')
    names = [x.decode('utf-8') for x in raw[:-1].split(b'\0')]
    if len(names) != len(set(names)) or 'updatev3.manifest' not in names:
        raise ValueError('Duplicate entries or missing update manifest')
    for name in names:
        path = PurePosixPath(name)
        source = work / name
        if (not name or path.is_absolute() or '..' in path.parts or ':' in name
                or '\\' in name or not source.resolve().is_relative_to(work)
                or source.is_symlink() or not source.is_file()
                or name in ('output.mar', 'output.mar.tmp')):
            raise ValueError('Unsafe or missing MAR input: ' + name)
    temporary = work / 'output.mar.tmp'
    try:
        with temporary.open('w+b') as output:
            with MarWriter(output, productversion=version, channel=channel) as writer:
                for name in names:
                    source = work / name
                    with source.open('rb') as stream:
                        writer.add_stream(iter(lambda: stream.read(1024*1024), b''),
                                          name, compress=None, flags=source.stat().st_mode & 0o777)
        os.replace(temporary, work / 'output.mar')
    finally:
        temporary.unlink(missing_ok=True)


def patch(source):
    path = Path(source) / 'tools/update-packaging/make_full_update.sh'
    text = path.read_text(encoding='utf-8')
    marker = 'eval "$mar_command $targetfiles"'
    replacement = '''# Rosavio: shell builtin writes filenames without the Windows argv limit.
if [[ -n "${ROSAVIO_MAR_WRITER:-}" ]]; then
  eval "printf '%s\\\\0' $targetfiles" > "$workdir/rosavio-mar-files"
  "${ROSAVIO_PYTHON:-python3}" "$ROSAVIO_MAR_WRITER" "$workdir" "$workdir/rosavio-mar-files" "$MOZ_PRODUCT_VERSION" "$MAR_CHANNEL_ID" || exit 1
else
  eval "$mar_command $targetfiles"
fi'''
    if replacement in text:
        return
    if text.count(marker) != 1:
        raise ValueError('Upstream MAR invocation changed')
    path.write_text(text.replace(marker, replacement), encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--patch', metavar='SOURCE')
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    if args.patch and not args.arguments:
        patch(args.patch)
    elif not args.patch and len(args.arguments) == 4:
        write(*args.arguments)
    else:
        parser.error('Expected workdir, file list, version and channel')
