#!/bin/bash

# ================================
# AI-Trader Complete Run Script
# ================================
# This script runs the complete AI-Trader workflow

set -e  # Exit on error

echo "🤖 AI-Trader Complete Workflow"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# Parse command line arguments
# ================================
CONFIG_FILE=""
SKIP_DATA=false
SKIP_SERVICES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --skip-data)
            SKIP_DATA=true
            shift
            ;;
        --skip-services)
            SKIP_SERVICES=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --config FILE    Use specific config file"
            echo "  --skip-data          Skip data refresh"
            echo "  --skip-services      Skip starting MCP services"
            echo "  -h, --help           Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ================================
# 1. Check environment
# ================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 1: Environment Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}Please run ./init.sh first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment OK${NC}"
echo ""

# ================================
# 2. Refresh data (optional)
# ================================
if [ "$SKIP_DATA" = false ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Step 2: Data Refresh${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    echo -e "${YELLOW}Do you want to refresh stock data? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        ./fresh_data.sh
    else
        echo -e "${YELLOW}⚠️  Skipping data refresh${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping data refresh (--skip-data)${NC}"
    echo ""
fi

# ================================
# 3. Start MCP services (optional)
# ================================
if [ "$SKIP_SERVICES" = false ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Step 3: Start MCP Services${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    ./start_services.sh
else
    echo -e "${YELLOW}⚠️  Skipping MCP services (--skip-services)${NC}"
    echo ""
fi

# ================================
# 4. Run trading
# ================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: Run AI Trading${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -z "$CONFIG_FILE" ]; then
    echo -e "${BLUE}Running with default config...${NC}"
    python3 main.py
else
    echo -e "${BLUE}Running with config: $CONFIG_FILE${NC}"
    python3 main.py "$CONFIG_FILE"
fi

# ================================
# 5. Calculate performance
# ================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 5: Performance Analysis${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

./calc_perf.sh

# ================================
# 6. Cleanup (optional)
# ================================
echo ""
echo -e "${YELLOW}Do you want to stop MCP services? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    ./stop_services.sh
else
    echo -e "${YELLOW}⚠️  MCP services still running${NC}"
    echo -e "${BLUE}Run ./stop_services.sh to stop them${NC}"
fi

# ================================
# Success Message
# ================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 AI-Trader workflow complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 Results:${NC}"
echo -e "  - Performance report: ${YELLOW}performance_report.json${NC}"
echo -e "  - Agent data: ${YELLOW}data/agent_data/${NC}"
echo -e "  - Logs: ${YELLOW}data/agent_data/*/log/${NC}"
echo ""
