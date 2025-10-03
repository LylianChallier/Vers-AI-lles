# Versailles Concierge — Les 4 MousquetAIres

AI concierge built at the Datacraft × Château de Versailles hackathon. It blends a FastAPI + LangChain backend with a React (Vite) web application, MCP tool servers for weather and routing, and optional Streamlit prototypes.

> 🇫🇷 Le projet rassemble un agent conversationnel multilingue capable de répondre aux visiteurs, planifier des itinéraires dans Versailles et recommander des activités en s'appuyant sur des graphes de connaissances et des sources météo.

---

## Project layout

| Path | Description |
| --- | --- |
| `backend/` | FastAPI service orchestrating the LangChain/LangGraph agent and exposing `/chat` + tool endpoints |
| `web/` | React + Vite front-end (main UI: "Versailles Concierge") with the new crown/chat-bubble branding |
| `mcp_servers/` | Model Context Protocol servers (weather + OSM routing bridges) used by the agent |
| `frontend/` | Legacy Streamlit prototype kept for reference |
| `docker-compose.yaml` | Spins up the backend, MCP services, and optional Streamlit UI |

---

## Prerequisites

- Docker & Docker Compose **or** Python 3.11 + Node.js ≥ 18
- A `.env` file at repository root with the required API keys
- (Optional) Vercel CLI for production deployment of the Vite front-end

### Environment variables

Copy `.env` from the sample provided and populate the keys that matter to your deployment:

- `MISTRAL_API_KEY`, `MISTRAL_MODEL`, `EMBEDDING_MODEL` for the LLM
- Weather + routing providers: `OPENWEATHER_API_KEY`, `OPEN_METEO_BASE`, `OSM_NOMINATIM_URL`, `OSRM_BASE_URL`
- Optional paid providers: `MAPBOX_TOKEN`, `ORS_API_KEY`, `LOCATIONIQ_KEY`, `GEOAPIFY_KEY`
- Front-end build variable: `VITE_API_BASE_URL` (defaults to `http://localhost:8002`)
- `OSM_CONTACT_EMAIL` is recommended by OpenStreetMap for bulk usage

Keep the file out of version control; each service (Docker, Vite build, FastAPI) reads from the root `.env`.

---

## Quick start (Docker Compose)

```bash
docker compose up --build
```

Services become available when the logs show `Uvicorn running on http://0.0.0.0:8002`. The FastAPI docs live at [http://localhost:8002/docs](http://localhost:8002/docs). The Streamlit prototype (if you keep the `frontend` service) publishes on [http://localhost:8501](http://localhost:8501).

To rebuild after changing dependencies:

```bash
docker compose up --build --force-recreate
```

Stop everything with `docker compose down`.

---

## Local development (without Docker)

### Backend (FastAPI + LangChain)

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
uvicorn backend.app:app --host 0.0.0.0 --port 8002 --reload
```

The interactive docs and OpenAPI explorer remain at `http://localhost:8002/docs`.

### MCP bridges

Weather and OSM tooling run inside the API process, but you can test them directly via the scripts in `mcp_servers/`. Example:

```bash
python mcp_servers/osm_server.py --help
```

### Web front-end (Vite React)

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173` and ensure `VITE_API_BASE_URL` points to your backend. The production build command is `npm run build` (output in `web/dist`). The `web/public/icons` directory now holds the crown + chat bubble assets wired into `index.html` and the header component.

### Legacy Streamlit app (optional)

```bash
cd frontend
pip install -r requirements.txt
streamlit run front.py
```

It connects to the same API endpoints exposed by the FastAPI service.

---

## API overview

Key routes exposed by `backend/app.py`:

- `POST /chat` — evaluation endpoint returning a short-form answer (stateless)
- `POST /` — conversational agent with session support, itinerary and plan payloads
- `POST /tools/weather` — summarize weather window for a date/time span
- `POST /tools/versailles_route` — detailed itinerary recommendations
- `POST /tools/route` / `POST /tools/route_multi` — routing helpers (single or multi-stop)
- `POST /tools/share_location` — stores the visitor location for context-aware replies
- `POST /tools/recalc_plan` — refreshes a visit plan when conditions change
- `GET /chat/sessions` & `DELETE /chat/sessions/{session_id}` — manage cached conversation state

Swagger UI (`/docs`) and ReDoc (`/redoc`) give payload schemas and sample bodies.

---

## Deployment notes

- **Web app (Vite):** push the repository to GitHub and import the `web/` folder into Vercel. Use `npm run build` as build command and `dist` as the output directory. Populate the same `VITE_*` variables under Project → Settings → Environment Variables.
- **Backend:** deploy on a FastAPI-friendly host (Railway, Render, Fly.io, Azure Container Apps, etc.) or ship the Docker image built from `backend/Dockerfile`. Remember to provide the same `.env` variables and open port `8002`.
- **Static icons:** the favicon bundle already lives in `web/public/icons` and is referenced by `<link rel="icon">`, the header brand image, and Apple touch metadata.

---

## Troubleshooting

- Missing API keys → most endpoints rely on third-party providers; check your `.env` values and restart.
- CORS errors in the browser → confirm the backend host is listed in `VITE_API_BASE_URL` and that FastAPI is reachable.
- Unexpected agent answers → wipe cached sessions via `DELETE /chat/sessions/{session_id}` or clear `localStorage` (`versailles-concierge-*` keys).
- Docker build failures → ensure you have internet access for Python package installation and re-run with `--build`.

---

Built with ❤️ by the 4 MousquetAIres for the Château de Versailles hackathon — contributions and suggestions welcome!

