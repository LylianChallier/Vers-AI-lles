"""
MCP servers for routing (OpenStreetMap/OSRM) and weather (Open‑Meteo/OpenWeather).

Run individually, e.g.:

  python mcp_servers/osm_server.py
  python mcp_servers/weather_server.py

Both servers expose tools compatible with the Model Context Protocol (MCP)
so MCP‑aware LLM clients (e.g., Claude Desktop) can call them.
"""

