#!/bin/bash
set -e  # Exit on error

cd /home/ubuntu/qs-backend

echo "Pulling latest code..."
git pull origin main

# Set up virtualenv if not already
if [ ! -d ~/qs-backend/venv ]; then
    python3 -m venv ~/qs-backend/venv
fi

echo "Activating virtualenv..."
source /home/ubuntu/qs-backend/venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting backend service..."
sudo systemctl restart qs-backend

echo "Backend deployed successfully."
