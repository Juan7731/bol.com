"""
Complete Test Script - Test All System Components

This script tests all major components of the Bol.com order processing system.
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_api_connection():
    """Test Bol.com API connection"""
    print("\n" + "="*80)
    print("TEST 1: Bol.com API Connection")
    print("="*80)
    
    try:
        from bol_api_client import BolAPIClient
        from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET
        
        client = BolAPIClient(BOL_CLIENT_ID, BOL_CLIENT_SECRET, test_mode=True)
        orders = client.get_all_open_orders()
        
        print(f"✅ API Connection OK")
        print(f"   Found {len(orders)} open orders")
        return True
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        return False


def test_database():
    """Test database functionality"""
    print("\n" + "="*80)
    print("TEST 2: Database")
    print("="*80)
    
    try:
        from order_database import init_database, get_processed_count, get_processed_orders_summary
        
        init_database()
        count = get_processed_count()
        summary = get_processed_orders_summary()
        
        print(f"✅ Database OK")
        print(f"   Processed orders: {count}")
        print(f"   Summary: {summary}")
        return True
    except Exception as e:
        print(f"❌ Database Test Failed: {e}")
        return False


def test_sftp_connection():
    """Test SFTP connection"""
    print("\n" + "="*80)
    print("TEST 3: SFTP Connection")
    print("="*80)
    
    try:
        import paramiko
        from config import SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD
        
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Test listing directory
        try:
            sftp.listdir("/data/sites/web/trivium-ecommercecom/FTP/Batches")
            print(f"✅ SFTP Connection OK")
            print(f"   Host: {SFTP_HOST}:{SFTP_PORT}")
            print(f"   Username: {SFTP_USERNAME}")
            sftp.close()
            transport.close()
            return True
        except Exception as e:
            print(f"⚠️  SFTP Connected but directory access issue: {e}")
            sftp.close()
            transport.close()
            return False
            
    except Exception as e:
        print(f"❌ SFTP Connection Failed: {e}")
        return False


def test_email_config():
    """Test email configuration"""
    print("\n" + "="*80)
    print("TEST 4: Email Configuration")
    print("="*80)
    
    try:
        from config import (
            EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_USERNAME,
            EMAIL_FROM, EMAIL_RECIPIENTS
        )
        
        print(f"✅ Email Configuration OK")
        print(f"   SMTP Host: {EMAIL_SMTP_HOST}")
        print(f"   SMTP Port: {EMAIL_SMTP_PORT}")
        print(f"   From: {EMAIL_FROM}")
        print(f"   Recipients: {len(EMAIL_RECIPIENTS)}")
        print(f"   Note: Actual email sending requires valid credentials")
        return True
    except Exception as e:
        print(f"❌ Email Configuration Error: {e}")
        return False


def test_config_manager():
    """Test configuration manager"""
    print("\n" + "="*80)
    print("TEST 5: Configuration Manager")
    print("="*80)
    
    try:
        from config_manager import load_config, get_config_summary, get_active_bol_accounts
        
        config = load_config()
        summary = get_config_summary()
        active_accounts = get_active_bol_accounts()
        
        print(f"✅ Configuration Manager OK")
        print(f"   Processing times: {summary['processing_times']}")
        print(f"   Active accounts: {len(active_accounts)}")
        print(f"   Default shop: {summary['default_shop']}")
        return True
    except Exception as e:
        print(f"❌ Configuration Manager Error: {e}")
        return False


def test_callback_handler():
    """Test callback handler (without processing files)"""
    print("\n" + "="*80)
    print("TEST 6: Status Callback Handler")
    print("="*80)
    
    try:
        import time
        from status_callback_handler import fetch_callback_files_sftp
        
        # Small delay to avoid connection limit issues
        time.sleep(2)
        
        files = fetch_callback_files_sftp()
        
        print(f"✅ Callback Handler OK")
        print(f"   Found {len(files)} HTML files in callback directory")
        if files:
            print(f"   Files: {[f['filename'] for f in files]}")
        else:
            print(f"   (No callback files found - this is normal if none exist)")
        return True
    except Exception as e:
        print(f"❌ Callback Handler Error: {e}")
        return False


def test_csv_generation():
    """Test CSV file generation"""
    print("\n" + "="*80)
    print("TEST 7: CSV File Generation")
    print("="*80)
    
    try:
        import glob
        import os
        
        pattern = "batches/**/*.csv"
        files = glob.glob(pattern, recursive=True)
        
        if files:
            latest = max(files, key=os.path.getmtime)
            size = os.path.getsize(latest)
            print(f"✅ CSV Files Found")
            print(f"   Total files: {len(files)}")
            print(f"   Latest: {latest}")
            print(f"   Size: {size} bytes")
            return True
        else:
            print(f"⚠️  No CSV files found")
            print(f"   Run 'python order_processing.py' to generate files")
            return None
    except Exception as e:
        print(f"❌ CSV Generation Test Error: {e}")
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("BOL.COM ORDER PROCESSING SYSTEM - COMPLETE TEST")
    print("="*80)
    print(f"Test started at: {datetime.now()}")
    
    results = {}
    
    # Run all tests
    results['api'] = test_api_connection()
    results['database'] = test_database()
    results['sftp'] = test_sftp_connection()
    results['email'] = test_email_config()
    results['config'] = test_config_manager()
    results['callback'] = test_callback_handler()
    results['csv'] = test_csv_generation()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name.upper()}: PASSED")
        elif result is False:
            print(f"❌ {test_name.upper()}: FAILED")
        else:
            print(f"⏭️  {test_name.upper()}: SKIPPED")
    
    print("\n" + "="*80)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*80)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

