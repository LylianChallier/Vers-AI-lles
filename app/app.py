from fastapi import FastAPI
from pydantic import BaseModel
from agent_multistep import run_agent  # ton agent multi-step avec tools + mémoire Redis

app = FastAPI()

class UserMessage(BaseModel):
    session_id: str
    message: str

@app.post("/interact")
def interact(msg: UserMessage):
    """
    Envoie le message à l'agent. 
    L'agent analyse et déclenche le tool approprié si besoin.
    """
    response = run_agent(msg.session_id, msg.message)
    return {"response": response}
