"""Micro Radar Android application."""

from __future__ import annotations

import sys
import traceback

from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from microradar_app.android_log import log_error, log_exception, log_info
from microradar_app.controller import RadarController
from microradar_app.screens import MicroRadarRoot

COMPASS_START_DELAY_S = 0.5


def _install_excepthook() -> None:
    def _hook(exc_type, exc, tb):
        log_error("".join(traceback.format_exception(exc_type, exc, tb)))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


class MicroRadarApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Micro Radar"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.controller: RadarController | None = None
        self._dialog: MDDialog | None = None

    def build(self):
        try:
            log_info("build() start")
            Window.softinput_mode = "adjustResize"
            self.controller = RadarController(load_persisted=False)
            self.controller.set_callbacks(
                on_fetch_done=self._on_fetch_done,
                on_error=self._show_message,
                on_save_done=self._show_message,
                on_heading_update=self._on_heading_update,
            )
            root = MicroRadarRoot(controller=self.controller)
            log_info("build() done")
            return root
        except Exception:
            log_exception("build() failed")
            raise

    def on_start(self):
        self._load_persisted_config()
        Clock.schedule_once(lambda _dt: self._safe_start_compass(), COMPASS_START_DELAY_S)

    def on_pause(self):
        self._safe_stop_compass()
        return True

    def on_resume(self):
        Clock.schedule_once(lambda _dt: self._safe_start_compass(), 0.25)

    def on_stop(self):
        self._safe_stop_compass()

    def _load_persisted_config(self) -> None:
        if self.controller is None or not isinstance(self.root, MicroRadarRoot):
            return
        try:
            self.controller.load_config()
            self.root.main_screen.settings.sync_from_controller()
            log_info("config loaded")
        except Exception:
            log_exception("config load failed")

    def _safe_start_compass(self) -> None:
        if self.controller is None:
            return
        try:
            self.controller.start_compass()
            log_info("compass started")
        except Exception:
            log_exception("compass start failed")

    def _safe_stop_compass(self) -> None:
        if self.controller is None:
            return
        try:
            self.controller.stop_compass()
        except Exception:
            log_exception("compass stop failed")

    def _main_settings(self):
        root = self.root
        if isinstance(root, MicroRadarRoot):
            return root.main_screen.settings
        return None

    def _on_heading_update(self) -> None:
        settings = self._main_settings()
        if settings:
            settings.update_heading_display()

    def _on_fetch_done(self, stats) -> None:
        settings = self._main_settings()
        if settings and self.controller:
            settings.update_stats(self.controller.format_stats(stats))

    def _show_message(self, text: str) -> None:
        if self._dialog:
            self._dialog.dismiss()
        self._dialog = MDDialog(
            title="Micro Radar",
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda *_: self._dialog.dismiss() if self._dialog else None,
                )
            ],
        )
        self._dialog.open()


def main() -> None:
    _install_excepthook()
    log_info("MicroRadar main()")
    MicroRadarApp().run()
