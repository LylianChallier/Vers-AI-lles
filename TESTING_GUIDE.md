# 🧪 Testing Guide for WSL

This guide provides commands you can run in WSL to test the Versailles Agent implementation.

## Quick Test Commands

### 1. Run Automated Test Script

```bash
# Make script executable
chmod +x test_implementation.sh

# Run bash tests
bash test_implementation.sh

# Or run Python tests
python3 test_implementation.py
```

---

## Manual Testing Commands

### Test 1: Python Environment

```bash
python3 --version
pip3 --version
```

**Expected:** Python 3.9+ and pip installed

---

### Test 2: Import Tests

```bash
# Test langgraph_flow
python3 -c "import agents.langgraph_flow; print('✓ langgraph_flow OK')"

# Test agent_multistep
python3 -c "import agents.agent_multistep; print('✓ agent_multistep OK')"

# Test app
python3 -c "import app.app; print('✓ app OK')"

# Test mcp_server
python3 -c "import mcp_server; print('✓ mcp_server OK')"
```

**Expected:** All imports succeed without errors

---

### Test 3: ReservationPlan Model

```bash
python3 << 'EOF'
from llm.reservation_memory import ReservationPlan

# Create empty plan
rp = ReservationPlan()
print(f"Missing slots: {rp.get_missing_slots()}")
print(f"Completion: {rp.get_completion_percentage()}%")
print(f"Is complete: {rp.is_complete()}")

# Fill some data
rp.date = "2025-06-15"
rp.participants = 2
print(f"\nAfter filling 2 fields:")
print(f"Completion: {rp.get_completion_percentage()}%")
print(f"Missing: {rp.get_missing_slots()}")

print("\n✓ ReservationPlan works correctly")
EOF
```

**Expected:** Shows missing slots, completion percentage, and updates correctly

---

### Test 4: Tool Functionality

```bash
# Test Google Maps tool
python3 << 'EOF'
from tools.google_maps_tool import google_maps_route

result = google_maps_route.invoke({
    "origin": "Paris Gare de Lyon",
    "destination": "Château de Versailles",
    "mode": "transit"
})
print(result)
print("\n✓ Google Maps tool works")
EOF
```

```bash
# Test Parking Info tool
python3 << 'EOF'
from tools.parking_restaurants import get_parking_info

result = get_parking_info.invoke({"location": "Versailles"})
print(result)
print("\n✓ Parking info tool works")
EOF
```

```bash
# Test Restaurant Finder
python3 << 'EOF'
from tools.parking_restaurants import find_restaurants

result = find_restaurants.invoke({
    "location": "Versailles",
    "cuisine": "français",
    "budget": "moyen"
})
print(result)
print("\n✓ Restaurant finder works")
EOF
```

```bash
# Test Ticket Booking
python3 << 'EOF'
from tools.book_versailles_tickets import book_versailles_tickets

result = book_versailles_tickets.invoke({
    "date": "2025-06-15",
    "type_billet": "passeport",
    "participants": 2,
    "horaire": "09:00"
})
print(result)
print("\n✓ Ticket booking works")
EOF
```

**Expected:** Each tool returns appropriate formatted responses

---

### Test 5: Memory System

```bash
python3 << 'EOF'
from memory.memory import save_session, load_session

# Save session
test_data = {
    "chat_history": "User: Hello\nAgent: Hi!",
    "reservation_plan": {"date": "2025-06-15"}
}
save_session("test_session", test_data)
print("✓ Session saved")

# Load session
loaded = load_session("test_session")
print(f"✓ Session loaded: {loaded.get('chat_history')}")
EOF
```

**Expected:** Session saves and loads correctly (requires Redis)

---

### Test 6: LangGraph Routing

```bash
python3 << 'EOF'
from agents.langgraph_flow import route_input, State

# Test agent routing (complex query)
agent_state = State(
    input_text="Je veux réserver un billet pour Versailles",
    response="",
    session_id="test"
)
route = route_input(agent_state)
print(f"Complex query routes to: {route}")
assert route == "Agent_Response", "Should route to Agent"

# Test LLM routing (simple query)
llm_state = State(
    input_text="Bonjour, comment allez-vous ?",
    response="",
    session_id="test"
)
route = route_input(llm_state)
print(f"Simple query routes to: {route}")
assert route == "LLM_Response", "Should route to LLM"

print("\n✓ Routing logic works correctly")
EOF
```

