"""Shared radar logic for desktop simulator and Android app."""

from microradar_core.coordinates import (
    parse_coordinate,
    parse_coordinate_pair,
    validate_coordinates,
)
from microradar_core.opensky_client import Aircraft, FetchResult, OpenSkyClient
from microradar_core.radar_engine import RadarEngine, RadarStats, SCREEN_SIZE, TrackedAircraft

__all__ = [
    "Aircraft",
    "FetchResult",
    "OpenSkyClient",
    "RadarEngine",
    "RadarStats",
    "SCREEN_SIZE",
    "TrackedAircraft",
    "parse_coordinate",
    "parse_coordinate_pair",
    "validate_coordinates",
]
