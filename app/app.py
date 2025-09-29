# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from agent_multistep import run_agent

app = FastAPI(title="Travel Assistant Agent")

class UserRequest(BaseModel):
    session_id: str
    message: str

@app.post("/interact")
def interact(req: UserRequest):
    try:
        result = run_agent(req.session_id, req.message)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}

# Lancer uvicorn app:app --reload
