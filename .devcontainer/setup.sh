#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  Multimax AI Hub - Dev Container Setup"
echo "========================================"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
cd /workspaces/multimax-ai-hub/backend
pip install --upgrade pip
pip install -r requirements.txt
pip install ruff mypy pytest pytest-asyncio httpx pytest-cov

# Install Node.js dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
cd /workspaces/multimax-ai-hub/frontend
npm install

# Create .env files if they don't exist
echo ""
echo "🔧 Creating environment files..."
cd /workspaces/multimax-ai-hub
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "  Created backend/.env from .env.example"
fi
if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "  Created frontend/.env from .env.example"
fi

# Verify Docker availability
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "  Docker is available: $(docker --version)"
else
    echo "  ⚠️ Docker is not installed. Some features may require Docker."
fi

# Check if Ollama is available
echo ""
echo "🤖 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  Ollama is available: $(ollama --version)"
else
    echo "  ⚠️ Ollama is not installed locally. It will be available via Docker."
fi

# Setup pre-commit hooks if pre-commit is available
echo ""
echo "🔗 Setting up pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "  Pre-commit hooks installed."
else
    echo "  ⚠️ pre-commit not found. Install with: pip install pre-commit"
fi

echo ""
echo "========================================"
echo "  ✅ Setup complete!"
echo "========================================"
echo ""
echo "To start development:"
echo "  Backend : cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  Frontend: cd frontend && npm run dev"
echo "  Docker  : docker compose -f docker/docker-compose.yml up -d"
echo ""