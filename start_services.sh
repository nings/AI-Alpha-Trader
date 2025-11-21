#!/bin/bash

# ================================
# AI-Trader MCP Services Starter
# ================================
# Start all MCP services in background

set -e  # Exit on error

echo "🚀 Starting AI-Trader MCP services..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# Check if services are already running
# ================================
echo -e "${BLUE}📌 Checking for existing services...${NC}"

# Check ports
MATH_PORT=${MATH_HTTP_PORT:-8000}
SEARCH_PORT=${SEARCH_HTTP_PORT:-8001}
TRADE_PORT=${TRADE_HTTP_PORT:-8002}
GETPRICE_PORT=${GETPRICE_HTTP_PORT:-8003}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check all ports
SERVICES_RUNNING=false
if check_port $MATH_PORT; then
    echo -e "${YELLOW}⚠️  Port $MATH_PORT already in use (Math service)${NC}"
    SERVICES_RUNNING=true
fi
if check_port $SEARCH_PORT; then
    echo -e "${YELLOW}⚠️  Port $SEARCH_PORT already in use (Search service)${NC}"
    SERVICES_RUNNING=true
fi
if check_port $TRADE_PORT; then
    echo -e "${YELLOW}⚠️  Port $TRADE_PORT already in use (Trade service)${NC}"
    SERVICES_RUNNING=true
fi
if check_port $GETPRICE_PORT; then
    echo -e "${YELLOW}⚠️  Port $GETPRICE_PORT already in use (GetPrice service)${NC}"
    SERVICES_RUNNING=true
fi

if [ "$SERVICES_RUNNING" = true ]; then
    echo -e "${YELLOW}⚠️  Some services are already running${NC}"
    echo -e "${BLUE}To stop them, run: ./stop_services.sh${NC}"
    echo ""
fi

# ================================
# Start MCP services
# ================================
echo -e "${BLUE}📌 Starting MCP services...${NC}"

cd agent_tools

# Start services in background
python3 start_mcp_services.py &
MCP_PID=$!

# Save PID for later
echo $MCP_PID > ../.mcp_services.pid

echo -e "${GREEN}✅ MCP services started (PID: $MCP_PID)${NC}"
echo ""

# Wait a moment for services to start
sleep 2

# Verify services are running
echo -e "${BLUE}📌 Verifying services...${NC}"
SERVICES_OK=true

if ! check_port $MATH_PORT; then
    echo -e "${RED}❌ Math service (port $MATH_PORT) not responding${NC}"
    SERVICES_OK=false
fi

if ! check_port $SEARCH_PORT; then
    echo -e "${RED}❌ Search service (port $SEARCH_PORT) not responding${NC}"
    SERVICES_OK=false
fi

if ! check_port $TRADE_PORT; then
    echo -e "${RED}❌ Trade service (port $TRADE_PORT) not responding${NC}"
    SERVICES_OK=false
fi

if ! check_port $GETPRICE_PORT; then
    echo -e "${RED}❌ GetPrice service (port $GETPRICE_PORT) not responding${NC}"
    SERVICES_OK=false
fi

cd ..

if [ "$SERVICES_OK" = true ]; then
    echo -e "${GREEN}✅ All MCP services running successfully${NC}"
    echo ""
    echo -e "${BLUE}Service ports:${NC}"
    echo -e "  - Math: ${GREEN}$MATH_PORT${NC}"
    echo -e "  - Search: ${GREEN}$SEARCH_PORT${NC}"
    echo -e "  - Trade: ${GREEN}$TRADE_PORT${NC}"
    echo -e "  - GetPrice: ${GREEN}$GETPRICE_PORT${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 MCP services ready!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo -e "  - Run ${YELLOW}python main.py${NC} to start trading"
    echo -e "  - Run ${YELLOW}./stop_services.sh${NC} to stop services"
    echo ""
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo -e "${YELLOW}Check logs for details${NC}"
    exit 1
fi
