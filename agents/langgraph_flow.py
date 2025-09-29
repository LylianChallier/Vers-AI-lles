# app/langgraph_flow.py
from langgraph import Graph, Node
from .agent import agent
from langchain_mistralai import ChatMistralAI

llm = ChatMistralAI(api_key="TON_API_KEY_MISTRAL", model="mistral-large-latest")

graph = Graph()

# Node LLM direct
llm_node = Node(name="LLM_Response", func=lambda input_text: llm.generate(input_text))

# Node Agent
agent_node = Node(name="Agent_Response", func=lambda input_text: agent.run(input_text))

graph.add_nodes([llm_node, agent_node])

# Choisir le node selon la question
def route_input(input_text: str):
    keywords = ["réserver", "billet", "Versailles", "SNCF", "Airbnb", "trajet", "maps", "météo"]
    if any(k.lower() in input_text.lower() for k in keywords):
        return "Agent_Response"
    return "LLM_Response"

def run_graph(input_text: str):
    node_name = route_input(input_text)
    return graph.run_node(node_name, input_text)
