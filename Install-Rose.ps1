param([Parameter(Mandatory=$true)][string]$PackageDirectory)
$ErrorActionPreference = 'Stop'
$rosePackage = (Resolve-Path -LiteralPath $PackageDirectory).Path
if (!(Test-Path -LiteralPath (Join-Path $rosePackage 'rose.exe'))) { throw 'Das kompilierte Rose-Paket mit rose.exe fehlt.' }
$roseIni = [System.IO.File]::ReadAllText((Join-Path $rosePackage 'application.ini'))
if ($roseIni -notmatch '(?m)^Name=Rose\s*$') { throw 'Dieses Paket ist kein eigenstaendiger Rose-Build.' }
$roseInstallDir = Join-Path $env:LOCALAPPDATA 'Programs\Rose'
if (Test-Path -LiteralPath (Join-Path $roseInstallDir 'rose.exe')) { throw 'Rose ist bereits installiert. Fuer Aktualisierungen den signierten Updater verwenden.' }
New-Item -ItemType Directory -Force -Path $roseInstallDir | Out-Null
Get-ChildItem -LiteralPath $rosePackage -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $roseInstallDir -Recurse -Force }
$roseMenu = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Microsoft\Windows\Start Menu\Programs'
$roseShell = New-Object -ComObject WScript.Shell
$roseShortcut = $roseShell.CreateShortcut((Join-Path $roseMenu 'Rose.lnk'))
$roseShortcut.TargetPath = Join-Path $roseInstallDir 'rose.exe'
$roseShortcut.WorkingDirectory = $roseInstallDir
$roseShortcut.IconLocation = (Join-Path $roseInstallDir 'rose.exe') + ',0'
$roseShortcut.Description = 'Rose Browser'
$roseShortcut.Save()
Write-Output 'Rose wurde fuer dein Windows-Benutzerkonto installiert.'
