param([switch]$Force, [ValidateSet('Build','Package')][string]$Phase='Build')
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
function Invoke-Checked([scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Build command failed with exit code $LASTEXITCODE" }
}
function Expand-SourceArchive([string]$Archive, [string]$Destination) {
    $rosavio7Zip=(Get-Command 7z.exe -ErrorAction Stop).Source
    $rosavioExtractor=Start-Process -FilePath $rosavio7Zip -ArgumentList @('x',$Archive,"-o$Destination",'-y','-bd','-bso0') -PassThru -NoNewWindow
    if (-not $rosavioExtractor.WaitForExit(900000)) {
        Stop-Process -Id $rosavioExtractor.Id -Force
        throw "Source extraction exceeded 15 minutes: $Archive"
    }
    if ($rosavioExtractor.ExitCode -ne 0) { throw "7-Zip source extraction failed: $Archive (exit $($rosavioExtractor.ExitCode))" }
}
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:GITHUB_REPOSITORY -ne 'aheinen1971-cmd/rosavio') { throw 'Run only on the Rosavio GitHub runner' }
$rosavioProject = (Get-Location).Path.Replace('\','/')
$rosavioRoot = 'D:/rv'
if ($Phase -eq 'Build') {
Write-Output 'Phase: check official Firefox release and previous Rosavio release'
$rosavioVersions = Invoke-RestMethod 'https://product-details.mozilla.org/1.0/firefox_versions.json' -TimeoutSec 60
$rosavioVersion = $rosavioVersions.LATEST_FIREFOX_VERSION
if ($rosavioVersion -notmatch '^\d+\.\d+(\.\d+)?$') { throw 'Invalid stable version' }
$rosavioPublished = Invoke-RestMethod 'https://api.github.com/repos/aheinen1971-cmd/rosavio/releases/latest' -TimeoutSec 60
$rosavioFeedResponse = Invoke-WebRequest 'https://github.com/aheinen1971-cmd/rosavio/releases/latest/download/rosavio-win64-update.xml' -TimeoutSec 60
$rosavioFeedText = if ($rosavioFeedResponse.Content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($rosavioFeedResponse.Content) } else { $rosavioFeedResponse.Content }
[xml]$rosavioFeed = $rosavioFeedText
$rosavioPreviousVersion = [string]$rosavioFeed.updates.update.appVersion
if (-not $Force -and [version]$rosavioVersion -le [version]$rosavioPreviousVersion) {
    'No new stable Firefox version.' | Out-File $env:GITHUB_STEP_SUMMARY -Append
    'built=false' | Out-File $env:GITHUB_OUTPUT -Append
    exit 0
}
$rosavioRoot = 'D:/rv'
New-Item -ItemType Directory -Path $rosavioRoot -Force | Out-Null
if ((Get-PSDrive D).Free -lt 40GB) { throw 'Not enough disk space for Firefox' }
$rosavioBase = "https://archive.mozilla.org/pub/firefox/releases/$rosavioVersion"
$rosavioManifest = (Invoke-WebRequest "$rosavioBase/SHA512SUMS" -TimeoutSec 60).Content
if ($rosavioManifest -is [byte[]]) { $rosavioManifest = [Text.Encoding]::UTF8.GetString($rosavioManifest) }
$rosavioSourceName = "source/firefox-$rosavioVersion.source.tar.xz"
$rosavioMatch = [regex]::Match($rosavioManifest, '(?m)^([a-fA-F0-9]{128})\s+\*?' + [regex]::Escape($rosavioSourceName) + '\r?$')
if (-not $rosavioMatch.Success) { throw 'Source SHA-512 missing from official Mozilla manifest' }
$rosavioArchive = "$rosavioRoot/source.tar.xz"
Write-Output "Phase: download Firefox $rosavioVersion source (15 minute limit per attempt)"
Invoke-Checked { curl.exe --fail --location --retry 2 --connect-timeout 30 --max-time 900 --output $rosavioArchive "$rosavioBase/$rosavioSourceName" }
Write-Output 'Phase: verify SHA-512 and extract source'
if ((Get-FileHash $rosavioArchive -Algorithm SHA512).Hash -ne $rosavioMatch.Groups[1].Value) { throw 'Mozilla source checksum mismatch' }
Write-Output 'Phase: decompress XZ using 7-Zip (15 minute limit)'
Expand-SourceArchive $rosavioArchive $rosavioRoot
Write-Output 'Phase: extract TAR using 7-Zip (15 minute limit)'
Expand-SourceArchive "$rosavioRoot/source.tar" $rosavioRoot
$rosavioSource = "$rosavioRoot/firefox-$rosavioVersion"
if (-not (Test-Path "$rosavioSource/mach")) { throw 'Unexpected Mozilla archive layout' }
$rosavioInstaller = "$rosavioRoot/mozillabuild.exe"
Write-Output 'Phase: download and verify MozillaBuild installer'
Invoke-Checked { curl.exe --fail --location --retry 2 --connect-timeout 30 --max-time 300 --output $rosavioInstaller 'https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuildSetup-4.2.1.exe' }
if ((Get-AuthenticodeSignature $rosavioInstaller).Status -ne 'Valid') { throw 'MozillaBuild installer signature invalid' }
Write-Output 'Phase: install MozillaBuild (10 minute limit)'
$rosavioSetup = Start-Process -FilePath $rosavioInstaller -ArgumentList '/S' -PassThru -WindowStyle Hidden
if (-not $rosavioSetup.WaitForExit(600000)) { Stop-Process -Id $rosavioSetup.Id -Force; throw 'MozillaBuild installer timed out' }
if ($rosavioSetup.ExitCode -ne 0) { throw 'MozillaBuild installation failed' }
$env:MOZILLABUILD = 'C:\mozilla-build\'
$env:CHERE_INVOKING = '1'
$env:MOZBUILD_STATE_PATH = "$rosavioRoot/state"
$env:MOZ_BUILD_DATE = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss')
$env:MOZCONFIG = "$rosavioSource/mozconfig"
$env:MOZ_NOSPAM = '1'
$env:MACH_HIDE_DEV_DRIVE_SUGGESTION = '1'
$env:PYTHONUNBUFFERED = '1'
$env:ROSAVIO_SOURCE = $rosavioSource
$env:ROSAVIO_PROJECT = $rosavioProject
$rosavioPython = 'C:/mozilla-build/python3/python3.exe'
Invoke-Checked { & $rosavioPython -m pip install -r "$rosavioProject/requirements.txt" }
$rosavioConfig = Get-Content "$rosavioProject/rosavio.config.json" -Raw | ConvertFrom-Json
$rosavioConfig.upstreamVersion = $rosavioVersion
$rosavioConfig.hosting.repository = 'aheinen1971-cmd/rosavio'
$rosavioConfig | ConvertTo-Json -Depth 8 | Set-Content "$rosavioProject/rosavio.config.json" -Encoding utf8NoBOM
@{version=$rosavioVersion;url="$rosavioBase/$rosavioSourceName";sha512=$rosavioMatch.Groups[1].Value;verified=$true} | ConvertTo-Json | Set-Content "$rosavioProject/upstream.json" -Encoding utf8NoBOM
Invoke-Checked { & $rosavioPython "$rosavioProject/scripts/prepare-source.py" $rosavioSource --github-repo aheinen1971-cmd/rosavio }
$rosavioMozconfig = [IO.File]::ReadAllText("$rosavioSource/mozconfig").Replace('MOZ_MAKE_FLAGS=-j8','MOZ_MAKE_FLAGS=-j3')
$rosavioMozconfig += "ac_add_options --disable-debug-symbols`nac_add_options --enable-bootstrap`n"
[IO.File]::WriteAllText("$rosavioSource/mozconfig",$rosavioMozconfig,[Text.UTF8Encoding]::new($false))
Invoke-Checked { git -C $rosavioSource init --quiet }
Write-Output 'Phase: index source files for Mozilla toolchain resource hashing'
Invoke-Checked { git -C $rosavioSource -c core.autocrlf=false -c core.longpaths=true add --all }
Invoke-Checked { git -C $rosavioSource -c user.name=Rosavio -c user.email=build@rosavio.invalid commit -m 'Verified Mozilla source archive with Rosavio overlay' --quiet }
$rosavioL10nRevision = (Get-Content "$rosavioSource/browser/locales/l10n-changesets.json" -Raw | ConvertFrom-Json).de.revision
Invoke-Checked { git clone --filter=blob:none --no-checkout https://github.com/mozilla-l10n/firefox-l10n "$rosavioRoot/l10n" }
Invoke-Checked { git -C "$rosavioRoot/l10n" sparse-checkout set de fr es-ES nl }
Invoke-Checked { git -C "$rosavioRoot/l10n" checkout --detach $rosavioL10nRevision }
Invoke-Checked { & $rosavioPython "$rosavioProject/scripts/prepare-german.py" $rosavioSource "$rosavioRoot/l10n" }
Invoke-Checked { & $rosavioPython "$rosavioProject/scripts/prepare-multilocale.py" $rosavioSource "$rosavioRoot/l10n" }
$rosavioBash = 'C:/mozilla-build/msys2/usr/bin/bash.exe'
Write-Output 'Phase: bootstrap compiler and build dependencies'
Invoke-Checked { rustup update stable --no-self-update }
Invoke-Checked { rustup default stable }
$env:RUSTC=(Get-Command rustc.exe -ErrorAction Stop).Source.Replace('\','/')
$env:CARGO=(Get-Command cargo.exe -ErrorAction Stop).Source.Replace('\','/')
Invoke-Checked { & $rosavioBash -lc 'cd "$ROSAVIO_SOURCE" && ./mach --no-interactive bootstrap --application-choice browser --no-system-changes' }
Write-Output 'Phase: configure with explicit Mozilla toolchain bootstrap'
Invoke-Checked { & $rosavioBash -lc 'cd "$ROSAVIO_SOURCE" && ./mach --no-interactive configure' }
Write-Output 'Phase: compile native Rosavio'
Invoke-Checked { & $rosavioBash -lc 'cd "$ROSAVIO_SOURCE" && ./mach --no-interactive build' }
Invoke-Checked { & $rosavioBash -lc 'cd "$ROSAVIO_SOURCE" && ./mach --no-interactive package && ./mach --no-interactive package-multi-locale --locales de fr es-ES nl && ./mach --no-interactive build installer' }
@{version=$rosavioVersion;source=$rosavioSource;previous=$rosavioPublished;buildID=$env:MOZ_BUILD_DATE} | ConvertTo-Json -Depth 20 | Set-Content "$rosavioRoot/build-state.json" -Encoding utf8NoBOM
'built=true' | Out-File $env:GITHUB_OUTPUT -Append
exit 0
}
$rosavioState = Get-Content "$rosavioRoot/build-state.json" -Raw | ConvertFrom-Json
$rosavioVersion = $rosavioState.version
$rosavioSource = $rosavioState.source
$rosavioPublished = $rosavioState.previous
$env:MOZILLABUILD = 'C:\mozilla-build\'
$env:CHERE_INVOKING = '1'
$env:MOZBUILD_STATE_PATH = "$rosavioRoot/state"
$env:ROSAVIO_SOURCE = $rosavioSource
$env:ROSAVIO_PROJECT = $rosavioProject
$rosavioBash = 'C:/mozilla-build/msys2/usr/bin/bash.exe'
$rosavioPython = 'C:/mozilla-build/python3/python3.exe'
$rosavioReleaseDir = "$rosavioRoot/release"
New-Item -ItemType Directory -Path $rosavioReleaseDir -Force | Out-Null
$rosavioPackage = "$rosavioSource/obj-rose/dist/rosavio"
$env:ROSAVIO_PACKAGE_DIR = $rosavioPackage
$env:ROSAVIO_LOCALE = 'de'
$env:ROSAVIO_EXPECT_LOCALE = 'de'
$env:ROSAVIO_PYTHON = $rosavioPython
$env:ROSAVIO_NODE = (Get-Command node).Source.Replace('\','/')
$env:ROSAVIO_RELEASE_DIR = $rosavioReleaseDir
Invoke-Checked { node "$rosavioProject/scripts/check-locales.cjs" "$rosavioPackage/rosavio.exe" "$rosavioReleaseDir/locale-check" }
Invoke-Checked { node --test "$rosavioProject/tests/*.test.mjs" }
Invoke-Checked { & $rosavioPython "$rosavioProject/tests/test_signing.py" }
if (-not $env:ROSAVIO_UPDATE_KEY -or -not $env:ROSAVIO_SIGNING_PASSWORD) { throw 'Signing secrets missing' }
$rosavioKeyPath = "$rosavioRoot/update-key.pem"
[IO.File]::WriteAllText($rosavioKeyPath,$env:ROSAVIO_UPDATE_KEY)
Remove-Item Env:ROSAVIO_UPDATE_KEY
$env:ROSAVIO_KEY_PATH = $rosavioKeyPath
try {
    Invoke-Checked { & $rosavioBash -lc 'bash "$ROSAVIO_PROJECT/scripts/package-update.sh" "$ROSAVIO_SOURCE" "$ROSAVIO_RELEASE_DIR" "$ROSAVIO_KEY_PATH"' }
} finally {
    Remove-Item -LiteralPath $rosavioKeyPath -ErrorAction SilentlyContinue
    Remove-Item Env:ROSAVIO_SIGNING_PASSWORD -ErrorAction SilentlyContinue
}
$rosavioTag = "v$rosavioVersion-rosavio.$env:GITHUB_RUN_ID"
Invoke-Checked { node "$rosavioProject/scripts/write-github-feed.mjs" aheinen1971-cmd/rosavio $rosavioTag $rosavioReleaseDir }
$rosavioInstallerOutput = @(Get-ChildItem "$rosavioSource/obj-rose/dist" -Filter '*.win64.installer.exe')
if ($rosavioInstallerOutput.Count -ne 1) { throw 'Expected exactly one German installer' }
Copy-Item $rosavioInstallerOutput[0].FullName "$rosavioReleaseDir/Rosavio-Setup-Deutsch.exe"
Invoke-Checked { tar -a -cf "$rosavioReleaseDir/Rosavio-Deutsch-Windows.zip" -C (Split-Path $rosavioPackage -Parent) rosavio }
$rosavioPreviousZip = @($rosavioPublished.assets | Where-Object name -eq 'Rosavio-Deutsch-Windows.zip')
if ($rosavioPreviousZip.Count -ne 1) { throw 'Previous release package missing' }
Invoke-WebRequest $rosavioPreviousZip[0].browser_download_url -OutFile "$rosavioRoot/previous.zip"
Invoke-Checked { tar -xf "$rosavioRoot/previous.zip" -C $rosavioRoot }
$env:ROSAVIO_PREVIOUS_BINARY = "$rosavioRoot/rosavio/rosavio.exe"
Invoke-Checked { node "$rosavioProject/scripts/cloud-update-test.cjs" }
$rosavioSourceExport="$rosavioRoot/source-project"
New-Item -ItemType Directory -Path $rosavioSourceExport -Force | Out-Null
$rosavioTrackedFiles=@(git -C $rosavioProject ls-files)
if ($LASTEXITCODE -ne 0) { throw 'Cannot enumerate public project sources' }
foreach($rosavioTrackedFile in $rosavioTrackedFiles) {
    if($rosavioTrackedFile -match '(^|/)(\.\.|\.git)(/|$)' -or [IO.Path]::IsPathRooted($rosavioTrackedFile)) { throw 'Unsafe source export path' }
    $rosavioExportFile=Join-Path $rosavioSourceExport $rosavioTrackedFile
    New-Item -ItemType Directory -Path (Split-Path $rosavioExportFile -Parent) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $rosavioProject $rosavioTrackedFile) -Destination $rosavioExportFile
}
@{locale='de';repository='https://github.com/mozilla-l10n/firefox-l10n';revision=(Get-Content "$rosavioSource/browser/locales/l10n-changesets.json" -Raw | ConvertFrom-Json).de.revision;upstreamVersion=$rosavioVersion;branding='Rosavio';packaging='native-single-locale-repack'} | ConvertTo-Json | Set-Content "$rosavioSourceExport/localization.json" -Encoding utf8NoBOM
Invoke-Checked { tar -a -cf "$rosavioReleaseDir/Rosavio-Browser-Quellprojekt.zip" -C $rosavioSourceExport . }
Get-ChildItem $rosavioReleaseDir -File | Where-Object Extension -in '.exe','.zip','.mar' | Where-Object Name -notlike '*.unsigned.mar' | ForEach-Object { $rosavioHash=Get-FileHash $_.FullName -Algorithm SHA256; "$($rosavioHash.Hash.ToLower())  $($_.Name)" } | Set-Content "$rosavioReleaseDir/Rosavio-SHA256SUMS.txt"
"built=true`ntag=$rosavioTag`nreleaseDir=$rosavioReleaseDir" | Out-File $env:GITHUB_OUTPUT -Append
'Native build, signing, German startup and local update tests passed.' | Out-File $env:GITHUB_STEP_SUMMARY -Append


