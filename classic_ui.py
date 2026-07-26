"""Legacy Win95-style tkinter UI (optional: python yt-wav-cutter.py --classic)."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import core

APP_TITLE = "YT Media Downloader (Classic)"


def run_classic() -> int:
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

    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=420)
    status_label = tk.Label(root, text="", bg="#C0C0C0", font=font_style, wraplength=480, justify="left")

    def status(msg: str) -> None:
        status_label.config(text=msg)
        root.update_idletasks()
        print(msg)

    def progress(pct: float, _speed: str | None = None) -> None:
        progress_bar["value"] = max(0.0, min(100.0, pct))
        root.update_idletasks()

    def job(mode: str, cut: bool) -> None:
        url = url_entry.get().strip()
        if not url:
            status("Paste a YouTube URL first.")
            return
        ext = "wav" if mode == "audio" else "mp4"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()} files", f"*.{ext}")],
            title="Save as",
        )
        if not path:
            status("Save cancelled.")
            return

        def worker() -> None:
            core.run_job(
                url=url,
                mode=mode,
                cut_on=cut,
                start=start_entry.get().strip() or "00:00:00",
                end=end_entry.get().strip(),
                output_path=path,
                on_status=lambda m: root.after(0, status, m),
                on_progress=lambda p, s: root.after(0, progress, p, s),
            )

        threading.Thread(target=worker, daemon=True).start()

    tk.Button(
        root, text="Download and Cut Audio", command=lambda: job("audio", True), relief="groove", font=font_style
    ).pack(pady=(12, 0))
    tk.Button(
        root, text="Download and Cut Video", command=lambda: job("video", True), relief="groove", font=font_style
    ).pack(pady=(5, 0))
    tk.Button(
        root, text="Download Audio Full", command=lambda: job("audio", False), relief="groove", font=font_style
    ).pack(pady=(5, 0))
    tk.Button(
        root, text="Download Video Full", command=lambda: job("video", False), relief="groove", font=font_style
    ).pack(pady=(5, 10))

    progress_bar.pack(pady=(0, 5))
    status_label.pack(pady=(0, 8))

    deps = core.dependency_status()
    note = f"ffmpeg: {'OK' if deps['ffmpeg'] else 'MISSING'} | js: {'OK' if deps['js_ok'] else 'MISSING'} | yt-dlp {deps['yt_dlp']}"
    tk.Label(root, text=note, bg="#C0C0C0", font=("MS Sans Serif", 8), fg="#333").pack()
    if deps["problems"]:
        messagebox.showwarning(APP_TITLE, "\n\n".join(deps["problems"]))

    root.mainloop()
    return 0
