#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the project root
cd "$(dirname "$0")/.."

# Pull the latest changes from GitHub
echo "Pulling latest changes from GitHub..."
git pull origin main

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Restart the service
echo "Restarting the service..."
sudo systemctl restart fastapi

echo "Deployment completed successfully!"