# Dependencies — YT Media Downloader V2

## Python packages

From the repo folder:

```powershell
py -3 -m pip install -U -r requirements.txt
```

That installs:

- **yt-dlp** — YouTube download
- **pywebview** — Aqua Gel UI window (pulls in `pythonnet` / Edge WebView2 on Windows)

## System tools

| Tool | Purpose | Install |
|---|---|---|
| **Python 3.10+** | App runtime | [python.org](https://www.python.org/downloads/) — enable PATH + tcl/tk |
| **ffmpeg** | Convert to WAV, cut audio/video | `choco install ffmpeg` or [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) — must be on `PATH` |
| **Node.js LTS** | JS runtime for YouTube (yt-dlp) | [nodejs.org](https://nodejs.org/) — `node` on `PATH` |
| **WebView2** | Renders the HTML UI | Bundled with modern Edge / [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) |

### Why Node?

Newer yt-dlp versions expect a JS runtime for YouTube. Without it you may see deprecation warnings, missing formats, or 403s.

Details: https://github.com/yt-dlp/yt-dlp/wiki/EJS

## Sanity checks

```powershell
py -3 -c "import yt_dlp, webview; print('yt-dlp', yt_dlp.version.__version__); print('webview ok')"
ffmpeg -version
node -v
```

## Run

```powershell
py -3 yt-wav-cutter.py
```

Classic UI:

```powershell
py -3 yt-wav-cutter.py --classic
```
