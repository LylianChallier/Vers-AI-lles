from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.abspath('../agents'))
sys.path.append(os.path.abspath('..'))
from agents.agent_multistep import run_agent


app = FastAPI()

class UserMessage(BaseModel):
    message: str
    session_id: str = "default_session"

@app.post("/interact")
def interact(msg: UserMessage):
    response = run_agent(msg.session_id, msg.message)
    return {"response": response}
