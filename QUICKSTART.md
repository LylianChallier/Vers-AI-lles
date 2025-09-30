# 🚀 Quick Start Guide

Get the Versailles Visit Planning Agent up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Redis server
- API Keys (Mistral AI, OpenWeatherMap)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file has these keys:

```bash
MISTRAL_API_KEY=your_mistral_key
OPENWEATHER_API_KEY=your_weather_key
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Start Redis

```bash
# Windows (if installed)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7.0
```

### 4. Initialize Vector Store

```bash
python rag/initialize_db.py
```

This loads 300+ Versailles documents into ChromaDB (takes ~2 minutes).

### 5. Start the Application

Choose one:

#### Option A: FastAPI Server
```bash
python app/app.py
```
Access at: http://localhost:8000

#### Option B: MCP Server
```bash
python mcp_server.py
```
Use with Claude Desktop or other MCP clients.

## Quick Test

### Test the API

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quels sont les horaires d'\''ouverture du château ?",
    "session_id": "test123"
  }'
```

### Test in Python

```python
from agents.langgraph_flow import run_graph

response = run_graph(
    input_text="Je veux visiter Versailles le 15 juin avec 2 personnes",
    session_id="test123"
)
print(response)
```

## Common Issues

### Redis Connection Error
```
Error: Redis is not running
```
**Solution:** Start Redis server or use Docker

### Missing API Key
```
Error: MISTRAL_API_KEY not found
```
**Solution:** Add your API key to `.env` file

### Vector Store Not Initialized
```
Error: No documents found
```
**Solution:** Run `python rag/initialize_db.py`

## What's Next?

- 📖 Read the full [README.md](README.md)
- 🔧 Explore the [API docs](http://localhost:8000/docs)
- 🛠️ Check available [tools](README.md#available-tools)
- 🎯 Try the [MCP server](README.md#mcp-server)

## Example Queries

Try these with the agent:

```
"Quels sont les horaires d'ouverture ?"
"Je veux réserver pour 2 personnes le 15 juin"
"Comment aller à Versailles depuis Paris ?"
"Quel temps fera-t-il à Versailles demain ?"
"Où puis-je me garer ?"
"Recommande-moi un restaurant"
"Parle-moi de la galerie des Glaces"
```

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [TODO.md](TODO.md) for implementation details
- Open an issue on GitHub

---

**Happy coding! 🏰**
