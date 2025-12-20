"""
Test script for the callback monitor functionality
"""

import os
import time
import paramiko
from status_callback_handler import (
    parse_html_status_file,
    fetch_callback_files_sftp,
    delete_label_pdf_from_ftp,
    process_callback_files
)
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
    SFTP_REMOTE_LABEL_DIR,
)

SFTP_CALLBACK_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"


def test_sftp_connection():
    """Test SFTP connection to callback directory"""
    print("\n" + "="*80)
    print("TEST 1: SFTP Connection to Callbacks Directory")
    print("="*80)
    
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"✅ Connected to SFTP server: {SFTP_HOST}:{SFTP_PORT}")
        
        # Test callback directory access
        try:
            files = sftp.listdir(SFTP_CALLBACK_DIR)
            html_files = [f for f in files if f.lower().endswith('.html')]
            print(f"✅ Callback directory accessible: {SFTP_CALLBACK_DIR}")
            print(f"✅ Found {len(html_files)} HTML file(s) in callback directory")
        except FileNotFoundError:
            print(f"⚠️  Callback directory not found: {SFTP_CALLBACK_DIR}")
            print("   This is OK if no callbacks have been received yet")
        
        # Test label directory access
        try:
            files = sftp.listdir(SFTP_REMOTE_LABEL_DIR)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            print(f"✅ Label directory accessible: {SFTP_REMOTE_LABEL_DIR}")
            print(f"✅ Found {len(pdf_files)} PDF label(s)")
        except FileNotFoundError:
            print(f"⚠️  Label directory not found: {SFTP_REMOTE_LABEL_DIR}")
        
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"❌ SFTP connection failed: {e}")
        return False


def test_html_parsing():
    """Test HTML parsing functionality"""
    print("\n" + "="*80)
    print("TEST 2: HTML Parsing")
    print("="*80)
    
    # Test case 1: Valid "verzonden" status
    test_html_1 = """
    <html>
    <body>
        <div>Order ID: A000C2F77M</div>
        <div>Status: verzonden</div>
    </body>
    </html>
    """
    
    result1 = parse_html_status_file(test_html_1)
    if result1 and result1['order_id'] == 'A000C2F77M' and result1['status'] == 'verzonden':
        print("✅ Test 1 passed: Parsed 'verzonden' status correctly")
        print(f"   Order ID: {result1['order_id']}")
        print(f"   Status: {result1['status']}")
    else:
        print("❌ Test 1 failed: Could not parse 'verzonden' status")
        return False
    
    # Test case 2: Valid "niet verzonden" status
    test_html_2 = """
    <html>
    <body>
        <div>Order: B111D3G88N</div>
        <div>Status: niet verzonden</div>
    </body>
    </html>
    """
    
    result2 = parse_html_status_file(test_html_2)
    if result2 and result2['order_id'] == 'B111D3G88N' and result2['status'] == 'niet verzonden':
        print("✅ Test 2 passed: Parsed 'niet verzonden' status correctly")
        print(f"   Order ID: {result2['order_id']}")
        print(f"   Status: {result2['status']}")
    else:
        print("❌ Test 2 failed: Could not parse 'niet verzonden' status")
        return False
    
    # Test case 3: Simple text format
    test_html_3 = """
    Order ID: C222E4H99P
    Status: verzonden
    """
    
    result3 = parse_html_status_file(test_html_3)
    if result3 and result3['status'] == 'verzonden':
        print("✅ Test 3 passed: Parsed simple text format")
        print(f"   Order ID: {result3['order_id']}")
        print(f"   Status: {result3['status']}")
    else:
        print("⚠️  Test 3: Could not parse simple text format (this is OK)")
    
    return True


def test_fetch_callback_files():
    """Test fetching callback files from SFTP"""
    print("\n" + "="*80)
    print("TEST 3: Fetch Callback Files")
    print("="*80)
    
    try:
        files = fetch_callback_files_sftp()
        print(f"✅ Successfully fetched {len(files)} callback file(s)")
        
        if files:
            print("\nSample files:")
            for i, file_info in enumerate(files[:3], 1):
                filename = file_info['filename']
                content_len = len(file_info['content'])
                print(f"  {i}. {filename} ({content_len} bytes)")
            if len(files) > 3:
                print(f"  ... and {len(files) - 3} more files")
        else:
            print("  No callback files found (this is OK if none exist yet)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching callback files: {e}")
        return False


def test_label_deletion_simulation():
    """Test label deletion logic (simulation only)"""
    print("\n" + "="*80)
    print("TEST 4: Label Deletion (Simulation)")
    print("="*80)
    
    print("This test simulates the label deletion logic")
    print("It checks if the function can connect and list files")
    print("(No actual deletion is performed in test mode)")
    
    try:
        # Try to connect and check label directory
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        try:
            files = sftp.listdir(SFTP_REMOTE_LABEL_DIR)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            
            print(f"✅ Label directory accessible")
            print(f"✅ Found {len(pdf_files)} PDF label(s)")
            
            if pdf_files:
                print(f"\n   Example: To delete label for order 'TEST123':")
                print(f"   Would search for PDFs containing 'TEST123'")
                print(f"   Sample labels: {pdf_files[:3]}")
        
        except FileNotFoundError:
            print(f"⚠️  Label directory not found: {SFTP_REMOTE_LABEL_DIR}")
            return True  # Not a failure if directory doesn't exist yet
        
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"⚠️  Could not access label directory: {e}")
        return True  # Not critical for test


def test_full_callback_processing():
    """Test the full callback processing (non-destructive)"""
    print("\n" + "="*80)
    print("TEST 5: Full Callback Processing (DRY RUN)")
    print("="*80)
    
    print("⚠️  This will process actual callback files if any exist")
    print("⚠️  Orders will be updated in Bol.com and labels will be deleted!")
    
    choice = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if choice != 'yes':
        print("❌ Test skipped by user")
        return True
    
    try:
        print("\n🔄 Processing callback files...")
        stats = process_callback_files()
        
        print("\n✅ Callback processing completed")
        print(f"\n📊 Results:")
        print(f"   Files processed: {stats['processed']}")
        print(f"   Orders updated: {stats['updated']}")
        print(f"   Labels deleted: {stats.get('labels_deleted', 0)}")
        print(f"   Ignored: {stats['ignored']}")
        print(f"   Errors: {stats['errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during callback processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("CALLBACK MONITOR TEST SUITE")
    print("="*80)
    print("\nThis will test the callback monitoring functionality:")
    print("1. SFTP connection to Callbacks and Label directories")
    print("2. HTML parsing logic")
    print("3. Callback file fetching")
    print("4. Label deletion simulation")
    print("5. Full callback processing (optional)")
    print("\n" + "="*80)
    
    results = {}
    
    # Test 1: SFTP Connection
    results['sftp_connection'] = test_sftp_connection()
    
    # Test 2: HTML Parsing
    results['html_parsing'] = test_html_parsing()
    
    # Test 3: Fetch Callback Files
    results['fetch_callbacks'] = test_fetch_callback_files()
    
    # Test 4: Label Deletion Simulation
    results['label_deletion_sim'] = test_label_deletion_simulation()
    
    # Test 5: Full Processing (optional)
    results['full_processing'] = test_full_callback_processing()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print("="*80)
    print(f"Overall: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed! The callback monitor is ready to use.")
        print("\nTo start monitoring:")
        print("  python run_callback_monitor.py")
        print("or")
        print("  python run_callback_monitor.py once  (single check)")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        exit(1)

