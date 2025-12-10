# 🚀 RUN THIS NOW - Process All Open Orders

## ✅ What This Script Does

The `process_both_shops.py` script will:

1. **Fetch ALL open orders** from Jean's API
2. **Fetch ALL open orders** from Trivium's API
3. **Generate shipping labels** (PDFs saved to `label/` folder)
4. **Generate CSV files** with correct shop names (saved to `batches/YYYYMMDD/`)
5. **Upload CSV files** to SFTP server `/Batches/` directory
6. **Upload label PDFs** to SFTP server `/label/` directory
7. **Show detailed summary** of what was processed

---

## 🚀 Run This Command:

```powershell
python process_both_shops.py
```

---

## 📊 What You'll See:

```
================================================================================
PROCESSING BOTH SHOPS: JEAN & TRIVIUM
Processing ALL OPEN ORDERS
================================================================================

================================================================================
Processing Jean Shop
================================================================================
Retrieved 3 open orders for Jean
Processing ALL 3 open orders for Jean
Order breakdown for Jean:
  - Single: 3 orders
  - SingleLine: 0 orders
  - Multi: 0 orders
📋 Processing order item 3836994284...
✅ Created shipping label: 287d2297-e182-4bdf-b106-744529873641
✅ Saved PDF label: 287d2297-e182-4bdf-b106-744529873641.pdf
Generated 1 CSV files for Jean:
  - S-003.csv
Uploading 1 CSV files for Jean...
✅ Successfully uploaded S-003.csv (450 bytes)
✅ CSV files uploaded to SFTP /Batches/ for Jean
Uploading label PDFs for Jean...
📤 Uploading 287d2297-e182-4bdf-b106-744529873641.pdf...
✅ Successfully uploaded 287d2297-e182-4bdf-b106-744529873641.pdf (1901 bytes)
✅ Label PDFs uploaded to SFTP /label/ for Jean

================================================================================
Processing Trivium Shop
================================================================================
Retrieved 8 open orders for Trivium
Processing ALL 8 open orders for Trivium
Order breakdown for Trivium:
  - Single: 5 orders
  - SingleLine: 2 orders
  - Multi: 1 orders
📋 Processing order items...
✅ Created shipping labels...
✅ Saved PDF labels...
Generated 3 CSV files for Trivium:
  - S-004.csv
  - SL-001.csv
  - M-001.csv
Uploading 3 CSV files for Trivium...
✅ Successfully uploaded S-004.csv (890 bytes)
✅ Successfully uploaded SL-001.csv (340 bytes)
✅ Successfully uploaded M-001.csv (230 bytes)
✅ CSV files uploaded to SFTP /Batches/ for Trivium
Uploading label PDFs for Trivium...
📤 Uploading multiple PDFs...
✅ Label PDFs uploaded to SFTP /label/ for Trivium

================================================================================
PROCESSING SUMMARY
================================================================================

📊 Jean Shop:
   Total orders: 3
   Processed: 3
   Files created: 1
      - batches/20251209/S-003.csv
   Status: ✅ Success

📊 Trivium Shop:
   Total orders: 8
   Processed: 8
   Files created: 3
      - batches/20251209/S-004.csv
      - batches/20251209/SL-001.csv
      - batches/20251209/M-001.csv
   Status: ✅ Success

🎯 Total orders processed: 11
================================================================================
```

---

## 📁 Where Files Are Saved

### Local Files:

**CSV Files:**
```
batches/
└── 20251209/
    ├── S-003.csv    (Jean - Single orders)
    ├── S-004.csv    (Trivium - Single orders)
    ├── SL-001.csv   (Trivium - SingleLine orders)
    └── M-001.csv    (Trivium - Multi orders)
```

**Label PDFs:**
```
label/
├── 287d2297-e182-4bdf-b106-744529873641.pdf  (Jean order)
├── 9824c116-655a-41b6-ba23-6bf9050a8e7b.pdf  (Jean order)
├── abc12345-6789-0123-4567-890abcdef123.pdf  (Trivium order)
└── ... (more label PDFs)
```

### SFTP Server:

**CSV Files:**
- `/data/sites/web/trivium-ecommercecom/FTP/Batches/S-003.csv`
- `/data/sites/web/trivium-ecommercecom/FTP/Batches/S-004.csv`
- `/data/sites/web/trivium-ecommercecom/FTP/Batches/SL-001.csv`
- `/data/sites/web/trivium-ecommercecom/FTP/Batches/M-001.csv`

**Label PDFs:**
- `/data/sites/web/trivium-ecommercecom/FTP/label/287d2297-...pdf`
- `/data/sites/web/trivium-ecommercecom/FTP/label/9824c116-...pdf`
- `/data/sites/web/trivium-ecommercecom/FTP/label/abc12345-...pdf`

---

## 📊 CSV File Format

### Jean's Orders (S-003.csv):
```csv
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000CN1J16,Jean,8721161953173,1,287d2297-e182-4bdf-b106-744529873641,2025-12-09 20:51:44,Single,S-003,open
A000CMWRA0,Jean,8721161953289,1,9824c116-655a-41b6-ba23-6bf9050a8e7b,2025-12-09 19:42:59,Single,S-003,open
A000C0P28J,Jean,8721161953173,1,abc12345-6789-0123-4567-890abcdef123,2025-12-09 17:44:17,Single,S-003,open
```

### Trivium's Orders (S-004.csv):
```csv
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000CN0PWN,Trivium,8721161953173,1,def45678-9012-3456-7890-abcdef123456,2025-12-09 15:30:00,Single,S-004,open
A000CML44F,Trivium,8721161953289,1,ghi78901-2345-6789-0123-456789abcdef,2025-12-09 14:20:00,Single,S-004,open
```

**✅ Shop column is CORRECT for each order!**

---

## ✅ Verification Commands

### Check Local CSV Files:
```powershell
# List all CSV files
Get-ChildItem -Path batches -Recurse -Filter *.csv

# View latest CSV content
$csv = Get-ChildItem -Path batches -Recurse -Filter *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $csv.FullName
```

### Check Local Label PDFs:
```powershell
# List all PDF labels
Get-ChildItem -Path label -Filter *.pdf

# Count PDFs
(Get-ChildItem -Path label -Filter *.pdf).Count
```

### Check SFTP Server:
```powershell
python verify_ftp_upload.py
```

---

## 🎯 Key Features

✅ **Processes ALL open orders** (not just new ones)  
✅ **Correct shop names** (Jean vs Trivium)  
✅ **Downloads shipping labels** (saved as PDFs)  
✅ **Generates CSV files** (with all order details)  
✅ **Uploads CSV to SFTP** `/Batches/` directory  
✅ **Uploads labels to SFTP** `/label/` directory  
✅ **Detailed logging** (see exactly what's happening)  
✅ **Error handling** (continues even if one shop fails)  

---

## ⚠️ Important Notes

1. **All open orders will be processed** - even if they were processed before
2. **Duplicate prevention is disabled** - this ensures all open orders are included
3. **Files are uploaded immediately** after generation
4. **Labels are uploaded separately** from CSV files
5. **Both shops processed in sequence** - Jean first, then Trivium

---

## 🚀 READY TO RUN?

```powershell
python process_both_shops.py
```

**This will:**
- ✅ Collect ALL open orders from both shops
- ✅ Save labels to `label/` folder
- ✅ Save CSV files to `batches/` folder
- ✅ Upload everything to SFTP server
- ✅ Show you a complete summary

---

**Run it now!** 🎉

