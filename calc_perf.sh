#!/bin/bash

# ================================
# AI-Trader Performance Calculation Script
# ================================
# Calculate and display trading performance metrics

set -e  # Exit on error

echo "📊 Calculating AI-Trader performance metrics..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# 1. Check if data exists
# ================================
echo -e "${BLUE}📌 Step 1: Checking for trading data...${NC}"

if [ ! -d "data/agent_data" ]; then
    echo -e "${RED}❌ Agent data directory not found${NC}"
    echo -e "${YELLOW}Please run trading first: python main.py${NC}"
    exit 1
fi

# Count agent directories
AGENT_COUNT=$(find data/agent_data -mindepth 1 -maxdepth 1 -type d | wc -l)

if [ "$AGENT_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No agent data found${NC}"
    echo -e "${YELLOW}Please run trading first: python main.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found data for $AGENT_COUNT agent(s)${NC}"
echo ""

# ================================
# 2. Run performance calculation
# ================================
echo -e "${BLUE}📌 Step 2: Calculating performance metrics...${NC}"
python3 calculate_performance.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Performance calculation complete${NC}"
else
    echo -e "${RED}❌ Error calculating performance${NC}"
    exit 1
fi
echo ""

# ================================
# 3. Display report location
# ================================
if [ -f "performance_report.json" ]; then
    echo -e "${BLUE}📄 Performance report saved to: ${YELLOW}performance_report.json${NC}"
    echo ""
fi

# ================================
# Success Message
# ================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Performance analysis complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
