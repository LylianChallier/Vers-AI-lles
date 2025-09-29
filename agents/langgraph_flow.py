# app/langgraph_flow.py
import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.agent_multistep import run_agent
from langchain_mistralai import ChatMistralAI

# Définir l’état du graphe (ce que chaque node va recevoir / retourner)
class State(TypedDict):
    input_text: str
    response: str

# LLM Mistral
llm = ChatMistralAI(
    api_key=os.getenv("MISTRAL_API_KEY", "TON_API_KEY_MISTRAL"),
    model="mistral-large-latest"
)

# Node LLM direct
def llm_node(state: State) -> State:
    resp = llm.invoke(state["input_text"])
    return {"input_text": state["input_text"], "response": resp.content}

# Node Agent
def agent_node(state: State) -> State:
    # TODO: Change into agent or in import of package or else
    resp = agent.run(state["input_text"])
    return {"input_text": state["input_text"], "response": resp}

# Router pour choisir le bon node
def route_input(state: State) -> str:
    keywords = ["réserver", "billet", "Versailles", "SNCF", "Airbnb", "trajet", "maps", "météo"]
    if any(k.lower() in state["input_text"].lower() for k in keywords):
        return "Agent_Response"
    return "LLM_Response"

# Construire le graphe
graph = StateGraph(State)
graph.add_node("LLM_Response", llm_node)
graph.add_node("Agent_Response", agent_node)

# Point d’entrée conditionnel
graph.set_conditional_entry_point(
    route_input,
    {"LLM_Response": "LLM_Response", "Agent_Response": "Agent_Response"}
)

# Relier à la fin
graph.add_edge("LLM_Response", END)
graph.add_edge("Agent_Response", END)

# Compiler le graphe
app = graph.compile()

def run_graph(input_text: str) -> str:
    result = app.invoke({"input_text": input_text})
    return result["response"]