**Expected:** Complex queries route to Agent, simple queries to LLM

---

### Test 7: Syntax Validation

```bash
# Check Python syntax for all main files
python3 -m py_compile agents/langgraph_flow.py && echo "✓ langgraph_flow.py syntax OK"
python3 -m py_compile agents/agent_multistep.py && echo "✓ agent_multistep.py syntax OK"
python3 -m py_compile app/app.py && echo "✓ app.py syntax OK"
python3 -m py_compile mcp_server.py && echo "✓ mcp_server.py syntax OK"
python3 -m py_compile llm/reservation_memory.py && echo "✓ reservation_memory.py syntax OK"
```

**Expected:** All files compile without syntax errors

---

### Test 8: Check Redis Connection (Optional)

```bash
python3 << 'EOF'
import redis
import os

try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )
    r.ping()
    print("✓ Redis is running and accessible")
except Exception as e:
    print(f"⚠ Redis not available: {e}")
    print("  (This is OK - agent will use fallback memory)")
EOF
```

**Expected:** Either Redis is running, or fallback message shown

---

### Test 9: Initialize Vector Store (Optional)

```bash
# This will take 2-3 minutes
python3 rag/initialize_db.py
```

**Expected:** Loads 300+ documents into ChromaDB

---

### Test 10: Start FastAPI Server (Manual)

```bash
# Start the server
python3 app/app.py
```

Then in another terminal:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quels sont les horaires d'\''ouverture ?",
    "session_id": "test123"
  }'
```

**Expected:** Server starts and responds to requests

---

## Test Results Checklist

After running tests, check:

- [ ] All imports work without errors
- [ ] ReservationPlan model functions correctly
- [ ] Tools return appropriate responses
- [ ] Memory system saves/loads data
- [ ] LangGraph routing works
- [ ] No syntax errors in any files
- [ ] Redis connection (optional)
- [ ] Vector store can be initialized (optional)
- [ ] FastAPI server starts (optional)

---

## Common Issues & Solutions

### Issue: Import errors
**Solution:** Make sure you're in the project root directory and dependencies are installed:
```bash
cd /path/to/les_4_MousquetAIres
pip3 install -r requirements.txt
```

### Issue: Redis connection failed
**Solution:** This is OK - the agent will use fallback in-memory storage. To use Redis:
```bash
# Start Redis in Docker
docker run -d -p 6379:6379 redis:7.0
```

### Issue: Missing API keys
**Solution:** Make sure your `.env` file has:
```
MISTRAL_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
```

### Issue: ChromaDB errors
**Solution:** Install ChromaDB dependencies:
```bash
pip3 install chromadb sentence-transformers
```

---

## Quick Success Test

Run this single command to test core functionality:

```bash
python3 << 'EOF'
print("Testing Versailles Agent Core Functionality...\n")

# Test 1: Imports
try:
    import agents.langgraph_flow
    import agents.agent_multistep
    from llm.reservation_memory import ReservationPlan
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Model
try:
    rp = ReservationPlan()
    assert len(rp.get_missing_slots()) == 4
    print("✓ ReservationPlan works")
except Exception as e:
    print(f"✗ Model failed: {e}")
    exit(1)

# Test 3: Tool
try:
    from tools.google_maps_tool import google_maps_route
    result = google_maps_route.invoke({
        "origin": "Paris",
        "destination": "Versailles",
        "mode": "transit"
    })
    assert "google.com/maps" in result
    print("✓ Tools work")
except Exception as e:
    print(f"✗ Tool failed: {e}")
    exit(1)

# Test 4: Routing
try:
    from agents.langgraph_flow import route_input, State
    state = State(input_text="réserver", response="", session_id="test")
    assert route_input(state) == "Agent_Response"
    print("✓ Routing works")
except Exception as e:
    print(f"✗ Routing failed: {e}")
    exit(1)

print("\n✅ All core tests passed!")
print("The agent is ready to use!")
EOF
```

**Expected:** All 4 tests pass

---

## Next Steps After Testing

If all tests pass:
1. Initialize the vector store: `python3 rag/initialize_db.py`
2. Start the server: `python3 app/app.py`
3. Test with real queries via the API
4. Or use the MCP server: `python3 mcp_server.py`

---

**Happy Testing! 🏰**
