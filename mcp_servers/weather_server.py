# weather_server.py
# Run: python weather_server.py
# Tools:
#  - get_weather_summary: windowed hourly summary + decision flags (FR/EN-agnostic)
#  - versailles_weather_summary: convenience wrapper for the Château coordinates
#
# Notes:
#  - Returns structured JSON (stable keys) so LLMs can reason without guessing.
#  - Emits rule_ids you can map in RAG (e.g., "tips.rain.not_cancel").

import os
import math
import asyncio
import datetime as dt
from typing import Optional, Literal
from xmlrpc import client

import httpx
from pydantic import BaseModel, Field, field_validator
try:
    from ._fastmcp_compat import MCP, tool, FASTMCP_AVAILABLE
except ImportError:  # pragma: no cover - allows running as script
    from _fastmcp_compat import MCP, tool, FASTMCP_AVAILABLE

# --------- Config ---------
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5"   # /onecall (2.5)
OPEN_METEO_BASE = os.getenv("OPEN_METEO_BASE", "https://api.open-meteo.com/v1/forecast")
OSM_NOMINATIM = os.getenv("OSM_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")

# Château de Versailles (default)
VERSAILLES_LAT = 48.8049
VERSAILLES_LON = 2.1204
TZ = "Europe/Paris"

app = MCP("weather-tools")

if not FASTMCP_AVAILABLE:  # pragma: no cover - informational only
    import warnings

    warnings.warn(
        "fastmcp package unavailable - MCP stdio mode disabled; using fallback decorators",
        RuntimeWarning,
    )


