#!/bin/bash

# WealthX Data Puller - 10-Day Production Setup Guide
# Run this script to set up the system for continuous 10-day operation

echo "🌟 WealthX Data Puller - 10-Day Production Setup"
echo "=================================================="

# Step 1: Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the pull-wealthx directory"
    exit 1
fi

# Step 2: Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Error: Virtual environment not found. Run ./setup.sh first"
    exit 1
}

# Step 3: Check MongoDB
echo "🗄️  Checking MongoDB connection..."
if ! python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017/').admin.command('ismaster')" 2>/dev/null; then
    echo "⚠️  MongoDB not running or not accessible"
    echo "   Starting MongoDB with Docker..."
    docker run -d --name wealthx-mongo -p 27017:27017 mongo:7.0 || {
        echo "❌ Error: Could not start MongoDB. Please install and start MongoDB manually"
        echo "   Option 1: Install MongoDB locally"
        echo "   Option 2: Use Docker: docker run -d --name wealthx-mongo -p 27017:27017 mongo:7.0"
        echo "   Option 3: Use cloud MongoDB (update MONGO_URI in .env)"
        exit 1
    }
    echo "✅ MongoDB started with Docker"
    sleep 5  # Wait for MongoDB to start
else
    echo "✅ MongoDB is running"
fi

# Step 4: Validate configuration
echo "⚙️  Validating configuration..."
python test_setup.py || {
    echo "❌ Configuration validation failed"
    echo "   Please check your .env file and ensure:"
    echo "   1. WEALTHX_API_KEY is set with your actual API key"
    echo "   2. WEALTHX_API_SECRET is set with your actual API secret"
    echo "   3. MongoDB is running and accessible"
    exit 1
}

# Step 5: Run a test batch
echo "🧪 Running test batch to verify everything works..."
python main.py --max-batches 1 || {
    echo "❌ Test batch failed"
    echo "   Please check the logs in logs/ directory"
    echo "   Common issues:"
    echo "   - Invalid WealthX API credentials"
    echo "   - Network connectivity issues"
    echo "   - MongoDB connection problems"
    exit 1
}

echo "✅ Test batch completed successfully!"

# Step 6: Show current status
echo "📊 Current system status:"
python main.py --status

# Step 7: Create systemd service for production (Linux) or launchd (macOS)
echo ""
echo "🚀 PRODUCTION DEPLOYMENT OPTIONS:"
echo "=================================="

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - create launchd service
    echo "For macOS (launchd service):"
    echo "1. Create ~/Library/LaunchAgents/com.wealthx.scheduler.plist:"
    cat << EOF > ~/Library/LaunchAgents/com.wealthx.scheduler.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wealthx.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/venv/bin/python</string>
        <string>$(pwd)/scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$(pwd)/logs/scheduler.out</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/logs/scheduler.err</string>
</dict>
</plist>
EOF
    
    echo "2. Load and start the service:"
    echo "   launchctl load ~/Library/LaunchAgents/com.wealthx.scheduler.plist"
    echo "   launchctl start com.wealthx.scheduler"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - create systemd service
    echo "For Linux (systemd service):"
    echo "1. Create /etc/systemd/system/wealthx-scheduler.service:"
    echo "   sudo tee /etc/systemd/system/wealthx-scheduler.service << EOF"
    cat << EOF
[Unit]
Description=WealthX Data Puller Scheduler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "   EOF"
    echo ""
    echo "2. Enable and start the service:"
    echo "   sudo systemctl enable wealthx-scheduler.service"
    echo "   sudo systemctl start wealthx-scheduler.service"
    echo "   sudo systemctl status wealthx-scheduler.service"
fi

echo ""
echo "🐳 DOCKER OPTION (Recommended for Production):"
echo "=============================================="
echo "1. docker-compose up -d mongodb"
echo "2. docker-compose up -d scheduler"
echo ""
echo "Monitor with:"
echo "  docker-compose logs -f scheduler"

echo ""
echo "📊 MONITORING DURING 10-DAY RUN:"
echo "================================"
echo "Check status:           python main.py --status"
echo "View logs:              tail -f logs/wealthx_pull.log"
echo "View scheduler logs:    tail -f logs/scheduler.log"
echo "Check progress:         cat progress.json | python -m json.tool"
echo "Database records:       python -c \"from src.mongo_client import MongoDBClient; print(f'Records: {MongoDBClient().get_total_documents():,}')\""

echo ""
echo "⚠️  IMPORTANT FOR 10-DAY RUN:"
echo "============================"
echo "1. Ensure your system stays running (no sleep/hibernate)"
echo "2. Monitor disk space for logs and MongoDB"
echo "3. Check logs daily for any issues"
echo "4. The system will automatically resume if interrupted"
echo "5. Estimated completion: $(python -c "
from src.config import get_batch_schedule
schedule = get_batch_schedule(420000, 10, 3)
print(f'{schedule[\"estimated_completion_days\"]:.1f} days')
")"

echo ""
echo "🎉 Setup complete! The system is ready for 10-day production run."
echo ""
echo "To start immediately:"
echo "  python scheduler.py"
echo ""
echo "Or start as background service using the systemd/launchd instructions above."
