# 🏰 Les 4 MousquetAIres - Versailles Visit Planning Agent

An intelligent AI agent to help clients plan and book visits to the Château de Versailles, powered by LangChain, Mistral AI, and MCP (Model Context Protocol).

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [MCP Server](#mcp-server)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)

## ✨ Features

### 🎯 Core Capabilities

- **Intelligent Conversation**: Natural language interaction for visit planning
- **RAG-Powered Knowledge Base**: ChromaDB vector store with 300+ Versailles documents
- **Multi-Tool Agent**: 18+ integrated tools for comprehensive assistance
- **State Management**: Redis-based conversation memory
- **MCP Integration**: FastMCP server exposing all tools via Model Context Protocol
- **LangGraph Routing**: Smart routing between LLM and Agent based on query complexity

### 🛠️ Available Tools

#### Versailles Knowledge Base (4 tools)
- Search Versailles information
- Get opening hours
- Get ticket information
- Get access information

#### Booking & Availability (3 tools)
- Check ticket availability
- Book Versailles tickets
- Detailed availability check

#### Transportation (4 tools)
- Get next metro/bus passages (RATP API)
- Get schedules at specific times
- Search train connections
- Book train tickets

#### Accommodation (2 tools)
- Search Airbnb listings
- Book accommodations

#### Practical Information (5 tools)
- Weather forecast (OpenWeatherMap API)
- Parking information
- Restaurant recommendations
- Luggage storage info
- Google Maps routes

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│                    (app/app.py)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  LangGraph Router                            │
│              (agents/langgraph_flow.py)                      │
│                                                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  LLM Node    │              │  Agent Node  │            │
│  │  (Simple Q)  │              │  (Complex)   │            │
│  └──────────────┘              └──────┬───────┘            │
└────────────────────────────────────────┼────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-Step Agent                                │
│          (agents/agent_multistep.py)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    18+ Tools                          │  │
│  │  • Versailles KB (RAG)  • Transportation             │  │
│  │  • Booking              • Accommodation              │  │
│  │  • Practical Info       • Weather & Maps             │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Memory & State                              │
│  • Redis (Conversation History)                              │
│  • ChromaDB (Vector Store)                                   │
│  • ReservationPlan (Structured State)                        │
└─────────────────────────────────────────────────────────────┘
```

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│                  (mcp_server.py)                             │
│                                                              │
│  Exposes all 18 tools via Model Context Protocol            │
│  Compatible with Claude Desktop, Cline, and other MCP clients│
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.9+
- Redis Server
- Git

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd les_4_MousquetAIres
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and Start Redis

#### Windows
```bash
# Download Redis from https://github.com/microsoftarchive/redis/releases
# Or use Docker:
docker run -d -p 6379:6379 redis:7.0
```

#### Linux/Mac
```bash
# Install Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis                  # macOS

# Start Redis
redis-server
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (use your existing keys):

```bash
# Mistral AI API Key (Required)
MISTRAL_API_KEY=your_mistral_api_key

# OpenWeatherMap API Key (Required for weather)
OPENWEATHER_API_KEY=your_openweather_api_key

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=versailles_knowledge

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8001

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
```

### Initialize Vector Store

Before first use, initialize the ChromaDB vector store with Versailles data:

```bash
python rag/initialize_db.py
```

This will:
- Load 300+ documents from `data/versailles_semantic_complete_20250813_204248.jsonl`
- Create embeddings using sentence-transformers
- Store in ChromaDB for fast retrieval

## 📖 Usage

### Option 1: FastAPI Application

Start the FastAPI server:

```bash
# From project root
python app/app.py

# Or using uvicorn directly
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

Access the API:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Example API Calls

```bash
# Send a message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Je veux visiter Versailles le 15 juin",
    "session_id": "user123"
  }'

# Get reservation status
curl "http://localhost:8000/reservation/user123"

# Reset session
curl -X DELETE "http://localhost:8000/session/user123"
```

### Option 2: MCP Server

Start the MCP server to expose tools via Model Context Protocol:

```bash
python mcp_server.py
```

The MCP server runs on stdio and can be integrated with:
- **Claude Desktop**: Add to `claude_desktop_config.json`
- **Cline**: Configure in VS Code settings
- **Other MCP Clients**: Use stdio transport

#### MCP Configuration for Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "versailles-agent": {
      "command": "python",
      "args": ["C:/path/to/les_4_MousquetAIres/mcp_server.py"],
      "env": {
        "MISTRAL_API_KEY": "your_key",
        "OPENWEATHER_API_KEY": "your_key"
      }
    }
  }
}
```

