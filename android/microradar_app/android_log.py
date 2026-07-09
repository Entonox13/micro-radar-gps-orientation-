"""Log helper for Android logcat debugging."""

from __future__ import annotations

import traceback


def log_info(message: str) -> None:
    _log("i", message)


def log_error(message: str) -> None:
    _log("e", message)


def log_exception(message: str) -> None:
    log_error(f"{message}\n{traceback.format_exc()}")


def _log(level: str, message: str) -> None:
    try:
        from jnius import autoclass

        Log = autoclass("android.util.Log")
        if level == "e":
            Log.e("MicroRadar", message)
        else:
            Log.i("MicroRadar", message)
    except Exception:
        print(f"[MicroRadar/{level}] {message}")
