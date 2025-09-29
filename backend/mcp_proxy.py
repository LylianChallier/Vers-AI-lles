from typing import Literal, Optional

from fastapi import HTTPException

# Import the async tool functions directly from MCP servers
# These functions use httpx under the hood and return structured dicts.
from mcp_servers.osm_server import (
    versailles_itinerary as _osm_versailles_itinerary,
    route_between as _osm_route_between,
    VersaillesItineraryInput,
    RouteBetweenInput,
)

from mcp_servers.weather_server import (
    WeatherWindowInput,
    WeatherDailyInput,
    versailles_weather_summary as _versailles_weather_summary,
    get_weather_summary as _get_weather_summary,
    get_weather_daily as _get_weather_daily,
)


async def itinerary_to_versailles(origin: str, profile: Literal["walking", "driving", "cycling"] = "walking") -> dict:
    """Convenience route from an origin to Château de Versailles."""
    try:
        payload = VersaillesItineraryInput(origin=origin, profile=profile)
        return await _osm_versailles_itinerary(payload)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Itinerary tool failed: {e}")


async def route_between_places(origin: str, destination: str, profile: Literal["walking", "driving", "cycling"] = "walking") -> dict:
    """Route between two places using OSRM via the OSM MCP tool."""
    try:
        payload = RouteBetweenInput(origin=origin, destination=destination, profile=profile)
        return await _osm_route_between(payload)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Routing tool failed: {e}")


async def versailles_weather(date: str, start_time: str = "14:00", duration_min: int = 180) -> dict:
    """Windowed weather summary for Versailles on a given date/time window."""
    try:
        return await _versailles_weather_summary(date=date, start_time=start_time, duration_min=duration_min)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Weather tool failed: {e}")


async def weather_at_place(place: str, date: str, start_time: str = "14:00", duration_min: int = 180, lang: str = "auto") -> dict:
    """Windowed weather summary for any place using OSM geocoding + Open-Meteo."""
    try:
        payload = WeatherWindowInput(
            date=date, start_time=start_time, duration_min=duration_min, place=place, lang=lang
        )
        return await _get_weather_summary(payload)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Weather tool failed: {e}")


async def weather_daily(date: str, place: Optional[str] = None) -> dict:
    """Single-day min/max/precip summary (OpenWeather if available, else Open-Meteo)."""
    try:
        payload = WeatherDailyInput(date=date, place=place)
        return await _get_weather_daily(payload)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Daily weather tool failed: {e}")
