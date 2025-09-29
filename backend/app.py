from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.memory import ConversationBufferMemory
from typing import Dict
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model

app = FastAPI(title="MetroMind AI Agent API", description="Backend with LangChain AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model = init_chat_model("mistral-large-latest", model_provider="mistralai")

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
        # Créer ou récupérer la mémoire pour cette session
        if chat_message.session_id not in chat_sessions:
            chat_sessions[chat_message.session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        memory = chat_sessions[chat_message.session_id]
                
        # Récupérer l'historique de conversation
        chat_history = memory.chat_memory.messages
        
        # Construire la liste des messages avec l'historique + nouveau message
        # messages = chat_history + [HumanMessage(content=chat_message.message)]
        # Invoquer le modèle avec tout l'historique
        # ai_message = ask_with_rag(messages, chat_message.message)
        ai_message = model.invoke(chat_message.message)
        text_content = ai_message.content
        
        # IMPORTANT: Sauvegarder dans la mémoire
        memory.chat_memory.add_user_message(chat_message.message)
        memory.chat_memory.add_ai_message(text_content)
        
        return ChatResponse(response=text_content, session_id=chat_message.session_id)
        
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

@app.get("/")
def read_root():
    return {"message": "MetroMind AI Agent Backend", "status": "active"}
