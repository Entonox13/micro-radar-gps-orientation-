"""KivyMD screens for Micro Radar Android."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from microradar_app.controller import RadarController
from microradar_app.radar_widget import RadarWidget


class RadarSettingsPanel(MDBoxLayout):
    def __init__(self, controller: RadarController, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = (dp(12), dp(8), dp(12), dp(16))
        self.controller = controller
        self._build_fields()

    def _build_fields(self) -> None:
        s = self.controller.settings

        self.add_widget(MDLabel(text="Configuration", font_style="H6", theme_text_color="Primary"))

        gps_card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(260),
            md_bg_color=(0.07, 0.09, 0.15, 1),
        )
        gps_card.add_widget(
            MDLabel(
                text="Position GPS (WGS84)",
                font_style="Subtitle1",
                theme_text_color="Primary",
            )
        )
        gps_card.add_widget(
            MDLabel(
                text="Ex. Google Maps : clic droit → coordonnées",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )

        self.lat_field = MDTextField(hint_text="Latitude (°)", text=s.latitude, mode="rectangle")
        self.lon_field = MDTextField(hint_text="Longitude (°)", text=s.longitude, mode="rectangle")
        self.paste_field = MDTextField(hint_text="Coller lat, lon", text=s.paste, mode="rectangle")
        gps_card.add_widget(self.lat_field)
        gps_card.add_widget(self.lon_field)
        gps_card.add_widget(self.paste_field)

        self.position_label = MDLabel(
            text=self.controller.position_status(),
            theme_text_color="Custom",
            text_color=(0.29, 0.87, 0.5, 1),
            font_style="Caption",
        )
        gps_card.add_widget(self.position_label)

        apply_btn = MDRaisedButton(
            text="Appliquer la position",
            md_bg_color=(0.13, 0.77, 0.37, 1),
            on_release=lambda *_: self._apply_position(),
        )
        gps_card.add_widget(apply_btn)
        self.add_widget(gps_card)

        self.radius_field = MDTextField(hint_text="Rayon (°)", text=s.radius, mode="rectangle")
        self.client_id_field = MDTextField(
            hint_text="OpenSky Client ID",
            text=s.client_id,
            mode="rectangle",
        )
        self.client_secret_field = MDTextField(
            hint_text="OpenSky Client Secret",
            text=s.client_secret,
            password=True,
            mode="rectangle",
        )
        for field in (self.radius_field, self.client_id_field, self.client_secret_field):
            self.add_widget(field)

        btn_row = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
        btn_row.add_widget(
            MDRaisedButton(
                text="Rafraîchir",
                on_release=lambda *_: self._refresh(),
            )
        )
        btn_row.add_widget(
            MDRaisedButton(
                text="Sauvegarder",
                on_release=lambda *_: self._save(),
            )
        )
        self.add_widget(btn_row)

        options_card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(4),
            size_hint_y=None,
            height=dp(220),
            md_bg_color=(0.07, 0.09, 0.15, 1),
        )
        options_card.add_widget(MDLabel(text="Options", font_style="Subtitle1"))
        for label, attr in [
            ("Rotation boussole", "compass_mode"),
            ("Mode batterie", "battery_mode"),
            ("Ligne de balayage", "scanline"),
            ("Triangles directionnels", "triangles"),
            ("Infos avion", "info"),
        ]:
            row = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            cb = MDCheckbox(active=getattr(s, attr), size_hint=(None, None), size=(dp(36), dp(36)))
            cb.bind(active=lambda _w, value, a=attr: self._set_option(a, value))
            row.add_widget(cb)
            row.add_widget(MDLabel(text=label, valign="center"))
            options_card.add_widget(row)
        self.add_widget(options_card)

        heading_card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(180),
            md_bg_color=(0.07, 0.09, 0.15, 1),
        )
        self.cap_section_label = MDLabel(text="Cap (°)", font_style="Subtitle1")
        heading_card.add_widget(self.cap_section_label)
        self.compass_status_label = MDLabel(
            text=self.controller.compass_status_line(),
            font_style="Caption",
            theme_text_color="Secondary",
        )
        heading_card.add_widget(self.compass_status_label)
        self.heading_slider = MDSlider(min=0, max=359, value=s.heading)
        self.heading_slider.bind(value=self._on_heading)
        heading_card.add_widget(self.heading_slider)
        self.heading_label = MDLabel(text=f"{int(s.heading)}°", font_style="Caption")
        heading_card.add_widget(self.heading_label)
        self.compass_offset_field = MDTextField(
            hint_text="Offset boussole (°)",
            text=str(s.compass_offset),
        )
        heading_card.add_widget(self.compass_offset_field)
        heading_card.add_widget(
            MDLabel(
                text="Activez « Rotation boussole » : le cap suit le magnétomètre du téléphone.",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        self.add_widget(heading_card)

        stats_card = MDCard(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(220),
            md_bg_color=(0.06, 0.09, 0.16, 1),
        )
        stats_card.add_widget(MDLabel(text="Statut / fiabilité", font_style="Subtitle1"))
        self.stats_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(0.29, 0.87, 0.5, 1),
        )
        stats_card.add_widget(self.stats_label)
        self.add_widget(stats_card)

        self.add_widget(
            MDLabel(
                text="Astuce : 6 décimales ≈ précision de 10 m.",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )

    def sync_from_controller(self) -> None:
        s = self.controller.settings
        self.lat_field.text = s.latitude
        self.lon_field.text = s.longitude
        self.paste_field.text = s.paste
        self.radius_field.text = s.radius
        self.client_id_field.text = s.client_id
        self.client_secret_field.text = s.client_secret
        self.heading_slider.value = s.heading
        self.heading_label.text = f"{int(self.controller.effective_heading())}°"
        self.compass_offset_field.text = str(s.compass_offset)
        self.position_label.text = self.controller.position_status()
        self.update_heading_display()

    def update_heading_display(self) -> None:
        uses_compass = self.controller.uses_live_compass()
        self.compass_status_label.text = self.controller.compass_status_line()
        self.cap_section_label.text = "Cap boussole (°)" if uses_compass else "Cap manuel (°)"
        self.heading_slider.disabled = uses_compass
        if uses_compass:
            self.heading_label.text = f"{int(self.controller.effective_heading())}°"
        else:
            self.heading_label.text = f"{int(self.controller.settings.heading)}°"

    def pull_settings(self) -> None:
        s = self.controller.settings
        s.latitude = self.lat_field.text or ""
        s.longitude = self.lon_field.text or ""
        s.paste = self.paste_field.text or ""
        s.radius = self.radius_field.text or "1.0"
        s.client_id = self.client_id_field.text or ""
        s.client_secret = self.client_secret_field.text or ""
        self._apply_compass_offset()
        self.controller.apply_settings_to_engine()

    def _apply_compass_offset(self) -> None:
        raw = (self.compass_offset_field.text or "0").strip().replace(",", ".")
        try:
            self.controller.settings.compass_offset = float(raw)
        except ValueError:
            self.controller.settings.compass_offset = 0.0

    def _set_option(self, attr: str, value: bool) -> None:
        setattr(self.controller.settings, attr, value)
        self.pull_settings()

    def _on_heading(self, _slider, value: float) -> None:
        if self.controller.uses_live_compass():
            return
        self.controller.settings.heading = value
        self.heading_label.text = f"{int(value)}°"
        self.controller.apply_settings_to_engine()

    def _apply_position(self) -> None:
        self.pull_settings()
        self.controller.apply_gps_position()
        self.position_label.text = self.controller.position_status()

    def _refresh(self) -> None:
        self.pull_settings()
        self.controller.fetch_now()

    def _save(self) -> None:
        self.pull_settings()
        self.controller.save_config()
        self.position_label.text = self.controller.position_status()

    def update_stats(self, text: str) -> None:
        self.stats_label.text = text


class MainScreen(Screen):
    def __init__(self, controller: RadarController, manager: ScreenManager, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.screen_manager = manager

        root = MDBoxLayout(orientation="vertical")
        root.add_widget(
            MDTopAppBar(
                title="Micro Radar",
                elevation=2,
                md_bg_color=(0.07, 0.09, 0.15, 1),
            )
        )

        body = MDBoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))

        radar_card = MDCard(
            orientation="vertical",
            padding=dp(4),
            size_hint_y=None,
            height=dp(280),
            md_bg_color=(0, 0, 0, 1),
        )
        radar_header = MDBoxLayout(size_hint_y=None, height=dp(36), padding=(dp(8), 0))
        radar_header.add_widget(MDLabel(text="Radar", font_style="Subtitle1"))
        radar_header.add_widget(
            MDRaisedButton(
                text="Plein écran",
                size_hint_x=None,
                width=dp(120),
                md_bg_color=(0.13, 0.77, 0.37, 1),
                on_release=lambda *_: self.screen_manager.set_current("fullscreen"),
            )
        )
        radar_card.add_widget(radar_header)

        self.radar = RadarWidget(engine=controller.engine, size_hint=(1, 1))
        radar_card.add_widget(self.radar)
        body.add_widget(radar_card)

        scroll = MDScrollView()
        self.settings = RadarSettingsPanel(controller)
        scroll.add_widget(self.settings)
        body.add_widget(scroll)

        root.add_widget(body)
        self.add_widget(root)

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

        self.hint = MDLabel(
            text="Double tap pour quitter le plein écran",
            size_hint_y=None,
            height=dp(32),
            halign="center",
            theme_text_color="Secondary",
            font_style="Caption",
        )
        root.add_widget(self.hint)
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
        Clock.schedule_interval(self._tick, 0.05)

    def _tick(self, _dt: float) -> None:
        stats = self.controller.tick()
        main = self.get_screen("main")
        main.settings.update_stats(self.controller.format_stats(stats))
        main.settings.update_heading_display()
