"""Multi-step agent for Versailles visit planning with integrated tools and memory."""

import os
import sys
sys.path.append(os.path.abspath('../tools'))
sys.path.append(os.path.abspath('../memory'))
sys.path.append(os.path.abspath('..'))

from langchain.agents import initialize_agent, AgentType
from langchain_mistralai import ChatMistralAI
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory
from dotenv import load_dotenv
import redis

# Import tools
from tools.check_versailles_availability import check_versailles_availability
from tools.book_versailles_tickets import book_versailles_tickets, check_ticket_availability
from tools.get_next_passage import get_next_passages
from tools.get_schedule_at_times import get_schedules_at_time
from tools.get_weather import get_weather
from tools.google_maps_tool import google_maps_route
from tools.search_train import search_train
from tools.book_train import book_train
from tools.search_airbnb import search_airbnb
from tools.book_airbnb import book_airbnb
from tools.search_versailles_info import (
    search_versailles_info,
    get_versailles_opening_hours,
    get_versailles_ticket_info,
    get_versailles_access_info
)
from tools.parking_restaurants import (
    get_parking_info,
    find_restaurants,
    get_luggage_storage_info
)

# Import memory
from memory.memory import load_session, save_session
from prompts.reservation_prompt import reservation_template

load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")

# Redis configuration
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    r.ping()  # Test connection
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Redis not available: {e}")
    REDIS_AVAILABLE = False


def get_memory(session_id: str):
    """
    Get conversation memory for the session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        ConversationBufferMemory instance
    """
    if REDIS_AVAILABLE:
        try:
            chat_history = RedisChatMessageHistory(
                redis_client=r,
                session_id=session_id
            )
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                chat_memory=chat_history,
                return_messages=True
            )
            return memory
        except Exception as e:
            print(f"Error creating Redis memory: {e}")
    
    # Fallback to in-memory
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )


# Initialize LLM with system prompt
llm = ChatMistralAI(
    api_key=API_KEY,
    model="mistral-large-latest",
    temperature=0.2
)

# All available tools
tools = [
    # Versailles knowledge base
    search_versailles_info,
    get_versailles_opening_hours,
    get_versailles_ticket_info,
    get_versailles_access_info,
    
    # Versailles booking
    check_versailles_availability,
    check_ticket_availability,
    book_versailles_tickets,
    
    # Transportation
    get_next_passages,
    get_schedules_at_time,
    search_train,
    book_train,
    
    # Accommodation
    search_airbnb,
    book_airbnb,
    
    # Practical info
    get_weather,
    get_parking_info,
    find_restaurants,
    get_luggage_storage_info,
    google_maps_route,
]


def create_agent(session_id: str):
    """
    Create an agent instance with memory and tools.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Initialized agent
    """
    memory = get_memory(session_id)
    
    # Create agent with system prompt
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        agent_kwargs={
            "prefix": reservation_template
        }
    )
    
    return agent


def run_agent(session_id: str, user_message: str) -> str:
    """
    Execute the agent with user message and manage conversation state.
    
    Args:
        session_id: Session identifier
        user_message: User's input message
        
    Returns:
        Agent's response
    """
    try:
        # Load session data (backup)
        session_data = load_session(session_id)
        previous_context = session_data.get("chat_history", "")
        
        # Create agent with memory
        agent = create_agent(session_id)
        
        # Build context-aware message
        if previous_context:
            context_msg = f"Contexte précédent : {previous_context[-500:]}\n\nUtilisateur : {user_message}"
        else:
            context_msg = user_message
        
        # Run agent
        response = agent.run(context_msg)
        
        # Save to backup memory
        session_data["chat_history"] = previous_context + f"\nUtilisateur : {user_message}\nAgent : {response}"
        save_session(session_id, session_data)
        
        return response
    
    except Exception as e:
        error_msg = f"Erreur lors du traitement de votre demande: {str(e)}"
        print(f"Agent error: {e}")
        return error_msg


def reset_session(session_id: str):
    """
    Reset a session's conversation history.
    
    Args:
        session_id: Session identifier to reset
    """
    try:
        if REDIS_AVAILABLE:
            # Clear Redis history
            chat_history = RedisChatMessageHistory(
                redis_client=r,
                session_id=session_id
            )
            chat_history.clear()
        
        # Clear backup
        save_session(session_id, {"chat_history": ""})
        print(f"Session {session_id} reset successfully")
    
    except Exception as e:
        print(f"Error resetting session: {e}")
