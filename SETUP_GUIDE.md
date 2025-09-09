# WealthX Data Puller - Updated Setup Guide

## 🔄 **IMPORTANT UPDATES MADE**

Based on your actual WealthX API curl example, I've updated the entire system to work with the real API:

### **API Changes Made:**

1. **Endpoint**: Changed from `https://api.wealthx.com/v1/` to `https://connect.wealthx.com/rest/v1/`
2. **Authentication**: Changed from API key/secret to username/password headers
3. **Request Format**: Changed from offset/limit to fromIndex/toIndex (1-based indexing)
4. **Data Structure**: Updated to handle `dossiers` array instead of `profiles`
5. **ID Field**: Updated to use `ID` field instead of `wealthx_id`

### **MongoDB Changes:**

- Collection name changed to `dossiers` (from `profiles`)
- Indexes updated for WealthX dossier structure (`ID`, `dossierCategory`, `dossierState`, etc.)
- Upsert logic updated to use `ID` field as unique identifier

### **Progress Tracking:**

- Changed from offset-based to index-based tracking (1-based indexing)
- Resume capability now uses the highest `ID` from MongoDB

---

## 🚀 **COMPLETE SETUP FOR 10-DAY RUN**

### **Step 1: Configure Credentials**

Edit your `.env` file with actual WealthX credentials:

```bash
# WealthX API Configuration
WEALTHX_API_URL=https://connect.wealthx.com/rest/v1/
WEALTHX_USERNAME=your_actual_username
WEALTHX_PASSWORD=your_actual_password

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=wealthx_data
MONGO_COLLECTION=dossiers

# Batch Configuration (optimized for 420k records in 10 days)
BATCH_SIZE=500
MAX_RETRIES=3
RETRY_DELAY=60
REQUEST_TIMEOUT=30
DAILY_RUNS=3
```

### **Step 2: Test the API Connection**

```bash
# Test your credentials and API connection
python test_wealthx_api.py
```

### **Step 3: Run Production Setup**

```bash
# This will validate everything and set up services
./production_setup.sh
```

### **Step 4: Start the 10-Day Process**

**Option A: Direct Scheduler (Foreground)**

```bash
source venv/bin/activate
python scheduler.py
```

**Option B: Background Service (macOS)**

```bash
# Load and start the service
launchctl load ~/Library/LaunchAgents/com.wealthx.scheduler.plist
launchctl start com.wealthx.scheduler

# Check status
launchctl list | grep wealthx
```

**Option C: Docker (Recommended)**

```bash
# Start MongoDB and scheduler
docker-compose up -d mongodb
docker-compose up -d scheduler

# Monitor logs
docker-compose logs -f scheduler
```

### **Step 5: Monitor the 10-Day Run**

**Real-time Dashboard:**

```bash
python monitor.py
```

**Quick Status:**

```bash
python main.py --status
```

**Manual Test (single batch):**

```bash
python main.py --max-batches 1
```

---

## 📊 **10-DAY EXECUTION PLAN**

### **Updated Batch Strategy:**

- **Total Records**: ~420,000 dossiers
- **Batch Size**: 500 records per batch (adjustable based on API limits)
- **Total Batches**: ~840 batches needed
- **Schedule**: 3 runs per day (8 AM, 2 PM, 8 PM)
- **Batches per Run**: ~28 batches
- **Estimated Time**: ~8-10 days with built-in buffer

### **What the System Does:**

1. **Calls API**: `GET https://connect.wealthx.com/rest/v1/alldossiers?dossierType=both&fromIndex=1&toIndex=500`
2. **Processes Response**: Extracts `dossiers` array from JSON response
3. **Stores Data**: Upserts each dossier into MongoDB using `ID` as unique key
4. **Tracks Progress**: Saves highest processed `ID` for resume capability
5. **Schedules Next**: Waits for next scheduled time (3x daily)

### **Resume Logic:**

- If interrupted, finds the highest `ID` in MongoDB
- Resumes from `ID + 1` to avoid duplicates
- Maintains all progress and statistics

---

## 🔧 **MONITORING & MAINTENANCE**

### **Key Files to Watch:**

- `logs/scheduler.log` - Scheduling and system events
- `logs/wealthx_pull.log` - API calls and data processing
- `progress.json` - Current progress and statistics

### **Important Commands:**

```bash
# View current progress
cat progress.json | python -m json.tool

# Count records in MongoDB
python -c "
from src.mongo_client import MongoDBClient
client = MongoDBClient()
print(f'Total dossiers: {client.get_total_documents():,}')
client.close()
"

# Reset if needed (careful!)
python main.py --reset

# Cleanup duplicates
python main.py --cleanup
```

---

## 🎯 **READY TO START?**

1. **Edit `.env`** with your actual WealthX username/password
2. **Test connection**: `python test_wealthx_api.py`
3. **Run setup**: `./production_setup.sh`
4. **Start scheduler**: `python scheduler.py`
5. **Monitor**: `python monitor.py`

The system is now properly configured for the actual WealthX API and will efficiently pull all dossiers into MongoDB over 10 days with full resume capability! 🎉
