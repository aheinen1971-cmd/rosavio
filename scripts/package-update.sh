#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 3 ]]; then
  echo 'Usage: bash scripts/package-update.sh SOURCE RELEASE_DIR ENCRYPTED_PRIVATE_KEY' >&2
  exit 2
fi
source_dir="$(cd "$1" && pwd)"
mkdir -p "$2"
release_dir="$(cd "$2" && pwd)"
private_key="$3"
project="$(cd "$(dirname "$0")/.." && pwd)"
cd "$source_dir"
version="$(tr -d '\r\n' < browser/config/version.txt)"
package="$source_dir/obj-rose/dist/rose"
build_id="$(sed -n 's/^BuildID=//p' "$package/application.ini" | tr -d '\r\n')"
[[ "$build_id" =~ ^[0-9]{14}$ ]] || { echo 'Invalid build ID' >&2; exit 1; }
signmar="$source_dir/obj-rose/dist/bin/signmar.exe"
mar="$source_dir/obj-rose/dist/host/bin/mar.exe"
test -f "$package/rose.exe"
test -f "$package/precomplete"
test -f "$signmar"
test -f "$mar"
unsigned="$release_dir/rose-$version-$build_id.unsigned.mar"
signed="$release_dir/rose-$version-$build_id.complete.mar"
MAR="$mar" MOZ_PRODUCT_VERSION="$version" MAR_CHANNEL_ID=rose-release \
  bash tools/update-packaging/make_full_update.sh "$unsigned" "$package" rose
python3 "$project/scripts/sign-mar.py" "$unsigned" "$signed" "$private_key" "$project/certificates/rose-update.der"
"$signmar" -D "$project/certificates/rose-update.der" -v "$signed"
node "$project/scripts/publish-release.mjs" "$signed" "$package/application.ini" "$signmar" "$project/certificates/rose-update.der"
echo 'Signed MAR and release.json are ready in the release directory.'
