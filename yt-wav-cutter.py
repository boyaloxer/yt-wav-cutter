"""
YT Media Downloader entrypoint.

Default: Aqua Gel UI (pywebview).
Legacy Win95 tkinter UI:  python yt-wav-cutter.py --classic
"""

from __future__ import annotations

import sys


def main() -> int:
    if "--classic" in sys.argv:
        from classic_ui import run_classic

        return run_classic()
    from app import main as run_app

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
