from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from typing import Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.middleware.cors import CORSMiddleware
from setup_graph import GraphManager, GraphManagerEval, State, INIT_MESSAGE
# from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from setup_graph import talk_to_agent
from mcp_bridge import weather_summary_sync, versailles_itinerary_sync, route_between_sync, multi_route_sync

app = FastAPI(title="4 mousquet'AIres", description="Backend with Langchain & Langgraph AI Agent")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MISTRAL_MODEL = os.getenv('MISTRAL_MODEL', 'mistral-medium-latest')

model = init_chat_model(MISTRAL_MODEL, model_provider="mistralai")
state : State = State()
mgr = GraphManager()
mgreval = GraphManagerEval()
class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    route: dict | None = None
    plan: dict | None = None

# Nouveaux modèles pour l'évaluation
class EvaluationRequest(BaseModel):
    question: str

class EvaluationResponse(BaseModel):
    answer: str

class WeatherWindowRequest(BaseModel):
    date: str
    start_time: str
    duration_text: Optional[str] = None
    duration_min: Optional[int] = None
    place: Optional[str] = "Château de Versailles, France"
    lang: Optional[str] = "fr"

class RouteRequest(BaseModel):
    origin: str
    destination: Optional[str] = None
    profile: Optional[str] = "walking"

class MultiRouteRequest(BaseModel):
    places: list[str]
    profile: Optional[str] = "walking"

chat_sessions: Dict[str, ConversationBufferMemory] = {}

@app.post("/chat", response_model=EvaluationResponse)
def chat_evaluation(request: EvaluationRequest):
    """
    Endpoint dédié pour l'évaluation - comportement stateless
    Accepte {"question": "..."} et retourne {"answer": "..."}
    """
    try:
        # Pas de gestion de session pour l'évaluation - comportement stateless
        ai_response = talk_to_agent(state, mgreval, request.question)

        # Extraire le texte de la réponse si c'est un objet SpecificInfoOutput
        if hasattr(ai_response, 'response'):
            ai_message = ai_response.response
        elif hasattr(ai_response, 'text'):
            ai_message = ai_response.text
        else:
            ai_message = str(ai_response)

        return EvaluationResponse(answer=ai_message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent: {str(e)}")

@app.post("/", response_model=ChatResponse)
def chat_with_agent(chat_message: ChatMessage):
    try:
        # Créer ou récupérer la mémoire pour cette session
        if chat_message.session_id not in chat_sessions:
            chat_sessions[chat_message.session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        memory = chat_sessions[chat_message.session_id]
                
        # Récupérer l'historique de conversation
        # chat_history = memory.chat_memory.messages
        
        # Construire la liste des messages avec l'historique + nouveau message
        # messages = chat_history + [HumanMessage(content=chat_message.message)]
        # Invoquer le modèle avec tout l'historique
        ai_response = talk_to_agent(state, mgr, chat_message.message)

        # Extraire le texte de la réponse + éventuelle route
        if hasattr(ai_response, 'response'):
            ai_message = ai_response.response
        elif hasattr(ai_response, 'text'):
            ai_message = ai_response.text
        else:
            ai_message = str(ai_response)
        route_payload = getattr(ai_response, 'route', None)
        plan_payload = getattr(ai_response, 'plan', None)
        
        # IMPORTANT: Sauvegarder dans la mémoire
        memory.chat_memory.add_user_message(chat_message.message)
        memory.chat_memory.add_ai_message(ai_message)
        
        return ChatResponse(
            response=ai_message,
            session_id=chat_message.session_id,
            route=route_payload,
            plan=plan_payload,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent: {str(e)}")
    

@app.post("/tools/weather")
def tool_weather(req: WeatherWindowRequest):
    try:
        duration_text = req.duration_text or (f"{req.duration_min} min" if req.duration_min else "180 min")
        return weather_summary_sync(
            date=req.date,
            start_time=req.start_time,
            duration_text=duration_text,
            place=req.place,
            lang=req.lang,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"weather tool error: {e}")


@app.post("/tools/versailles_route")
def tool_versailles_route(req: RouteRequest):
    try:
        return versailles_itinerary_sync(origin=req.origin, profile=req.profile)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"route tool error: {e}")


@app.post("/tools/route")
def tool_route_between(req: RouteRequest):
    try:
        if not req.destination:
            raise HTTPException(status_code=400, detail="destination is required")
        return route_between_sync(origin=req.origin, destination=req.destination, profile=req.profile)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"route tool error: {e}")


@app.post("/tools/route_multi")
def tool_route_multi(req: MultiRouteRequest):
    try:
        return multi_route_sync(places=req.places, profile=req.profile or "walking")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"multi-route tool error: {e}")


@app.get("/chat/sessions")
def get_chat_sessions():
    return {"sessions": chat_sessions}

@app.delete("/chat/sessions/{session_id}")
def clear_chat_session(session_id: str):
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": f"Session {session_id} supprimée"}
    else:
        raise HTTPException(status_code=404, detail="Session non trouvée")
