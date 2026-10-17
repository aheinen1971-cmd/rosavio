$ErrorActionPreference='Stop'
if ($env:GITHUB_REPOSITORY -ne 'aheinen1971-cmd/rosavio') { throw 'Wrong repository' }
$rosavioRoot='D:/rv'
$rosavioReleaseDir="$rosavioRoot/release"
$rosavioState=Get-Content "$rosavioRoot/build-state.json" -Raw | ConvertFrom-Json
$rosavioLocalTest=Get-Content "$rosavioReleaseDir/local-update-test.json" -Raw | ConvertFrom-Json
if ($rosavioLocalTest.passed -ne $true) { throw 'Native local update test required' }
$rosavioTag="v$($rosavioState.version)-rosavio.$env:GITHUB_RUN_ID"
$rosavioAssets=@(Get-ChildItem $rosavioReleaseDir -File | Where-Object { $_.Name -notlike '*.unsigned.mar' -and ($_.Extension -in '.exe','.zip','.mar','.xml','.txt' -or $_.Name -eq 'local-update-test.json') } | ForEach-Object FullName)
gh release create $rosavioTag @rosavioAssets --repo aheinen1971-cmd/rosavio --title "Rosavio $($rosavioState.version) – Deutsch" --notes 'Auf offizieller Firefox-Quelle gebaut. Deutsche Oberfläche, eigene signierte Updates. Nativer Start- und Update-Test vor Veröffentlichung bestanden.' --draft --target $env:GITHUB_SHA
if ($LASTEXITCODE -ne 0) { throw 'Draft release failed' }
gh release edit $rosavioTag --repo aheinen1971-cmd/rosavio --draft=false --latest
if ($LASTEXITCODE -ne 0) { throw 'Release publication failed' }
$env:ROSAVIO_RELEASE_DIR=$rosavioReleaseDir
$env:ROSAVIO_SOURCE=$rosavioState.source
$env:ROSAVIO_PREVIOUS_BINARY="$rosavioRoot/rosavio/rosavio.exe"
$env:ROSAVIO_PUBLIC_TEST='1'
try {
    node scripts/cloud-update-test.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Public native update test failed' }
    gh release upload $rosavioTag "$rosavioReleaseDir/public-update-test.json" --repo aheinen1971-cmd/rosavio
    if ($LASTEXITCODE -ne 0) { throw 'Public test report upload failed' }
} catch {
    gh release edit $rosavioState.previous.tag_name --latest --repo aheinen1971-cmd/rosavio
    gh release edit $rosavioTag --prerelease --repo aheinen1971-cmd/rosavio
    throw
}
"## Rosavio $($rosavioState.version) published and public native update test passed.`nhttps://github.com/aheinen1971-cmd/rosavio/releases/tag/$rosavioTag" | Out-File $env:GITHUB_STEP_SUMMARY -Append
