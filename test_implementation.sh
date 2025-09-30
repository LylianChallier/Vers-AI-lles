#!/bin/bash

# Test script for Versailles Agent - Run in WSL
# Usage: bash test_implementation.sh

echo "=========================================="
echo "🏰 Versailles Agent - Critical Path Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1. Python Environment Tests"
echo "----------------------------"
run_test "Python version" "python3 --version"
run_test "Pip installed" "pip3 --version"
echo ""

echo "2. Import Tests"
echo "---------------"
run_test "Import langgraph_flow" "python3 -c 'import agents.langgraph_flow'"
run_test "Import agent_multistep" "python3 -c 'import agents.agent_multistep'"
run_test "Import reservation_memory" "python3 -c 'from llm.reservation_memory import ReservationPlan'"
run_test "Import vector_store" "python3 -c 'from rag.vector_store import VersaillesVectorStore'"
run_test "Import retriever" "python3 -c 'from rag.retriever import VersaillesRetriever'"
echo ""

echo "3. Model Tests"
echo "--------------"
run_test "Create ReservationPlan" "python3 -c 'from llm.reservation_memory import ReservationPlan; rp = ReservationPlan(); assert len(rp.get_missing_slots()) == 4'"
run_test "ReservationState" "python3 -c 'from llm.reservation_memory import ReservationState; rs = ReservationState(session_id=\"test\")'"
echo ""

echo "4. Tool Import Tests"
echo "--------------------"
run_test "Import search_versailles_info" "python3 -c 'from tools.search_versailles_info import search_versailles_info'"
run_test "Import book_versailles_tickets" "python3 -c 'from tools.book_versailles_tickets import book_versailles_tickets'"
run_test "Import parking_restaurants" "python3 -c 'from tools.parking_restaurants import get_parking_info'"
run_test "Import get_weather" "python3 -c 'from tools.get_weather import get_weather'"
run_test "Import google_maps_tool" "python3 -c 'from tools.google_maps_tool import google_maps_route'"
echo ""

echo "5. Syntax Validation"
echo "--------------------"
run_test "langgraph_flow.py syntax" "python3 -m py_compile agents/langgraph_flow.py"
run_test "agent_multistep.py syntax" "python3 -m py_compile agents/agent_multistep.py"
run_test "app.py syntax" "python3 -m py_compile app/app.py"
run_test "mcp_server.py syntax" "python3 -m py_compile mcp_server.py"
echo ""

echo "6. Tool Functionality Tests (Simulated)"
echo "----------------------------------------"
run_test "Google Maps tool" "python3 -c 'from tools.google_maps_tool import google_maps_route; result = google_maps_route.invoke({\"origin\": \"Paris\", \"destination\": \"Versailles\", \"mode\": \"transit\"}); assert \"google.com/maps\" in result'"
run_test "Parking info tool" "python3 -c 'from tools.parking_restaurants import get_parking_info; result = get_parking_info.invoke({\"location\": \"Versailles\"}); assert \"parking\" in result.lower()'"
run_test "Restaurant finder" "python3 -c 'from tools.parking_restaurants import find_restaurants; result = find_restaurants.invoke({\"location\": \"Versailles\"}); assert \"restaurant\" in result.lower()'"
echo ""

echo "7. Memory Tests"
echo "---------------"
run_test "Load/Save session" "python3 -c 'from memory.memory import save_session, load_session; save_session(\"test\", {\"data\": \"test\"}); data = load_session(\"test\"); assert data.get(\"data\") == \"test\"'"
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Check the output above.${NC}"
    exit 1
fi
