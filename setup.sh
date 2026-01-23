#!/bin/bash
# ============================================================
# SOL-SWARM ELITE - COMPLETE SETUP SCRIPT
# Run this after cloning or extracting the update
# ============================================================

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         SOL-SWARM ELITE - AUTOMATED SETUP                ║"
echo "║         \$AGENT Token | 100 AI Agents | 25/25/25/25       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}[1/6] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}[2/6] Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo ""
echo -e "${YELLOW}[3/6] Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup .env
echo ""
echo -e "${YELLOW}[4/6] Setting up configuration...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from template${NC}"
    echo -e "${YELLOW}  ⚠️  Please edit .env with your wallet addresses${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Create directories
echo ""
echo -e "${YELLOW}[5/6] Creating directories...${NC}"
mkdir -p logs data assets
echo -e "${GREEN}✓ Directories created${NC}"

# Verify installation
echo ""
echo -e "${YELLOW}[6/6] Verifying installation...${NC}"
python3 -c "
import sys
try:
    from src.tokenomics.agent_token import get_token_manager
    from src.agents.agent_spawner import get_agent_spawner
    from src.command_center import get_command_center
    print('✓ Core modules loaded')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo ""
echo "1. Configure your wallets in .env:"
echo "   - BOT_TRADING_WALLET=your_wallet_address"
echo "   - INFRASTRUCTURE_WALLET=your_wallet_address"
echo "   - DEVELOPMENT_WALLET=your_wallet_address"
echo "   - BUILDER_WALLET=your_wallet_address"
echo ""
echo "2. Launch \$AGENT token on pump.fun:"
echo "   python src/tokenomics/token_launch.py"
echo ""
echo "3. Start the dashboard:"
echo "   streamlit run main.py"
echo ""
echo "4. Or run the command center directly:"
echo "   python src/command_center.py"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Start with MAINNET_ENABLED=false (paper trading)${NC}"
echo ""
