#!/bin/bash

# Pharma Supply Chain Setup Script
# This script sets up the entire development environment

echo "🚀 Setting up Pharma Supply Chain Tracking System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 14 or higher."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt
pip install -r scripts/requirements.txt

# Install Solidity compiler
echo "🔧 Installing Solidity compiler..."
pip install py-solc-x
python -c "from solcx import install_solc; install_solc('0.8.19')"

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Set up your environment variables:"
echo "   - Copy backend/.env.example to backend/.env"
echo "   - Add your Infura Project ID"
echo "   - Add your private key (with Sepolia ETH)"
echo ""
echo "2. Deploy the smart contract:"
echo "   cd scripts && python deploy_contract.py"
echo ""
echo "3. Start the backend server:"
echo "   cd backend && python app.py"
echo ""
echo "4. Open the frontend:"
echo "   Open frontend/index.html in your browser"
echo ""
echo "📚 For detailed instructions, see README.md"
