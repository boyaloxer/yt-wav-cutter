"""
Backend for YT Media Downloader — yt-dlp + ffmpeg, no UI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import traceback
from collections.abc import Callable
from shutil import which

from yt_dlp import YoutubeDL

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ProgressCb = Callable[[float, str | None], None]  # percent, speed label
StatusCb = Callable[[str], None]


def detect_js_runtimes() -> dict:
    runtimes = {}
    node = which("node")
    if node:
        runtimes["node"] = {"path": node}
    deno = which("deno")
    if deno:
        runtimes["deno"] = {"path": deno}
    return runtimes


def yt_dlp_version() -> str:
    try:
        import yt_dlp.version as v

        return str(v.__version__)
    except Exception:
        return "?"


def dependency_status() -> dict:
    js = detect_js_runtimes()
    ffmpeg_ok = which("ffmpeg") is not None
    return {
        "ffmpeg": ffmpeg_ok,
        "node": "node" in js,
        "deno": "deno" in js,
        "js_ok": bool(js),
        "yt_dlp": yt_dlp_version(),
        "problems": check_dependencies(),
    }


def check_dependencies() -> list[str]:
    problems = []
    if not which("ffmpeg"):
        problems.append("ffmpeg not found on PATH (needed to convert/cut media).")
    if not detect_js_runtimes():
        problems.append(
            "No Node.js or Deno on PATH. YouTube downloads may break or miss formats. "
            "Install Node LTS: https://nodejs.org/"
        )
    return problems


def _format_speed(bytes_per_sec: float | None) -> str | None:
    if not bytes_per_sec or bytes_per_sec <= 0:
        return None
    mb = bytes_per_sec / (1024 * 1024)
    if mb >= 0.1:
        return f"{mb:.1f} MB/S"
    kb = bytes_per_sec / 1024
    return f"{kb:.0f} KB/S"


def make_progress_hook(on_progress: ProgressCb | None):
    def hook(d: dict) -> None:
        if on_progress is None:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            speed = _format_speed(d.get("speed"))
            if total:
                on_progress(downloaded * 100.0 / total, speed)
            else:
                raw = str(d.get("_percent_str", "0")).strip().replace("%", "")
                try:
                    on_progress(float(raw), speed)
                except ValueError:
                    pass
        elif d.get("status") == "finished":
            on_progress(100.0, None)

    return hook


def base_ydl_opts(
    on_progress: ProgressCb | None = None,
    *,
    player_clients: list[str] | None = None,
) -> dict:
    # YouTube often 403s certain android_* clients; prefer default minus known-bad ones.
    clients = player_clients or ["default", "-android_sdkless"]
    opts: dict = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "progress_hooks": [make_progress_hook(on_progress)],
        "nocheckcertificate": False,
        "retries": 10,
        "fragment_retries": 10,
        "http_headers": {
            "Referer": "https://www.youtube.com/",
            "Origin": "https://www.youtube.com",
        },
        "extractor_args": {
            "youtube": {
                "player_client": clients,
            }
        },
    }
    js = detect_js_runtimes()
    if js:
        opts["js_runtimes"] = js
    # Let yt-dlp fetch EJS components when needed (helps challenge solving)
    opts["remote_components"] = ["ejs:github"]
    return opts


def audio_ydl_opts(
    outtmpl: str,
    on_progress: ProgressCb | None = None,
    **base_kwargs,
) -> dict:
    opts = base_ydl_opts(on_progress, **base_kwargs)
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


def video_ydl_opts(
    outtmpl: str,
    on_progress: ProgressCb | None = None,
    **base_kwargs,
) -> dict:
    opts = base_ydl_opts(on_progress, **base_kwargs)
    opts.update(
        {
            # Don't force mp4-only streams — those often 403; merge whatever we get to mp4 when possible
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
        }
    )
    return opts


def _is_403(exc: BaseException) -> bool:
    text = str(exc)
    return "403" in text or "Forbidden" in text


def run_ffmpeg_cut(input_file: str, start: str, end: str, output_file: str) -> None:
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
    directory = os.path.dirname(prefix_path) or "."
    base = os.path.basename(prefix_path)
    for ext in extensions:
        candidate = prefix_path if prefix_path.endswith(ext) else prefix_path + ext
        if os.path.isfile(candidate):
            return candidate
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


def cleanup_prefix(prefix: str) -> None:
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


def parse_hms(value: str) -> int | None:
    parts = (value or "").strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = (int(p) for p in parts)
    except ValueError:
        return None
    if h < 0 or m < 0 or m > 59 or s < 0 or s > 59:
        return None
    return h * 3600 + m * 60 + s


def run_job(
    *,
    url: str,
    mode: str,
    cut_on: bool,
    start: str,
    end: str,
    output_path: str,
    on_status: StatusCb | None = None,
    on_progress: ProgressCb | None = None,
) -> dict:
    """
    Download (and optionally cut). Returns {ok, message, path?}.
    """

    def status(msg: str) -> None:
        print(msg)
        if on_status:
            on_status(msg)

    url = (url or "").strip()
    if not url:
        return {"ok": False, "message": "Paste a YouTube URL first."}

    mode = "video" if mode == "video" else "audio"
    start = (start or "00:00:00").strip()
    end = (end or "").strip()

    if cut_on:
        if parse_hms(start) is None or parse_hms(end) is None:
            return {"ok": False, "message": "Start/end must be HH:MM:SS."}
        if parse_hms(end) - parse_hms(start) <= 0:
            return {"ok": False, "message": "End must be after start."}

    is_audio = mode == "audio"
    tmp_prefix = os.path.join(WORKDIR, "_tmp_audio" if is_audio else "_tmp_video")
    if cut_on:
        tmp_prefix += "_cut"
    else:
        tmp_prefix += "_full"

    # Retry ladder for YouTube 403 / client blocks
    client_attempts: list[list[str] | None] = [
        None,  # default opts (default, -android_sdkless)
        ["tv", "tv_embedded", "web_safari"],
        ["mweb", "web_safari"],
        ["default", "-android_sdkless", "-android_vr"],
    ]

    last_exc: BaseException | None = None
    try:
        if on_progress:
            on_progress(0.0, None)

        media = None
        for i, clients in enumerate(client_attempts):
            kwargs = {} if clients is None else {"player_clients": clients}
            try:
                if is_audio:
                    status("DOWNLOADING AUDIO…" if i == 0 else f"RETRY AUDIO (client set {i + 1})…")
                    with YoutubeDL(audio_ydl_opts(tmp_prefix, on_progress, **kwargs)) as ydl:
                        ydl.download([url])
                    media = find_downloaded_file(tmp_prefix, (".wav",))
                else:
                    status("DOWNLOADING VIDEO…" if i == 0 else f"RETRY VIDEO (client set {i + 1})…")
                    with YoutubeDL(video_ydl_opts(tmp_prefix, on_progress, **kwargs)) as ydl:
                        ydl.download([url])
                    media = find_downloaded_file(tmp_prefix, (".mp4", ".mkv", ".webm", ".mov"))
                break
            except Exception as exc:
                last_exc = exc
                cleanup_prefix(tmp_prefix)
                if _is_403(exc) and i < len(client_attempts) - 1:
                    status(f"403 from YouTube — trying another client…")
                    continue
                raise

        if not media:
            raise last_exc or RuntimeError("Download failed with no output file.")

        if cut_on:
            status("CUTTING…")
            run_ffmpeg_cut(media, start, end, output_path)
        else:
            # Normalize extension for video if merger made mkv/webm
            if not is_audio:
                real_ext = os.path.splitext(media)[1].lower() or ".mp4"
                want_ext = os.path.splitext(output_path)[1].lower()
                if want_ext == ".mp4" and real_ext != ".mp4":
                    # keep user's folder/name but correct extension if we didn't get mp4
                    output_path = os.path.splitext(output_path)[0] + real_ext
            if os.path.abspath(media) != os.path.abspath(output_path):
                if os.path.isfile(output_path):
                    os.remove(output_path)
                shutil.move(media, output_path)

        kind = "WAV" if is_audio else os.path.splitext(output_path)[1].lstrip(".").upper() or "MP4"
        msg = f"SAVED. ENJOY UR {kind}"
        status(msg)
        if on_progress:
            on_progress(100.0, None)
        return {"ok": True, "message": msg, "path": output_path}
    except Exception as exc:
        traceback.print_exc()
        detail = str(exc).strip()
        if detail.lower().startswith("error:"):
            detail = detail[6:].strip()
        if _is_403(exc):
            msg = (
                "YouTube blocked the download (HTTP 403). "
                "Update yt-dlp (`pip install -U yt-dlp`), keep Node installed, "
                "or try again later. "
                f"Detail: {detail}"
            )
        else:
            msg = f"Error: {detail}"
        status(msg)
        return {"ok": False, "message": msg}
    finally:
        cleanup_prefix(tmp_prefix)
