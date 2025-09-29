# osm_server.py
# Run: python osm_server.py
# Tools:
#  - geocode_place: name → (lat, lon, display_name)
#  - route_between: OSRM route between two places (walking|driving|cycling)
#  - versailles_itinerary: convenience to the Château de Versailles
#
# Returns structured JSON for LLM reasoning.

import os
import asyncio
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, Field
from fastmcp import MCP, tool

OSM_NOMINATIM = os.getenv("OSM_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
OSRM_ROUTE = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org/route/v1")
USER_AGENT = "les_4_MousquetAIres/1.0 (MCP fastmcp server)"

VERSAILLES_PLACE = "Château de Versailles, Versailles, France"
VERSAILLES_LAT = 48.8049
VERSAILLES_LON = 2.1204

app = MCP("osm-routing")


# --------- Models ---------
class GeocodeInput(BaseModel):
    place: str = Field(..., description="Freeform place name or address")


class RouteBetweenInput(BaseModel):
    origin: str = Field(..., description="Start place name/address")
    destination: str = Field(..., description="End place name/address")
    profile: Literal["walking", "driving", "cycling"] = Field("walking")


class VersaillesItineraryInput(BaseModel):
    origin: str = Field(..., description="Start place name/address")
    profile: Literal["walking", "driving", "cycling"] = Field("walking")


# --------- Helpers ---------
async def _geocode(client: httpx.AsyncClient, place: str) -> dict:
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


async def _route(client: httpx.AsyncClient, origin: tuple[float, float], destination: tuple[float, float],
                 profile: Literal["walking", "driving", "cycling"]) -> dict:
    o_lat, o_lon = origin
    d_lat, d_lon = destination
    url = f"{OSRM_ROUTE}/{profile}/{o_lon},{o_lat};{d_lon},{d_lat}"
    params = {"overview": "false", "steps": "true", "alternatives": "false", "annotations": "false", "geometries": "geojson"}
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
    }


# --------- Tools ---------
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
    Compute an itinerary using OSRM between two place names.
    Returns distance (m), duration (s), and compact step list.
    """
    async with httpx.AsyncClient() as client:
        o = await _geocode(client, inp.origin)
        d = await _geocode(client, inp.destination)
        route = await _route(client, (o["lat"], o["lon"]), (d["lat"], d["lon"]), inp.profile)

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
        "source": {"provider": "osrm", "endpoint": OSRM_ROUTE}
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
