# Dependencies — YT Media Downloader V2

## Python packages

```powershell
py -3 -m pip install -U -r requirements.txt
```

Installs **yt-dlp** and **pywebview**.

On Windows, pywebview uses **Edge WebView2** (already on modern Windows 10/11).

## System tools

| Tool | Purpose | Install |
|---|---|---|
| **ffmpeg** | Convert to WAV, cut media | `choco install ffmpeg` or [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) |
| **Node.js LTS** | JS runtime for YouTube (yt-dlp) | [nodejs.org](https://nodejs.org/) |

See: https://github.com/yt-dlp/yt-dlp/wiki/EJS

## Sanity checks

```powershell
py -3 -c "import yt_dlp, webview; print(yt_dlp.version.__version__, 'webview ok')"
ffmpeg -version
node -v
```

## Run

```powershell
py -3 yt-wav-cutter.py
```
