#!/bin/bash

# Local development setup script for University Hub

echo "========================================="
echo "University Hub - Local Setup"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "Activating virtual environment..."

# Activate based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✅ Pip upgraded"
echo ""

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
echo "✅ Requirements installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found"
    echo "Creating .env from .env.development..."
    cp .env.development .env
    echo "✅ .env file created"
    echo "⚠️  Please update the .env file with your local settings"
else
    echo "✅ .env file exists"
fi

echo ""
echo "========================================="
echo "Setup complete! Next steps:"
echo "========================================="
echo ""
echo "1. Update your .env file with correct database credentials"
echo "2. Create database: CREATE DATABASE university_hub CHARACTER SET utf8mb4;"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Load sample data (optional): python manage.py populate_sample_data"
echo "6. Run server: python manage.py runserver"
echo ""
echo "========================================="

