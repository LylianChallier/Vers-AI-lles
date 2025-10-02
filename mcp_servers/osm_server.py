# osm_server.py
# Run: python osm_server.py
# Tools:
#  - geocode_place: name → (lat, lon, display_name)
#  - route_between: OSRM route between two places (walking|driving|cycling)
#  - versailles_itinerary: convenience to the Château de Versailles
#
# Returns structured JSON for LLM reasoning.

import os
from typing import Literal

import httpx
from pydantic import BaseModel, Field
try:
    from ._fastmcp_compat import MCP, tool, FASTMCP_AVAILABLE
except ImportError:  # pragma: no cover - allows running as script
    from _fastmcp_compat import MCP, tool, FASTMCP_AVAILABLE

OSM_NOMINATIM = os.getenv("OSM_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
OSRM_ROUTE = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org/route/v1")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
ORS_API_KEY = os.getenv("ORS_API_KEY")
LOCATIONIQ_KEY = os.getenv("LOCATIONIQ_KEY")
GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY")
OSM_CONTACT_EMAIL = os.getenv("OSM_CONTACT_EMAIL")
USER_AGENT = os.getenv(
    "OSM_USER_AGENT",
    f"les_4_MousquetAIres/1.0 (+{OSM_CONTACT_EMAIL or 'no-email'})"
)

VERSAILLES_PLACE = "Château de Versailles, Versailles, France"
VERSAILLES_LAT = 48.8049
VERSAILLES_LON = 2.1204

app = MCP("osm-routing")

if not FASTMCP_AVAILABLE:  # pragma: no cover - informational only
    import warnings

    warnings.warn(
        "fastmcp package unavailable - MCP stdio mode disabled; using fallback decorators",
        RuntimeWarning,
    )

class GeocodeInput(BaseModel):
    place: str = Field(..., description="Freeform place name or address")

class RouteBetweenInput(BaseModel):
    origin: str = Field(..., description="Start place name/address")
    destination: str = Field(..., description="End place name/address")
    profile: Literal["walking", "driving", "cycling"] = Field("walking")

class VersaillesItineraryInput(BaseModel):
    origin: str = Field(..., description="Start place name/address")
    profile: Literal["walking", "driving", "cycling"] = Field("walking")

async def _geocode_nominatim(client: httpx.AsyncClient, place: str) -> dict:
    params = {"q": place, "format": "json", "limit": 1, "addressdetails": 0}
    headers = {"User-Agent": USER_AGENT}
    r = await client.get(OSM_NOMINATIM, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"No geocoding result for '{place}'.")
    item = data[0]
    return {
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "display_name": item.get("display_name", place),
    }


async def _geocode_locationiq(client: httpx.AsyncClient, place: str) -> dict:
    if not LOCATIONIQ_KEY:
        raise RuntimeError("LOCATIONIQ_KEY not set")
    url = "https://us1.locationiq.com/v1/search"
    params = {"key": LOCATIONIQ_KEY, "q": place, "format": "json", "limit": 1}
    r = await client.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"No geocoding result for '{place}' (LocationIQ).")
    item = data[0]
    return {
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "display_name": item.get("display_name", place),
    }


async def _geocode_geoapify(client: httpx.AsyncClient, place: str) -> dict:
    if not GEOAPIFY_KEY:
        raise RuntimeError("GEOAPIFY_KEY not set")
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": place, "limit": 1, "apiKey": GEOAPIFY_KEY}
    r = await client.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features") or []
    if not feats:
        raise ValueError(f"No geocoding result for '{place}' (Geoapify).")
    props = feats[0]["properties"]
    return {
        "lat": float(props["lat"]),
        "lon": float(props["lon"]),
        "display_name": props.get("formatted") or place,
    }


async def _geocode(client: httpx.AsyncClient, place: str) -> dict:
    if LOCATIONIQ_KEY:
        try:
            return await _geocode_locationiq(client, place)
        except Exception:
            pass
    if GEOAPIFY_KEY:
        try:
            return await _geocode_geoapify(client, place)
        except Exception:
            pass
    return await _geocode_nominatim(client, place)


async def _route(client: httpx.AsyncClient, origin: tuple[float, float], destination: tuple[float, float],
                 profile: Literal["walking", "driving", "cycling"]) -> dict:
    """OSRM (public demo)"""
    o_lat, o_lon = origin
    d_lat, d_lon = destination
    url = f"{OSRM_ROUTE}/{profile}/{o_lon},{o_lat};{d_lon},{d_lat}"
    # Request a lightweight overview geometry for map display and per-step details for instructions
    params = {"overview": "simplified", "steps": "true", "alternatives": "false", "annotations": "false", "geometries": "geojson"}
    r = await client.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("Routing failed or no route found.")
    route = data["routes"][0]

    # Convert OSRM steps to a compact LLM-friendly list
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            man = step.get("maneuver", {})
            stype = man.get("type")
            modifier = man.get("modifier")
            road = step.get("name") or ""
            dist = int(step.get("distance", 0))
            entry = {
                "type": stype or "step",
                "modifier": modifier,
                "road": road if road else None,
                "distance_m": dist
            }
            steps.append(entry)

    return {
        "distance_m": int(route.get("distance", 0)),
        "duration_s": int(route.get("duration", 0)),
        "steps": steps[:200],  # cap just in case
        # GeoJSON LineString (lon,lat). Frontend can render after swapping to (lat,lon)
        "geometry": route.get("geometry"),
    }


