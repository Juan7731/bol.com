# 🚀 How to Run the Whole Project

## 📋 Prerequisites

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `requests>=2.31.0` - For API calls
- `paramiko>=3.4.0` - For SFTP uploads
- `reportlab>=4.0.0` - For PDF generation

### 2. Configure Settings
Edit `config.py` to set your:
- Bol.com API credentials (`BOL_CLIENT_ID`, `BOL_CLIENT_SECRET`)
- SFTP server details
- Email settings
- Processing times

## 🎯 Main Ways to Run the Project

### Option 1: Single Processing Run (Recommended for Testing)
Run one complete processing cycle:
```bash
python order_processing.py
```

**What it does:**
1. ✅ Fetches open orders from Bol.com API
2. ✅ Classifies orders (Single, SingleLine, Multi)
3. ✅ Downloads shipping labels (PDFs)
4. ✅ Generates CSV files (S-001.csv, SL-001.csv, M-001.csv)
5. ✅ Uploads CSV files to SFTP server
6. ✅ Sends email summary

**Expected Output:**
```
Starting Bol.com order processing run...
Retrieved 8 open orders
Processing 8 new orders
Generated S-001.csv with 8 orders
✅ Successfully uploaded S-001.csv
Email sent successfully
Processing run completed. Orders processed: 8
```

---

### Option 2: Scheduled Processing (Production Mode)
Run continuously and process orders at configured times:
```bash
python run_scheduler.py
```

**What it does:**
- Runs continuously in the background
- Processes orders automatically at configured times (default: 08:00 and 15:01)
- Checks every 30 seconds if it's time to process
- Press `Ctrl+C` to stop

**Configure processing times in `config.py`:**
```python
PROCESS_TIMES = [
    "08:00",  # Morning run
    "15:01",  # Afternoon run
    "",       # Optional slot 3
    "",       # Optional slot 4
]
```

---

### Option 3: Process Multiple Accounts
If you have multiple Bol.com accounts (Trivium, Jean, etc.):
```bash
python multi_account_processor.py
```

**What it does:**
- Processes orders from all active Bol.com accounts
- Generates separate CSV files for each account
- Uploads all files to SFTP

---

### Option 4: Process Status Callbacks
Check FTP for order status updates and update Bol.com:
```bash
# Run once
python run_callback_scheduler.py

# Run continuously (checks every 60 seconds)
python run_callback_scheduler.py --continuous 60
```

**What it does:**
- Downloads HTML status files from FTP
- Checks for "verzonden" (shipped) status
- Updates Bol.com orders via API

---

## 🧪 Testing Commands

### Test Everything at Once
```bash
python run_all_tests.py
```
Tests all components: API, database, SFTP, email, CSV generation

### Quick System Test
```bash
python test_system.py
```
Comprehensive test of all features

### Quick Status Check
```bash
python quick_test.py
```
Checks database and CSV files

### Test SFTP Connection
```bash
python verify_ftp_upload.py
```
Verifies SFTP connection and file upload

### Force Generate CSV (for testing)
```bash
python generate_test_excel.py
```
Generates CSV files even if orders are already processed

---

## 📊 Check Project Status

### Check Processed Orders Count
```bash
python -c "from order_database import get_processed_count; print(f'Processed: {get_processed_count()}')"
```

### View Generated CSV Files
```bash
# Windows PowerShell
Get-ChildItem -Path batches -Recurse -Filter *.csv | Sort-Object LastWriteTime -Descending

# Windows CMD
dir batches\*\*.csv /s /o-d

# Linux/Mac
find batches -name "*.csv" -type f | sort -r
```

### Check Configuration
```bash
python -c "from config_manager import get_config_summary; import json; print(json.dumps(get_config_summary(), indent=2))"
```

---

## 🔧 Troubleshooting

### Reset Database (Process All Orders Again)
```bash
# Delete the database file
del bol_orders.db

# Run processing again
python order_processing.py
```

