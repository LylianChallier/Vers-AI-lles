from dotenv import load_dotenv
import os
from datetime import datetime
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional

from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

from mcp_servers.weather_server import (
    WeatherWindowInput, WeatherDailyInput,
    get_weather_summary, versailles_weather_summary, get_weather_daily
)

from backend.schemas import PlanRequest, PlanResponse
from backend.planner import plan

app = FastAPI(title="Les 4 MousquetAIres – Versailles Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ease local demos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Chat (as you had) ----------
model = init_chat_model("mistral-large-latest", model_provider="mistralai")
USE_LLM_RENDER = os.getenv("USE_LLM_RENDER", "0") == "1"

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

chat_sessions: Dict[str, ConversationBufferMemory] = {}

@app.post("/chat", response_model=ChatResponse)
def chat_with_agent(chat_message: ChatMessage):
    try:
        if chat_message.session_id not in chat_sessions:
            chat_sessions[chat_message.session_id] = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )
        memory = chat_sessions[chat_message.session_id]
        ai_message = model.invoke(chat_message.message)
        text_content = ai_message.content
        memory.chat_memory.add_user_message(chat_message.message)
        memory.chat_memory.add_ai_message(text_content)
        return ChatResponse(response=text_content, session_id=chat_message.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent: {str(e)}")

# ---------- NEW: /plan for the quantitative eval ----------
@app.post("/plan", response_model=PlanResponse)
async def make_plan(req: PlanRequest):
    try:
        date_str = req.date or datetime.now().strftime("%Y-%m-%d")
        start_hm = req.start_time or "14:00"
        duration = req.duration_min or 180

        weather_payload = None
        try:
            weather_payload = await versailles_weather_summary(
                date=date_str, start_time=start_hm, duration_min=duration
            )
        except Exception:
            weather_payload = None

        result = plan(req, weather=weather_payload)

        if weather_payload and weather_payload.get("summary"):
            summary = weather_payload["summary"]
            label = summary.get("label")
            advice = summary.get("advice")
            if label:
                result.warnings.append(f"Météo: {label}")
            if advice:
                result.alternatives.insert(0, f"Conseil météo: {advice}")

        if USE_LLM_RENDER:
            brief = {
                "itinerary": [s.model_dump() for s in result.itinerary],
                "tickets": [t.model_dump() for t in result.tickets],
                "warnings": result.warnings,
                "alternatives": result.alternatives,
                "weather": (weather_payload or {}).get("summary"),
            }
            prompt = (
                "Rédige une réponse claire et synthétique (<= 180 mots) pour un visiteur. "
                "Inclure: chronologie des étapes, billets/conseils, et un paragraphe météo (pluie/chaleur/vent) si utile. "
                "Voilà les données:\n"
                f"{brief}"
            )
            try:
                ai_message = model.invoke(prompt)
                if getattr(ai_message, "content", None):
                    result.reponse = ai_message.content
            except Exception:
                pass
        # IMPORTANT: ensure 'reponse' contains the full text (the grader reads only this field).
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planification échouée: {e}")

@app.get("/")
def read_root():
    return {"message": "Versailles Planner API", "status": "active"}


@app.get("/_probe/weather/window")
async def probe_weather_window(
    date: str,                 # "YYYY-MM-DD"
    start_time: str = "14:00", # "HH:MM"
    duration_min: int = 180,
    place: Optional[str] = None,
    lang: str = "auto"
):
    """
    Windowed hourly summary + decision flags (uses Open-Meteo).
    If 'place' is omitted, defaults to Château de Versailles coords.
    """
    if place:
        inp = WeatherWindowInput(
            date=date, start_time=start_time, duration_min=duration_min,
            place=place, lang=lang
        )
        return await get_weather_summary(inp)
    # Versailles convenience
    return await versailles_weather_summary(date=date, start_time=start_time, duration_min=duration_min)

@app.get("/_probe/weather/daily")
async def probe_weather_daily(
    date: str,                 # "YYYY-MM-DD"
    place: Optional[str] = None
):
    """
    Single-day min/max/precip (tries OpenWeather if key present, else Open-Meteo).
    """
    inp = WeatherDailyInput(date=date, place=place)
    return await get_weather_daily(inp)
