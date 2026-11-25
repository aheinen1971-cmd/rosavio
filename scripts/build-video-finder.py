"""Build an isolated, self-contained helper; never publishes or builds the browser."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'native/toolchain.json').read_text())
FFMPEG_FLAGS=['--disable-autodetect','--disable-network','--disable-x86asm',
 '--disable-debug','--disable-doc','--disable-everything','--enable-ffmpeg','--enable-ffprobe',
 '--enable-protocol=file,pipe','--enable-demuxer=mov,matroska,aac,mp3,ogg',
 '--enable-muxer=matroska,mp4','--enable-parser=aac,h264,hevc,av1,vp9,opus',
 '--enable-bsf=aac_adtstoasc,extract_extradata,h264_mp4toannexb,hevc_mp4toannexb',
 '--enable-static','--disable-shared']

def run(*args,cwd=None,env=None):
    subprocess.run([str(a) for a in args],cwd=cwd,env=env,check=True)

def fetch(item,path):
    if not path.exists():
        with urllib.request.urlopen(item['url'],timeout=120) as src,path.open('wb') as dst:
            shutil.copyfileobj(src,dst)
    with path.open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=item['sha256']:
            raise ValueError('Dependency checksum mismatch: '+path.name)

def build(output):
    platform='win64' if sys.platform=='win32' else 'linux-x64'
    suffix='.exe' if platform=='win64' else ''
    work=ROOT/'build/video-finder-work'
    work.mkdir(parents=True,exist_ok=True)
    if output.exists():
        raise ValueError('Output already exists; refusing to overwrite a qualified helper')
    node_archive=work/('node.zip' if suffix else 'node.tar.xz')
    fetch(CONFIG['node'][platform],node_archive)
    node_dir=work/'node'
    node_dir.mkdir(exist_ok=True)
    if suffix:
        with zipfile.ZipFile(node_archive) as z:
            for name in z.namelist():
                if not (node_dir/name).resolve().is_relative_to(node_dir.resolve()): raise ValueError('Unsafe node archive')
            z.extractall(node_dir)
    else:
        with tarfile.open(node_archive) as t: t.extractall(node_dir,filter='data')
    ff_archive=work/'ffmpeg-source.tar.xz'
    fetch(CONFIG['ffmpeg'],ff_archive)
    ff_dir=work/'ffmpeg'
    ff_dir.mkdir(exist_ok=True)
    with tarfile.open(ff_archive) as t: t.extractall(ff_dir,filter='data')
    ff_source=next(ff_dir.glob('ffmpeg-*'))
    environment=os.environ.copy()
    if suffix:
        # Standard free Windows runner's MSYS2/MinGW. No administrator installation.
        compiler=shutil.which('gcc')
        mingw=Path(compiler).parent if compiler else Path('C:/msys64/mingw64/bin')
        bash=Path('C:/msys64/usr/bin/bash.exe')
        if not (mingw/'gcc.exe').exists():
            raise ValueError('Free runner lacks the MinGW compiler; no browser build started')
        make=Path('C:/msys64/usr/bin/make.exe')
        if not make.exists():
            # Install only the build tool on the disposable runner, retaining package signatures.
            run('C:/msys64/usr/bin/pacman.exe','-S','--noconfirm','--needed','make')
        environment['PATH']=str(mingw)+os.pathsep+'C:/msys64/usr/bin'+os.pathsep+environment['PATH']
        run(bash,'./configure',*FFMPEG_FLAGS,'--target-os=mingw32','--extra-ldflags=-static',cwd=ff_source,env=environment)
        run(make,'-j2',cwd=ff_source,env=environment)
    else:
        run('bash','./configure',*FFMPEG_FLAGS,cwd=ff_source,env=environment)
        run('make','-j2',cwd=ff_source,env=environment)
    venv=work/'venv'
    if not venv.exists(): run(sys.executable,'-m','venv',venv)
    python=venv/('Scripts/python.exe' if suffix else 'bin/python')
    run(python,'-m','pip','install','--only-binary=:all:','--report',work/'python-dependencies.json',
        'pyinstaller==6.17.0','yt-dlp[default]=='+CONFIG['ytDlp'])
    run(python,'-m','PyInstaller','--noconfirm','--clean','--onedir','--name','video-finder-host',
        '--collect-all','yt_dlp','--collect-all','yt_dlp_ejs','--hidden-import','worker',
        '--paths',ROOT/'native/video_finder','--distpath',work/'dist','--workpath',work/'pyinstaller',
        '--specpath',work,ROOT/'native/video_finder/host.py')
    shutil.copytree(work/'dist/video-finder-host',output)
    node_roots=[p for p in node_dir.iterdir() if p.is_dir() and p.name.startswith('node-v')]
    if len(node_roots)!=1: raise ValueError('Ambiguous Node archive root')
    node_binary=node_roots[0]/('node.exe' if suffix else 'bin/node')
    if not node_binary.is_file(): raise ValueError('Node executable missing')
    shutil.copy2(node_binary,output/('node'+suffix))
    for name in ('ffmpeg','ffprobe'): shutil.copy2(ff_source/(name+suffix),output/(name+suffix))
    licenses=output/'licenses'
    licenses.mkdir()
    for name in ('COPYING.LGPLv2.1','LICENSE.md'):
        shutil.copy2(ff_source/name,licenses/('ffmpeg-'+name))
    node_license=node_roots[0]/'LICENSE'
    shutil.copy2(node_license,licenses/'node-LICENSE.txt')
    python_license=Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.exists(): python_license=Path(sys.base_prefix)/'LICENSE'
    if python_license.exists(): shutil.copy2(python_license,licenses/'Python-LICENSE.txt')
    for info in venv.rglob('*.dist-info'):
        for path in info.rglob('*'):
            if path.is_file() and any(x in path.name.lower() for x in ('license','copying','notice')):
                dest=licenses/info.name/path.relative_to(info)
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,dest)
    source=output/'source'
    source.mkdir()
    shutil.copy2(ff_archive,source/'ffmpeg-9.1.tar.xz')
    shutil.copytree(ROOT/'native/video_finder',source/'video_finder',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(__file__,source/'build-video-finder.py')
    shutil.copy2(ROOT/'native/toolchain.json',source/'toolchain.json')
    (source/'ffmpeg-configure.json').write_text(json.dumps(FFMPEG_FLAGS,indent=2))
    shutil.copy2(work/'python-dependencies.json',source/'python-dependencies.json')
    run(output/('node'+suffix),'--version')
    run(output/('ffmpeg'+suffix),'-version')
    run(sys.executable,ROOT/'tests/check_video_finder_bundle.py',output)
    inventory={}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            with path.open('rb') as stream: inventory[path.relative_to(output).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
    (output/'bundle.json').write_text(json.dumps({'schema':1,'qualified':True,'platform':platform,'files':inventory},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'build/video-finder')
    a=p.parse_args();build(a.output.resolve())
