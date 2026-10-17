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
package="${ROSAVIO_PACKAGE_DIR:-$source_dir/obj-rose/dist/rosavio}"
locale="${ROSAVIO_LOCALE:-en-US}"
[[ "$locale" == de || "$locale" == en-US ]] || { echo 'Unsupported locale' >&2; exit 1; }
build_id="$(sed -n 's/^BuildID=//p' "$package/application.ini" | tr -d '\r\n')"
[[ "$build_id" =~ ^[0-9]{14}$ ]] || { echo 'Invalid build ID' >&2; exit 1; }
signmar="$source_dir/obj-rose/dist/bin/signmar.exe"
mar="$source_dir/obj-rose/dist/host/bin/mar.exe"
test -f "$package/rosavio.exe"
test -f "$package/precomplete"
test -f "$signmar"
test -f "$mar"
ROSAVIO_EXPECT_LOCALE="$locale" "${ROSAVIO_NODE:-node}" "$project/scripts/check-native.cjs" "$package/rosavio.exe" "$release_dir/native-check"
"${ROSAVIO_NODE:-node}" "$project/scripts/check-package-identity.mjs" "$package/application.ini" "$release_dir/native-check/report.json" "$locale"
unsigned="$release_dir/rosavio-$version-$build_id-$locale.unsigned.mar"
signed="$release_dir/rosavio-$version-$build_id-$locale.complete.mar"
MAR="$mar" MOZ_PRODUCT_VERSION="$version" MAR_CHANNEL_ID=rosavio-release \
  bash tools/update-packaging/make_full_update.sh "$unsigned" "$package" rosavio
"${ROSAVIO_PYTHON:-python3}" "$project/scripts/sign-mar.py" "$unsigned" "$signed" "$private_key" "$project/certificates/rosavio-update.der"
"$signmar" -D "$project/certificates/rosavio-update.der" -v "$signed"
"${ROSAVIO_NODE:-node}" "$project/scripts/publish-release.mjs" "$signed" "$package/application.ini" "$signmar" "$project/certificates/rosavio-update.der" "$locale" "$release_dir/native-check/report.json"
echo 'Signed MAR and release.json are ready in the release directory.'
