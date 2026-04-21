@echo off
REM Pharma Supply Chain Setup Script for Windows
REM This script sets up the entire development environment

echo 🚀 Setting up Pharma Supply Chain Tracking System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 14 or higher.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Create virtual environment
echo 📦 Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install Python dependencies
echo 📥 Installing Python dependencies...
pip install -r requirements.txt
pip install -r scripts\requirements.txt

REM Install Solidity compiler
echo 🔧 Installing Solidity compiler...
pip install py-solc-x
python -c "from solcx import install_solc; install_solc('0.8.19')"

echo ✅ Setup completed successfully!
echo.
echo 🎯 Next steps:
echo 1. Set up your environment variables:
echo    - Copy backend\.env.example to backend\.env
echo    - Add your Infura Project ID
echo    - Add your private key (with Sepolia ETH)
echo.
echo 2. Deploy the smart contract:
echo    cd scripts ^&^& python deploy_contract.py
echo.
echo 3. Start the backend server:
echo    cd backend ^&^& python app.py
echo.
echo 4. Open the frontend:
echo    Open frontend\index.html in your browser
echo.
echo 📚 For detailed instructions, see README.md
pause
