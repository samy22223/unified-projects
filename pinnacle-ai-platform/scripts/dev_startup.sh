#!/bin/bash
# Pinnacle AI Platform - Development Startup Script
# This script sets up and starts the development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"

echo -e "${BLUE}🚀 Pinnacle AI Platform - Development Startup${NC}"
echo "Project root: $PROJECT_ROOT"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $REQUIRED_VERSION or higher is required. Found Python $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

if ! command_exists pip; then
    echo -e "${RED}❌ pip is not installed. Please install pip.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install/update requirements
echo -e "${YELLOW}📦 Installing/updating requirements...${NC}"
if [ -f "$REQUIREMENTS_FILE" ]; then
    pip install -r "$REQUIREMENTS_FILE"
    echo -e "${GREEN}✓ Requirements installed${NC}"
else
    echo -e "${RED}❌ Requirements file not found: $REQUIREMENTS_FILE${NC}"
    exit 1
fi

# Install development dependencies
echo -e "${YELLOW}🛠️  Installing development dependencies...${NC}"
pip install -e .
echo -e "${GREEN}✓ Development dependencies installed${NC}"

# Setup pre-commit hooks
echo -e "${YELLOW}🔒 Setting up pre-commit hooks...${NC}"
if command_exists pre-commit; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  pre-commit not found. Install with: pip install pre-commit${NC}"
fi

# Create .env file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚙️  Creating .env file from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✓ .env file created. Please update with your configuration.${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.example not found. Please create .env file manually.${NC}"
    fi
fi

# Check if Docker is available
if command_exists docker; then
    echo -e "${YELLOW}🐳 Checking Docker setup...${NC}"
    if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        echo -e "${GREEN}✓ Docker configuration found${NC}"
        echo -e "${BLUE}💡 To start with Docker: docker-compose up -d${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Install Docker for containerized development.${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/uploads"
mkdir -p "$PROJECT_ROOT/cache"
echo -e "${GREEN}✓ Directories created${NC}"

echo
echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo
echo -e "${BLUE}🚀 To start the development server:${NC}"
echo "  Option 1 - Direct:"
echo "    uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo
echo "  Option 2 - With Docker:"
echo "    docker-compose up"
echo
echo "  Option 3 - Django (if using Django):"
echo "    python manage.py runserver"
echo
echo -e "${BLUE}📚 API Documentation will be available at:${NC}"
echo "  http://localhost:8000/docs (FastAPI)"
echo "  http://localhost:8000/redoc (ReDoc)"
echo
echo -e "${BLUE}🔧 Useful commands:${NC}"
echo "  Run tests: pytest"
echo "  Format code: black ."
echo "  Sort imports: isort ."
echo "  Type checking: mypy ."
echo "  Linting: flake8 ."
echo
echo -e "${YELLOW}⚠️  Don't forget to:${NC}"
echo "  1. Update .env file with your configuration"
echo "  2. Set up your database (PostgreSQL recommended)"
echo "  3. Configure your AI service API keys"
echo "  4. Set up Redis for caching and sessions"
echo
echo -e "${GREEN}Happy coding! 🎉${NC}"