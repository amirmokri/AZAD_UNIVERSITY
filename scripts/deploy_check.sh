#!/bin/bash

# Deployment readiness check script

echo "========================================="
echo "Deployment Readiness Check"
echo "========================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Check if required environment variables are set
echo "Checking required environment variables..."
required_vars=("SECRET_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "DB_HOST")

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" .env; then
        echo "✅ $var is set"
    else
        echo "❌ $var is not set in .env file"
        exit 1
    fi
done

echo ""
echo "Checking optional environment variables..."
optional_vars=("USE_S3_STORAGE" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")

for var in "${optional_vars[@]}"; do
    if grep -q "^${var}=" .env; then
        echo "✅ $var is set"
    else
        echo "⚠️  $var is not set (optional)"
    fi
done

echo ""
echo "Running Django deployment checks..."
python manage.py check --deploy

echo ""
echo "Running custom deployment check..."
python manage.py check_deployment

echo ""
echo "========================================="
echo "Deployment check complete!"
echo "========================================="

