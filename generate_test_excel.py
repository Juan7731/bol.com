"""
Test script to generate Excel files for verification
This will process orders even if they're already in the database (for testing)
"""

import os
import sys
import logging
from order_processing import (
    classify_orders,
    generate_excel_batches,
    upload_files_sftp,
    send_summary_email,
)

# Import label uploader
try:
    from label_uploader import upload_all_labels
    LABEL_UPLOADER_AVAILABLE = True
except ImportError:
    LABEL_UPLOADER_AVAILABLE = False
from bol_api_client import BolAPIClient
from bol_dtos import Order
from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE
from order_database import init_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_excel_files_force():
    """
    Force generate Excel files for all open orders
    (ignores database - for testing only)
    """
    print("="*80)
    print("FORCE GENERATING EXCEL FILES (TEST MODE)")
    print("="*80)
    print("\nThis will generate Excel files for ALL open orders,")
    print("even if they're already processed (for testing purposes).\n")
    
    # Initialize database
    init_database()
    
    # Connect to Bol.com API
    print("1. Connecting to Bol.com API...")
    client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=TEST_MODE)
    
    # Fetch all open orders
    print("2. Fetching all open orders...")
    raw_orders = client.get_all_open_orders()
    orders = [Order.from_dict(o) for o in raw_orders]
    
    if not orders:
        print("❌ No open orders found from Bol.com")
        return False
    
    print(f"   Found {len(orders)} open orders")
    
    # Classify orders
    print("3. Classifying orders...")
    grouped = classify_orders(orders)
    
    for cat, order_list in grouped.items():
        if order_list:
            print(f"   {cat}: {len(order_list)} orders")
    
    # Generate Excel files
    print("4. Generating Excel files...")
    files_created, total_orders = generate_excel_batches(grouped, client)
    
    if not files_created:
        print("❌ No Excel files were generated")
        return False
    
    print(f"\n✅ Generated {len(files_created)} Excel file(s):")
    for file_path in files_created:
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"   - {os.path.basename(file_path)} ({file_size:.2f} KB)")
        print(f"     Path: {file_path}")
    
    # Upload CSV files to SFTP
    print("\n5. Uploading CSV files to SFTP...")
    try:
        upload_files_sftp(files_created)
        print("   ✅ CSV files uploaded successfully")
    except Exception as e:
        print(f"   ⚠️  CSV upload failed: {e}")
    
    # Upload label PDFs to SFTP
    print("\n6. Uploading label PDFs to SFTP...")
    if LABEL_UPLOADER_AVAILABLE:
        try:
            upload_all_labels()
            print("   ✅ Label PDFs uploaded successfully")
        except Exception as e:
            print(f"   ⚠️  Label upload failed: {e}")
    else:
        print("   ⚠️  Label uploader not available")
    
    # Send email
    print("\n7. Sending email notification...")
    try:
        send_summary_email(total_orders, files_created)
        print("   ✅ Email sent")
    except Exception as e:
        print(f"   ⚠️  Email failed: {e}")
    
    print("\n" + "="*80)
    print("✅ EXCEL FILES GENERATED SUCCESSFULLY")
    print("="*80)
    print(f"\nTotal orders processed: {total_orders}")
    print(f"Files created: {len(files_created)}")
    print("\nYou can now:")
    print("1. Check the Excel files in the batches/ folder")
    print("2. Verify column structure (Batch Type, Shop, ZPL labels)")
    print("3. Check SFTP server for uploaded files")
    
    return True


if __name__ == "__main__":
    try:
        success = generate_excel_files_force()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

