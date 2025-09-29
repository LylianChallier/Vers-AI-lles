# agent_multistep.py
from langchain.agents import initialize_agent, AgentType
from langchain_mistralai import ChatMistralAI
from tools.multi_tools import *
import os
from dotenv import load_dotenv
load_dotenv()

from memory import load_session, save_session

API_KEY=os.getenv("MISTRAL_API_KEY")

# LLM Mistral
llm = ChatMistralAI(
    api_key=API_KEY,
    model="mistral-large-latest",
    temperature=0.2
)

tools = [
    check_versailles_availability,
    get_next_passage,
    get_weather,
    search_train,
    book_train,
    search_airbnb,
    book_airbnb
]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def run_agent(session_id: str, user_message: str) -> str:
    # Charger la mémoire persistante
    session_data = load_session(session_id)
    
    # Ici on pourrait injecter le contexte dans le prompt ou LLM
    # Exemple simple : ajouter contexte au message
    context_msg = f"Contexte précédent : {session_data}\nUtilisateur : {user_message}"
    
    response = agent.run(context_msg)
    
    # Sauvegarder la réponse dans la session
    session_data['last_interaction'] = user_message
    session_data['last_response'] = response
    save_session(session_id, session_data)
    
    return response
