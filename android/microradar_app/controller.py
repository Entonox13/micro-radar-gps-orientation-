"""Application state — settings, fetch loop, persistence."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from microradar_core.coordinates import (
    parse_coordinate,
    parse_coordinate_pair,
    validate_coordinates,
)
from microradar_core.opensky_client import OpenSkyClient, load_credentials_file
from microradar_core.radar_engine import RadarEngine, RadarStats

from microradar_app.compass_provider import CompassProvider
from microradar_app.config import get_config_path, get_credentials_path, load_json, save_json


@dataclass
class AppSettings:
    latitude: str = ""
    longitude: str = ""
    paste: str = ""
    radius: str = "1.0"
    client_id: str = ""
    client_secret: str = ""
    compass_mode: bool = False
    battery_mode: bool = False
    scanline: bool = True
    triangles: bool = True
    info: bool = False
    heading: float = 0.0
    compass_offset: float = 0.0


class RadarController:
    def __init__(self) -> None:
        self.engine = RadarEngine(client=OpenSkyClient())
        self.settings = AppSettings()
        self.compass = CompassProvider()
        self._busy = False
        self._on_fetch_done: Callable[[RadarStats], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._on_save_done: Callable[[str], None] | None = None
        self._on_heading_update: Callable[[], None] | None = None
        self.compass.set_update_callback(self._on_compass_heading)
        self.load_config()

    def set_callbacks(
        self,
        on_fetch_done: Callable[[RadarStats], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_save_done: Callable[[str], None] | None = None,
        on_heading_update: Callable[[], None] | None = None,
    ) -> None:
        self._on_fetch_done = on_fetch_done
        self._on_error = on_error
        self._on_save_done = on_save_done
        self._on_heading_update = on_heading_update

    def start_compass(self) -> None:
        self.compass.start()
        self.compass.set_calibration_offset(self.settings.compass_offset)
        self.compass.set_active(self.settings.compass_mode)

    def stop_compass(self) -> None:
        self.compass.stop()

    def _on_compass_heading(self, _heading: float) -> None:
        if self.settings.compass_mode:
            self.apply_settings_to_engine()
            if self._on_heading_update:
                self._on_heading_update()

    def uses_live_compass(self) -> bool:
        return (
            self.settings.compass_mode
            and self.compass.available
            and self.compass.has_heading
        )

    def effective_heading(self) -> float:
        if self.uses_live_compass():
            return self.compass.heading_deg
        return float(self.settings.heading)

    def compass_status_line(self) -> str:
        if not self.settings.compass_mode:
            return "Rotation boussole désactivée"
        if not self.compass.available:
            return "Boussole : capteur indisponible (slider de secours)"
        if self.compass.has_heading:
            return f"Boussole : {self.compass.heading_deg:.0f}°"
        return "Boussole : initialisation…"

    def read_coordinates(self) -> tuple[float, float]:
        lat = parse_coordinate(self.settings.latitude)
        lon = parse_coordinate(self.settings.longitude)
        validate_coordinates(lat, lon)
        return lat, lon

    def apply_pasted_coordinates(self, silent: bool = False) -> bool:
        paste = self.settings.paste.strip()
        if not paste:
            return False
        try:
            lat, lon = parse_coordinate_pair(paste)
            validate_coordinates(lat, lon)
            self.settings.latitude = f"{lat:.6f}"
            self.settings.longitude = f"{lon:.6f}"
            self.apply_settings_to_engine()
            self.fetch_now()
            return True
        except ValueError as exc:
            if not silent and self._on_error:
                self._on_error(str(exc))
            return False

    def apply_gps_position(self) -> None:
        paste = self.settings.paste.strip()
        lat_empty = not self.settings.latitude.strip()
        lon_empty = not self.settings.longitude.strip()
        if paste and (lat_empty or lon_empty):
            if not self.apply_pasted_coordinates(silent=False):
                return
            return

        try:
            lat, lon = self.read_coordinates()
        except ValueError as exc:
            if self._on_error:
                self._on_error(str(exc))
            return

        self.settings.latitude = f"{lat:.6f}"
        self.settings.longitude = f"{lon:.6f}"
        self.apply_settings_to_engine()
        self.fetch_now()

    def apply_settings_to_engine(self) -> bool:
        try:
            lat, lon = self.read_coordinates()
            self.engine.latitude = lat
            self.engine.longitude = lon
            self.engine.radius_deg = max(
                0.000001,
                min(2.5, float(self.settings.radius.replace(",", "."))),
            )
        except ValueError:
            return False

        self.engine.client.set_credentials(
            self.settings.client_id,
            self.settings.client_secret,
        )
        self.engine.compass_mode = self.settings.compass_mode
        self.engine.battery_mode = self.settings.battery_mode
        self.engine.show_scanline = self.settings.scanline
        self.engine.show_triangles = self.settings.triangles
        self.engine.show_info = self.settings.info
        self.compass.set_calibration_offset(self.settings.compass_offset)
        self.compass.set_active(self.settings.compass_mode)
        self.engine.heading_deg = self.effective_heading()
        return True

    def load_config(self) -> None:
        data = load_json(get_config_path())
        if data:
            self.settings.latitude = str(data.get("latitude", ""))
            self.settings.longitude = str(data.get("longitude", ""))
            self.settings.radius = str(data.get("radius", "1.0"))
            self.settings.compass_mode = bool(data.get("compass_mode", False))
            self.settings.battery_mode = bool(data.get("battery_mode", False))
            self.settings.scanline = bool(data.get("scanline", True))
            self.settings.triangles = bool(data.get("triangles", True))
            self.settings.info = bool(data.get("info", False))
            self.settings.heading = float(data.get("heading", 0.0))
            self.settings.compass_offset = float(data.get("compass_offset", 0.0))

        client_id, client_secret = load_credentials_file(get_credentials_path())
        if client_id and client_secret:
            self.settings.client_id = client_id
            self.settings.client_secret = client_secret
        elif data:
            self.settings.client_id = str(data.get("opensky_id", ""))
            self.settings.client_secret = str(data.get("opensky_secret", ""))

        self.apply_settings_to_engine()

    def save_config(self) -> None:
        try:
            lat, lon = self.read_coordinates()
        except ValueError as exc:
            if self._on_error:
                self._on_error(str(exc))
            return

        if not self.apply_settings_to_engine():
            if self._on_error:
                self._on_error("Impossible d'enregistrer : coordonnées invalides.")
            return

        payload = {
            "latitude": lat,
            "longitude": lon,
            "radius": self.engine.radius_deg,
            "compass_mode": self.settings.compass_mode,
            "battery_mode": self.settings.battery_mode,
            "scanline": self.settings.scanline,
            "triangles": self.settings.triangles,
            "info": self.settings.info,
            "heading": self.settings.heading,
            "compass_offset": self.settings.compass_offset,
        }
        save_json(get_config_path(), payload)
        if self._on_save_done:
            self._on_save_done(f"Configuration enregistrée dans\n{get_config_path()}")

    def fetch_now(self) -> None:
        if self._busy:
            return
        try:
            self.read_coordinates()
        except ValueError as exc:
            if self._on_error:
                self._on_error(str(exc))
            return

        self._busy = True
        if not self.apply_settings_to_engine():
            self._busy = False
            if self._on_error:
                self._on_error("Entrez une latitude et une longitude valides.")
            return

        def worker() -> None:
            stats = self.engine.update(force=True)
            self._busy = False
            callback = self._on_fetch_done
            if callback:
                try:
                    from kivy.clock import Clock

                    Clock.schedule_once(lambda _dt: callback(stats), 0)
                except Exception:
                    callback(stats)

        threading.Thread(target=worker, daemon=True).start()

    def has_valid_position(self) -> bool:
        try:
            self.read_coordinates()
            return True
        except ValueError:
            return False

    def tick(self) -> RadarStats:
        self.compass.set_active(self.settings.compass_mode)
        if self.settings.compass_mode and self.uses_live_compass():
            self.engine.heading_deg = self.effective_heading()
        if self.has_valid_position() and not self._busy and self.engine.should_fetch(self.engine.now_ms()):
            self.fetch_now()
        return self.engine.build_stats(self.engine.now_ms())

    def format_stats(self, stats: RadarStats) -> str:
        auth = (
            "authentifié"
            if self.settings.client_id and self.settings.client_secret
            else "anonyme"
        )
        lines = [
            f"Position : {self.engine.latitude:.6f}°, {self.engine.longitude:.6f}°",
            self.compass_status_line(),
            f"Avions en vol : {stats.aircraft_in_air}",
            f"Total suivi : {stats.aircraft_total}",
            f"API : {'OK' if stats.last_fetch_ok else 'ERREUR'} ({stats.last_fetch_ms:.0f} ms)",
            f"Mode : {auth}",
            f"Intervalle : {stats.fetch_interval_s:.0f} s",
            f"Prochain fetch : {stats.next_fetch_in_s:.0f} s",
            "",
            stats.reliability_hint,
        ]
        if stats.last_error:
            lines.insert(4, f"Erreur : {stats.last_error}")
        return "\n".join(lines)

    def position_status(self) -> str:
        if not self.settings.latitude.strip() or not self.settings.longitude.strip():
            return "Entrez vos coordonnées GPS."
        try:
            lat, lon = self.read_coordinates()
            return f"Position : {lat:.6f}°, {lon:.6f}°"
        except ValueError:
            return "Coordonnées invalides."
