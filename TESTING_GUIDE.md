# Testing Guide for Updated Shipping Label Code

## Quick Test Commands

### 1. Check Order Items and FBR Status
First, see what order items you have and their FBR status:

```bash
cd C:\Users\Lucky\Pictures\Bol
python get_order_item_ids.py
```

This will show:
- All order items from open orders
- Their orderItemIds (use these, NOT order IDs!)
- Fulfilment method (FBR or not)
- Which items can get shipping labels

### 2. Test Shipping Label Fetch for Specific Item
Test fetching a shipping label for a specific order item:

```bash
python test_shipping_label.py <orderItemId>
```

**Example:**
```bash
python test_shipping_label.py 3833872755
```

**Important:** Use `orderItemId` (numeric like `3833872755`), NOT `orderId` (like `A000CHRC72`)

### 3. Run Full Order Processing
Process all orders and generate CSV files:

```bash
python order_processing.py
```

This will:
- Fetch all open orders
- Check FBR status for each item
- Attempt to fetch shipping labels for FBR items
- Generate CSV files with shipping labels
- Upload to SFTP
- Send email summary

### 4. Check API Response Structure (Debug)
If you need to see the raw API response structure:

```bash
python check_fulfilment_structure.py
```

This shows the actual API response format to help debug issues.

## Step-by-Step Testing Process

### Step 1: Verify You Have Orders
```bash
python get_order_item_ids.py
```

**Expected Output:**
- List of orders with their items
- Fulfilment status for each item
- Summary showing FBR vs non-FBR items

**If you see "FBR items (can get labels): 0":**
- All your current orders are non-FBR
- You need FBR orders to test shipping labels
- The code will skip non-FBR items automatically

### Step 2: Test with a Specific Order Item
If you have FBR items, test one:

```bash
python test_shipping_label.py <orderItemId>
```

**What to Look For:**
- ✅ "Found X delivery options" - Item is FBR
- ✅ "Successfully fetched ZPL label" - Label retrieved
- ❌ "404 Not Found" - Item is not FBR or invalid ID
- ❌ "No delivery options" - Item cannot get labels

### Step 3: Run Full Processing
```bash
python order_processing.py
```

**Check the Logs For:**
- "Processing order item..." - Shows each item being processed
- "Fulfilment: FBR" or "Fulfilment: Unknown" - FBR status
- "✅ Successfully fetched ZPL label" - Labels retrieved
- "⚠️ Order item is not FBR" - Non-FBR items skipped
- "❌ Failed to fetch ZPL label" - Errors

### Step 4: Verify CSV Files
Check the generated CSV files:

```bash
# Files are in: batches/YYYYMMDD/
# Example: batches/20251205/S-001.csv
```

Open the CSV file and check:
- Column E "Shipping Label" should contain ZPL data (not empty)
- ZPL data should start with `^XA` or contain "ZPL"
- Non-FBR items will have empty shipping labels (expected)

## Troubleshooting

### Problem: All items show "Fulfilment: Unknown"
**Solution:** The code will automatically check delivery options to determine FBR status. This is normal.

### Problem: "404 Not Found" errors
**Possible Causes:**
1. Using Order ID instead of Order Item ID
2. Item is not FBR (only FBR items can get labels)
3. Order item doesn't exist

**Solution:**
- Use `get_order_item_ids.py` to find valid orderItemIds
- Make sure you're using numeric orderItemId, not alphanumeric orderId

### Problem: Shipping Label column is still empty
**Check:**
1. Are the items FBR? (Run `get_order_item_ids.py`)
2. Check logs for error messages
3. Verify API credentials in `config.py`
4. Check if TEST_MODE is correct

### Problem: "No new unprocessed orders"
**Solution:**
- Orders are already processed (stored in database)
- Delete `bol_orders.db` to reset: `del bol_orders.db`
- Or wait for new orders

## Test Scenarios

### Scenario 1: Test with FBR Item
```bash
# 1. Find FBR items
python get_order_item_ids.py

# 2. Test with FBR orderItemId
python test_shipping_label.py 3833872755

# 3. Run full processing
python order_processing.py
```

### Scenario 2: Test with Non-FBR Item
```bash
# The code will automatically skip non-FBR items
python order_processing.py

# Check logs - should see:
# "⚠️ Order item is not FBR - skipping label fetch"
```

### Scenario 3: Test with Unknown Fulfilment
```bash
# Code will check delivery options automatically
python order_processing.py

# Check logs - should see:
# "⚠️ Fulfilment method unknown - checking if FBR by attempting to get delivery options"
```

## Expected Behavior

### For FBR Items:
1. ✅ Delivery options retrieved
2. ✅ Shipping label created
3. ✅ ZPL label data fetched
4. ✅ CSV file contains ZPL data in "Shipping Label" column

### For Non-FBR Items:
1. ⚠️ Delivery options return 404
2. ⚠️ Label fetch skipped
3. ⚠️ CSV file has empty "Shipping Label" column (expected)

### For Unknown Fulfilment:
1. 🔍 Code checks delivery options first
2. ✅ If delivery options available → proceed with label fetch
3. ⚠️ If delivery options fail → skip label fetch

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python get_order_item_ids.py` | List all order items and FBR status |
| `python test_shipping_label.py <id>` | Test label fetch for one item |
| `python order_processing.py` | Run full processing |
| `python check_fulfilment_structure.py` | Debug API response structure |
| `python test_system.py` | Run comprehensive system tests |

## Notes

- **TEST_MODE**: Check `config.py` - should be `True` for testing
- **Order IDs vs Order Item IDs**: Always use `orderItemId` (numeric), not `orderId` (alphanumeric)
- **FBR Only**: Shipping labels only work for FBR (Fulfilled By Retailer) items
- **Logs**: All important information is logged - check console output for details
