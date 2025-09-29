from langchain.agents import initialize_agent, AgentType
import os
import sys
sys.path.append(os.path.abspath('../tools'))
sys.path.append(os.path.abspath('../memory'))
sys.path.append(os.path.abspath('..'))

from langchain_mistralai import ChatMistralAI
from tools.book_airbnb import book_airbnb
from tools.book_train  import book_train
from tools.get_next_passage import get_next_passages
from tools.check_versailles_availability import check_versailles_availability
from tools.get_schedule_at_times import get_schedules_at_time
from tools.get_weather import get_weather
from tools.google_maps_tool import google_maps_route
from tools.redis import store_session, get_session
from tools.search_airbnb import search_airbnb
from tools.search_train import search_train

from memory.memory import load_session, save_session
from dotenv import load_dotenv
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory
import redis

load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")

# Redis
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Historique partagé LangChain + Redis
def get_memory(session_id: str):
    # Historique des messages dans Redis
    chat_history = RedisChatMessageHistory(redis_client=r, session_id=session_id)
    # ConversationBufferMemory pour l'agent
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=chat_history)
    return memory

# LLM
llm = ChatMistralAI(
    api_key=API_KEY,
    model="mistral-large-latest",
    temperature=0.2
)

# Tools
tools = [
    check_versailles_availability,
    get_next_passages,
    get_weather,
    search_train,
    book_train,
    search_airbnb,
    book_airbnb
]

# Agent factory
def create_agent(session_id: str):
    memory = get_memory(session_id)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )
    return agent

# Fonction principale
def run_agent(session_id: str, user_message: str) -> str:
    """
    Exécute le message utilisateur via l’agent et stocke la conversation dans Redis.
    Contexte précédent injecté dans le prompt.
    """
    # Charger le contexte précédent (backup)
    session_data = load_session(session_id)
    previous_context = session_data.get("chat_history", "")

    # Construire le prompt avec contexte
    context_msg = f"Contexte précédent : {previous_context}\nUtilisateur : {user_message}"

    # Créer agent avec mémoire
    agent = create_agent(session_id)
    response = agent.run(context_msg)

    # Sauvegarder le contexte dans Redis backup
    session_data["chat_history"] = previous_context + f"\nUtilisateur : {user_message}\nAgent : {response}"
    save_session(session_id, session_data)

    return response
