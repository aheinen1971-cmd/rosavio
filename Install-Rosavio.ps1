param([Parameter(Mandatory=$true)][string]$PackageDirectory)
$ErrorActionPreference = 'Stop'
$rosavioPackage = (Resolve-Path -LiteralPath $PackageDirectory).Path
if (!(Test-Path -LiteralPath (Join-Path $rosavioPackage 'rosavio.exe'))) { throw 'Das kompilierte Rosavio-Paket mit rosavio.exe fehlt.' }
$rosavioIni = [System.IO.File]::ReadAllText((Join-Path $rosavioPackage 'application.ini'))
if ($rosavioIni -notmatch '(?m)^Name=Rosavio\s*$') { throw 'Dieses Paket ist kein eigenstaendiger Rosavio-Build.' }
$rosavioInstallDir = Join-Path $env:LOCALAPPDATA 'Programs\Rosavio'
if (Test-Path -LiteralPath (Join-Path $rosavioInstallDir 'rosavio.exe')) { throw 'Rosavio ist bereits installiert. Fuer Aktualisierungen den signierten Updater verwenden.' }
New-Item -ItemType Directory -Force -Path $rosavioInstallDir | Out-Null
Get-ChildItem -LiteralPath $rosavioPackage -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $rosavioInstallDir -Recurse -Force }
$rosavioMenu = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Microsoft\Windows\Start Menu\Programs'
$rosavioShell = New-Object -ComObject WScript.Shell
$rosavioShortcut = $rosavioShell.CreateShortcut((Join-Path $rosavioMenu 'Rosavio.lnk'))
$rosavioShortcut.TargetPath = Join-Path $rosavioInstallDir 'rosavio.exe'
$rosavioShortcut.WorkingDirectory = $rosavioInstallDir
$rosavioShortcut.IconLocation = (Join-Path $rosavioInstallDir 'rosavio.exe') + ',0'
$rosavioShortcut.Description = 'Rosavio Browser'
$rosavioShortcut.Save()
Write-Output 'Rosavio wurde fuer dein Windows-Benutzerkonto installiert.'
