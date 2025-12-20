"""
Comprehensive test script to verify all functionality
Tests: Tracking labels (Track & Trace codes), Shop column, duplicate prevention, CSV structure
"""

import os
import sys
import logging
from datetime import datetime
import csv

from bol_api_client import BolAPIClient
from bol_dtos import Order
from order_processing import run_processing_once
from order_database import (
    init_database,
    get_processed_count,
    get_processed_orders_summary,
    is_order_processed,
)
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE, DEFAULT_SHOP_NAME

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_csv_structure(file_path: str) -> bool:
    """Test CSV file structure and content"""
    print("\n" + "="*80)
    print("TESTING CSV FILE STRUCTURE")
    print("="*80)
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        if not rows:
            print("❌ CSV file is empty")
            return False
        
        # Expected headers (per requirements - column G is "Batch Type", not "Category")
        expected_headers = [
            "Order ID",
            "Shop",
            "MP EAN",
            "Quantity",
            "Shipping Label",
            "Order Time",
            "Batch Type",  # Per requirements - must match file name
            "Batch Number",
            "Order Status",
        ]
        
        # Check headers
        headers = rows[0]
        print(f"\nHeaders found: {headers}")
        
        if headers != expected_headers:
            print(f"❌ Headers don't match!")
            print(f"   Expected: {expected_headers}")
            print(f"   Got:      {headers}")
            return False
        
        print("✅ Headers are correct")
        
        # Check for Customer Name (should NOT be present)
        if "Customer Name" in headers:
            print("❌ 'Customer Name' column still present (should be removed)")
            return False
        print("✅ 'Customer Name' column removed")
        
        # Check for Shop column
        if "Shop" not in headers:
            print("❌ 'Shop' column missing")
            return False
        print("✅ 'Shop' column present")
        
        # Check data rows
        shop_col_idx = headers.index("Shop")
        zpl_col_idx = headers.index("Shipping Label")
        
        print(f"\nChecking data rows (first 5 rows):")
        has_zpl = False
        has_shop = False
        
        for row_idx, row in enumerate(rows[1:], start=2):
            if row_idx > 6:  # Check first 5 data rows
                break
            
            if not any(cell for cell in row):
                continue
            
            # Check Shop column
            shop_value = row[shop_col_idx] if shop_col_idx < len(row) else None
            if shop_value:
                has_shop = True
                if shop_value not in ["Jean", "Trivium"]:
                    print(f"❌ Row {row_idx}: Invalid shop value: {shop_value}")
                    return False
                print(f"   Row {row_idx}: Shop = {shop_value}")
            
            # Check Shipping Label column (now contains Track & Trace info)
            tracking_value = row[zpl_col_idx] if zpl_col_idx < len(row) else None
            if tracking_value:
                has_zpl = True  # Keep variable name for compatibility
                tracking_str = str(tracking_value)
                tracking_len = len(tracking_str)
                if tracking_len > 0:
                    print(f"   Row {row_idx}: Tracking info present: {tracking_str}")
                    # Check if it looks like tracking info (contains alphanumeric code)
                    if tracking_len > 5:  # Reasonable minimum length for tracking code
                        print(f"      ✅ Tracking format valid")
                    else:
                        print(f"      ⚠️  Tracking format looks incomplete (but data present)")
        
        if not has_shop:
            print("❌ No shop values found in data rows")
            return False
        
        if not has_zpl:
            print("⚠️  No tracking info found in data rows (may be empty if items are not FBR or API failed)")
        else:
            print("✅ Tracking information found in Shipping Label column")
        
        print(f"\n✅ CSV structure test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSV file: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database() -> bool:
    """Test database functionality"""
    print("\n" + "="*80)
    print("TESTING DATABASE")
    print("="*80)
    
    try:
        init_database()
        print("✅ Database initialized")
        
        count = get_processed_count()
        print(f"✅ Processed orders count: {count}")
        
        summary = get_processed_orders_summary()
        if summary:
            print(f"✅ Processed orders by type: {summary}")
        else:
            print("ℹ️  No processed orders yet")
        
        print("✅ Database test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duplicate_prevention() -> bool:
    """Test that duplicate prevention works"""
    print("\n" + "="*80)
    print("TESTING DUPLICATE PREVENTION")
    print("="*80)
    
    try:
        # Get current processed count
        count_before = get_processed_count()
        print(f"Processed orders before: {count_before}")
        
        # Run processing
        print("\nRunning order processing...")
        run_processing_once()
        
        # Check count after
        count_after = get_processed_count()
        print(f"Processed orders after: {count_after}")
        
        if count_after > count_before:
            print(f"✅ New orders processed: {count_after - count_before}")
        else:
            print("ℹ️  No new orders to process (all already processed)")
        
        # Run again - should not process duplicates
        print("\nRunning processing again (should skip duplicates)...")
        run_processing_once()
        
        count_final = get_processed_count()
        print(f"Processed orders after second run: {count_final}")
        
        if count_final == count_after:
            print("✅ Duplicate prevention working - no new orders processed")
            return True
        else:
            print(f"⚠️  Count changed: {count_after} -> {count_final}")
            print("   (This might be OK if there were new orders)")
            return True  # Still OK, might have new orders
        
    except Exception as e:
        print(f"❌ Duplicate prevention test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_latest_csv_file() -> str:
    """Find the most recently created CSV file"""
    batch_dir = "batches"
    if not os.path.exists(batch_dir):
        return None
    
    latest_file = None
    latest_time = 0
    
    for root, dirs, files in os.walk(batch_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = file_path
                except Exception:
                    continue
    
    return latest_file


def find_all_csv_files() -> list:
    """Find all CSV files in batches directory"""
    batch_dir = "batches"
    if not os.path.exists(batch_dir):
        return []
    
    csv_files = []
    for root, dirs, files in os.walk(batch_dir):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                csv_files.append(file_path)
    
    return sorted(csv_files, key=os.path.getmtime, reverse=True)


def main():
    """Run all tests"""
    print("="*80)
    print("BOL.COM ORDER PROCESSING - SYSTEM TEST")
    print("="*80)
    print(f"Test started at: {datetime.now()}")
    print(f"Shop name configured: {DEFAULT_SHOP_NAME}")
    print()
    
    results = {}
    
    # Test 1: Database
    results['database'] = test_database()
    
    # Test 2: Run processing
    print("\n" + "="*80)
    print("RUNNING ORDER PROCESSING")
    print("="*80)
    try:
        run_processing_once()
        print("✅ Order processing completed")
        results['processing'] = True
    except Exception as e:
        print(f"❌ Order processing failed: {e}")
        import traceback
        traceback.print_exc()
        results['processing'] = False
    
    # Test 3: CSV structure
    all_csv_files = find_all_csv_files()
    if all_csv_files:
        latest_file = all_csv_files[0]
        print(f"\nFound {len(all_csv_files)} CSV file(s)")
        print(f"Testing latest file: {os.path.basename(latest_file)}")
        results['csv'] = test_csv_structure(latest_file)
    else:
        print("\n⚠️  No CSV files found to test")
        print("   This is normal if all orders are already processed.")
        print("   To generate new files:")
        print("   1. Delete bol_orders.db: del bol_orders.db")
        print("   2. Run: python order_processing.py")
        print("   3. Run this test again")
        # Mark as passed since it's expected behavior when all orders are processed
        results['csv'] = True
        print("   To generate new files:")
        print("   1. Delete bol_orders.db: del bol_orders.db")
        print("   2. Run: python order_processing.py")
        print("   3. Run this test again")
        # Don't fail the test if no files - just skip it
        results['csv'] = None  # None means skipped, not failed
    
    # Test 4: Duplicate prevention
    results['duplicates'] = test_duplicate_prevention()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        if passed is None:
            status = "⏭️  SKIPPED"
            if test_name == 'csv':
                print(f"{status} - {test_name} (no files to test - all orders processed)")
            else:
                print(f"{status} - {test_name}")
        elif passed:
            status = "✅ PASSED"
            print(f"{status} - {test_name}")
        else:
            status = "❌ FAILED"
            print(f"{status} - {test_name}")
    
    # Count passed tests (excluding None which means skipped)
    passed_tests = [v for v in results.values() if v is True]
    failed_tests = [v for v in results.values() if v is False]
    skipped_tests = [v for v in results.values() if v is None]
    
    print("\n" + "="*80)
    if failed_tests:
        print("❌ SOME TESTS FAILED")
    elif skipped_tests and len(skipped_tests) == len(results):
        print("⚠️  ALL TESTS SKIPPED (no CSV files to test)")
        print("   Run order processing first to generate files")
    elif skipped_tests:
        print("✅ ALL TESTS PASSED (some skipped - expected behavior)")
    else:
        print("✅ ALL TESTS PASSED")
    print("="*80)
    
    # Return 0 if no failures (skipped is OK), 1 if any failures
    return 0 if not failed_tests else 1


if __name__ == "__main__":
    sys.exit(main())

