# WealthX Data Puller

A Python application to pull WealthX data in batches into a MongoDB database with resume capability.

## Features

- Batch processing of ~420k WealthX records
- Configurable batch sizes (default: 12,000 records per batch)
- Resume capability from last successful pull
- Scheduled execution (3-4 times per day)
- Error handling and retry logic
- Progress tracking and logging

## Quick Setup for 10-Day Run

### Prerequisites

- Python 3.11+
- MongoDB (local or cloud)
- WealthX API credentials

### Step 1: Initial Setup

```bash
# Clone/navigate to project directory
cd /path/to/pull-wealthx

# Run automated setup
./setup.sh
```

### Step 2: Configure Credentials

```bash
# Edit .env with your actual WealthX credentials
cp .env.example .env
nano .env  # or your preferred editor

# Required: Add your WealthX API credentials
WEALTHX_USERNAME=your_actual_username
WEALTHX_PASSWORD=your_actual_password
```

### Step 3: Production Setup for 10-Day Run

```bash
# Run production setup (handles MongoDB, testing, and service configuration)
./production_setup.sh
```

### Step 4: Start the 10-Day Process

Choose one of these options:

**Option A: Start Scheduler Directly (Foreground)**

```bash
python scheduler.py
```

**Option B: Start as Background Service (macOS)**

```bash
launchctl load ~/Library/LaunchAgents/com.wealthx.scheduler.plist
launchctl start com.wealthx.scheduler
```

**Option C: Docker Deployment (Recommended)**

```bash
docker-compose up -d mongodb
docker-compose up -d scheduler
```

### Step 5: Monitor Progress

```bash
# Real-time monitoring dashboard
python monitor.py

# Check status
python main.py --status

# View logs
tail -f logs/scheduler.log
```

## Configuration

The application can be configured via environment variables in `.env`:

- `WEALTHX_API_KEY`: Your WealthX API key
- `WEALTHX_API_SECRET`: Your WealthX API secret
- `MONGO_URI`: MongoDB connection string
- `BATCH_SIZE`: Number of records to pull per batch (default: 12,000)
- `MAX_RETRIES`: Maximum retry attempts for failed requests
- `RETRY_DELAY`: Delay in seconds between retries

## Usage

### Manual Execution

```bash
python main.py --batch-size 10000 --resume
```

### Scheduled Execution

```bash
python scheduler.py
```

The scheduler will run the data pull 3 times per day at configured intervals.

## Architecture

- `main.py`: Entry point and CLI interface
- `src/wealthx_client.py`: WealthX API client
- `src/mongo_client.py`: MongoDB operations
- `src/batch_processor.py`: Batch processing logic
- `src/progress_tracker.py`: Resume capability and progress tracking
- `scheduler.py`: Automated scheduling
