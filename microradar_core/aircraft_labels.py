"""Aircraft display helpers."""

from __future__ import annotations

from microradar_core.opensky_client import Aircraft


def aircraft_altitude_m(aircraft: Aircraft) -> int | None:
    """Barometric altitude in metres, falling back to geometric altitude."""
    if aircraft.baro_altitude > 0:
        return int(round(aircraft.baro_altitude))
    if aircraft.geo_altitude > 0:
        return int(round(aircraft.geo_altitude))
    return None


def aircraft_info_label(aircraft: Aircraft) -> str:
    callsign = aircraft.callsign.strip()
    altitude_m = aircraft_altitude_m(aircraft)
    if altitude_m is not None:
        return f"{callsign}\n{altitude_m}m"
    return callsign
