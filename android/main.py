#!/usr/bin/env python3
"""Launch Micro Radar on Android or desktop (for UI testing)."""

from __future__ import annotations

from microradar_app.bootstrap import bootstrap

bootstrap()

from microradar_app.app import main  # noqa: E402

if __name__ == "__main__":
    main()