async def _route_mapbox(client: httpx.AsyncClient, origin: tuple[float, float], destination: tuple[float, float],
                        profile: Literal["walking", "driving", "cycling"]) -> dict:
    if not MAPBOX_TOKEN:
        raise RuntimeError("MAPBOX_TOKEN not set")
    o_lat, o_lon = origin
    d_lat, d_lon = destination
    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{o_lon},{o_lat};{d_lon},{d_lat}"
    params = {
        "alternatives": "false",
        "overview": "simplified",
        "steps": "true",
        "geometries": "geojson",
        "language": "fr",
        "access_token": MAPBOX_TOKEN,
    }
    r = await client.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    routes = data.get("routes") or []
    if not routes:
        raise ValueError("Mapbox: no route returned")
    route = routes[0]
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            man = step.get("maneuver", {}) or {}
            steps.append({
                "type": man.get("type") or "step",
                "modifier": man.get("modifier"),
                "road": step.get("name") or None,
                "distance_m": int(step.get("distance", 0)),
            })
    return {
        "distance_m": int(route.get("distance", 0)),
        "duration_s": int(route.get("duration", 0)),
        "steps": steps[:200],
        "geometry": route.get("geometry"),
    }


def _ors_profile(profile: str) -> str:
    return {"walking": "foot-walking", "driving": "driving-car", "cycling": "cycling-regular"}.get(profile, "foot-walking")


async def _route_ors(client: httpx.AsyncClient, origin: tuple[float, float], destination: tuple[float, float],
                     profile: Literal["walking", "driving", "cycling"]) -> dict:
    if not ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY not set")
    o_lat, o_lon = origin
    d_lat, d_lon = destination
    url = f"https://api.openrouteservice.org/v2/directions/{_ors_profile(profile)}"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    payload = {"coordinates": [[o_lon, o_lat], [d_lon, d_lat]]}
    r = await client.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    feature = (data.get("features") or [None])[0]
    if not feature:
        raise ValueError("ORS: no route returned")
    props = feature["properties"]
    summary = props.get("summary") or {}
    segments = props.get("segments") or []
    steps = []
    for segment in segments:
        for step in segment.get("steps", []):
            steps.append({
                "type": "instruction",
                "modifier": None,
                "road": step.get("instruction"),
                "distance_m": int(step.get("distance", 0)),
            })
    return {
        "distance_m": int(summary.get("distance", 0)),
        "duration_s": int(summary.get("duration", 0)),
        "steps": steps[:200],
        "geometry": feature.get("geometry"),
    }


@app.tool()
async def geocode_place(inp: GeocodeInput) -> dict:
    """
    Geocode a place name via OSM Nominatim.
    """
    async with httpx.AsyncClient() as client:
        res = await _geocode(client, inp.place)
    return {"place": res["display_name"], "lat": res["lat"], "lon": res["lon"]}


@app.tool()
async def route_between(inp: RouteBetweenInput) -> dict:
    """
    Compute an itinerary between two place names with provider fallback.
    Returns distance (m), duration (s), and compact step list.
    """
    async with httpx.AsyncClient() as client:
        o = await _geocode(client, inp.origin)
        d = await _geocode(client, inp.destination)
        # Choose routing provider by available keys: Mapbox → ORS → OSRM
        try:
            if MAPBOX_TOKEN:
                route = await _route_mapbox(client, (o["lat"], o["lon"]), (d["lat"], d["lon"]), inp.profile)
                provider = "mapbox"
            elif ORS_API_KEY:
                route = await _route_ors(client, (o["lat"], o["lon"]), (d["lat"], d["lon"]), inp.profile)
                provider = "openrouteservice"
            else:
                route = await _route(client, (o["lat"], o["lon"]), (d["lat"], d["lon"]), inp.profile)
                provider = "osrm"
        except Exception:
            # Robust fallback chain
            try:
                route = await _route(client, (o["lat"], o["lon"]), (d["lat"], d["lon"]), inp.profile)
                provider = "osrm"
            except Exception:
                raise

    km = route["distance_m"] / 1000.0
    mins = round(route["duration_s"] / 60)
    return {
        "origin": {"name": o["display_name"], "lat": o["lat"], "lon": o["lon"]},
        "destination": {"name": d["display_name"], "lat": d["lat"], "lon": d["lon"]},
        "profile": inp.profile,
        "distance_m": route["distance_m"],
        "duration_s": route["duration_s"],
        "duration_min_approx": mins,
        "distance_km_approx": round(km, 1),
        "steps": route["steps"],
        "geometry": route.get("geometry"),
        "source": {
            "provider": provider,
            "endpoint": OSRM_ROUTE if provider == "osrm" else ("mapbox" if provider == "mapbox" else "openrouteservice")
        }
    }


@app.tool()
async def versailles_itinerary(inp: VersaillesItineraryInput) -> dict:
    """
    Convenience route to the Château de Versailles from an origin place.
    """
    payload = RouteBetweenInput(origin=inp.origin, destination=VERSAILLES_PLACE, profile=inp.profile)
    return await route_between(payload)


if __name__ == "__main__":
    app.run_stdio()
