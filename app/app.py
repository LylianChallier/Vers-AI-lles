# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from agents.langgraph_flow import run_graph

app = FastAPI()

class UserMessage(BaseModel):
    message: str

@app.post("/interact")
def interact(msg: UserMessage):
    response = run_graph(msg.message)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
