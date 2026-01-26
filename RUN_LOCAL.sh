#!/bin/bash
# SOL-SWARM Elite - One Command Start
set -e

echo "🤖 SOL-SWARM Elite Starting..."

# Create venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Use pre-configured .env
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo "🚀 Launching dashboard at http://localhost:8501"
streamlit run main.py --server.port=8501
