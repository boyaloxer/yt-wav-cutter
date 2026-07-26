"""
YT Media Downloader — download YouTube audio/video, optional segment cut.
Requires: Python 3.10+, yt-dlp, ffmpeg on PATH. Node.js recommended for YouTube JS.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import traceback
from shutil import which

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL

APP_TITLE = "YT Media Downloader"
WORKDIR = os.path.dirname(os.path.abspath(__file__))


def run_in_thread(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

    return wrapper


def update_status(message: str) -> None:
    if status_label is not None:
        status_label.config(text=message)
    if root is not None:
        root.update_idletasks()
    print(message)


def update_progress(percent: float) -> None:
    if progress_bar is not None:
        progress_bar["value"] = max(0.0, min(100.0, percent))
    if root is not None:
        root.update_idletasks()


def detect_js_runtimes() -> dict:
    """yt-dlp 2025+ prefers a JS runtime for YouTube. Prefer node, then deno."""
    runtimes = {}
    node = which("node")
    if node:
        runtimes["node"] = {"path": node}
    deno = which("deno")
    if deno:
        runtimes["deno"] = {"path": deno}
    return runtimes


def check_dependencies() -> list[str]:
    problems = []
    if not which("ffmpeg"):
        problems.append("ffmpeg not found on PATH (needed to convert/cut media).")
    if not detect_js_runtimes():
        problems.append(
            "No Node.js or Deno on PATH. YouTube downloads may break or miss formats.\n"
            "Install Node LTS: https://nodejs.org/"
        )
    return problems


def ydl_hook(d: dict) -> None:
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes") or 0
        if total:
            update_progress(downloaded * 100.0 / total)
        else:
            # Fallback for older progress fields
            raw = str(d.get("_percent_str", "0")).strip().replace("%", "")
            try:
                update_progress(float(raw))
            except ValueError:
                pass
    elif d.get("status") == "finished":
        update_progress(100)


def base_ydl_opts() -> dict:
    opts = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "progress_hooks": [ydl_hook],
        "nocheckcertificate": False,
    }
    js = detect_js_runtimes()
    if js:
        opts["js_runtimes"] = js
    return opts


def audio_ydl_opts(outtmpl: str) -> dict:
    opts = base_ydl_opts()
    opts.update(
        {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
        }
    )
    return opts


def video_ydl_opts(outtmpl: str) -> dict:
    opts = base_ydl_opts()
    opts.update(
        {
            # Modern yt-dlp: prefer mp4 merge when possible
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
        }
    )
    return opts


def run_ffmpeg_cut(input_file: str, start: str, end: str, output_file: str) -> None:
    """
    Cut [start, end). Re-encode audio WAV (stream copy is inaccurate / flaky on PCM).
    Video tries stream copy first, then re-encode fallback.
    """
    ext = os.path.splitext(output_file)[1].lower()
    if ext == ".wav":
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            start,
            "-to",
            end,
            "-i",
            input_file,
            "-acodec",
            "pcm_s16le",
            output_file,
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return

    copy_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        start,
        "-to",
        end,
        "-i",
        input_file,
        "-c",
        "copy",
        output_file,
    ]
    result = subprocess.run(copy_cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.isfile(output_file) and os.path.getsize(output_file) > 0:
        return

    reenc = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        start,
        "-to",
        end,
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_file,
    ]
    subprocess.run(reenc, check=True, capture_output=True, text=True)


def find_downloaded_file(prefix_path: str, extensions: tuple[str, ...]) -> str:
    """yt-dlp outtmpl may be without extension; find the real output file."""
    directory = os.path.dirname(prefix_path) or "."
    base = os.path.basename(prefix_path)
    # Exact match with extension already present
    for ext in extensions:
        candidate = prefix_path if prefix_path.endswith(ext) else prefix_path + ext
        if os.path.isfile(candidate):
            return candidate
    # Search directory for newest matching file starting with base
    matches = []
    for name in os.listdir(directory):
        lower = name.lower()
        if not any(lower.endswith(ext) for ext in extensions):
            continue
        stem = os.path.splitext(name)[0]
        if stem == base or name.startswith(base):
            matches.append(os.path.join(directory, name))
    if not matches:
        raise FileNotFoundError(f"No output file found for {prefix_path} ({', '.join(extensions)})")
    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return matches[0]


def require_url() -> str | None:
    url = url_entry.get().strip()
    if not url:
        update_status("Paste a YouTube URL first.")
        return None
    return url


def require_times() -> tuple[str, str] | None:
    start = start_entry.get().strip() or "00:00:00"
    end = end_entry.get().strip()
    if not end:
        update_status("End time is required for cutting (HH:MM:SS).")
        return None
    return start, end


@run_in_thread
def download_and_cut_audio():
    url = require_url()
    if not url:
        return
    times = require_times()
    if not times:
        return
    start, end = times

    output_clip = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        title="Save clipped audio as",
    )
    if not output_clip:
        update_status("Save cancelled.")
        return

    tmp_prefix = os.path.join(WORKDIR, "_tmp_audio")
    try:
        update_status("Downloading audio...")
        update_progress(0)
        with YoutubeDL(audio_ydl_opts(tmp_prefix)) as ydl:
            ydl.download([url])
        wav = find_downloaded_file(tmp_prefix, (".wav",))
        update_status("Cutting audio...")
        run_ffmpeg_cut(wav, start, end, output_clip)
        update_status(f"Saved clip to: {output_clip}")
    except Exception as exc:
        update_status(f"Error: {exc}")
        traceback.print_exc()
    finally:
        update_progress(0)
        _cleanup_prefix(tmp_prefix)


@run_in_thread
def download_full_audio():
    url = require_url()
    if not url:
        return

    output_file = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        title="Save full audio as",
    )
    if not output_file:
        update_status("Save cancelled.")
        return

    # Download to temp then move, so yt-dlp outtmpl stays extension-free
    tmp_prefix = os.path.join(WORKDIR, "_tmp_audio_full")
    try:
        update_status("Downloading full audio...")
        update_progress(0)
        with YoutubeDL(audio_ydl_opts(tmp_prefix)) as ydl:
            ydl.download([url])
        wav = find_downloaded_file(tmp_prefix, (".wav",))
        if os.path.abspath(wav) != os.path.abspath(output_file):
            if os.path.isfile(output_file):
                os.remove(output_file)
            shutil.move(wav, output_file)
        update_status(f"Saved full audio to: {output_file}")
    except Exception as exc:
        update_status(f"Error: {exc}")
        traceback.print_exc()
    finally:
        update_progress(0)
        _cleanup_prefix(tmp_prefix)


@run_in_thread
def download_and_cut_video():
    url = require_url()
    if not url:
        return
    times = require_times()
    if not times:
        return
    start, end = times

    output_clip = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="Save clipped video as",
    )
    if not output_clip:
        update_status("Save cancelled.")
        return

    tmp_prefix = os.path.join(WORKDIR, "_tmp_video")
    try:
        update_status("Downloading video...")
        update_progress(0)
        with YoutubeDL(video_ydl_opts(tmp_prefix)) as ydl:
            ydl.download([url])
        video = find_downloaded_file(tmp_prefix, (".mp4", ".mkv", ".webm", ".mov"))
        update_status("Cutting video...")
        run_ffmpeg_cut(video, start, end, output_clip)
        update_status(f"Saved video clip to: {output_clip}")
    except Exception as exc:
        update_status(f"Error: {exc}")
        traceback.print_exc()
    finally:
        update_progress(0)
        _cleanup_prefix(tmp_prefix)


@run_in_thread
def download_full_video():
    url = require_url()
    if not url:
        return

    output_file = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="Save full video as",
    )
    if not output_file:
        update_status("Save cancelled.")
        return

    tmp_prefix = os.path.join(WORKDIR, "_tmp_video_full")
    try:
        update_status("Downloading full video...")
        update_progress(0)
        # Write directly when possible
        opts = video_ydl_opts(os.path.splitext(output_file)[0])
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        video = find_downloaded_file(os.path.splitext(output_file)[0], (".mp4", ".mkv", ".webm", ".mov"))
        if os.path.abspath(video) != os.path.abspath(output_file):
            if os.path.isfile(output_file):
                os.remove(output_file)
            shutil.move(video, output_file)
        update_status(f"Saved full video to: {output_file}")
    except Exception as exc:
        update_status(f"Error: {exc}")
        traceback.print_exc()
    finally:
        update_progress(0)
        _cleanup_prefix(tmp_prefix)


def _cleanup_prefix(prefix: str) -> None:
    directory = os.path.dirname(prefix) or "."
    base = os.path.basename(prefix)
    try:
        for name in os.listdir(directory):
            if name == base or name.startswith(base + ".") or name.startswith(base):
                path = os.path.join(directory, name)
                if os.path.isfile(path) and ("_tmp_" in name or name.startswith("_tmp_")):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
    except OSError:
        pass


# --- GUI (built only when launched as a script) ---
root = None
url_entry = None
start_entry = None
end_entry = None
progress_bar = None
status_label = None


def build_gui() -> tk.Tk:
    global root, url_entry, start_entry, end_entry, progress_bar, status_label

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("520x500")
    root.configure(bg="#C0C0C0")

    font_style = ("MS Sans Serif", 10)

    tk.Label(root, text="YouTube URL:", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
    url_entry = tk.Entry(root, width=64, font=font_style)
    url_entry.pack()

    tk.Label(root, text="Start Time (HH:MM:SS):", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
    start_entry = tk.Entry(root, font=font_style)
    start_entry.insert(0, "00:00:00")
    start_entry.pack()

    tk.Label(root, text="End Time (HH:MM:SS):", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
    end_entry = tk.Entry(root, font=font_style)
    end_entry.insert(0, "00:00:20")
    end_entry.pack()

    tk.Button(
        root, text="Download and Cut Audio", command=download_and_cut_audio, relief="groove", font=font_style
    ).pack(pady=(12, 0))
    tk.Button(
        root, text="Download and Cut Video", command=download_and_cut_video, relief="groove", font=font_style
    ).pack(pady=(5, 0))
    tk.Button(
        root, text="Download Audio Full", command=download_full_audio, relief="groove", font=font_style
    ).pack(pady=(5, 0))
    tk.Button(
        root, text="Download Video Full", command=download_full_video, relief="groove", font=font_style
    ).pack(pady=(5, 10))

    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=420)
    progress_bar.pack(pady=(0, 5))
    progress_bar["value"] = 0

    status_label = tk.Label(root, text="", bg="#C0C0C0", font=font_style, wraplength=480, justify="left")
    status_label.pack(pady=(0, 8))

    js = detect_js_runtimes()
    js_note = "JS runtime: " + (", ".join(js.keys()) if js else "none (install Node.js)")
    dep_note = "ffmpeg: " + ("found" if which("ffmpeg") else "MISSING")
    tk.Label(
        root,
        text=f"{js_note}  |  {dep_note}",
        bg="#C0C0C0",
        font=("MS Sans Serif", 8),
        fg="#333333",
    ).pack(pady=(0, 6))

    problems = check_dependencies()
    if problems:
        messagebox.showwarning(APP_TITLE, "Dependency check:\n\n" + "\n\n".join(problems))

    return root


if __name__ == "__main__":
    build_gui()
    root.mainloop()
