# Hackathon Datacraft - Château de Versailles

AI Assistant to organize visits to the Château de Versailles.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Mistral AI API Key (create a `.env` file at the root with your key)

### Configuration
Create a `.env` file at the root of the project:
```bash
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_MODEL=mistral-medium-latest
EMBEDDING_MODEL=mistral-embed
```

### Launch
From the project root, execute:
```bash
docker compose up --build
```

Wait until the logs display:
```
backend-1  | INFO:     Started server process [1]
backend-1  | INFO:     Application startup complete.
backend-1  | INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Service Access
- **Frontend (user interface)**: [http://localhost:8501](http://localhost:8501)
- **Backend API (Swagger UI)**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📚 Project Architecture

### General Structure
```
Vers-AI-lles/
├── backend/          # FastAPI API + LangGraph agents
├── frontend/         # Streamlit Interface
└── docker-compose.yaml
```

### Backend (`/backend`)

The backend is built with **FastAPI** and **LangGraph** to orchestrate conversational AI agents.

#### Main Files

**`app.py`** - FastAPI entry point
- Exposes 2 endpoints:
  - `POST /chat`: Evaluation endpoint (stateless)
  - `POST /`: Main endpoint with session management
- Configures CORS to allow frontend requests
- Initializes graph managers (`GraphManager` and `GraphManagerEval`)

**`setup_graph.py`** - Core of the LangGraph agent system
- **State**: Pydantic model that maintains conversation state
  - `messages`: Message history
  - `user_wants_road_in_versailles`: User wants an itinerary
  - `user_wants_specific_info`: User wants specific information
  - `user_asks_off_topic`: Off-topic question
  - `necessary_info_for_road`: Information collected to create the itinerary (date, time, group type, duration, budget)

- **Agents**:
  - `IntentAgent`: Analyzes user intent (visit, specific info, off-topic)
  - `ItineraryInfoAgent`: Collects necessary information to create an itinerary (conversational mode)
  - `ItineraryInfoAgentEval`: Evaluation version that extracts all info in a single pass
  - `RoadInVersaillesAgent`: Generates personalized itinerary using RAG
  - `SpecificInfoAgent`: Answers specific questions about the château
  - `OffTopicAgent`: Handles off-topic or courtesy questions

- **Graphs**:
  - `GraphManager`: Standard conversational mode (progressive info collection)
  - `GraphManagerEval`: Evaluation mode (direct extraction without intermediate questions)

**`embedding.py`** - Embedding system
- Uses Mistral AI API to generate embeddings
- `embed_query()` function: Handles long texts by splitting them into chunks with overlap
- Similarity functions: cosine, Manhattan, Euclidean
- `select_top_n_similar_documents()`: Selects the most relevant documents for RAG

**`create_db.py`** - Data preparation
- Loads data from `data/tips.json` (tips about Versailles)
- Generates embeddings for each tip
- Saves enriched documents in `data/tips_embedded.json`

**`list.py`** - In-memory database
- Contains `longlist`: list of embedding documents loaded at startup
- Used by `RoadInVersaillesAgent` for RAG

**`rag_config.py`** - RAG Configuration (legacy)
- Configuration file for the RAG system

### Frontend (`/frontend`)

User interface built with **Streamlit**.

**`front.py`** - Main application
- Chat interface with the backend
- Message history management in `st.session_state`
- API calls to `http://backend:8001/`
- Styled display of user and assistant messages

**`components.py`** - UI Components
- HTML rendering functions for messages
- Header, loading spinner, etc.

**`styles.css`** - Custom styles
- Modern design for the chat interface

### Docker

**`docker-compose.yaml`**
- `backend` service: Exposes port 8001
- `frontend` service: Exposes port 8501
- Environment variables shared from `.env`
- Mounted volumes for hot development

---

## 🤖 System Operation

### Conversational Flow

1. **Intent Analysis**: The `IntentAgent` determines what the user wants
2. **Conditional Routing**:
   - If visit → `ItineraryInfoAgent` collects necessary info
   - If specific info → `SpecificInfoAgent` responds directly
   - If off-topic → `OffTopicAgent` redirects politely
3. **Itinerary Generation**: Once all info is collected, `RoadInVersaillesAgent` creates a personalized plan using RAG (Retrieval-Augmented Generation) with 50 relevant documents

### RAG (Retrieval-Augmented Generation)

The system uses a database of tips about Versailles:
- Embedding documents with Mistral AI
- Similarity calculated by Euclidean distance
- Top 50 documents injected into the prompt to contextualize the response

---

## 🔧 Development

### Backend only
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### Frontend only
```bash
cd frontend
pip install -r requirements.txt
streamlit run front.py
```

### Regenerate embedding database
```bash
cd backend
python create_db.py
```

---

## 📝 Technical Notes

- **LangGraph** allows creating agent workflows with routing conditions
- **Structured Output**: All agents use `with_structured_output()` to guarantee valid JSON responses
- **Evaluation mode**: Disabled for now, designed to extract information in a single request
- **Session management**: Messages are kept in the `State` to maintain context

---

## 🏗️ Team - Les 4 mousquet'AIres

Project developed during Hackathon Datacraft 2024