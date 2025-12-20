# Testing Commands for Updated Shipping Label Code

## Quick Test Guide

### Step 1: Check Available Order Items and FBR Status
First, see what order items you have and which ones are FBR:

```bash
cd C:\Users\Lucky\Pictures\Bol
python get_order_item_ids.py
```

**What this shows:**
- All open orders
- Order item IDs (use these, NOT order IDs)
- Which items are FBR (can get shipping labels)
- Which items are not FBR (cannot get shipping labels)

**Example output:**
```
orderItemId: 3833872755
Fulfilment: FBR ✅ FBR
✅ Can get shipping label for this item
```

---

### Step 2: Test Shipping Label Fetch for a Specific Item
Test fetching a shipping label for a specific order item ID:

```bash
python test_shipping_label.py <orderItemId>
```

**Replace `<orderItemId>` with an actual order item ID from Step 1**

**Example:**
```bash
python test_shipping_label.py 3833872755
```

**What this shows:**
- Step-by-step process of fetching delivery options
- Creating shipping label
- Getting the actual label data
- Any errors that occur

---

### Step 3: Run Full Order Processing
Run the complete processing cycle (fetch orders, generate CSV, upload, email):

```bash
python order_processing.py
```

**What this does:**
- Fetches all open orders
- Checks FBR status for each item
- Attempts to fetch shipping labels for FBR items
- Generates CSV files (S-001.csv, SL-001.csv, M-001.csv)
- Uploads to SFTP
- Sends email summary

**What to look for in logs:**
- ✅ "Successfully fetched ZPL label" - Label was retrieved
- ⚠️ "Fulfilment method unknown" - Checking if FBR
- ⚠️ "is not FBR" - Skipping non-FBR items
- ❌ "Failed to fetch ZPL label" - Error occurred

---

### Step 4: Check Generated CSV Files
After running processing, check the generated CSV files:

```bash
# Files are in: batches/YYYYMMDD/
# Example: batches/20251205/S-001.csv

# On Windows PowerShell:
Get-ChildItem -Path batches -Recurse -Filter *.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

**Or manually navigate to:**
```
C:\Users\Lucky\Pictures\Bol\batches\YYYYMMDD\
```

**Check the "Shipping Label" column (Column E):**
- Should contain ZPL label data (starts with `^XA`)
- If empty, check the logs to see why

---

### Step 5: Run Comprehensive System Test
Run the full test suite to verify everything:

```bash
python test_system.py
```

**What this tests:**
- Database functionality
- CSV file structure
- Shipping labels in CSV
- Shop column values
- Duplicate prevention

---

## Troubleshooting Commands

### Check API Response Structure
See the actual API response structure for order items:

```bash
python check_fulfilment_structure.py
```

This helps debug if fulfilment method is being extracted correctly.

---

### Check Database Status
See which orders have been processed:

```bash
python -c "from order_database import init_database, get_processed_count, get_processed_orders_summary; init_database(); print(f'Processed: {get_processed_count()}'); print(get_processed_orders_summary())"
```

---

### Reset Database (if needed)
To process orders again (for testing):

```bash
# Delete the database file
del bol_orders.db

# Then run processing again
python order_processing.py
```

---

## Expected Behavior

### For FBR Items:
1. ✅ Checks delivery options → Success
2. ✅ Creates shipping label → Success
3. ✅ Gets label data → ZPL data retrieved
4. ✅ CSV file has label in "Shipping Label" column

### For Non-FBR Items:
1. ⚠️ Checks delivery options → 404 Error
2. ⚠️ Logs "is not FBR, skipping label fetch"
3. ✅ CSV file has empty "Shipping Label" column (expected)

### For Unknown Fulfilment:
1. ⚠️ Checks delivery options first
2. If delivery options available → Treats as FBR → Fetches label
3. If delivery options fail → Treats as non-FBR → Skips label

---

## Quick Test Sequence

```bash
# 1. Check what you have
python get_order_item_ids.py

# 2. Test with a specific item (if you have FBR items)
python test_shipping_label.py <orderItemId>

# 3. Run full processing
python order_processing.py

# 4. Check results
python test_system.py
```

---

## Notes

- **Test Mode**: Make sure `TEST_MODE = True` in `config.py`
- **Order Item ID vs Order ID**: Always use `orderItemId` (numeric), NOT `orderId` (starts with "A000")
- **FBR Items Only**: Shipping labels only work for FBR (Fulfilled By Retailer) items
- **Logs**: Check the console output for detailed information about what's happening




