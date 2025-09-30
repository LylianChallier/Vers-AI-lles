from __future__ import annotations
import asyncio
import re
from typing import Optional

# Import the coroutine tools and their input models (work even without fastmcp)
from mcp_servers.weather_server import WeatherWindowInput, get_weather_summary
from mcp_servers.osm_server import (
    RouteBetweenInput,
    VersaillesItineraryInput,
    route_between,
    versailles_itinerary,
)


def _run(coro):
    """Run an async coroutine from sync code safely."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    else:
        return asyncio.run(coro)


def _normalize_hhmm(s: str) -> str:
    """Normalize user-provided times like '10h30' to HH:MM."""
    s = s.strip().lower().replace("h", ":").replace(" ", "")
    m = re.match(r"^(\d{1,2}):?(\d{2})?$", s)
    if not m:
        return "10:00"
    h = int(m.group(1))
    mm = m.group(2) or "00"
    return f"{max(0, min(23, h)):02d}:{max(0, min(59, int(mm))):02d}"


def _parse_duration_to_min(s: Optional[str]) -> int:
    """Convert flexible duration expressions to minutes."""
    if not s:
        return 180
    s = s.strip().lower()
    m = re.match(r"^(?:(\d{1,2})\s*h(?:\s*(\d{1,2}))?)$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r"^(\d+)\s*(?:min|m)?$", s)
    if m:
        return int(m.group(1))
    return 180


def weather_summary_sync(
    date: str,
    start_time: str,
    duration_text: Optional[str],
    place: Optional[str] = "Château de Versailles, France",
    lang: str = "fr",
) -> dict:
    """Fetch a weather summary synchronously via MCP weather tool."""
    payload = WeatherWindowInput(
        date=date,
        start_time=_normalize_hhmm(start_time),
        duration_min=_parse_duration_to_min(duration_text),
        place=place,
        lang="fr" if lang.startswith("fr") else "auto",
    )
    return _run(get_weather_summary(payload))


def versailles_itinerary_sync(origin: str, profile: str = "walking") -> dict:
    """Compute an itinerary from the MCP OSM server."""
    payload = VersaillesItineraryInput(origin=origin, profile=profile)  # type: ignore[arg-type]
    return _run(versailles_itinerary(payload))


def route_between_sync(origin: str, destination: str, profile: str = "walking") -> dict:
    """Compute a route between two places via MCP OSM server."""
    payload = RouteBetweenInput(
        origin=origin,
        destination=destination,
        profile=profile,
    )  # type: ignore[arg-type]
    return _run(route_between(payload))


__all__ = [
    "weather_summary_sync",
    "versailles_itinerary_sync",
    "route_between_sync",
]
