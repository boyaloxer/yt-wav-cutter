# User-friendly install without Inno Setup.
# Installs the portable build into %LOCALAPPDATA%\YT Media Downloader
# and creates Desktop + Start Menu shortcuts.
#
# Usage (after build_windows.ps1):
#   powershell -ExecutionPolicy Bypass -File installer\Install-User.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Source = Join-Path $Root "dist\YT Media Downloader"
$Dest = Join-Path $env:LOCALAPPDATA "YT Media Downloader"
$ExeName = "YT Media Downloader.exe"

if (-not (Test-Path (Join-Path $Source $ExeName))) {
    Write-Host "App not built yet. Run:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File build\build_windows.ps1"
    exit 1
}

Write-Host "Installing to $Dest ..."
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $Dest -Recurse -Force

$Exe = Join-Path $Dest $ExeName
$Wsh = New-Object -ComObject WScript.Shell

$Desktop = [Environment]::GetFolderPath("Desktop")
$DeskLnk = Join-Path $Desktop "YT Media Downloader.lnk"
$sc = $Wsh.CreateShortcut($DeskLnk)
$sc.TargetPath = $Exe
$sc.WorkingDirectory = $Dest
$sc.IconLocation = "$Exe,0"
$sc.Description = "Download YouTube audio/video"
$sc.Save()
Write-Host "Desktop shortcut: $DeskLnk"

$StartDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
New-Item -ItemType Directory -Force -Path $StartDir | Out-Null
$StartLnk = Join-Path $StartDir "YT Media Downloader.lnk"
$sc2 = $Wsh.CreateShortcut($StartLnk)
$sc2.TargetPath = $Exe
$sc2.WorkingDirectory = $Dest
$sc2.IconLocation = "$Exe,0"
$sc2.Save()
Write-Host "Start Menu shortcut: $StartLnk"

# Uninstall helper
$Uninstall = Join-Path $Dest "Uninstall.ps1"
@"
`$ErrorActionPreference = 'Stop'
Remove-Item -LiteralPath '$DeskLnk' -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath '$StartLnk' -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath '$Dest' -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'YT Media Downloader removed.'
"@ | Set-Content -Path $Uninstall -Encoding UTF8

Write-Host ""
Write-Host "Done. Launching..."
Start-Process -FilePath $Exe -WorkingDirectory $Dest

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Note: Node.js not found on PATH. Install LTS from https://nodejs.org/ for best YouTube support."
}
