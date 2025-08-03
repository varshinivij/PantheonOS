#!/bin/bash

# Development server with proper environment setup

echo "🚀 Starting Pantheon documentation development server..."

# Check if we're in the docs directory
if [ ! -f "Makefile" ] || [ ! -d "source" ]; then
    echo "❌ Error: Please run this script from the docs directory"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Using micromamba environment: pantheon-test${NC}"

# Ensure sphinx-autobuild is available
echo "📦 Checking sphinx-autobuild installation..."
micromamba run -n pantheon-test pip install -U sphinx-autobuild watchdog

# Clean build directory for fresh start
echo "🧹 Cleaning build directory..."
rm -rf build/*

# Configuration
HOST="127.0.0.1"
PORT="8080"

echo -e "${BLUE}Configuration:${NC}"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Environment: pantheon-test"
echo ""

echo -e "${GREEN}✨ Starting auto-reload server...${NC}"
echo -e "${GREEN}📍 URL: http://$HOST:$PORT${NC}"
echo ""
echo "The browser should auto-refresh when you save files!"
echo "Press Ctrl+C to stop"
echo ""

# Run sphinx-autobuild with explicit settings
exec micromamba run -n pantheon-test sphinx-autobuild \
    --host "$HOST" \
    --port "$PORT" \
    --delay 1 \
    --watch "source" \
    --watch "../pantheon" \
    --ignore "*.pyc" \
    --ignore "*.swp" \
    --ignore "*~" \
    --ignore ".git" \
    --ignore "build/*" \
    --ignore "__pycache__" \
    -W \
    source build/html