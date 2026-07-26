# Dependencies — YT Media Downloader

## Python packages

```powershell
py -3 -m pip install -U -r requirements.txt
```

That installs / upgrades **yt-dlp**.

`tkinter` ships with the official Windows Python installer if you left **tcl/tk and IDLE** checked.

## System tools

| Tool | Purpose | Install |
|---|---|---|
| **ffmpeg** | Convert to WAV, cut audio/video | `choco install ffmpeg` or [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) — must be on `PATH` |
| **Node.js LTS** | JS runtime for YouTube extraction (yt-dlp) | [nodejs.org](https://nodejs.org/) — must be on `PATH` as `node` |
| **Deno** (optional alt) | Alternate JS runtime | [deno.land](https://deno.land/) |

### Why Node / Deno?

Newer **yt-dlp** versions warn:

> YouTube extraction without a JS runtime has been deprecated

The app auto-detects `node` or `deno` and passes them to yt-dlp. Prefer Node if you already have it.

Details: https://github.com/yt-dlp/yt-dlp/wiki/EJS

## Sanity checks

```powershell
py -3 -c "import tkinter, yt_dlp; print(yt_dlp.version.__version__)"
ffmpeg -version
node -v
```

## Packaging

```powershell
py -3 -m pip install pyinstaller
pyinstaller --onefile --windowed yt-wav-cutter.py
```
