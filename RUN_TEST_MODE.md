# How to Run the Project in Test Mode

## ✅ Test Mode Status
Test mode is **already enabled** in `config.py`:
```python
TEST_MODE = True  # Set to False for production
```

## 🚀 Running Options

### Option 1: Single Processing Cycle (Recommended for Testing)
Run one complete processing cycle (fetch orders, generate CSV, upload to SFTP, send email):

```bash
cd C:\Users\Lucky\Pictures\Bol
python order_processing.py
```

This will:
- Fetch open orders from Bol.com API (test environment)
- Classify orders (Single, SingleLine, Multi)
- Generate CSV files with shipping labels
- Upload to SFTP
- Send email summary

### Option 2: Comprehensive System Test
Run the full test suite to verify everything works:

```bash
cd C:\Users\Lucky\Pictures\Bol
python test_system.py
```

This tests:
- ✅ Database functionality
- ✅ CSV file structure
- ✅ Shipping labels (ZPL) in CSV
- ✅ Shop column values
- ✅ Duplicate prevention

### Option 3: Scheduler Mode (Continuous)
Run as a long-running scheduler that processes orders at configured times:

```bash
cd C:\Users\Lucky\Pictures\Bol
python order_processing.py --scheduler
```

Press `Ctrl+C` to stop the scheduler.

**Note:** Processing times are configured in `config.py`:
```python
PROCESS_TIMES = [
    "08:00",
    "15:01",
    "",      # optional slot 3
    "",      # optional slot 4
]
```

## 📋 Prerequisites

Make sure you have installed dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `requests>=2.31.0`
- `paramiko>=3.4.0`

## 🔍 Verify Test Mode

To confirm test mode is active, check the logs. You should see:
- API calls going to test environment
- Test mode indicators in log messages

## 📁 Output Files

Generated CSV files will be saved to:
```
batches/YYYYMMDD/S-001.csv
batches/YYYYMMDD/SL-001.csv
batches/YYYYMMDD/M-001.csv
```

Where:
- `YYYYMMDD` = Today's date (e.g., 20241215)
- `S-001` = Single orders, batch 001
- `SL-001` = SingleLine orders, batch 001
- `M-001` = Multi orders, batch 001

## 🐛 Troubleshooting

If shipping labels are still empty:
1. Check the logs for API errors
2. Verify your Bol.com API credentials in `config.py`
3. Ensure you have test orders available in the Bol.com test environment
4. Check that the API endpoints are correct (should use v10 endpoints)

## 📝 Notes

- Test mode uses Bol.com's test/sandbox environment
- Orders processed in test mode won't affect production
- Shipping labels are fetched from the test API
- All operations (SFTP, email) will use test credentials if configured
