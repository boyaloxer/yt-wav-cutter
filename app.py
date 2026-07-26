"""
YT Media Downloader — Aqua Gel UI (pywebview) + yt-dlp/ffmpeg backend.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import webview

import core

APP_TITLE = "YT Media Downloader"


def _resource_root() -> Path:
    """Where ui/ and assets/ live (PyInstaller _MEIPASS when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = _resource_root()
UI_PAGE = (ROOT / "ui" / "index.html").as_uri()
ICON_PATH = ROOT / "assets" / "yt-wav-cutter.ico"
if not ICON_PATH.is_file():
    ICON_PATH = _app_dir() / "assets" / "yt-wav-cutter.ico"


class Api:
    def __init__(self) -> None:
        self._window: webview.Window | None = None
        self._busy = False
        self._clip_root = None  # persistent tk root — destroy clears Windows clipboard

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def get_deps(self) -> dict:
        return core.dependency_status()

    def _clip_tk(self):
        import tkinter as tk

        if self._clip_root is None:
            self._clip_root = tk.Tk()
            self._clip_root.withdraw()
        return self._clip_root

    def paste_clipboard(self) -> str:
        try:
            r = self._clip_tk()
            try:
                return r.clipboard_get() or ""
            except Exception:
                return ""
        except Exception:
            return ""

    def copy_clipboard(self, text: str) -> dict:
        """Copy text to the system clipboard (for error messages)."""
        text = "" if text is None else str(text)
        # 1) PowerShell Set-Clipboard (most reliable on modern Windows)
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
                ],
                input=text,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode == 0:
                return {"ok": True, "via": "powershell"}
        except Exception as exc:
            print("powershell clipboard failed:", exc)

        # 2) Persistent tkinter clipboard (do NOT destroy the root)
        try:
            r = self._clip_tk()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            return {"ok": True, "via": "tkinter"}
        except Exception as exc:
            print("tk clipboard failed:", exc)
            return {"ok": False, "error": str(exc)}

    def _push(self, payload: dict) -> None:
        if not self._window:
            return
        # Escape for JS string
        data = json.dumps(payload)
        self._window.evaluate_js(f"window.__ytUpdate && window.__ytUpdate({data})")

    def _tk_save_dialog(self, default_name: str, ext: str) -> str | None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            r = tk.Tk()
            r.withdraw()
            r.attributes("-topmost", True)
            path = filedialog.asksaveasfilename(
                parent=r,
                defaultextension=f".{ext}",
                filetypes=[(f"{ext.upper()} files", f"*.{ext}"), ("All files", "*.*")],
                initialfile=default_name,
                title="Save as",
            )
            r.destroy()
            return path or None
        except Exception as exc:
            print("tk save dialog failed:", exc)
            return None

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
        # pywebview expects Sequence[str], e.g. "WAV Files (*.wav)" — not (label, pattern) tuples
        file_types = (
            f"{ext.upper()} Files (*.{ext})",
            "All files (*.*)",
        )

        if not self._window:
            return {"ok": False, "message": "Window not ready."}

        try:
            result = self._window.create_file_dialog(
                webview.FileDialog.SAVE if hasattr(webview, "FileDialog") else webview.SAVE_DIALOG,
                save_filename=default_name,
                file_types=file_types,
            )
        except TypeError as exc:
            # Older/newer pywebview quirks — fall back to tk save dialog
            print(f"create_file_dialog failed ({exc}); using tkinter fallback")
            result = self._tk_save_dialog(default_name, ext)

        if not result:
            return {"cancelled": True}

        # create_file_dialog returns Sequence[str] | None
        if isinstance(result, (list, tuple)):
            output_path = result[0] if result else ""
        else:
            output_path = result
        if isinstance(output_path, (list, tuple)):
            output_path = output_path[0] if output_path else ""
        output_path = str(output_path or "").strip()
        if not output_path:
            return {"cancelled": True}

        if not output_path.lower().endswith(f".{ext}"):
            output_path = f"{output_path}.{ext}"

        self._busy = True

        def worker() -> None:
            try:
                def on_status(msg: str) -> None:
                    is_err = msg.startswith("Error")
                    self._push(
                        {
                            "status": msg,
                            "error": is_err,
                            "errorDetail": msg if is_err else None,
                        }
                    )

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
                msg = outcome.get("message", "")
                self._push(
                    {
                        "done": True,
                        "error": not outcome.get("ok"),
                        "status": msg,
                        "errorDetail": None if outcome.get("ok") else msg,
                        "progress": 100 if outcome.get("ok") else 0,
                    }
                )
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "started": True}

    def window_close(self) -> None:
        if self._window:
            self._window.destroy()

    def window_minimize(self) -> None:
        if self._window:
            self._window.minimize()

    def window_toggle_fullscreen(self) -> dict:
        """Green traffic light — toggle fullscreen."""
        if not self._window:
            return {"fullscreen": False}
        self._window.toggle_fullscreen()
        self._fullscreen = not getattr(self, "_fullscreen", False)
        return {"fullscreen": self._fullscreen}


def main() -> int:
    if not (ROOT / "ui" / "index.html").is_file():
        raise SystemExit(f"UI not found at {ROOT / 'ui' / 'index.html'}")

    api = Api()
    # Frameless: our Aqua Gel titlebar IS the window chrome (no OS window-in-window)
    window_kwargs = dict(
        title=APP_TITLE,
        url=UI_PAGE,
        js_api=api,
        width=520,
        height=620,
        background_color="#CFE1EF",
        resizable=False,
        frameless=True,
        easy_drag=False,  # only .pywebview-drag-region (titlebar) moves the window
        shadow=True,
    )
    def _create(**extra):
        try:
            return webview.create_window(**window_kwargs, **extra)
        except TypeError:
            # Older pywebview may not support icon=/shadow=
            return None

    window = None
    if ICON_PATH.is_file():
        window = _create(icon=str(ICON_PATH))
    if window is None:
        window = _create()
    if window is None:
        # Last resort: drop optional frameless extras that might still fail
        window_kwargs.pop("shadow", None)
        window = webview.create_window(**window_kwargs)

    api.set_window(window)
    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