# --------- Models ---------
class WeatherWindowInput(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD (local date for Europe/Paris)")
    start_time: str = Field(..., description="HH:MM 24h")
    duration_min: int = Field(..., ge=30, le=1440, description="Visit window length in minutes (30..1440)")
    place: Optional[str] = Field(None, description="Freeform place name; if omitted use lat/lon")
    lat: Optional[float] = Field(None, description="Latitude (ignored if 'place' given)")
    lon: Optional[float] = Field(None, description="Longitude (ignored if 'place' given)")
    lang: Literal["auto", "fr", "en"] = Field("auto", description="Language hint for phrasing (advice field)")

    @field_validator("date")
    @classmethod
    def _valid_date(cls, v: str) -> str:
        try:
            dt.date.fromisoformat(v)
            return v
        except Exception:
            raise ValueError("date must be YYYY-MM-DD")

    @field_validator("start_time")
    @classmethod
    def _valid_time(cls, v: str) -> str:
        try:
            hh, mm = v.split(":")
            h, m = int(hh), int(mm)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return v
        except Exception:
            pass
        raise ValueError("start_time must be HH:MM (24h)")


class WeatherDailyInput(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    place: Optional[str] = Field(None, description="Freeform place name")
    lat: Optional[float] = Field(None)
    lon: Optional[float] = Field(None)


# --------- Helpers ---------
async def _geocode_place(client: httpx.AsyncClient, place: str) -> dict:
    params = {"q": place, "format": "json", "limit": 1, "addressdetails": 0}
    headers = {"User-Agent": "les_4_MousquetAIres/1.0 (MCP fastmcp server)"}
    r = await client.get(OSM_NOMINATIM, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"No geocoding result for '{place}'.")
    item = data[0]
    return {"lat": float(item["lat"]), "lon": float(item["lon"]), "display_name": item.get("display_name", place)}


async def _open_meteo_hourly(client: httpx.AsyncClient, lat: float, lon: float, date: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,precipitation,windspeed_10m",
        "start_date": date,
        "end_date": date,
        "timezone": TZ,
    }
    try:
        r = await client.get(OPEN_METEO_BASE, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            params.pop("start_date", None)
            params.pop("end_date", None)
            params["forecast_days"] = 16
            r2 = await client.get(OPEN_METEO_BASE, params=params, timeout=30)
            r2.raise_for_status()
            return r2.json()
        raise

async def _openweather_daily(client: httpx.AsyncClient, lat: float, lon: float, date: dt.date) -> Optional[dict]:
    """Try OpenWeather One Call (daily up to ~7 days). Falls back to None otherwise."""
    if not OPENWEATHER_KEY:
        return None
    params = {"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHER_KEY, "exclude": "minutely,hourly,alerts"}
    url = f"{OPENWEATHER_BASE}/onecall"
    r = await client.get(url, params=params, timeout=30)
    if r.status_code >= 400:
        return None
    data = r.json()
    target = date.toordinal()
    best = None
    for day in data.get("daily", []):
        d = dt.datetime.utcfromtimestamp(day.get("dt", 0)).date()
        if d.toordinal() == target:
            best = {
                "date": d.isoformat(),
                "tmin_c": day.get("temp", {}).get("min"),
                "tmax_c": day.get("temp", {}).get("max"),
                "precip_mm": (day.get("rain") or 0.0),
                "code": day.get("weather", [{}])[0].get("id"),
                "desc": day.get("weather", [{}])[0].get("description"),
                "provider": "openweather",
            }
            break
    return best


def _label_from_hourly(hourly_rows: list[dict]) -> tuple[str, dict, str]:
    # Derive a compact decision layer from hourly data
    any_rain = any((h.get("precip_prob", 0) or 0) >= 30 or (h.get("precip_mm", 0) or 0) >= 0.3 for h in hourly_rows)
    heavy = any((h.get("precip_mm", 0) or 0) >= 2.0 for h in hourly_rows)
    heat = any((h.get("temp_c", 0) or 0) >= 30 for h in hourly_rows)
    windy = any((h.get("wind_kmh", 0) or 0) >= 35 for h in hourly_rows)

    if heavy:
        label = "heavy_rain"
    elif any_rain and heat:
        label = "mixed"
    elif any_rain:
        label = "rain_risk"
    elif heat:
        label = "heat"
    elif windy:
        label = "windy"
    else:
        label = "pleasant"

    flags = {
        "prefer_indoor": label in ("rain_risk", "heavy_rain", "mixed"),
        "heat_precautions": label in ("heat", "mixed"),
        "remind_water_fountains": label in ("heat", "mixed"),
        "night_fountains_not_cancelled": True,  # rule from Tips
    }

    advice_map = {
        "heavy_rain": "Prévoir un parcours indoor et des alternatives courtes.",
        "rain_risk": "Ayez un plan pluie avec étapes indoor proches.",
        "heat": "Favoriser matin/indoor et points d’eau.",
        "mixed": "Alterner indoor/outdoor; prévoir pauses et eau.",
        "windy": "Itinéraire abrité recommandé.",
        "pleasant": "Conditions favorables.",
    }
    return label, flags, advice_map[label]


def _hm_to_minutes(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hm(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


# --------- Tools ---------
@app.tool()
async def get_weather_summary(inp: WeatherWindowInput) -> dict:
    """
    Summarize hourly weather for a visit window and expose decision flags.
    If 'place' is provided, geocode it; else use lat/lon (or Versailles by default).
    """
    date = dt.date.fromisoformat(inp.date)
    start_min = _hm_to_minutes(inp.start_time)
    end_min = start_min + int(inp.duration_min)

    async with httpx.AsyncClient() as client:
        if inp.place:
            loc = await _geocode_place(client, inp.place)
            lat, lon, display = loc["lat"], loc["lon"], loc["display_name"]
        else:
            lat = inp.lat if inp.lat is not None else VERSAILLES_LAT
            lon = inp.lon if inp.lon is not None else VERSAILLES_LON
            display = f"{lat:.5f},{lon:.5f}"

        # Prefer Open-Meteo hourly (robust + free)
        data = await _open_meteo_hourly(client, lat, lon, inp.date)
        H = data.get("hourly", {}) or {}
        times = H.get("time", []) or []
        temps = H.get("temperature_2m", []) or []
        probs = H.get("precipitation_probability", []) or []
        precs = H.get("precipitation", []) or []
        winds = H.get("windspeed_10m", []) or []

        hourly_rows = []
        for i, ts in enumerate(times):
            # ts format 'YYYY-MM-DDTHH:00'
            hh = int(ts[11:13])
            mm = int(ts[14:16])
            mins = hh * 60 + mm
            if start_min <= mins <= end_min:
                row = {
                    "ts": f"{ts}+02:00",  # simple hint; adjust if you need exact DST
                    "temp_c": temps[i] if i < len(temps) else None,
                    "precip_mm": precs[i] if i < len(precs) else None,
                    "precip_prob": probs[i] if i < len(probs) else None,
                    "wind_kmh": winds[i] if i < len(winds) else None,
                }
                hourly_rows.append(row)

        label, flags, advice = _label_from_hourly(hourly_rows)
        return {
            "window": {"place": display, "date": inp.date, "start": inp.start_time, "end": _minutes_to_hm(end_min), "tz": TZ},
            "summary": {
                "label": label,
                "advice": advice if inp.lang != "en" else "See indoor/heat precautions based on forecast.",
                "flags": flags,
                "rationale": "Derived from hourly forecast (Open-Meteo)."
            },
            "hourly": hourly_rows,
            "source": {"provider": "open-meteo", "endpoint": OPEN_METEO_BASE},
            "support": [{"rule_id": "tips.rain.not_cancel", "hint": "Rain does not cancel night fountains."}]
        }


@app.tool()
async def versailles_weather_summary(date: str, start_time: str, duration_min: int) -> dict:
    """
    Convenience wrapper for the Château de Versailles.
    """
    payload = WeatherWindowInput(
        date=date, start_time=start_time, duration_min=duration_min,
        lat=VERSAILLES_LAT, lon=VERSAILLES_LON
    )
    return await get_weather_summary(payload)


@app.tool()
async def get_weather_daily(inp: WeatherDailyInput) -> dict:
    """
    Single-day summary (min/max/precip) using OpenWeather if available, else Open-Meteo daily.
    """
    d = dt.date.fromisoformat(inp.date)
    async with httpx.AsyncClient() as client:
        if inp.place:
            loc = await _geocode_place(client, inp.place)
            lat, lon, display = loc["lat"], loc["lon"], loc["display_name"]
        else:
            lat = inp.lat if inp.lat is not None else VERSAILLES_LAT
            lon = inp.lon if inp.lon is not None else VERSAILLES_LON
            display = f"{lat:.5f},{lon:.5f}"

        ow = await _openweather_daily(client, lat, lon, d)
        if ow:
            return {
                "place": display, "date": ow["date"],
                "tmin_c": ow["tmin_c"], "tmax_c": ow["tmax_c"], "precip_mm": ow["precip_mm"],
                "conditions": ow.get("desc"), "provider": ow["provider"]
            }

        # Fallback: Open-Meteo daily via forecast API (meteofrance endpoint supports hourly best; keep this minimal)
        # Use a simple hourly window approximation for min/max/precip over the day
        data = await _open_meteo_hourly(client, lat, lon, inp.date)
        H = data.get("hourly", {}) or {}
        temps = [t for t in (H.get("temperature_2m") or []) if t is not None]
        precs = [p for p in (H.get("precipitation") or []) if p is not None]
        return {
            "place": display, "date": inp.date,
            "tmin_c": min(temps) if temps else None,
            "tmax_c": max(temps) if temps else None,
            "precip_mm": sum(precs) if precs else 0.0,
            "conditions": None, "provider": "open-meteo"
        }


if __name__ == "__main__":
    # fastmcp runs over stdio by default; perfect for LLM tool-calling
    app.run_stdio()
