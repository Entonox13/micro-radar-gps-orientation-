"""GPS coordinate parsing — shared by desktop simulator and Android app."""

from __future__ import annotations

import re

_WS_RE = re.compile(r"[\s\u00a0\u2009\u202f]+")
_COORD_PAIR_RE = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d+(?:[.,]\d+)?)",
)


def _normalize_coordinate_text(value: str) -> str:
    cleaned = value.strip()
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("º", "").replace("°", "")
    cleaned = re.sub(r"\s*[NSEW]\s*", " ", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def parse_coordinate(value: str) -> float:
    """Parse decimal degrees, accepting comma as decimal separator."""
    cleaned = value.strip()
    cleaned = _WS_RE.sub("", cleaned)
    if cleaned.count(",") == 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def parse_coordinate_pair(value: str) -> tuple[float, float]:
    """Parse 'lat, lon' pasted from Google Maps or similar."""
    cleaned = _normalize_coordinate_text(value)
    if not cleaned:
        raise ValueError("Format attendu : latitude, longitude")

    if re.search(r",\s", cleaned):
        parts = re.split(r",\s+", cleaned, maxsplit=1)
        if len(parts) == 2:
            return parse_coordinate(parts[0]), parse_coordinate(parts[1])

    match = _COORD_PAIR_RE.search(cleaned)
    if not match:
        raise ValueError("Format attendu : latitude, longitude")
    return parse_coordinate(match.group(1)), parse_coordinate(match.group(2))


def validate_coordinates(lat: float, lon: float) -> None:
    if not -90.0 <= lat <= 90.0:
        raise ValueError("La latitude doit être entre -90 et 90.")
    if not -180.0 <= lon <= 180.0:
        raise ValueError("La longitude doit être entre -180 et 180.")
