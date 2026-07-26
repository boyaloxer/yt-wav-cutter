# -*- mode: python ; coding: utf-8 -*-
# Build:  py -3 -m PyInstaller yt-wav-cutter.spec

from pathlib import Path

block_cipher = None
root = Path(SPEC).parent

a = Analysis(
    ['yt-wav-cutter.py'],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'ui'), 'ui'),
        (str(root / 'assets' / 'yt-wav-cutter.ico'), 'assets'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        'clr_loader',
        'pythonnet',
        'bottle',
        'proxy_tools',
        'yt_dlp',
        'core',
        'app',
        'classic_ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YT Media Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(root / 'assets' / 'yt-wav-cutter.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='YT Media Downloader',
)
