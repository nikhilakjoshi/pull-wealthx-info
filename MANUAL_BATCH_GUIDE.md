# Manual Batch Trigger Guide

This guide explains how to use the `manual_batch_trigger.py` script to manually control your WealthX data fetching process.

## Overview

Your WealthX data puller fetches ~420k profiles/dossiers from the WealthX API and stores them in MongoDB. The system works with two batch sizes:

- **API batches**: 500 records per WealthX API call
- **Processing sessions**: 14,000 records per session (≈28 API calls)

The manual trigger script gives you full control over when and how batches are processed.

## Quick Start

```bash
# Basic batch session (14,000 records)
python manual_batch_trigger.py

# Check current status
python manual_batch_trigger.py --status-only
```

## Command Reference

### Basic Operations

| Command | Description |
|---------|-------------|
| `python manual_batch_trigger.py` | Run a single batch session with default settings |
| `python manual_batch_trigger.py --status-only` | Show current status and exit |
| `python manual_batch_trigger.py --full-sync` | Run continuous sessions until all data is processed |

### Customization Options

| Option | Description | Example |
|--------|-------------|---------|
| `--processing-batch-size N` | Custom records per session | `--processing-batch-size 5000` |
| `--max-api-batches N` | Limit API calls (testing) | `--max-api-batches 5` |
| `--no-resume` | Start from beginning | `--no-resume` |
| `--quiet` | Suppress console output | `--quiet` |
| `--log-level LEVEL` | Set logging level | `--log-level DEBUG` |

### Maintenance Operations

| Command | Description | Use Case |
|---------|-------------|----------|
| `--cleanup` | Remove duplicates and optimize DB | After large imports |
| `--reset-progress` | Reset all progress tracking | Start completely over |

## Usage Examples

### Testing and Development

```bash
# Small test run (5 API batches = ~2,500 records)
python manual_batch_trigger.py --max-api-batches 5

# Custom smaller session for testing
python manual_batch_trigger.py --processing-batch-size 1000

# Check status without running anything
python manual_batch_trigger.py --status-only
```

### Production Operations

```bash
# Standard single session
python manual_batch_trigger.py

# Full synchronization (runs until complete)
python manual_batch_trigger.py --full-sync

# Run with minimal console output
python manual_batch_trigger.py --quiet

# Emergency fresh start (resets all progress)
python manual_batch_trigger.py --reset-progress
```

### Maintenance

```bash
# Clean up duplicates and optimize database
python manual_batch_trigger.py --cleanup

# Reset progress tracking (use with caution!)
python manual_batch_trigger.py --reset-progress
```

## Understanding the Output

### Status Display
```
==================================================
     WealthX Data Puller - Current Status
==================================================
Database Records:     245,832
Session ID:           20240909_143022
Batches Completed:    18
Records Processed:    245,832
Last Index:           245,832
Total Records:        421,847
Errors:               0
WealthX API:          ✓ Connected
MongoDB:              ✓ Connected
Completion:           58.29%
==================================================
```

### Session Completion
```
==================================================
     BATCH SESSION COMPLETED
==================================================
Session Records:      14,000
API Calls Made:       28
Total Processed:      259,832
Completion:           61.61%
Est. Remaining Days:  4.2
Session Duration:     324.5s
==================================================
```

## Progress Tracking

The system automatically tracks:
- **Last processed index**: Where to resume from
- **Total records processed**: Cumulative count
- **Session statistics**: Per-run metrics
- **Error count**: Failed operations
- **Completion percentage**: Overall progress

Progress is saved after each API batch, so you can safely interrupt and resume.

## Safety Features

### Connection Validation
- Tests WealthX API connectivity
- Validates MongoDB connection
- Fails safely if services unavailable

### Progress Protection
- Resume capability from last successful batch
- Progress saved after each API call
- Safe interrupt handling (Ctrl+C)

### Confirmation Prompts
- `--reset-progress` requires typing 'YES'
- Clear warnings for destructive operations

## Troubleshooting

### Common Issues

**Connection Failed**
```bash
# Check your .env file has correct credentials
python manual_batch_trigger.py --status-only
```

**Want to Start Over**
```bash
# Reset progress (will ask for confirmation)
python manual_batch_trigger.py --reset-progress
```

**Database Issues**
```bash
# Clean up duplicates and optimize
python manual_batch_trigger.py --cleanup
```

### Logs

All operations are logged to:
- `logs/manual_batch.log` - Script-specific logs
- `logs/wealthx_pull.log` - General application logs

Use `--log-level DEBUG` for detailed troubleshooting.

## Integration with Existing System

### Relationship to Scheduler
- `scheduler.py` - Automated 3-4 times daily
- `manual_batch_trigger.py` - On-demand control
- Both use the same `BatchProcessor` core

### Relationship to Main Script
- `main.py` - Original CLI interface
- `manual_batch_trigger.py` - Enhanced manual control
- Compatible and complementary

## Best Practices

### For Testing
1. Use `--max-api-batches 5` for quick tests
2. Check `--status-only` before large runs
3. Use `--processing-batch-size 1000` for small tests

### For Production
1. Run `--status-only` to check progress
2. Use `--full-sync` for complete data pulls
3. Run `--cleanup` periodically
4. Monitor logs in `logs/` directory

### For Maintenance
1. Regular `--cleanup` runs
2. Monitor disk space and MongoDB performance
3. Check logs for error patterns
4. Use `--reset-progress` only when necessary

## Environment Variables

The script respects all existing `.env` configuration:

```env
# API Configuration
WEALTHX_USERNAME=your_username
WEALTHX_PASSWORD=your_password
WEALTHX_API_URL=https://connect.wealthx.com/rest/v1/

# Batch Sizes
API_BATCH_SIZE=500
PROCESSING_BATCH_SIZE=14000

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=wealthx_data
MONGO_COLLECTION=dossiers

# Logging
LOG_LEVEL=INFO
```

## Security Notes

- Credentials are loaded from `.env` file
- No credentials exposed in command line
- Logs don't contain sensitive information
- Progress tracking doesn't store API data

---

**Need Help?**
- Check logs in `logs/` directory
- Use `--status-only` to diagnose issues
- Run with `--log-level DEBUG` for detailed output
- All operations are safely resumable