"""OpenSky Network API client — mirrors the ESP32 firmware auth + fetch flow."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

CREDENTIALS_PATH = Path(__file__).with_name("credentials.json")


def load_credentials_file(path: Path = CREDENTIALS_PATH) -> tuple[str, str]:
    """Load OpenSky OAuth2 credentials from credentials.json (OpenSky account export)."""
    if not path.exists():
        return "", ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "", ""

    client_id = str(data.get("clientId") or data.get("client_id") or "").strip()
    client_secret = str(data.get("clientSecret") or data.get("client_secret") or "").strip()
    return client_id, client_secret


@dataclass
class Aircraft:
    icao24: str
    callsign: str
    origin_country: str
    time_position: int
    last_contact: int
    longitude: float
    latitude: float
    baro_altitude: float
    on_ground: bool
    velocity: float
    true_track: float
    vertical_rate: float
    geo_altitude: float
    squawk: str
    spi: bool
    position_source: int
    category: int


@dataclass
class FetchResult:
    success: bool
    aircraft: list[Aircraft]
    status_code: int
    error: str
    elapsed_ms: float


def parse_aircraft(state: list[Any]) -> Aircraft:
    def s(idx: int, default: str = "") -> str:
        v = state[idx] if idx < len(state) else None
        return default if v is None else str(v).strip()

    def f(idx: int, default: float = 0.0) -> float:
        v = state[idx] if idx < len(state) else None
        return default if v is None else float(v)

    def i(idx: int, default: int = 0) -> int:
        v = state[idx] if idx < len(state) else None
        return default if v is None else int(v)

    def b(idx: int, default: bool = False) -> bool:
        v = state[idx] if idx < len(state) else None
        return default if v is None else bool(v)

    return Aircraft(
        icao24=s(0),
        callsign=s(1),
        origin_country=s(2),
        time_position=i(3),
        last_contact=i(4),
        longitude=f(5),
        latitude=f(6),
        baro_altitude=f(7),
        on_ground=b(8),
        velocity=f(9),
        true_track=f(10),
        vertical_rate=f(11),
        geo_altitude=f(13),
        squawk=s(14),
        spi=b(15),
        position_source=i(16),
        category=i(17),
    )


class OpenSkyClient:
    TOKEN_URL = (
        "https://auth.opensky-network.org/auth/realms/opensky-network/"
        "protocol/openid-connect/token"
    )
    STATES_URL = "https://opensky-network.org/api/states/all"

    ANONYMOUS_TOKENS_PER_DAY = 400
    AUTHED_TOKENS_PER_DAY = 4000
    TOKEN_BUFFER = 3

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "MicroRadar-Simulator/1.0"})
        self._bearer_token = ""
        self._token_expiry = 0.0
        self.client_id = ""
        self.client_secret = ""

    def set_credentials(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self._bearer_token = ""
        self._token_expiry = 0.0

    def fetch_interval_ms(self, battery_mode: bool = False) -> int:
        ms_per_day = 24 * 60 * 60 * 1000
        if self.client_id and self.client_secret:
            budget = self.AUTHED_TOKENS_PER_DAY - self.TOKEN_BUFFER
        else:
            budget = self.ANONYMOUS_TOKENS_PER_DAY - self.TOKEN_BUFFER
        interval = ms_per_day // budget
        if battery_mode:
            interval = int(interval * 1.5)
        return interval

    def _get_token(self) -> str:
        if not self.client_id or not self.client_secret:
            return ""

        now = time.time()
        if self._bearer_token and now < self._token_expiry:
            return self._bearer_token

        response = self._session.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token", "")
        if not token:
            raise RuntimeError("OpenSky token response missing access_token")

        self._bearer_token = token
        self._token_expiry = now + (29 * 60)
        return token

    def fetch_states(
        self,
        latitude: float,
        longitude: float,
        radius_deg: float,
    ) -> FetchResult:
        params = {
            "lamin": latitude - radius_deg,
            "lamax": latitude + radius_deg,
            "lomin": longitude - radius_deg,
            "lomax": longitude + radius_deg,
        }
        headers: dict[str, str] = {}
        try:
            token = self._get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        except Exception as exc:
            return FetchResult(False, [], 0, f"Auth failed: {exc}", 0.0)

        started = time.perf_counter()
        try:
            response = self._session.get(
                self.STATES_URL,
                params=params,
                headers=headers,
                timeout=20,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if response.status_code != 200:
                return FetchResult(
                    False,
                    [],
                    response.status_code,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    elapsed_ms,
                )

            payload = response.json()
            states = payload.get("states") or []
            aircraft = [parse_aircraft(state) for state in states if state]
            return FetchResult(True, aircraft, response.status_code, "", elapsed_ms)
        except requests.RequestException as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return FetchResult(False, [], 0, str(exc), elapsed_ms)