### Option 3: Direct Python Usage

```python
from agents.langgraph_flow import run_graph

# Simple usage
response = run_graph(
    input_text="Quels sont les horaires d'ouverture ?",
    session_id="user123"
)
print(response)
```

## 🔧 MCP Server

The MCP server exposes all 18 tools via the Model Context Protocol, making them accessible to any MCP-compatible client.

### Available MCP Tools

```python
# Versailles Knowledge
- search_versailles_knowledge(query: str)
- get_opening_hours(date: str = None)
- get_ticket_information()
- get_access_information()

# Booking
- check_availability(date: str, type_billet: str)
- check_tickets(date: str, type_billet: str)
- book_tickets(date: str, type_billet: str, participants: int, horaire: str)

# Transportation
- get_next_metro_bus(stop: str, line: str, transport_type: str)
- get_schedules(stop: str, line: str, time: str, transport_type: str)
- search_trains(from_station: str, to_station: str, date: str, time: str)
- book_train_ticket(from_station: str, to_station: str, date: str, time: str, passengers: int)

# Accommodation
- search_accommodations(city: str, checkin: str, checkout: str, guests: int)
- book_accommodation(city: str, checkin: str, checkout: str, guests: int, listing_id: str)

# Practical Info
- get_weather_forecast(city: str)
- get_parking_options(location: str)
- search_restaurants(location: str, cuisine: str, budget: str)
- get_luggage_storage()
- get_route_map(origin: str, destination: str, mode: str)
```

## 📚 API Documentation

### POST /chat

Send a message to the agent.

**Request:**
```json
{
  "message": "Je veux réserver pour 2 personnes le 15 juin",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "response": "Parfait ! Je vais vous aider...",
  "session_id": "user123"
}
```

### GET /reservation/{session_id}

Get current reservation status.

**Response:**
```json
{
  "session_id": "user123",
  "reservation_plan": {
    "date": "2025-06-15",
    "participants": 2,
    "type_billet": "passeport",
    "horaire": "09:00",
    ...
  },
  "completion_percentage": 75.0,
  "is_complete": false,
  "missing_slots": ["transport_info"]
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent_multistep.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Manual Testing

```bash
# Test RAG system
python rag/initialize_db.py

# Test individual tools
python -c "from tools.get_weather import get_weather; print(get_weather.invoke({'city': 'Versailles'}))"

# Test agent
python -c "from agents.agent_multistep import run_agent; print(run_agent('test', 'Quels sont les horaires ?'))"
```

## 🔨 Development

### Project Structure

```
les_4_MousquetAIres/
├── agents/                 # Agent implementations
│   ├── agent_multistep.py # Main agent with tools
│   └── langgraph_flow.py  # LangGraph routing
├── app/                    # FastAPI application
│   ├── app.py             # Main API
│   └── Dockerfile         # Docker configuration
├── data/                   # Versailles knowledge base
│   └── versailles_semantic_complete_20250813_204248.jsonl
├── llm/                    # LLM and memory models
│   └── reservation_memory.py
├── memory/                 # Memory management
│   └── memory.py          # Redis memory
├── prompts/                # Prompt templates
│   └── reservation_prompt.py
├── rag/                    # RAG system
│   ├── vector_store.py    # ChromaDB integration
│   ├── retriever.py       # Retrieval logic
│   └── initialize_db.py   # DB initialization
├── tools/                  # Agent tools (18 tools)
│   ├── search_versailles_info.py
│   ├── book_versailles_tickets.py
│   ├── parking_restaurants.py
│   └── ...
├── tests/                  # Test suite
├── mcp_server.py          # MCP server
├── requirements.txt       # Dependencies
├── docker-compose.yml     # Docker Compose
└── README.md              # This file
```

### Adding New Tools

1. Create tool in `tools/` directory:

```python
from langchain.tools import tool

@tool(description='Your tool description')
def your_tool(param: str) -> str:
    """Tool docstring."""
    # Implementation
    return result
```

2. Import in `agents/agent_multistep.py`
3. Add to `tools` list
4. Expose in `mcp_server.py` if needed

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions focused and small

## 🐳 Docker Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

- Château de Versailles for the data
- Mistral AI for the LLM
- LangChain for the agent framework
- FastMCP for MCP integration

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: [your-email]

---

**Built with ❤️ for the Château de Versailles Hackathon**
