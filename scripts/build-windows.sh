#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo 'Usage: bash scripts/build-windows.sh /c/path/to/prepared/firefox-source' >&2
  exit 2
fi
cd "$1"
test -f rosavio-build.json || { echo 'Run prepare-source.py first' >&2; exit 1; }
if grep -q -- '--enable-unverified-updates' mozconfig; then
  echo 'Refusing to build a Rosavio browser with unverified updates' >&2
  exit 1
fi
export MOZCONFIG="$PWD/mozconfig"
./mach build
./mach package
test -f obj-rose/dist/rosavio/rosavio.exe
echo 'Rosavio binary: obj-rose/dist/rosavio/rosavio.exe'
echo 'Package built. Publish only after the signed native-update integration test.'
