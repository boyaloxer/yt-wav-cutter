# Packaging for Windows users

Goal: something that feels like a normal Windows app — install, desktop icon, uninstall — without asking people to install Python themselves.

## What end users get

| Deliverable | Experience |
|---|---|
| **`YT-Media-Downloader-Setup.exe`** (Inno Setup) | Next → Next → Finish, optional desktop icon, Start Menu entry, uninstaller |
| **`YT-Media-Downloader-portable.zip`** | Unzip and run `YT Media Downloader.exe` (no install) |
| **`Install-User.ps1`** | Copies the built app into `%LOCALAPPDATA%` and makes shortcuts (no Inno required) |

**Bundled:** Python runtime (via PyInstaller), the Aqua Gel UI, **ffmpeg.exe**  
**Still recommended on the machine:** **Node.js LTS** (YouTube JS). The installer can remind users if Node is missing.

## Build (on your PC)

### One-time tools

1. Python 3.10+ (you already have this)
2. Optional for a real Setup.exe: [Inno Setup 6](https://jrsoftware.org/isinfo.php) (install the Unicode version)

### Build command

```powershell
cd yt-wav-cutter
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
```

This will:

1. `pip install` app + PyInstaller deps  
2. Build `dist\YT Media Downloader\` (onedir exe)  
3. Download & bundle **ffmpeg.exe** into that folder  
4. Zip a portable build  
5. If Inno Setup is installed, compile `installer\yt-wav-cutter.iss` → `dist\YT-Media-Downloader-Setup.exe`

### Install for yourself without Inno

```powershell
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
powershell -ExecutionPolicy Bypass -File installer\Install-User.ps1
```

That puts a **desktop shortcut** + Start Menu entry under your user profile.

## Release checklist

1. Run `build_windows.ps1` successfully  
2. Smoke-test the exe (download audio + video once)  
3. Upload `YT-Media-Downloader-Setup.exe` (and/or the portable zip) to a GitHub **Release**  
4. Point README “Download for Windows” at that release asset  

## Notes / tradeoffs

- **yt-dlp is frozen into the build.** When YouTube breaks, ship a new release (or later add an in-app “update yt-dlp” that drops a newer wheel next to the exe).  
- **Node isn’t bundled** (large + updates often). Reminding users once at install is the pragmatic approach.  
- Prefer **onedir** over onefile for pywebview reliability.  
- Temp downloads go to `%LOCALAPPDATA%\YTMediaDownloader` so Program Files installs stay writable.
