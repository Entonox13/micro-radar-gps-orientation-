#!/usr/bin/env python3
"""Launch Micro Radar on Android or desktop (for UI testing)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Configure Kivy before any kivy/kivymd import (required on Android).
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")
from kivy.config import Config  # noqa: E402

Config.set("kivy", "log_level", "info")
Config.set("graphics", "multisamples", "0")

try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

ANDROID_DIR = Path(__file__).resolve().parent

# On device, main.py and packaged modules live in the same private folder.
for path in (str(ANDROID_DIR),):
    if path not in sys.path:
        sys.path.insert(0, path)

# Desktop dev: microradar_core lives at repo root.
if "ANDROID_ARGUMENT" not in os.environ:
    repo_root = ANDROID_DIR.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from microradar_app.app import main

if __name__ == "__main__":
    main()
