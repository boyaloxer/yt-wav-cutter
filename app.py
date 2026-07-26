"""
YT Media Downloader — Aqua Gel UI (pywebview) + yt-dlp/ffmpeg backend.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import webview

import core

APP_TITLE = "YT Media Downloader"
ROOT = Path(__file__).resolve().parent
UI_PAGE = (ROOT / "ui" / "index.html").as_uri()


class Api:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._busy = False

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def get_deps(self) -> dict:
        return core.dependency_status()

    def paste_clipboard(self) -> str:
        try:
            import tkinter as tk

            r = tk.Tk()
            r.withdraw()
            try:
                text = r.clipboard_get()
            except tk.TclError:
                text = ""
            r.destroy()
            return text or ""
        except Exception:
            return ""

    def _push(self, payload: dict) -> None:
        if not self._window:
            return
        # Escape for JS string
        data = json.dumps(payload)
        self._window.evaluate_js(f"window.__ytUpdate && window.__ytUpdate({data})")

    def start_download(self, params: dict) -> dict:
        if self._busy:
            return {"ok": False, "message": "Already downloading."}

        url = (params or {}).get("url") or ""
        mode = (params or {}).get("mode") or "audio"
        cut_on = bool((params or {}).get("cutOn"))
        start = (params or {}).get("start") or "00:00:00"
        end = (params or {}).get("end") or ""

        is_audio = mode != "video"
        ext = "wav" if is_audio else "mp4"
        default_name = f"clip.{ext}" if cut_on else f"download.{ext}"
        file_types = (
            (f"{ext.upper()} Files (*.{ext})", f"*.{ext}"),
            ("All files (*.*)", "*.*"),
        )

        if not self._window:
            return {"ok": False, "message": "Window not ready."}

        result = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
            file_types=file_types,
        )
        if not result:
            return {"cancelled": True}

        # create_file_dialog may return str or tuple
        if isinstance(result, (list, tuple)):
            output_path = result[0] if result else ""
        else:
            output_path = str(result)
        if not output_path:
            return {"cancelled": True}

        if not output_path.lower().endswith(f".{ext}"):
            output_path = f"{output_path}.{ext}"

        self._busy = True

        def worker() -> None:
            try:
                def on_status(msg: str) -> None:
                    self._push({"status": msg, "error": msg.startswith("Error")})

                def on_progress(pct: float, speed: str | None) -> None:
                    self._push({"progress": pct, "speed": speed})

                outcome = core.run_job(
                    url=url,
                    mode=mode,
                    cut_on=cut_on,
                    start=start,
                    end=end,
                    output_path=output_path,
                    on_status=on_status,
                    on_progress=on_progress,
                )
                self._push(
                    {
                        "done": True,
                        "error": not outcome.get("ok"),
                        "status": outcome.get("message", ""),
                        "progress": 100 if outcome.get("ok") else 0,
                    }
                )
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "started": True}


def main() -> int:
    api = Api()
    window = webview.create_window(
        APP_TITLE,
        UI_PAGE,
        js_api=api,
        width=540,
        height=640,
        background_color="#DFE9EF",
        resizable=False,
    )
    api.set_window(window)
    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
