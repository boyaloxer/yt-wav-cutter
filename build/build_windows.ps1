# Build portable app folder + (optional) Inno Setup installer.
# Run:
#   powershell -ExecutionPolicy Bypass -File build\build_windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Py = "C:\Python313\python.exe"
if (-not (Test-Path $Py)) { $Py = "py" }

Write-Host "==> Installing build deps..."
& $Py -m pip install -U -r requirements.txt pyinstaller pillow | Out-Null

Write-Host "==> Cleaning old dist..."
Remove-Item -Recurse -Force (Join-Path $Root "dist\YT Media Downloader") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $Root "build\pyi") -ErrorAction SilentlyContinue

Write-Host "==> PyInstaller (onedir)..."
& $Py -m PyInstaller --noconfirm --clean --distpath (Join-Path $Root "dist") --workpath (Join-Path $Root "build\pyi") (Join-Path $Root "yt-wav-cutter.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$AppDir = Join-Path $Root "dist\YT Media Downloader"
if (-not (Test-Path $AppDir)) { throw "Missing output folder: $AppDir" }

$FfmpegDst = Join-Path $AppDir "ffmpeg.exe"
if (-not (Test-Path $FfmpegDst)) {
    Write-Host "==> Bundling ffmpeg.exe..."
    $tools = Join-Path $Root "build\tools"
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    $zip = Join-Path $tools "ffmpeg-essentials.zip"
    $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    if (-not (Test-Path $zip)) {
        Write-Host "    Downloading ffmpeg essentials zip..."
        Invoke-WebRequest -Uri $url -OutFile $zip
    }
    $extract = Join-Path $tools "ffmpeg-extract"
    Remove-Item -Recurse -Force $extract -ErrorAction SilentlyContinue
    Expand-Archive -Path $zip -DestinationPath $extract -Force
    $ff = Get-ChildItem -Path $extract -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    if (-not $ff) { throw "ffmpeg.exe not found inside essentials zip" }
    Copy-Item $ff.FullName $FfmpegDst -Force
    Write-Host "    Copied $($ff.FullName)"
} else {
    Write-Host "==> ffmpeg.exe already in app folder"
}

$ZipOut = Join-Path $Root "dist\YT-Media-Downloader-portable.zip"
if (Test-Path $ZipOut) { Remove-Item $ZipOut -Force }
Write-Host "==> Writing portable zip..."
Compress-Archive -Path $AppDir -DestinationPath $ZipOut -Force

$IsccCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
)
$Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if ($Iscc) {
    Write-Host "==> Compiling Inno Setup installer with $Iscc"
    & $Iscc (Join-Path $Root "installer\yt-wav-cutter.iss")
    Write-Host "Installer should be under dist\"
} else {
    Write-Host "==> Inno Setup not found - skipped Setup.exe"
    Write-Host "    Install from https://jrsoftware.org/isinfo.php then re-run this script."
    Write-Host "    Or use installer\Install-User.ps1 for a no-Inno local install."
}

$RunExe = Join-Path $AppDir "YT Media Downloader.exe"
Write-Host ""
Write-Host "Done."
Write-Host "  App folder : $AppDir"
Write-Host "  Portable   : $ZipOut"
Write-Host "  Run locally: $RunExe"
