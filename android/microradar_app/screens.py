"""Screen manager and main / fullscreen layouts."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView

from microradar_app.android_log import log_exception
from microradar_app.controller import RadarController
from microradar_app.radar_widget import RadarWidget
from microradar_app.settings_panel import RadarSettingsPanel
from microradar_app.theme import RADAR_BG, accent_button, app_header

TICK_INTERVAL_S = 0.05
TICK_START_DELAY_S = 0.1


class MainScreen(Screen):
    def __init__(self, controller: RadarController, manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.screen_manager = manager

        root = MDBoxLayout(orientation="vertical")
        root.add_widget(app_header())

        body = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        body.add_widget(self._build_radar_card())
        body.add_widget(self._build_settings_scroll())
        root.add_widget(body)
        self.add_widget(root)

    def _build_radar_card(self) -> MDCard:
        card = MDCard(
            orientation="vertical",
            padding=dp(4),
            size_hint_y=None,
            height=dp(280),
            md_bg_color=RADAR_BG,
        )
        header = MDBoxLayout(size_hint_y=None, height=dp(36), padding=(dp(8), 0))
        header.add_widget(MDLabel(text="Radar", font_style="Subtitle1"))
        fullscreen_btn = accent_button(
            "Plein écran",
            lambda *_: self.screen_manager.set_current("fullscreen"),
        )
        fullscreen_btn.size_hint_x = None
        fullscreen_btn.width = dp(120)
        header.add_widget(fullscreen_btn)
        card.add_widget(header)
        self.radar = RadarWidget(engine=self.controller.engine, size_hint=(1, 1))
        card.add_widget(self.radar)
        return card

    def _build_settings_scroll(self) -> MDScrollView:
        scroll = MDScrollView(size_hint_y=1, do_scroll_x=False)
        self.settings = RadarSettingsPanel(self.controller)
        scroll.add_widget(self.settings)
        return scroll

    def on_enter(self, *_args) -> None:
        self.radar.engine = self.controller.engine
        self.radar.double_tap_enabled = False
        self.settings.sync_from_controller()


class FullscreenScreen(Screen):
    def __init__(self, controller: RadarController, manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.screen_manager = manager

        root = MDBoxLayout(orientation="vertical")
        self.radar = RadarWidget(
            engine=controller.engine,
            show_border=False,
            double_tap_enabled=True,
        )
        self.radar.set_double_tap_callback(lambda: manager.set_current("main"))
        root.add_widget(self.radar)

        hint = MDLabel(
            text="Double tap pour quitter le plein écran",
            size_hint_y=None,
            height=dp(32),
            halign="center",
            theme_text_color="Secondary",
            font_style="Caption",
        )
        hint.bind(size=lambda inst, _val: setattr(inst, "text_size", (inst.width, None)))
        root.add_widget(hint)
        self.add_widget(root)

    def on_enter(self, *_args) -> None:
        self.radar.engine = self.controller.engine
        self.radar.double_tap_enabled = True


class MicroRadarRoot(ScreenManager):
    def __init__(self, controller: RadarController, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.add_widget(MainScreen(controller=controller, manager=self, name="main"))
        self.add_widget(FullscreenScreen(controller=controller, manager=self, name="fullscreen"))
        self.current = "main"
        self._tick_event = None
        Clock.schedule_once(self._start_tick, TICK_START_DELAY_S)

    @property
    def main_screen(self) -> MainScreen:
        return self.get_screen("main")

    def _start_tick(self, _dt: float) -> None:
        if self._tick_event is None:
            self._tick_event = Clock.schedule_interval(self._tick, TICK_INTERVAL_S)

    def _tick(self, _dt: float) -> None:
        try:
            stats = self.controller.tick()
            panel = self.main_screen.settings
            panel.update_stats(self.controller.format_stats(stats))
            panel.update_heading_display()
        except Exception:
            log_exception("ui tick failed")
