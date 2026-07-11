"""Settings form — GPS, OpenSky, options, heading."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField

from microradar_app.controller import RadarController
from microradar_app.theme import BG_STATS, STATUS_OK, accent_button, section_card

OPTION_ROWS = [
    ("Rotation boussole", "compass_mode"),
    ("Mode batterie", "battery_mode"),
    ("Ligne de balayage", "scanline"),
    ("Triangles directionnels", "triangles"),
    ("Infos avion", "info"),
]


class RadarSettingsPanel(MDBoxLayout):
    def __init__(self, controller: RadarController, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = (dp(12), dp(8), dp(12), dp(16))
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))
        self.controller = controller
        self._suppress_events = True
        self._build_fields()
        self._suppress_events = False

    def _build_fields(self) -> None:
        s = self.controller.settings
        self.add_widget(MDLabel(text="Configuration", font_style="H6", theme_text_color="Primary"))
        self._build_gps_section(s)
        self._build_opensky_fields(s)
        self._build_action_buttons()
        self._build_options_section(s)
        self._build_heading_section(s)
        self._build_stats_section()
        self.add_widget(
            MDLabel(
                text="Astuce : 6 décimales ≈ précision de 10 m.",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )

    def _build_gps_section(self, s) -> None:
        card = section_card(260)
        card.add_widget(MDLabel(text="Position GPS (WGS84)", font_style="Subtitle1", theme_text_color="Primary"))
        card.add_widget(
            MDLabel(
                text="Ex. Google Maps : clic droit → coordonnées",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        self.lat_field = MDTextField(hint_text="Latitude (°)", text=s.latitude, mode="rectangle")
        self.lon_field = MDTextField(hint_text="Longitude (°)", text=s.longitude, mode="rectangle")
        self.paste_field = MDTextField(hint_text="Coller lat, lon", text=s.paste, mode="rectangle")
        for field in (self.lat_field, self.lon_field, self.paste_field):
            card.add_widget(field)
        self.position_label = MDLabel(
            text=self.controller.position_status(),
            theme_text_color="Custom",
            text_color=STATUS_OK,
            font_style="Caption",
        )
        card.add_widget(self.position_label)
        card.add_widget(accent_button("Appliquer la position", lambda *_: self._apply_position()))
        self.add_widget(card)

    def _build_opensky_fields(self, s) -> None:
        self.radius_field = MDTextField(hint_text="Rayon (°)", text=s.radius, mode="rectangle")
        self.client_id_field = MDTextField(hint_text="OpenSky Client ID", text=s.client_id, mode="rectangle")
        self.client_secret_field = MDTextField(
            hint_text="OpenSky Client Secret",
            text=s.client_secret,
            password=True,
            mode="rectangle",
        )
        for field in (self.radius_field, self.client_id_field, self.client_secret_field):
            self.add_widget(field)

    def _build_action_buttons(self) -> None:
        row = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(48))
        row.add_widget(MDRaisedButton(text="Rafraîchir", on_release=lambda *_: self._refresh()))
        row.add_widget(MDRaisedButton(text="Sauvegarder", on_release=lambda *_: self._save()))
        self.add_widget(row)

    def _build_options_section(self, s) -> None:
        card = section_card(220)
        card.spacing = dp(4)
        card.add_widget(MDLabel(text="Options", font_style="Subtitle1"))
        for label, attr in OPTION_ROWS:
            row = MDBoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            cb = MDCheckbox(active=getattr(s, attr), size_hint=(None, None), size=(dp(36), dp(36)))
            cb.bind(active=lambda _w, value, a=attr: self._set_option(a, value))
            row.add_widget(cb)
            row.add_widget(MDLabel(text=label, valign="center"))
            card.add_widget(row)
        self.add_widget(card)

    def _build_heading_section(self, s) -> None:
        card = section_card(180)
        self.cap_section_label = MDLabel(text="Cap (°)", font_style="Subtitle1")
        card.add_widget(self.cap_section_label)
        self.compass_status_label = MDLabel(
            text=self.controller.compass_status_line(),
            font_style="Caption",
            theme_text_color="Secondary",
        )
        card.add_widget(self.compass_status_label)
        self.heading_label = MDLabel(text=f"{int(s.heading)}°", font_style="Caption")
        card.add_widget(self.heading_label)
        self.heading_slider = MDSlider(min=0, max=359, value=s.heading)
        self.heading_slider.bind(value=self._on_heading)
        card.add_widget(self.heading_slider)
        self.compass_offset_field = MDTextField(hint_text="Offset boussole (°)", text=str(s.compass_offset))
        card.add_widget(self.compass_offset_field)
        card.add_widget(
            MDLabel(
                text="Activez « Rotation boussole » : le cap suit le magnétomètre du téléphone.",
                font_style="Caption",
                theme_text_color="Secondary",
            )
        )
        self.add_widget(card)

    def _build_stats_section(self) -> None:
        card = section_card(220, bg=BG_STATS)
        card.add_widget(MDLabel(text="Statut / fiabilité", font_style="Subtitle1"))
        self.stats_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Custom",
            text_color=STATUS_OK,
        )
        card.add_widget(self.stats_label)
        self.add_widget(card)

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
        heading = self.controller.effective_heading() if uses_compass else self.controller.settings.heading
        self.heading_label.text = f"{int(heading)}°"

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
        if self._suppress_events:
            return
        setattr(self.controller.settings, attr, value)
        self.pull_settings()

    def _on_heading(self, _slider, value: float) -> None:
        if self._suppress_events or self.controller.uses_live_compass():
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
