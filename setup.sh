#!/bin/bash

# WealthX Data Puller Setup Script

echo "Setting up WealthX Data Puller..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your WealthX API credentials and MongoDB settings."
fi

# Create logs directory
mkdir -p logs

# Make scripts executable
chmod +x main.py
chmod +x scheduler.py

echo ""
echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your WealthX API credentials"
echo "2. Ensure MongoDB is running"
echo "3. Test the connection: python main.py --status"
echo "4. Run a test batch: python main.py --max-batches 1"
echo "5. Start scheduled pulls: python scheduler.py"
echo ""
echo "For help: python main.py --help"