### Test Email Configuration
```bash
python -c "from order_processing import send_summary_email; send_summary_email(1, []); print('Email sent!')"
```

### Test API Connection
```bash
python -c "
from bol_api_client import BolAPIClient
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET
client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=True)
orders = client.get_all_open_orders()
print(f'✅ API Connection OK - Found {len(orders)} orders')
"
```

### Verify CSV File Structure
```bash
python verify_batch_number.py
```
Checks that batch numbers in CSV files match filenames

---

## 📁 Project Structure

```
Bol/
├── order_processing.py      # Main processing script
├── run_scheduler.py          # Scheduled processing
├── multi_account_processor.py  # Multi-account processing
├── run_callback_scheduler.py   # Status callback handler
├── config.py                # Configuration file
├── requirements.txt          # Python dependencies
├── batches/                 # Generated CSV files
│   └── YYYYMMDD/
│       ├── S-001.csv
│       ├── SL-001.csv
│       └── M-001.csv
├── label/                   # Shipping label PDFs
└── bol_orders.db            # SQLite database
```

---

## 🎯 Quick Start Workflow

1. **First Time Setup:**
   ```bash
   pip install -r requirements.txt
   # Edit config.py with your credentials
   ```

2. **Test the System:**
   ```bash
   python run_all_tests.py
   ```

3. **Run Processing Once:**
   ```bash
   python order_processing.py
   ```

4. **Check Results:**
   ```bash
   python quick_test.py
   # Check batches/ folder for CSV files
   ```

5. **Run Scheduled (Production):**
   ```bash
   python run_scheduler.py
   ```

---

## ⚙️ Configuration Options

### Test Mode vs Production Mode
In `config.py`:
```python
TEST_MODE = False  # Set to True for testing, False for production
```

### Processing Times
```python
PROCESS_TIMES = [
    "08:00",  # Morning
    "15:01",  # Afternoon
    "",       # Optional 3rd time
    "",       # Optional 4th time
]
```

### Email Notifications
```python
EMAIL_ENABLED = True  # Set to False to disable emails
EMAIL_RECIPIENTS = [
    "finance@trivium-ecommerce.com",
    "constantijn@trivium-ecommerce.com",
]
```

---

## 📝 Expected File Output

After running, you'll find:

**CSV Files:**
- `batches/YYYYMMDD/S-001.csv` - Single orders
- `batches/YYYYMMDD/SL-001.csv` - SingleLine orders
- `batches/YYYYMMDD/M-001.csv` - Multi orders

**PDF Labels:**
- `label/{labelId}.pdf` - Shipping label PDFs

**Database:**
- `bol_orders.db` - SQLite database tracking processed orders

---

## 🆘 Common Issues

### "No orders to process"
- All orders have already been processed
- Reset database: `del bol_orders.db`

### "API connection failed"
- Check `BOL_CLIENT_ID` and `BOL_CLIENT_SECRET` in `config.py`
- Verify API credentials are correct

### "SFTP upload failed"
- Check SFTP credentials in `config.py`
- Verify network connection
- Test with: `python verify_ftp_upload.py`

### "No CSV files generated"
- No orders in any category
- Check order classification logic
- Verify orders exist in Bol.com account

---

## 🎉 Success Indicators

✅ **Successful Run:**
- CSV files created in `batches/` folder
- Files uploaded to SFTP server
- Email notification sent
- No error messages in console

✅ **Files Generated:**
- At least one CSV file (S-001.csv, SL-001.csv, or M-001.csv)
- PDF labels in `label/` folder (if FBR items exist)

✅ **Database Updated:**
- Orders marked as processed
- No duplicate processing

---

## 📞 Need Help?

1. Check logs in console output
2. Run `python run_all_tests.py` to diagnose issues
3. Verify configuration in `config.py`
4. Check CSV files in `batches/` folder for data

---

**Happy Processing! 🚀**

