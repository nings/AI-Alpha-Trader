#!/bin/bash

# ================================
# AI-Trader Data Refresh Script
# ================================
# This script downloads the latest stock price data and processes it

set -e  # Exit on error

echo "📊 Starting data refresh for AI-Trader..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# 1. Check Environment
# ================================
echo -e "${BLUE}📌 Step 1: Checking environment...${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with your API keys${NC}"
    exit 1
fi

# Check if ALPHAADVANTAGE_API_KEY is set
source .env
if [ -z "$ALPHAADVANTAGE_API_KEY" ] || [ "$ALPHAADVANTAGE_API_KEY" = "your_alpha_vantage_api_key_here" ]; then
    echo -e "${RED}❌ ALPHAADVANTAGE_API_KEY not configured in .env${NC}"
    echo -e "${YELLOW}Please add your Alpha Vantage API key to .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment check passed${NC}"
echo ""

# ================================
# 2. Navigate to data directory
# ================================
echo -e "${BLUE}📌 Step 2: Navigating to data directory...${NC}"
cd data
echo -e "${GREEN}✅ In data directory${NC}"
echo ""

# ================================
# 3. Download daily prices
# ================================
echo -e "${BLUE}📌 Step 3: Downloading NASDAQ 100 daily prices...${NC}"
echo -e "${YELLOW}⚠️  Note: Alpha Vantage free tier has rate limits (5 calls/min, 500 calls/day)${NC}"
echo -e "${YELLOW}⚠️  This may take some time for all stocks...${NC}"
echo ""

python3 get_daily_price.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Daily prices downloaded successfully${NC}"
else
    echo -e "${RED}❌ Error downloading daily prices${NC}"
    cd ..
    exit 1
fi
echo ""

# ================================
# 4. Merge data into unified format
# ================================
echo -e "${BLUE}📌 Step 4: Merging data into unified format...${NC}"
python3 merge_jsonl.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Data merged into merged.jsonl${NC}"
else
    echo -e "${RED}❌ Error merging data${NC}"
    cd ..
    exit 1
fi
echo ""

# ================================
# 5. Verify data
# ================================
echo -e "${BLUE}📌 Step 5: Verifying data...${NC}"
if [ -f "merged.jsonl" ]; then
    line_count=$(wc -l < merged.jsonl)
    echo -e "${GREEN}✅ merged.jsonl exists with $line_count stocks${NC}"
else
    echo -e "${RED}❌ merged.jsonl not found${NC}"
    cd ..
    exit 1
fi
echo ""

# ================================
# Return to root directory
# ================================
cd ..

# ================================
# Success Message
# ================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Data refresh complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 Data Statistics:${NC}"
echo -e "  - Stocks: $line_count"
echo -e "  - Data file: ${YELLOW}data/merged.jsonl${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "  1. Run ${YELLOW}python agent_tools/start_mcp_services.py${NC} to start MCP services"
echo -e "  2. Run ${YELLOW}python main.py${NC} to start trading"
echo ""
