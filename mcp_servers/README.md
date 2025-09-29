**Overview**
- Provides two MCP servers your LLM can call via the Model Context Protocol (MCP):
  - `osm-routing` for OpenStreetMap geocoding + OSRM routing
  - `weather` for Open‑Meteo (no key) and optionally OpenWeather (with API key)

**Tools**
- `osm_server.py`
  - `geocode_place(place)` → text with name + lat/lon
  - `route_between(origin, destination, profile)` → distance, ETA, steps
  - `versailles_itinerary(origin, profile)` → convenience route to “Château de Versailles, Versailles, France”
- `weather_server.py`
  - `versailles_weather_on_date(date)` → daily summary for Versailles (YYYY-MM-DD)
  - `weather_at_place_on_date(place, date)` → daily summary for any place

**Install**
- Add to your backend requirements (already updated): `mcp`, `httpx`.
- With Docker Compose: rebuild the backend image to install new deps:
  - `docker compose build backend`
  - Or locally: `pip install -r backend/requirements.txt`

**Run (stdio)**
- From project root:
  - `python mcp_servers/osm_server.py`
  - `python mcp_servers/weather_server.py`
- MCP‑aware clients (e.g., Claude Desktop) spawn these via stdio.

Or with Docker Compose (stdio via docker exec):
- `docker compose up -d mcp-osm mcp-weather`
- Then run inside the container so stdio is connected to your client:
  - `docker exec -i mcp-osm python /app/mcp_servers/osm_server.py`
  - `docker exec -i mcp-weather python /app/mcp_servers/weather_server.py`

**Claude Desktop example config**
- Add entries to `claude_desktop_config.json` (path varies by OS):
  - "mcpServers": {
    - EITHER run locally:
      - "osm-routing": {"command": "python", "args": ["/absolute/path/to/mcp_servers/osm_server.py"]},
      - "weather": {"command": "python", "args": ["/absolute/path/to/mcp_servers/weather_server.py"]}
    - OR run in Docker using exec (spawn via stdio in the container):
      - "osm-routing": {"command": "docker", "args": ["exec", "-i", "mcp-osm", "python", "/app/mcp_servers/osm_server.py"]},
      - "weather": {"command": "docker", "args": ["exec", "-i", "mcp-weather", "python", "/app/mcp_servers/weather_server.py"]}
  - }

**Environment**
- Optional: `OPENWEATHER_API_KEY` for OpenWeather daily forecasts (preferred when present).
- Defaults: Open‑Meteo for weather, OSRM public demo server for routing, OSM Nominatim for geocoding.

**Typical flow for Versailles visit**
- Ask the LLM to call:
  - `versailles_itinerary(origin="Paris, France", profile="walking" | "driving" | "cycling")`
  - `versailles_weather_on_date(date="YYYY-MM-DD")`

**Notes**
- OSRM demo server and Nominatim are rate‑limited for fair use; for production, deploy your own or use a paid provider.
- Dates far in the past/future may not be available from Open‑Meteo forecast; for past dates, historical endpoints may be needed.
