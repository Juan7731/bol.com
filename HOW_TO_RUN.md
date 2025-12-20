# How to Run and Test the Project

## Quick Start Commands

### 1. Process Orders (Main Function)
```bash
# Process orders from default account (Trivium)
python order_processing.py

# Process orders from all active accounts
python multi_account_processor.py
```

### 2. Test Order Processing (Force Generate CSV)
```bash
# Generate CSV files even if orders are already processed (for testing)
python generate_test_excel.py
```

### 3. Test System Components
```bash
# Run comprehensive system test
python test_system.py

# Quick test (check database and CSV files)
python quick_test.py
```

### 4. Process Status Callbacks
```bash
# Process callback files once
python run_callback_scheduler.py

# Process callback files continuously (every 60 seconds)
python run_callback_scheduler.py --continuous 60
```

### 5. Run Scheduled Processing
```bash
# Run scheduler (checks times and processes automatically)
python run_scheduler.py

# Or use the main script with scheduler flag
python order_processing.py --scheduler
```

## Testing Individual Components

### Test SFTP Connection and Upload
```bash
python verify_ftp_upload.py
```

### Test Email Configuration
```python
python -c "
from order_processing import send_summary_email
send_summary_email(5, ['test_file.csv'])
print('Email sent!')
"
```

### Test Configuration Manager
```python
# View current configuration
python -c "from config_manager import get_config_summary; import json; print(json.dumps(get_config_summary(), indent=2))"

# Update processing times
python -c "from config_manager import update_processing_times; update_processing_times(['08:30', '15:01', '', ''])"

# View active accounts
python -c "from config_manager import get_active_bol_accounts; print(get_active_bol_accounts())"
```

### Test Status Callback Handler
```python
# Test callback file processing
python -c "
from status_callback_handler import fetch_callback_files_sftp, process_callback_files
files = fetch_callback_files_sftp()
print(f'Found {len(files)} callback files')
if files:
    stats = process_callback_files()
    print(f'Processed: {stats}')
"
```

## Step-by-Step Testing Guide

### Step 1: Test API Connection
```bash
python -c "
from bol_api_client import BolAPIClient
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET
client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=True)
orders = client.get_all_open_orders()
print(f'✅ API Connection OK - Found {len(orders)} orders')
"
```

### Step 2: Test Order Processing
```bash
# This will:
# - Fetch orders from Bol.com
# - Classify them (Single/SingleLine/Multi)
# - Generate CSV files
# - Upload to SFTP
# - Send email notification
python order_processing.py
```

### Step 3: Verify Excel Files Generated
```bash
# Check local files
dir batches\*\*.xlsx

# Or use quick test
python quick_test.py
```

### Step 4: Verify SFTP Upload
```bash
python verify_ftp_upload.py
```

### Step 5: Check Email Sent
Check your email inbox for the summary email.

### Step 6: Test Callback Handler
```bash
# This will check FTP for HTML callback files
python run_callback_scheduler.py
```

## Complete Test Script

Run this to test everything at once:

```bash
python test_system.py
```

This will test:
- ✅ Database initialization
- ✅ Order processing
- ✅ CSV file structure
- ✅ Duplicate prevention

## Production Deployment

### Option 1: Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add these lines:
# Process orders at 08:00 and 15:01
0 8 * * * /usr/bin/python3 /path/to/order_processing.py
1 15 * * * /usr/bin/python3 /path/to/order_processing.py

# Process callbacks every minute
* * * * * /usr/bin/python3 /path/to/run_callback_scheduler.py
```

### Option 2: Python Scheduler (Long-running)
```bash
# Run order processing scheduler
python run_scheduler.py

# Run callback scheduler (in separate terminal)
python run_callback_scheduler.py --continuous 60
```

## Troubleshooting

### No Orders Processed
```bash
# Check if orders are already in database
python -c "from order_database import get_processed_count; print(f'Processed: {get_processed_count()}')"

# Reset database to process all orders again (for testing)
del bol_orders.db
python order_processing.py
```

### SFTP Upload Fails
```bash
# Test SFTP connection
python verify_ftp_upload.py
```

### Email Not Sending
```python
# Test email configuration
python -c "
from order_processing import send_summary_email
try:
    send_summary_email(1, [])
    print('✅ Email sent successfully')
except Exception as e:
    print(f'❌ Email error: {e}')
"
```

### No Callback Files Found
This is normal if there are no HTML files in the callback directory yet. The system will check every minute when running the scheduler.

## Expected Output

### Successful Order Processing
```
Starting Bol.com order processing run...
Retrieved 8 open orders
Processing 8 new orders
Generated S-001.csv with 8 orders
✅ Successfully uploaded S-001.csv
Email sent successfully
Processing run completed. Orders processed: 8
```

### Successful Callback Processing
```
BOL.COM STATUS CALLBACK PROCESSOR
Found 2 HTML files in callback directory
File callback1.html: Order A000C2F77M, Status: verzonden
✅ Successfully updated order A000C2F77M
Processing Summary:
  Files processed: 2
  Orders updated: 1
  Ignored (niet verzonden): 1
  Errors: 0
```

