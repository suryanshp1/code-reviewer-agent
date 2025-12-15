#!/bin/bash
# Quick start script for Code Reviewer CI Agent

set -e

echo "🤖 Code Reviewer CI Agent - Setup Script"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "📝 Please edit .env and add:"
    echo "   - Your LLM API key (OPENAI_API_KEY or GROQ_API_KEY)"
    echo "   - A secure REVIEW_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Source environment
export $(cat .env | grep -v '^#' | xargs)

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GROQ_API_KEY" ]; then
    echo "❌ No LLM API key configured in .env"
    echo "   Please set OPENAI_API_KEY or GROQ_API_KEY"
    exit 1
fi

if [ -z "$REVIEW_API_KEY" ]; then
    echo "❌ No REVIEW_API_KEY configured in .env"
    echo "   Please set a secure API key for authentication"
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Check for Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected"
    echo ""
    echo "Choose deployment mode:"
    echo "  1) Development (Docker Compose - no Ray Serve)"
    echo "  2) Production (Docker Compose with Ray Serve)"
    echo "  3) Local development (pip install)"
    echo ""
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            echo ""
            echo "🚀 Starting in development mode..."
            docker-compose up --build
            ;;
        2)
            echo ""
            echo "🚀 Starting in production mode with Ray Serve..."
            docker-compose --profile production up --build
            ;;
        3)
            echo ""
            echo "📦 Installing dependencies..."
            pip install -e .
            echo ""
            echo "🚀 Starting API server..."
            uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo "📦 Installing dependencies..."
    pip install -e .
    echo ""
    echo "🚀 Starting API server..."
    uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
fi
