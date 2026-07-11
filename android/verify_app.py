#!/usr/bin/env python3
"""Checks for the Android app package (run before APK build)."""

from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path

ANDROID_DIR = Path(__file__).resolve().parent
REPO_ROOT = ANDROID_DIR.parent


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def verify_syntax() -> None:
    if not compileall.compile_dir(ANDROID_DIR / "microradar_app", quiet=1):
        raise SystemExit("Python syntax check failed")
    _ok("syntax (compileall)")


def verify_no_mdtopappbar() -> None:
    forbidden = ("from kivymd.uix.toolbar import MDTopAppBar", "MDTopAppBar(")
    for path in (ANDROID_DIR / "microradar_app").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern in source:
                raise SystemExit(f"{path.name} must not use MDTopAppBar (Android SIGSEGV)")
    _ok("no MDTopAppBar in UI modules")


def verify_core_logic() -> None:
    env = os.environ.copy()
    env["KIVY_NO_CONSOLELOG"] = "1"
    env["KIVY_GRAPHICS"] = "mock"
    env["KIVY_WINDOW"] = "mock"
    script = """
import sys
sys.path[:0] = [{android!r}, {repo!r}]
from microradar_app.bootstrap import bootstrap
bootstrap()
from microradar_app.controller import RadarController
from microradar_app.config import get_config_path
ctrl = RadarController(load_persisted=False)
stats = ctrl.tick()
assert stats.aircraft_in_air >= 0
assert str(get_config_path()).endswith("config.json")
print("logic_ok")
""".format(android=str(ANDROID_DIR), repo=str(REPO_ROOT))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"core logic check failed (exit {result.returncode})")
    _ok("RadarController + config paths")


def verify_package_layout() -> None:
    required = [
        ANDROID_DIR / "main.py",
        ANDROID_DIR / "microradar_app" / "bootstrap.py",
        ANDROID_DIR / "microradar_app" / "theme.py",
        ANDROID_DIR / "microradar_app" / "settings_panel.py",
        ANDROID_DIR / "microradar_app" / "screens.py",
        ANDROID_DIR / "microradar_app" / "app.py",
    ]
    missing = [str(p.relative_to(ANDROID_DIR)) for p in required if not p.is_file()]
    if missing:
        raise SystemExit(f"missing modules: {', '.join(missing)}")
    _ok("package layout")


def main() -> int:
    print("Micro Radar Android — verification")
    verify_syntax()
    verify_no_mdtopappbar()
    verify_package_layout()
    verify_core_logic()
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
