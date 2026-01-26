#!/bin/bash
# =============================================================================
# SOL-SWARM Elite Setup Script
# =============================================================================

set -e

echo "🤖 SOL-SWARM Elite Setup"
echo "========================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Python 3.10+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "   ⚠️  Edit .env with your configuration"
fi

# Create necessary directories
mkdir -p logs
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "========================"
echo "🚀 NEXT STEPS:"
echo "========================"
echo ""
echo "1. Edit .env with your configuration:"
echo "   nano .env"
echo ""
echo "2. Generate fee wallets (optional):"
echo "   python generate_wallets.py"
echo ""
echo "3. Start the dashboard:"
echo "   streamlit run main.py"
echo ""
echo "4. Visit: http://localhost:8501"
echo ""
echo "========================"
echo "⚠️  IMPORTANT:"
echo "========================"
echo "• Paper trading is enabled by default"
echo "• Set MAINNET_ENABLED=true for real trading"
echo "• 90%+ of memecoins result in LOSS"
echo "• NEVER invest more than you can lose"
echo ""
