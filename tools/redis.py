from langchain.tools import tool
from redis_tool import save_session, load_session

@tool
def get_session(session_id: str) -> str:
    """Retrieve stored session"""
    data = load_session(session_id)
    return f"Session data: {data}" if data else "No session found."

@tool
def store_session(session_id: str, key: str, value: str) -> str:
    """Store a single key-value in the session"""
    session = load_session(session_id)
    session[key] = value
    save_session(session_id, session)
    return f"Stored {key} = {value} in session {session_id}"
