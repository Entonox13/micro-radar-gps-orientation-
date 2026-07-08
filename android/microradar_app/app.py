"""Micro Radar Android application."""

from __future__ import annotations

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

from microradar_app.controller import RadarController
from microradar_app.screens import MicroRadarRoot


class MicroRadarApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Micro Radar"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.controller = RadarController()
        self._dialog: MDDialog | None = None

    def build(self):
        self.controller.set_callbacks(
            on_fetch_done=self._on_fetch_done,
            on_error=self._show_message,
            on_save_done=self._show_message,
        )
        return MicroRadarRoot(controller=self.controller)

    def _on_fetch_done(self, stats) -> None:
        root = self.root
        if root:
            root.get_screen("main").settings.update_stats(self.controller.format_stats(stats))

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
    MicroRadarApp().run()
