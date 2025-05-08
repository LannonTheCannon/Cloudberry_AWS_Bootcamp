#!/bin/bash

echo "🔁 Restarting Flask app..."

# Activate virtual environment
source venv/bin/activate

# Kill any existing app running on port 5000
echo "🔪 Killing any existing app on port 5000..."
fuser -k 5000/tcp || true

# Pull the latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Start the Flask app
echo "🚀 Starting app on http://0.0.0.0:5000 ..."
nohup python3 app.py > flask.log 2>&1 &

echo "✅ Flask app restarted. Logs: tail -f flask.log"

