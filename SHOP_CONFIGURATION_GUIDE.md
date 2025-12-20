# 🏪 Shop Configuration Guide - Jean & Trivium

## ✅ Corrected Shop Configuration

Your system now has the **correct** shop names and credentials:

### Shop Accounts:

| Shop | Client ID | Usage |
|------|-----------|-------|
| **Jean** | `051dd4f6-c84e-4b98-876e-77a6727ca48a` | Single shop processing |
| **Trivium** | `f418eb2c-ca2c-4138-b5d3-fa89cb800dad` | Multi-shop processing |

---

## 🔧 What Was Fixed

### Before (INCORRECT):
- `config.py` had Jean's credentials but shop name was "Trivium" ❌
- `system_config.json` had shop names swapped ❌
- CSV files showed wrong shop names ❌

### After (CORRECT):
- ✅ `config.py` has Jean's credentials and shop name is "Jean"
- ✅ `system_config.json` has correct shop names
- ✅ Both accounts marked as `active: true`
- ✅ CSV files will show correct shop names

---

## 🚀 How to Process Orders

### Option 1: Process Jean Orders Only
```bash
python order_processing.py
```
**Result:**
- Uses Jean's credentials (`051dd4f6...`)
- Shop column in CSV = "Jean"
- Files: `S-001.csv`, `SL-001.csv`, `M-001.csv`

---

### Option 2: Process BOTH Jean AND Trivium Orders
```bash
python multi_account_processor.py
```
**Result:**
- Processes Jean orders (shop = "Jean")
- Processes Trivium orders (shop = "Trivium")
- Generates separate CSV files for each shop
- Uploads all files and labels to SFTP

**This is the RECOMMENDED approach for your setup!**

---

## 📊 Expected Output

### Single Shop (Jean only):
```
Processing Jean account...
Retrieved 2 open orders
Generated S-001.csv with 1 orders (Shop: Jean)
✅ Successfully uploaded S-001.csv
✅ Label PDFs uploaded
```

### Multiple Shops (Jean + Trivium):
```
Processing Jean account...
Generated S-001.csv with 1 orders (Shop: Jean)
✅ Uploaded Jean files

Processing Trivium account...
Generated S-002.csv with 3 orders (Shop: Trivium)
Generated SL-001.csv with 2 orders (Shop: Trivium)
✅ Uploaded Trivium files

Total processed: 6 orders across 2 shops
```

---

## 📁 CSV File Format

Each CSV file will now show the **correct shop name**:

```csv
Order ID,Shop,MP EAN,Quantity,Shipping Label,Order Time,Batch Type,Batch Number,Order Status
A000CMWRA0,Jean,8721161953173,1,287d2297-e182...,2025-12-09 10:12:30,Single,S-001,open
```

**The "Shop" column will correctly show "Jean" or "Trivium" based on which credentials were used!**

---

## 🔍 Verify Current Configuration

```bash
python -c "from config_manager import get_active_bol_accounts; print(get_active_bol_accounts())"
```

**Expected Output:**
```json
[
  {
    "name": "Jean",
    "client_id": "051dd4f6-c84e-4b98-876e-77a6727ca48a",
    "active": true
  },
  {
    "name": "Trivium",
    "client_id": "f418eb2c-ca2c-4138-b5d3-fa89cb800dad",
    "active": true
  }
]
```

---

## 🎯 Recommended Workflow

### For Daily Operations:

```bash
# Process both shops at once (RECOMMENDED)
python multi_account_processor.py
```

This will:
1. ✅ Process Jean orders with shop = "Jean"
2. ✅ Process Trivium orders with shop = "Trivium"
3. ✅ Generate separate CSV files for each
4. ✅ Upload all CSV files to SFTP
5. ✅ Upload all label PDFs to SFTP
6. ✅ Send summary email with totals

---

### For Testing Single Shop:

```bash
# Test Jean only
python order_processing.py

# Test Trivium only (need to change config.py temporarily)
# Or just use multi_account_processor.py
```

---

## 📝 Configuration Files

### `config.py` (Single Shop - Currently Jean)
```python
BOL_CLIENT_ID = "051dd4f6-c84e-4b98-876e-77a6727ca48a"  # Jean
BOL_CLIENT_SECRET = "O@A58WI8CHfiGhf8JxQT72?oO5BYF)YfhsWTxNZB2BxTlxoxoHKY!IHsFuWb3YLH"
DEFAULT_SHOP_NAME = "Jean"  # Must match credentials!
```

### `system_config.json` (Multiple Shops)
```json
{
  "bol_accounts": [
    {
      "name": "Jean",
      "client_id": "051dd4f6-c84e-4b98-876e-77a6727ca48a",
      "active": true
    },
    {
      "name": "Trivium",
      "client_id": "f418eb2c-ca2c-4138-b5d3-fa89cb800dad",
      "active": true
    }
  ]
}
```

---

## 🔄 Switching Between Shops

### To process Jean only:
No changes needed! `config.py` is already set for Jean.

### To process Trivium only:
**Option A:** Use multi-account processor (easier)
```bash
python multi_account_processor.py
```

**Option B:** Update `config.py`:
```python
BOL_CLIENT_ID = "f418eb2c-ca2c-4138-b5d3-fa89cb800dad"  # Trivium
BOL_CLIENT_SECRET = "rTj0Z!K1sZThWW!Rgu6u0t2@l62Z8jKXQDcNkx(QH0IX@m+cwiYnHpT4NNi42iVF"
DEFAULT_SHOP_NAME = "Trivium"
```

---

## ✅ Next Steps

### 1. Delete Old Incorrect Files
```powershell
# Optional: Remove the incorrectly labeled files
Remove-Item -Path "batches\20251209\S-001.csv"
Remove-Item -Path "batches\20251209\S-002.csv"

# Or just keep them for reference and let new ones be generated
```

### 2. Reset Database (Optional)
```powershell
# If you want to reprocess all orders with correct shop names
Remove-Item -Path "bol_orders.db"
```

### 3. Process Orders with Correct Shop Names
```bash
# RECOMMENDED: Process both shops at once
python multi_account_processor.py
```

This will generate:
- **Jean orders**: Files with shop column = "Jean"
- **Trivium orders**: Files with shop column = "Trivium"

---

## 📊 Expected Results

After running `python multi_account_processor.py`:

```
Jean Shop:
- S-003.csv (shop: Jean)
- Labels for Jean orders

Trivium Shop:
- S-004.csv (shop: Trivium)
- SL-001.csv (shop: Trivium) ← Multiple items!
- M-001.csv (shop: Trivium) ← Multiple EANs!
- Labels for Trivium orders

All uploaded to SFTP /Batches/ and /label/
```

---

## 🆘 Troubleshooting

### Issue: "Shop name still wrong"
**Solution:** Make sure you're using the correct command:
```bash
# Use this for both shops:
python multi_account_processor.py

# NOT this (only processes Jean):
python order_processing.py
```

### Issue: "No Trivium orders found"
**Check:**
1. Trivium credentials are correct in `system_config.json`
2. There are actually open orders in the Trivium account
3. Account is marked `active: true`

---

## ✅ Summary

**Configuration is now CORRECT:**
- ✅ Jean: `051dd4f6...` → Shop = "Jean"
- ✅ Trivium: `f418eb2c...` → Shop = "Trivium"
- ✅ Both accounts active
- ✅ CSV files will show correct shop names

**Run this command to process BOTH shops:**
```bash
python multi_account_processor.py
```

**Your system is ready!** 🚀

