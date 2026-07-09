#!/usr/bin/env python3
"""Launch Micro Radar on Android or desktop (for UI testing)."""

from __future__ import annotations

import sys
from pathlib import Path

ANDROID_DIR = Path(__file__).resolve().parent
REPO_ROOT = ANDROID_DIR.parent

for path in (str(ANDROID_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from microradar_app.app import main

if __name__ == "__main__":
    main()
