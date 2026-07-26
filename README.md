# yt-wav-cutter

Download YouTube **audio → WAV** or **video → MP4**, optionally cut a time range.

**V2 UI:** Aqua Gel / Y2K liquid look (HTML + **pywebview**), wired to the same yt-dlp / ffmpeg backend.

## Quick start (Windows)

```powershell
cd yt-wav-cutter
py -3 -m pip install -U -r requirements.txt
py -3 yt-wav-cutter.py
```

Legacy Win95 tkinter UI:

```powershell
py -3 yt-wav-cutter.py --classic
```

## Requirements

| Dependency | Why |
|---|---|
| **Python 3.10+** | App runtime |
| **yt-dlp** | YouTube download |
| **pywebview** | Aqua Gel window (Edge WebView2 on Windows) |
| **ffmpeg** on `PATH` | WAV extract + cutting |
| **Node.js** (recommended) | YouTube JS runtime for yt-dlp |

See [`DEPENDENCIES.md`](DEPENDENCIES.md).

## Usage (V2)

1. Paste a YouTube URL (or hit **paste**)
2. Pick **audio → wav** or **video → mp4**
3. Toggle **cut a segment** if you want a range
4. Hit **⬇ download it** and choose a save path

## Project layout

| File | Role |
|---|---|
| `yt-wav-cutter.py` | Entrypoint |
| `app.py` | pywebview shell + JS bridge |
| `core.py` | yt-dlp / ffmpeg jobs |
| `ui/` | Aqua Gel HTML / CSS / JS |
| `classic_ui.py` | Optional old tkinter UI |

## Keep it working

```powershell
py -3 -m pip install -U yt-dlp
```
