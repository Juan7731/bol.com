"""
Quick test to verify CSV files and system status
"""

import os
import glob
import csv
from order_database import get_processed_count, get_processed_orders_summary

def find_csv_files():
    """Find all CSV files in batches directory"""
    pattern = "batches/**/*.csv"
    files = glob.glob(pattern, recursive=True)
    return sorted(files, key=os.path.getmtime, reverse=True)

def test_csv_file(file_path):
    """Test a single CSV file"""
    print(f"\n{'='*80}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"Path: {file_path}")
    print('='*80)
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if not rows:
            print("❌ File is empty")
            return False
        
        # Get headers
        headers = rows[0]
        print(f"\n📋 Headers ({len(headers)} columns):")
        for i, header in enumerate(headers, 1):
            print(f"   {chr(64+i)}: {header}")
        
        # Check for required columns (per requirements)
        required = ["Order ID", "Shop", "MP EAN", "Quantity", "Shipping Label", 
                   "Order Time", "Batch Type", "Batch Number", "Order Status"]
        
        missing = [h for h in required if h not in headers]
        if missing:
            print(f"\n❌ Missing columns: {missing}")
        else:
            print(f"\n✅ All required columns present")
        
        # Check for removed column
        if "Customer Name" in headers:
            print(f"❌ 'Customer Name' column still present (should be removed)")
        else:
            print(f"✅ 'Customer Name' column removed")
        
        # Check Shop column
        if "Shop" in headers:
            shop_idx = headers.index("Shop")
            print(f"\n🏪 Shop Column (Column {chr(65+shop_idx)}):")
            
            # Check first 5 data rows
            shop_values = set()
            for row_idx, row in enumerate(rows[1:], start=2):
                if row_idx > 6:  # First 5 rows
                    break
                if any(cell for cell in row):
                    shop_val = row[shop_idx] if shop_idx < len(row) else None
                    if shop_val:
                        shop_values.add(shop_val)
                        print(f"   Row {row_idx}: {shop_val}")
            
            if shop_values:
                print(f"✅ Shop values found: {sorted(shop_values)}")
            else:
                print(f"⚠️  No shop values found in first rows")
        else:
            print(f"❌ 'Shop' column missing")
        
        # Check ZPL labels
        if "Shipping Label" in headers:
            zpl_idx = headers.index("Shipping Label")
            print(f"\n📦 Shipping Label Column (Column {chr(65+zpl_idx)}):")
            
            zpl_count = 0
            empty_count = 0
            for row_idx, row in enumerate(rows[1:], start=2):
                if row_idx > 10:  # Check first 10 rows
                    break
                if any(cell for cell in row):
                    zpl_val = row[zpl_idx] if zpl_idx < len(row) else None
                    if zpl_val:
                        zpl_count += 1
                        zpl_str = str(zpl_val)
                        if len(zpl_str) > 50:
                            print(f"   Row {row_idx}: ZPL present ({len(zpl_str)} chars) - {zpl_str[:50]}...")
                        else:
                            print(f"   Row {row_idx}: ZPL present ({len(zpl_str)} chars)")
                    else:
                        empty_count += 1
            
            if zpl_count > 0:
                print(f"✅ ZPL labels found: {zpl_count} rows with labels")
            else:
                print(f"⚠️  No ZPL labels found in first rows ({empty_count} empty)")
        else:
            print(f"❌ 'Shipping Label' column missing")
        
        # Count total rows
        total_rows = len([row for row in rows[1:] if any(cell for cell in row)])
        print(f"\n📊 Total data rows: {total_rows}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("QUICK SYSTEM TEST")
    print("="*80)
    
    # Check database
    print("\n📊 Database Status:")
    count = get_processed_count()
    print(f"   Processed orders: {count}")
    summary = get_processed_orders_summary()
    if summary:
        print(f"   By type: {summary}")
    
    # Find CSV files
    print("\n📁 Searching for CSV files...")
    csv_files = find_csv_files()
    
    if not csv_files:
        print("   ⚠️  No CSV files found in batches/ directory")
        print("\n   To generate new files:")
        print("   1. Reset database: Delete bol_orders.db")
        print("   2. Run: python order_processing.py")
        return
    
    print(f"   Found {len(csv_files)} CSV file(s)")
    
    # Test latest file
    if csv_files:
        latest = csv_files[0]
        print(f"\n   Testing latest file: {os.path.basename(latest)}")
        test_csv_file(latest)
    
    # Test all files if multiple
    if len(csv_files) > 1:
        print(f"\n\n{'='*80}")
        print(f"Testing all {len(csv_files)} files...")
        print('='*80)
        for file_path in csv_files[:5]:  # Test first 5
            test_csv_file(file_path)
    
    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80)
    print("\nTo test with new orders:")
    print("  1. Delete bol_orders.db to reset processed orders")
    print("  2. Run: python order_processing.py")
    print("  3. Run this test again: python quick_test.py")

if __name__ == "__main__":
    main()

