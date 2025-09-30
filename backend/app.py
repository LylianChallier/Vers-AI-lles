from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.middleware.cors import CORSMiddleware
from setup_graph import GraphManager, GraphManagerEval, State, INIT_MESSAGE
# from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from setup_graph import talk_to_agent

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

# Nouveaux modèles pour l'évaluation
class EvaluationRequest(BaseModel):
    question: str

class EvaluationResponse(BaseModel):
    answer: str

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

        # Extraire le texte de la réponse si c'est un objet SpecificInfoOutput
        if hasattr(ai_response, 'response'):
            ai_message = ai_response.response
        elif hasattr(ai_response, 'text'):
            ai_message = ai_response.text
        else:
            ai_message = str(ai_response)
        
        # IMPORTANT: Sauvegarder dans la mémoire
        memory.chat_memory.add_user_message(chat_message.message)
        memory.chat_memory.add_ai_message(ai_message)
        
        return ChatResponse(response=ai_message, session_id=chat_message.session_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de l'agent: {str(e)}")
    

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