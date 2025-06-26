🧩 Dependencies for YT A/V Downloader and Chopper

This application requires a few Python modules and external tools to function properly.
🐍 Python Modules

Install with pip:

pip install yt-dlp

    ✅ tkinter and ttk are included with most standard Python installations. If missing, install the python3-tk package (Linux) or ensure “tcl/tk and IDLE” is enabled during Windows/macOS Python installation.

🛠 System Tools
Tool	Purpose	Install Instructions
ffmpeg	Used to cut and convert media files	Download or choco install ffmpeg (Windows only)

    ⚠️ ffmpeg must either be in your system’s PATH or placed in the same folder as the .exe.

🛠 For Packaging as .exe

If you plan to build a standalone .exe for distribution:

pip install pyinstaller

Then run:

pyinstaller --onefile --windowed yt_wav_cutter.
