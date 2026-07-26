# yt-wav-cutter

Simple Windows-friendly GUI to:

- download YouTube **audio → WAV**
- download YouTube **video → MP4**
- optionally **cut a time range** (start / end)

Win95-ish gray UI on purpose.

## Quick start (Windows)

```powershell
cd yt-wav-cutter
py -3 -m pip install -U -r requirements.txt
py -3 yt-wav-cutter.py
```

Or:

```powershell
python -m pip install -U -r requirements.txt
python yt-wav-cutter.py
```

## Requirements

| Dependency | Why |
|---|---|
| **Python 3.10+** with **tkinter** | GUI |
| **yt-dlp** (`requirements.txt`) | YouTube download |
| **ffmpeg** on `PATH` | WAV extract + cutting |
| **Node.js** (recommended) | YouTube JS runtime for yt-dlp |

Without Node (or Deno), yt-dlp still often works today but prints a deprecation warning and may miss formats later. See [yt-dlp EJS wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

More detail: [`DEPENDENCIES.md`](DEPENDENCIES.md)

## Usage

1. Paste a YouTube URL  
2. Set start / end times (`HH:MM:SS`) if cutting  
3. Pick a button:
   - **Download and Cut Audio**
   - **Download and Cut Video**
   - **Download Audio Full**
   - **Download Video Full**
4. Choose where to save

The status line and progress bar show what’s happening. Errors show in the status line (details also print in the console if you launched from a terminal).

## Keep it working

YouTube breaks extractors often. When downloads fail:

```powershell
py -3 -m pip install -U yt-dlp
```

Re-run the app after upgrading.

## Packaging as .exe (optional)

```powershell
py -3 -m pip install pyinstaller
pyinstaller --onefile --windowed yt-wav-cutter.py
```

The built exe still needs **ffmpeg** (and ideally **Node**) available on the machine `PATH`.
