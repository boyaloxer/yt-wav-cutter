import tkinter as tk
from tkinter import filedialog
import subprocess
import os

def download_and_cut():
    url = url_entry.get()
    start = start_entry.get()
    end = end_entry.get()

    # Format-safe filenames
    filename = os.path.join(os.getcwd(), "downloaded_audio.wav")
    output_clip = os.path.join(os.getcwd(), "cut_clip.wav")

    status_label.config(text="Downloading...")
    root.update()

    # Download and convert to WAV
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "wav",
        "-o", filename, url
    ])

    status_label.config(text="Cutting clip...")
    root.update()

    # Cut the audio clip using ffmpeg
    subprocess.run([
        "ffmpeg", "-i", filename, "-ss", start, "-to", end,
        "-c", "copy", output_clip
    ])

    status_label.config(text=f"Saved clip to: {output_clip}")

# GUI setup
root = tk.Tk()
root.title("YT WAV Cutter")
root.geometry("460x260")
root.configure(bg="#C0C0C0")  # Windows 98 gray

font_style = ("MS Sans Serif", 10)

# URL Input
tk.Label(root, text="YouTube URL:", bg="#C0C0C0", font=font_style).pack(pady=(10, 0))
url_entry = tk.Entry(root, width=55, font=font_style)
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

# Download & Cut button
tk.Button(root, text="Download and Cut", command=download_and_cut, relief="groove", font=font_style).pack(pady=10)

# Status
status_label = tk.Label(root, text="", bg="#C0C0C0", font=font_style)
status_label.pack()

root.mainloop()
