#!/bin/bash

# ================================
# AI-Trader MCP Services Stopper
# ================================
# Stop all MCP services

echo "🛑 Stopping AI-Trader MCP services..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# Stop services by PID
# ================================
if [ -f ".mcp_services.pid" ]; then
    echo -e "${BLUE}📌 Stopping services by PID...${NC}"
    MCP_PID=$(cat .mcp_services.pid)

    if ps -p $MCP_PID > /dev/null 2>&1; then
        kill $MCP_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Stopped services (PID: $MCP_PID)${NC}"
        rm .mcp_services.pid
    else
        echo -e "${YELLOW}⚠️  Process $MCP_PID not running${NC}"
        rm .mcp_services.pid
    fi
else
    echo -e "${YELLOW}⚠️  No PID file found${NC}"
fi
echo ""

# ================================
# Stop services by port
# ================================
echo -e "${BLUE}📌 Stopping services by port...${NC}"

# Get ports from environment or use defaults
MATH_PORT=${MATH_HTTP_PORT:-8000}
SEARCH_PORT=${SEARCH_HTTP_PORT:-8001}
TRADE_PORT=${TRADE_HTTP_PORT:-8002}
GETPRICE_PORT=${GETPRICE_HTTP_PORT:-8003}

# Function to stop process on port
stop_port() {
    local port=$1
    local service_name=$2

    PID=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
        kill $PID 2>/dev/null || true
        echo -e "${GREEN}✅ Stopped $service_name (port $port, PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠️  No process on port $port ($service_name)${NC}"
    fi
}

stop_port $MATH_PORT "Math service"
stop_port $SEARCH_PORT "Search service"
stop_port $TRADE_PORT "Trade service"
stop_port $GETPRICE_PORT "GetPrice service"

echo ""

# ================================
# Verify all stopped
# ================================
echo -e "${BLUE}📌 Verifying services stopped...${NC}"

ALL_STOPPED=true
for port in $MATH_PORT $SEARCH_PORT $TRADE_PORT $GETPRICE_PORT; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}❌ Port $port still in use${NC}"
        ALL_STOPPED=false
    fi
done

if [ "$ALL_STOPPED" = true ]; then
    echo -e "${GREEN}✅ All services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may still be running${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 MCP services stopped!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
