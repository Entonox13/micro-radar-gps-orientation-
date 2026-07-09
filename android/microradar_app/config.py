"""Configuration persistence paths."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def platform_name() -> str:
    return _platform()


def _platform() -> str:
    try:
        from kivy.utils import platform

        return platform
    except ImportError:
        return "android" if "ANDROID_ARGUMENT" in os.environ else "linux"


if _platform() == "android":
    from android.storage import app_storage_path

    CONFIG_DIR = Path(app_storage_path())
else:
    CONFIG_DIR = Path(__file__).resolve().parent.parent / "data"

CONFIG_PATH = CONFIG_DIR / "config.json"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_config_dir()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
