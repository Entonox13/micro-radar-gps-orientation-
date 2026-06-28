"""Radar projection and aircraft tracking — mirrors AircraftManager + TrackedAircraft."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from opensky_client import Aircraft, FetchResult, OpenSkyClient

SCREEN_SIZE = 240


@dataclass
class TrackedAircraft:
    state: Aircraft
    last_seen_ms: float
    blend_from_lat: float = 0.0
    blend_from_lon: float = 0.0
    blend_alpha: float = 1.0
    last_tick_ms: float = 0.0

    def __post_init__(self) -> None:
        self.blend_from_lat = self.state.latitude
        self.blend_from_lon = self.state.longitude
        self.last_tick_ms = self.last_seen_ms

    def update(self, new_state: Aircraft, now_ms: float) -> None:
        cur_lat, cur_lon = self.get_display_position(now_ms)
        self.blend_from_lat = cur_lat
        self.blend_from_lon = cur_lon
        self.blend_alpha = 0.0
        self.state = new_state
        self.last_seen_ms = now_ms

    def tick(self, now_ms: float) -> None:
        delta_seconds = max(0.0, (now_ms - self.last_tick_ms) / 1000.0)
        self.last_tick_ms = now_ms
        blend_speed = 0.15
        self.blend_alpha = min(1.0, self.blend_alpha + delta_seconds * blend_speed)

    def _predict_position(self, now_ms: float) -> tuple[float, float]:
        data_age_on_arrival = 0.0
        if self.state.time_position > 0 and self.state.last_contact > 0:
            data_age_on_arrival = float(self.state.last_contact - self.state.time_position)

        local_elapsed = max(0.0, (now_ms - self.last_seen_ms) / 1000.0)
        dt = local_elapsed + data_age_on_arrival

        heading_rad = math.radians(self.state.true_track)
        lat_meters_per_deg = 111_320.0
        delta_lat = (self.state.velocity * dt * math.cos(heading_rad)) / lat_meters_per_deg
        cos_lat = math.cos(math.radians(self.state.latitude)) or 1e-6
        delta_lon = (self.state.velocity * dt * math.sin(heading_rad)) / (lat_meters_per_deg * cos_lat)
        return self.state.latitude + delta_lat, self.state.longitude + delta_lon

    def get_display_position(self, now_ms: float) -> tuple[float, float]:
        dead_lat, dead_lon = self._predict_position(now_ms)
        if self.blend_alpha >= 1.0:
            return dead_lat, dead_lon

        t = self.blend_alpha * self.blend_alpha * (3.0 - 2.0 * self.blend_alpha)
        lat = self.blend_from_lat + t * (dead_lat - self.blend_from_lat)
        lon = self.blend_from_lon + t * (dead_lon - self.blend_from_lon)
        return lat, lon


@dataclass
class RadarStats:
    aircraft_in_air: int = 0
    aircraft_total: int = 0
    last_fetch_ok: bool = False
    last_fetch_ms: float = 0.0
    last_error: str = ""
    next_fetch_in_s: float = 0.0
    fetch_interval_s: float = 0.0
    reliability_hint: str = ""


@dataclass
class RadarEngine:
    client: OpenSkyClient = field(default_factory=OpenSkyClient)
    latitude: float = 48.8566
    longitude: float = 2.3522
    radius_deg: float = 1.0
    heading_deg: float = 0.0
    compass_mode: bool = False
    battery_mode: bool = False
    show_scanline: bool = True
    show_info: bool = False
    show_triangles: bool = True

    tracked: dict[str, TrackedAircraft] = field(default_factory=dict)
    last_fetch_ms: float = -1.0
    last_result: FetchResult | None = None
    _start_mono: float = field(default_factory=time.monotonic)

    def now_ms(self) -> float:
        return (time.monotonic() - self._start_mono) * 1000.0

    def fetch_interval_ms(self) -> int:
        return self.client.fetch_interval_ms(self.battery_mode)

    def should_fetch(self, now_ms: float) -> bool:
        if self.last_fetch_ms < 0.0:
            return True
        return (now_ms - self.last_fetch_ms) >= self.fetch_interval_ms()

    def update(self, force: bool = False) -> RadarStats:
        now_ms = self.now_ms()
        if force or self.should_fetch(now_ms):
            result = self.client.fetch_states(self.latitude, self.longitude, self.radius_deg)
            self.last_result = result
            self.last_fetch_ms = now_ms

            if result.success:
                seen: set[str] = set()
                for ac in result.aircraft:
                    if not ac.icao24:
                        continue
                    seen.add(ac.icao24)
                    if ac.icao24 not in self.tracked:
                        self.tracked[ac.icao24] = TrackedAircraft(ac, now_ms)
                    else:
                        self.tracked[ac.icao24].update(ac, now_ms)

                for icao in list(self.tracked):
                    if icao not in seen:
                        del self.tracked[icao]

        for tracked in self.tracked.values():
            tracked.tick(now_ms)

        return self.build_stats(now_ms)

    def build_stats(self, now_ms: float) -> RadarStats:
        in_air = [t for t in self.tracked.values() if not t.state.on_ground]
        interval_s = self.fetch_interval_ms() / 1000.0
        next_fetch = max(0.0, interval_s - ((now_ms - self.last_fetch_ms) / 1000.0))

        hint = self._reliability_hint(len(in_air), interval_s)
        return RadarStats(
            aircraft_in_air=len(in_air),
            aircraft_total=len(self.tracked),
            last_fetch_ok=bool(self.last_result and self.last_result.success),
            last_fetch_ms=self.last_result.elapsed_ms if self.last_result else 0.0,
            last_error=self.last_result.error if self.last_result else "",
            next_fetch_in_s=next_fetch,
            fetch_interval_s=interval_s,
            reliability_hint=hint,
        )

    def _reliability_hint(self, in_air: int, interval_s: float) -> str:
        if self.last_result and not self.last_result.success:
            return "API inaccessible — vérifiez votre connexion ou vos identifiants OpenSky."

        if in_air == 0:
            return (
                "Aucun avion en vol dans la zone. Essayez d'augmenter le rayon "
                "ou vérifiez si vous êtes loin des couloirs aériens."
            )
        if in_air >= 8:
            return "Excellente couverture — le radar serait très vivant chez vous."
        if in_air >= 3:
            return "Bonne couverture — le projet devrait être fiable à cet endroit."
        return (
            f"Couverture faible ({in_air} avion(s)). Fonctionnel mais peu animé "
            f"(rafraîchissement ~{interval_s:.0f}s)."
        )

    def project(self, lat: float, lon: float) -> tuple[int, int]:
        d_lon = lon - self.longitude
        d_lat = lat - self.latitude

        norm_east = d_lon / (2.0 * self.radius_deg)
        norm_north = d_lat / (2.0 * self.radius_deg)

        if self.compass_mode:
            heading_rad = math.radians(-self.heading_deg)
            cos_h = math.cos(heading_rad)
            sin_h = math.sin(heading_rad)
            rotated_east = norm_east * cos_h - norm_north * sin_h
            rotated_north = norm_east * sin_h + norm_north * cos_h
            norm_east = rotated_east
            norm_north = rotated_north

        x = int((norm_east + 0.5) * SCREEN_SIZE)
        y = int(SCREEN_SIZE - ((norm_north + 0.5) * SCREEN_SIZE))
        return x, y

    def visible_aircraft(self, now_ms: float) -> list[tuple[TrackedAircraft, int, int]]:
        items: list[tuple[TrackedAircraft, int, int]] = []
        for tracked in self.tracked.values():
            if tracked.state.on_ground:
                continue
            lat, lon = tracked.get_display_position(now_ms)
            x, y = self.project(lat, lon)
            if -20 <= x <= SCREEN_SIZE + 20 and -20 <= y <= SCREEN_SIZE + 20:
                items.append((tracked, x, y))
        return items

    def triangle_points(self, tracked: TrackedAircraft, x: int, y: int) -> list[tuple[float, float]]:
        track = tracked.state.true_track
        if self.compass_mode:
            track -= self.heading_deg

        dx = math.sin(math.radians(track))
        dy = -math.cos(math.radians(track))
        px = -dy
        py = dx

        length = 6.0
        width = 3.0
        tip = (x + dx * length, y + dy * length)
        left = (x - dx * length * 0.5 + px * width * 0.5, y - dy * length * 0.5 + py * width * 0.5)
        right = (x - dx * length * 0.5 - px * width * 0.5, y - dy * length * 0.5 - py * width * 0.5)
        return [tip, left, right]
