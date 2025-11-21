#!/bin/bash

# ================================
# AI-Trader Initialization Script
# ================================
# This script sets up the AI-Trader project environment

set -e  # Exit on error

echo "🚀 Initializing AI-Trader project..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# 1. Check Python Version
# ================================
echo -e "${BLUE}📌 Step 1: Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✅ Python version $PYTHON_VERSION is compatible${NC}"
else
    echo -e "${RED}❌ Python 3.10+ is required. Current version: $PYTHON_VERSION${NC}"
    exit 1
fi
echo ""

# ================================
# 2. Create Virtual Environment
# ================================
echo -e "${BLUE}📌 Step 2: Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi
echo ""

# ================================
# 3. Activate Virtual Environment
# ================================
echo -e "${BLUE}📌 Step 3: Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# ================================
# 4. Upgrade pip
# ================================
echo -e "${BLUE}📌 Step 4: Upgrading pip...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✅ pip upgraded${NC}"
echo ""

# ================================
# 5. Install Dependencies
# ================================
echo -e "${BLUE}📌 Step 5: Installing dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# ================================
# 6. Setup Environment Variables
# ================================
echo -e "${BLUE}📌 Step 6: Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created from .env.example${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys:${NC}"
    echo -e "${YELLOW}   - OPENAI_API_KEY${NC}"
    echo -e "${YELLOW}   - ALPHAADVANTAGE_API_KEY${NC}"
    echo -e "${YELLOW}   - JINA_API_KEY${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
fi
echo ""

# ================================
# 7. Create Runtime Environment File
# ================================
echo -e "${BLUE}📌 Step 7: Creating runtime environment file...${NC}"
if [ ! -f ".runtime_env.json" ]; then
    echo '{"TODAY_DATE": "2025-10-01", "SIGNATURE": "default", "IF_TRADE": false}' > .runtime_env.json
    echo -e "${GREEN}✅ .runtime_env.json created${NC}"
else
    echo -e "${YELLOW}⚠️  .runtime_env.json already exists${NC}"
fi
echo ""

# ================================
# 8. Create Directory Structure
# ================================
echo -e "${BLUE}📌 Step 8: Creating directory structure...${NC}"
mkdir -p data/agent_data
mkdir -p logs
mkdir -p configs
mkdir -p tests
echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# ================================
# 9. Verify Installation
# ================================
echo -e "${BLUE}📌 Step 9: Verifying installation...${NC}"
python3 -c "import langchain; import langchain_openai; import fastmcp; print('✅ All core packages imported successfully')"
echo ""

# ================================
# Success Message
# ================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 AI-Trader initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "  1. Edit ${YELLOW}.env${NC} file and add your API keys"
echo -e "  2. Run ${YELLOW}./fresh_data.sh${NC} to download stock data"
echo -e "  3. Run ${YELLOW}python agent_tools/start_mcp_services.py${NC} to start MCP services"
echo -e "  4. Run ${YELLOW}python main.py${NC} to start trading"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo -e "  - README.md: Project overview and setup guide"
echo -e "  - configs/README.md: Configuration guide"
echo ""
echo -e "${BLUE}💡 Tip:${NC} Activate the virtual environment in new terminal sessions:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo ""
