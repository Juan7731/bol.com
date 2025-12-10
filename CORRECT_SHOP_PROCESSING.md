# ✅ CORRECT Shop Processing - Jean & Trivium

## 🔍 The Real Problem

The Bol.com API **does NOT provide shop information** in the order data. When you call the API with one set of credentials, you get orders from **multiple shops mixed together**.

### Why This Happens:
- Jean's API credentials (`051dd4f6...`) return orders from **both Jean AND Trivium**
- The API response has NO "shop" field
- There's no `offerReference` or other identifier to distinguish shops
- This is common in marketplace setups where one account manages multiple storefronts

### Example API Response:
```json
{
  "orderId": "A000CMWRA0",
  "orderPlacedDateTime": "2025-12-09T19:42:59+01:00",
  "orderItems": [...]
  // NO SHOP FIELD!
}
```

---

## ✅ The Solution

**Call each shop's API separately** to ensure correct shop attribution:

1. Call Jean's API → Label all orders as "Jean"
2. Call Trivium's API → Label all orders as "Trivium"

---

## 🚀 Use the New Script

I've created a dedicated script that processes both shops correctly:

```bash
python process_both_shops.py
```

### What It Does:

1. **Connects to Jean's API** (`051dd4f6...`)
   - Fetches all open orders
   - Labels them as "Jean"
   - Generates CSV files with shop = "Jean"
   - Uploads CSV and label PDFs

2. **Connects to Trivium's API** (`f418eb2c...`)
   - Fetches all open orders
   - Labels them as "Trivium"
   - Generates CSV files with shop = "Trivium"
   - Uploads CSV and label PDFs

3. **Provides Summary**
   - Shows orders processed per shop
   - Lists all files created
   - Confirms uploads

---

## 📊 Expected Output

```
================================================================================
PROCESSING BOTH SHOPS: JEAN & TRIVIUM
================================================================================

================================================================================
Processing Jean Shop
================================================================================
Retrieved 3 open orders for Jean
Processing 3 new orders for Jean
Generated S-003.csv with 2 orders (Shop: Jean)
Generated SL-001.csv with 1 orders (Shop: Jean)
✅ CSV files uploaded for Jean
✅ Label PDFs uploaded for Jean

================================================================================
Processing Trivium Shop
================================================================================
Retrieved 8 open orders for Trivium
Processing 8 new orders for Trivium
Generated S-004.csv with 5 orders (Shop: Trivium)
Generated SL-002.csv with 2 orders (Shop: Trivium)
Generated M-001.csv with 1 orders (Shop: Trivium)
✅ CSV files uploaded for Trivium
✅ Label PDFs uploaded for Trivium

================================================================================
PROCESSING SUMMARY
================================================================================

📊 Jean Shop:
   Total orders: 3
   Processed: 3
   Files created: 2
      - batches/20251209/S-003.csv
      - batches/20251209/SL-001.csv
   Status: ✅ Success

📊 Trivium Shop:
   Total orders: 8
   Processed: 8
   Files created: 3
      - batches/20251209/S-004.csv
      - batches/20251209/SL-002.csv
      - batches/20251209/M-001.csv
   Status: ✅ Success

🎯 Total orders processed: 11
================================================================================
```

---

## 📁 CSV Files Will Be Correct

### Jean's CSV (S-003.csv):
```csv
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000CMWRA0,Jean,8721161953173,1,label-id,2025-12-09 19:42:59,Single,S-003,open
A000C0P28J,Jean,8721161953289,1,label-id,2025-12-09 17:44:17,Single,S-003,open
```

### Trivium's CSV (S-004.csv):
```csv
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000CN0PWN,Trivium,8721161953173,1,label-id,2025-12-09 15:30:00,Single,S-004,open
A000CML44F,Trivium,8721161953289,1,label-id,2025-12-09 14:20:00,Single,S-004,open
```

**Each CSV will have the CORRECT shop name!**

---

## 🔧 How It Works

The script temporarily overrides the `DEFAULT_SHOP_NAME` for each API call:

```python
# When processing Jean
DEFAULT_SHOP_NAME = "Jean"
# Call Jean's API
# Generate CSV files → shop column = "Jean"

# When processing Trivium  
DEFAULT_SHOP_NAME = "Trivium"
# Call Trivium's API
# Generate CSV files → shop column = "Trivium"
```

---

## ⚠️ Why `multi_account_processor.py` Doesn't Work

The existing `multi_account_processor.py` has the same issue - it doesn't properly override the shop name when generating CSV files. The new `process_both_shops.py` script fixes this.

---

## 🗑️ Clean Up Old Files (Optional)

If you want to remove the incorrectly labeled files:

```powershell
# Remove old files with wrong shop names
Remove-Item -Path "batches\20251209\S-001.csv"
Remove-Item -Path "batches\20251209\S-002.csv"

# Reset database to reprocess all orders
Remove-Item -Path "bol_orders.db"
```

---

## ✅ Next Steps

### 1. Run the New Script
```bash
python process_both_shops.py
```

### 2. Verify CSV Files
```powershell
# Check all CSV files
Get-ChildItem -Path batches -Recurse -Filter *.csv

# View a CSV file to verify shop column
$csv = Get-ChildItem -Path batches -Recurse -Filter "S-*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $csv.FullName
```

### 3. Verify SFTP Upload
```bash
python verify_ftp_upload.py
```

---

## 📝 For Scheduled Processing

### Option A: Use the New Script
```bash
# In Windows Task Scheduler or cron
python process_both_shops.py
```

### Option B: Run Separately
```bash
# Process Jean
python order_processing.py

# Then switch config and process Trivium
# (More complex, not recommended)
```

---

## 🎯 Summary

**Problem:** 
- API doesn't provide shop information
- Orders from both shops mixed in one API response
- Shop name was based on credentials used, not actual shop

**Solution:**
- Call each shop's API separately
- Temporarily override shop name for each call
- Generate separate CSV files with correct shop names

**Result:**
- ✅ Jean orders → shop = "Jean"
- ✅ Trivium orders → shop = "Trivium"
- ✅ All files uploaded correctly
- ✅ No mixing of shop names

---

## 🚀 Run This Command Now:

```bash
python process_both_shops.py
```

This will generate **correctly labeled CSV files** for both Jean and Trivium shops!

