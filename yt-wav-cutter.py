import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import threading
import os
from yt_dlp import YoutubeDL
import subprocess

def run_in_thread(func):
    def wrapper():
        threading.Thread(target=func).start()
    return wrapper

def update_status(message):
    status_label.config(text=message)
    root.update()

def update_progress(percent):
    progress_bar["value"] = percent
    root.update()

def get_ydl_opts(output_path):
    return {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'progress_hooks': [ydl_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }]
    }

def ydl_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%').strip().replace('%', '')
        try:
            update_progress(float(percent))
        except ValueError:
            update_progress(0)
    elif d['status'] == 'finished':
        update_progress(100)

def run_ffmpeg_cut(input_file, start, end, output_file):
    subprocess.run([
        'ffmpeg', '-i', input_file, '-ss', start, '-to', end,
        '-c', 'copy', output_file
    ])

@run_in_thread
def download_and_cut_audio():
    url = url_entry.get()
    start = start_entry.get()
    end = end_entry.get()

    filename = os.path.join(os.getcwd(), "downloaded_audio.wav")
    output_clip = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        title="Save clipped audio as"
    )

    if not output_clip:
        update_status("Save cancelled.")
        return

    update_status("Downloading audio...")
    update_progress(0)

    with YoutubeDL(get_ydl_opts(filename)) as ydl:
        ydl.download([url])

    update_status("Cutting audio...")
    run_ffmpeg_cut(filename, start, end, output_clip)

    update_status(f"Saved clip to: {output_clip}")
    update_progress(0)

@run_in_thread
def download_full_audio():
    url = url_entry.get()
    output_file = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        title="Save full audio as"
    )

    if not output_file:
        update_status("Save cancelled.")
        return

    update_status("Downloading full audio...")
    update_progress(0)

    with YoutubeDL(get_ydl_opts(output_file)) as ydl:
        ydl.download([url])

    update_status(f"Saved full audio to: {output_file}")
    update_progress(0)

@run_in_thread
def download_and_cut_video():
    url = url_entry.get()
    start = start_entry.get()
    end = end_entry.get()

    filename = os.path.join(os.getcwd(), "downloaded_video.mp4")
    output_clip = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="Save clipped video as"
    )

    if not output_clip:
        update_status("Save cancelled.")
        return

    update_status("Downloading video...")
    update_progress(0)

    with YoutubeDL({
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': filename,
        'progress_hooks': [ydl_hook],
    }) as ydl:
        ydl.download([url])

    update_status("Cutting video...")
    run_ffmpeg_cut(filename, start, end, output_clip)

    update_status(f"Saved video clip to: {output_clip}")
    update_progress(0)

@run_in_thread
def download_full_video():
    url = url_entry.get()
    output_file = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="Save full video as"
    )

    if not output_file:
        update_status("Save cancelled.")
        return

    update_status("Downloading full video...")
    update_progress(0)

    with YoutubeDL({
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_file,
        'progress_hooks': [ydl_hook],
    }) as ydl:
        ydl.download([url])

    update_status(f"Saved full video to: {output_file}")
    update_progress(0)

# GUI setup
root = tk.Tk()
root.title("YT Media Downloader")
root.geometry("480x460")
root.configure(bg="#C0C0C0")

font_style = ("MS Sans Serif", 10)

# URL Input
tk.Label(root, text="YouTube URL:", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
url_entry = tk.Entry(root, width=60, font=font_style)
url_entry.pack()

# Start Time
tk.Label(root, text="Start Time (HH:MM:SS):", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
start_entry = tk.Entry(root, font=font_style)
start_entry.insert(0, "00:00:00")
start_entry.pack()

# End Time
tk.Label(root, text="End Time (HH:MM:SS):", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
end_entry = tk.Entry(root, font=font_style)
end_entry.insert(0, "00:20:00")
end_entry.pack()

# Buttons
tk.Button(root, text="Download and Cut Audio", command=download_and_cut_audio, relief="groove", font=font_style).pack(pady=(10, 0))
tk.Button(root, text="Download and Cut Video", command=download_and_cut_video, relief="groove", font=font_style).pack(pady=(5, 0))
tk.Button(root, text="Download Audio Full", command=download_full_audio, relief="groove", font=font_style).pack(pady=(5, 0))
tk.Button(root, text="Download Video Full", command=download_full_video, relief="groove", font=font_style).pack(pady=(5, 10))

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=400)
progress_bar.pack(pady=(0, 5))
progress_bar["value"] = 0

# Status Label
status_label = tk.Label(root, text="", bg="#C0C0C0", font=font_style)
status_label.pack()

root.mainloop()
