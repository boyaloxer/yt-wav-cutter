# yt-wav-cutter

Download YouTube **audio → WAV** or **video → MP4**, with an optional time-range cut.

**UI:** Aqua Gel / Y2K “liquid” window (HTML + [pywebview](https://pywebview.flowrl.com/)), backed by **yt-dlp** + **ffmpeg**.

Repo: https://github.com/boyaloxer/yt-wav-cutter

---

## Download for Windows (no Python)

**[YT Media Downloader v2.0.0 — portable zip](https://github.com/boyaloxer/yt-wav-cutter/releases/download/v2.0.0/YT-Media-Downloader-portable.zip)**

1. Download and unzip  
2. Run `YT Media Downloader.exe`  
3. (Recommended) Install [Node.js LTS](https://nodejs.org/) for more reliable YouTube downloads  

ffmpeg is bundled. Full notes: [Release v2.0.0](https://github.com/boyaloxer/yt-wav-cutter/releases/tag/v2.0.0)

---

## Quick start (Windows, from source)

### 1. Install system tools (once)

1. **Python 3.10+** from [python.org](https://www.python.org/downloads/)  
   - During setup, check **“Add python.exe to PATH”**  
   - Leave **tcl/tk** enabled (used for clipboard / classic UI)
2. **ffmpeg** on your PATH  
   - Chocolatey: `choco install ffmpeg`  
   - Or download a build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `bin` to PATH
3. **Node.js LTS** from [nodejs.org](https://nodejs.org/) (recommended — YouTube extraction needs a JS runtime)

Confirm in a new PowerShell:

```powershell
py -3 --version
ffmpeg -version
node -v
```

### 2. Get the app

```powershell
git clone https://github.com/boyaloxer/yt-wav-cutter.git
cd yt-wav-cutter
```

Or download the ZIP from GitHub and extract it, then `cd` into that folder.

### 3. Install Python packages + run

```powershell
py -3 -m pip install -U -r requirements.txt
py -3 yt-wav-cutter.py
```

You should see the **YT Media Downloader** window (blue/lilac Aqua Gel UI).

**Legacy gray tkinter UI** (if needed):

```powershell
py -3 yt-wav-cutter.py --classic
```

---

## How to use

1. Paste a YouTube URL (or click **paste**)
2. Choose **♪ audio → wav** or **video → mp4**
3. Optionally turn on **cut a segment** (off by default), set start/end as `HH:MM:SS`
4. Click **⬇ download it** and pick where to save

Status + progress show under the button. Dependency chips at the bottom show **FFMPEG / NODE / YT-DLP**.

If something fails, a **copy err** button appears so you can copy the full error.

---

## Requirements

| Need | Why |
|---|---|
| Python 3.10+ | Runs the app |
| `yt-dlp` + `pywebview` (`requirements.txt`) | Download + Aqua Gel window |
| **Edge WebView2** | Used by pywebview on Windows (already on most Win10/11) |
| **ffmpeg** on `PATH` | WAV convert + cutting |
| **Node.js** on `PATH` | YouTube JS challenges (strongly recommended) |

More detail: [`DEPENDENCIES.md`](DEPENDENCIES.md)

---

## Troubleshooting

**Window won’t open / blank UI**  
- Install/repair [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)  
- Run from a terminal so you can see Python errors: `py -3 yt-wav-cutter.py`

**`ffmpeg` / `NODE` chip is red**  
- Install the tool and **open a new** PowerShell so PATH updates apply, then relaunch

**HTTP 403 / “unable to download video data”**  
YouTube blocks old clients often. Try:

```powershell
py -3 -m pip install -U yt-dlp
py -3 yt-wav-cutter.py
```

Keep Node installed. The app retries a few YouTube client sets automatically; some videos may still need cookies later.

**Cut times**  
Must be `HH:MM:SS`, and end must be after start.

---

## Project layout

| Path | Role |
|---|---|
| `yt-wav-cutter.py` | Entrypoint (`--classic` for old UI) |
| `app.py` | pywebview shell + JS bridge |
| `core.py` | yt-dlp / ffmpeg download + cut |
| `ui/` | Aqua Gel HTML / CSS / JS |
| `classic_ui.py` | Optional Win95-style tkinter UI |
| `requirements.txt` | Python deps |

---

## Windows installer (friendly .exe)

For users who shouldn’t need Python:

See **[`PACKAGING.md`](PACKAGING.md)** — build a Setup.exe / portable zip with desktop shortcut.

```powershell
powershell -ExecutionPolicy Bypass -File build\build_windows.ps1
# optional, no Inno Setup required:
powershell -ExecutionPolicy Bypass -File installer\Install-User.ps1
```

## Keep it working

YouTube breaks extractors regularly. When downloads fail:

```powershell
py -3 -m pip install -U yt-dlp
```

Then relaunch the app. (Packaged `.exe` users need a new release when yt-dlp inside the build goes stale.)
