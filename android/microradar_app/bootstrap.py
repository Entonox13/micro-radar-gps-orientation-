"""Runtime bootstrap — Kivy config, paths, SSL (call before kivy imports)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ANDROID_DIR = Path(__file__).resolve().parent.parent


def configure_kivy() -> None:
    os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")
    from kivy.config import Config

    Config.set("kivy", "log_level", "info")
    Config.set("graphics", "multisamples", "0")


def configure_ssl() -> None:
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass


def configure_sys_path() -> None:
    android_path = str(ANDROID_DIR)
    if android_path not in sys.path:
        sys.path.insert(0, android_path)

    if "ANDROID_ARGUMENT" not in os.environ:
        repo_root = str(ANDROID_DIR.parent)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)


def bootstrap() -> None:
    configure_kivy()
    configure_ssl()
    configure_sys_path()
