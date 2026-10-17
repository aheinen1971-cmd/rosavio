$ErrorActionPreference = 'Stop'
$rosavioVersions = Invoke-RestMethod -Uri 'https://product-details.mozilla.org/1.0/firefox_versions.json'
$rosavioLatest = $rosavioVersions.LATEST_FIREFOX_VERSION
if ($rosavioLatest -notmatch '^\d+\.\d+(\.\d+)?$') { throw 'Invalid stable Firefox version' }
$rosavioFeed = Invoke-WebRequest -Uri 'https://github.com/aheinen1971-cmd/rosavio/releases/latest/download/rosavio-win64-update.xml'
$rosavioFeedText = if ($rosavioFeed.Content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($rosavioFeed.Content) } else { $rosavioFeed.Content }
[xml]$rosavioUpdate = $rosavioFeedText
$rosavioCurrent = [string]$rosavioUpdate.updates.update.appVersion
if ($rosavioCurrent -notmatch '^\d+\.\d+(\.\d+)?$') { throw 'Invalid published Rosavio version' }
$rosavioVolumes = @(Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -gt 0 } | ForEach-Object {
    @{ drive = $_.Name; freeGB = [math]::Round($_.Free / 1GB, 1) }
})
$rosavioReport = [ordered]@{
    checkedAt = [DateTime]::UtcNow.ToString('o')
    firefoxVersion = $rosavioLatest
    rosavioVersion = $rosavioCurrent
    updateAvailable = ([version]$rosavioLatest -gt [version]$rosavioCurrent)
    processorCount = [Environment]::ProcessorCount
    memoryGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
    disks = $rosavioVolumes
    sufficientInitialDisk = (@($rosavioVolumes | Where-Object { $_.freeGB -ge 40 }).Count -gt 0)
    signingSecretPresent = ($env:ROSAVIO_SIGNING_CONFIGURED -eq 'true')
    buildAndPublishEnabled = $false
}
$rosavioReport | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'cloud-readiness.json' -Encoding utf8
$rosavioSummary = @"
## Rosavio cloud readiness

Firefox: $rosavioLatest; published Rosavio: $rosavioCurrent.
New stable version: $($rosavioReport.updateAvailable).
CPU: $($rosavioReport.processorCount); RAM: $($rosavioReport.memoryGB) GB.
Disk: $($rosavioVolumes | ConvertTo-Json -Compress).
At least 40 GB free: $($rosavioReport.sufficientInitialDisk).
Signing configured: $($rosavioReport.signingSecretPresent).

This workflow checks releases and build capacity only. Automatic build and publication are not enabled yet.
"@
$rosavioSummary | Out-File -LiteralPath $env:GITHUB_STEP_SUMMARY -Append -Encoding utf8
Write-Output $rosavioSummary
