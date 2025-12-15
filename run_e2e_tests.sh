#!/bin/bash
# End-to-End Test Execution Script for Code Reviewer CI Agent
# This script automates the complete testing workflow

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Code Reviewer CI Agent - E2E Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Verify environment configuration
echo -e "${YELLOW}[1/6] Verifying environment configuration...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example${NC}"
    exit 1
fi

# Check for required API keys
if ! grep -q "REVIEW_API_KEY=" .env || grep -q "REVIEW_API_KEY=$" .env; then
    echo -e "${RED}❌ Error: REVIEW_API_KEY not set in .env${NC}"
    exit 1
fi

# Check for LLM provider configuration
if ! grep -q "LLM_PROVIDER=" .env; then
    echo -e "${RED}❌ Error: LLM_PROVIDER not set in .env${NC}"
    exit 1
fi

LLM_PROVIDER=$(grep "^LLM_PROVIDER=" .env | cut -d'=' -f2 | tr -d ' "')

if [ "$LLM_PROVIDER" = "openai" ]; then
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=sk-your" .env; then
        echo -e "${RED}❌ Error: Valid OPENAI_API_KEY not set in .env${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ OpenAI configuration found${NC}"
elif [ "$LLM_PROVIDER" = "groq" ]; then
    if ! grep -q "GROQ_API_KEY=" .env || grep -q "GROQ_API_KEY=$" .env || grep -q "GROQ_API_KEY=gsk_your" .env; then
        echo -e "${RED}❌ Error: Valid GROQ_API_KEY not set in .env${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Groq configuration found${NC}"
else
    echo -e "${RED}❌ Error: Invalid LLM_PROVIDER: $LLM_PROVIDER${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configuration verified${NC}"
echo ""

# Step 2: Check dependencies
echo -e "${YELLOW}[2/6] Checking dependencies...${NC}"

if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${RED}❌ Error: FastAPI not installed${NC}"
    echo -e "${YELLOW}Run: pip install -e .${NC}"
    exit 1
fi

if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${RED}❌ Error: pytest not installed${NC}"
    echo -e "${YELLOW}Run: pip install -e \".[dev]\"${NC}"
    exit 1
fi

if ! python -c "import httpx" 2>/dev/null; then
    echo -e "${RED}❌ Error: httpx not installed${NC}"
    echo -e "${YELLOW}Run: pip install httpx${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All dependencies installed${NC}"
echo ""

# Step 3: Start the application in background
echo -e "${YELLOW}[3/6] Starting FastAPI application...${NC}"

# Kill any existing uvicorn processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the app in background
uvicorn app.api:app --host 0.0.0.0 --port 8000 > /tmp/code-reviewer-app.log 2>&1 &
APP_PID=$!

echo -e "${GREEN}✓ Application started (PID: $APP_PID)${NC}"
echo ""

# Step 4: Wait for service to be ready
echo -e "${YELLOW}[4/6] Waiting for service to be ready...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is ready!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
    
    # Check if process is still running
    if ! kill -0 $APP_PID 2>/dev/null; then
        echo -e "\n${RED}❌ Application process died${NC}"
        echo -e "${YELLOW}Check logs at: /tmp/code-reviewer-app.log${NC}"
        cat /tmp/code-reviewer-app.log
        exit 1
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "\n${RED}❌ Service failed to start within 30 seconds${NC}"
    echo -e "${YELLOW}Check logs at: /tmp/code-reviewer-app.log${NC}"
    cat /tmp/code-reviewer-app.log
    kill $APP_PID 2>/dev/null || true
    exit 1
fi

echo ""

# Step 5: Run the tests
echo -e "${YELLOW}[5/6] Running end-to-end tests...${NC}"
echo ""

# Run pytest with verbose output and coverage
pytest tests/test_e2e.py -v --tb=short --color=yes || TEST_RESULT=$?

echo ""

# Step 6: Cleanup
echo -e "${YELLOW}[6/6] Cleaning up...${NC}"

# Kill the application
kill $APP_PID 2>/dev/null || true
sleep 1

# Ensure it's dead
kill -9 $APP_PID 2>/dev/null || true

echo -e "${GREEN}✓ Application stopped${NC}"
echo ""

# Final result
echo -e "${BLUE}========================================${NC}"
if [ ${TEST_RESULT:-0} -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${BLUE}========================================${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Check test output above for details${NC}"
    echo -e "${YELLOW}Application logs: /tmp/code-reviewer-app.log${NC}"
    exit 1
fi
