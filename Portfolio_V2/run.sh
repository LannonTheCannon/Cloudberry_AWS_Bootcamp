#!/bin/bash


# 1 Go to correct project directory 
cd ~/Cloudberry_AWS_Bootcamp/Portfolio_V2

# 2. Pull the latest code from Github main branch 
echo "🔄 Pulling latest changes from GitHub..."
git pull origin main

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Export Flask environment to production
export FLASK_ENV=production

# Optional: export AWS region if needed by boto3
export AWS_DEFAULT_REGION=us-west-1

# 3. Run the Flask app (make sure to set the port if different)
echo "🚀 Starting Flask app in production mode on port 5001..."
python3 app.py
