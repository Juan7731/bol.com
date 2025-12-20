# Quick Start Guide - Commands to Run

## 🚀 Most Common Commands

### Process Orders (Main Function)
```bash
python order_processing.py
```
**What it does:**
- Fetches orders from Bol.com
- Generates CSV files
- Uploads to SFTP
- Sends email notification

### Test Everything
```bash
python run_all_tests.py
```
**What it does:**
- Tests API connection
- Tests database
- Tests SFTP connection
- Tests email config
- Tests all components

### Process All Accounts
```bash
python multi_account_processor.py
```
**What it does:**
- Processes orders from all active Bol.com accounts (Trivium, Jean, etc.)

### Process Callback Files
```bash
python run_callback_scheduler.py
```
**What it does:**
- Checks FTP for HTML status files
- Updates Bol.com orders when "verzonden" is found

## 📋 Testing Commands

### Quick System Test
```bash
python quick_test.py
```
Checks database and CSV files

### Full System Test
```bash
python test_system.py
```
Comprehensive testing of all features

### Test SFTP Upload
```bash
python verify_ftp_upload.py
```
Verifies SFTP connection and file upload

### Force Generate CSV (for testing)
```bash
python generate_test_excel.py
```
Generates CSV files even if orders are already processed

## ⚙️ Configuration Commands

### View Configuration
```bash
python -c "from config_manager import get_config_summary; import json; print(json.dumps(get_config_summary(), indent=2))"
```

### Update Processing Times
```bash
python -c "from config_manager import update_processing_times; update_processing_times(['08:30', '15:01', '', ''])"
```

### Activate Jean Account
```bash
python -c "from config_manager import update_bol_account; update_bol_account('Jean', active=True)"
```

## 🔄 Scheduled Processing

### Run Scheduler (Long-running)
```bash
python run_scheduler.py
```
Runs continuously and processes orders at configured times

### Run Callback Scheduler (Continuous)
```bash
python run_callback_scheduler.py --continuous 60
```
Checks for callback files every 60 seconds

## 📊 Check Status

### Check Processed Orders
```bash
python -c "from order_database import get_processed_count; print(f'Processed: {get_processed_count()}')"
```

### Check Active Accounts
```bash
python -c "from config_manager import get_active_bol_accounts; print(get_active_bol_accounts())"
```

## 🐛 Troubleshooting

### Reset Database (to process all orders again)
```bash
del bol_orders.db
python order_processing.py
```

### Test Email Sending
```bash
python -c "from order_processing import send_summary_email; send_summary_email(1, []); print('Email sent!')"
```

## 📝 Expected Output

### Successful Order Processing:
```
Starting Bol.com order processing run...
Retrieved 8 open orders
Processing 8 new orders
Generated S-001.csv with 8 orders
✅ Successfully uploaded S-001.csv
Email sent successfully
```

### Successful Test:
```
✅ ALL TESTS PASSED!
Total: 7 passed, 0 failed, 0 skipped
```

