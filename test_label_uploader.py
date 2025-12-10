"""
Test script for the label uploader functionality
"""

import os
from label_uploader import (
    get_existing_pdf_files,
    upload_label_pdf_to_ftp,
    ensure_remote_label_directory
)
import paramiko
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
    SFTP_REMOTE_LABEL_DIR,
    LOCAL_LABEL_DIR
)

def test_sftp_connection():
    """Test SFTP connection and remote directory access"""
    print("\n" + "="*80)
    print("TEST 1: SFTP Connection")
    print("="*80)
    
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print(f"✅ Connected to SFTP server: {SFTP_HOST}:{SFTP_PORT}")
        
        # Test remote directory creation
        if ensure_remote_label_directory(sftp):
            print(f"✅ Remote label directory accessible: {SFTP_REMOTE_LABEL_DIR}")
        else:
            print(f"❌ Failed to access/create remote label directory")
            return False
        
        # List files in remote directory
        try:
            files = sftp.listdir(SFTP_REMOTE_LABEL_DIR)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            print(f"✅ Remote directory contains {len(pdf_files)} PDF file(s)")
        except Exception as e:
            print(f"⚠️  Could not list remote directory: {e}")
        
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"❌ SFTP connection failed: {e}")
        return False


def test_local_directory():
    """Test local label directory"""
    print("\n" + "="*80)
    print("TEST 2: Local Label Directory")
    print("="*80)
    
    if not os.path.exists(LOCAL_LABEL_DIR):
        print(f"⚠️  Creating local label directory: {LOCAL_LABEL_DIR}")
        os.makedirs(LOCAL_LABEL_DIR, exist_ok=True)
    
    pdf_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
    print(f"✅ Local directory exists: {LOCAL_LABEL_DIR}")
    print(f"✅ Found {len(pdf_files)} PDF file(s) in local directory")
    
    if pdf_files:
        print("\nSample files:")
        for i, filename in enumerate(list(pdf_files)[:5], 1):
            filepath = os.path.join(LOCAL_LABEL_DIR, filename)
            size = os.path.getsize(filepath)
            print(f"  {i}. {filename} ({size:,} bytes)")
        if len(pdf_files) > 5:
            print(f"  ... and {len(pdf_files) - 5} more files")
    
    return True


def test_upload_single_file():
    """Test uploading a single file"""
    print("\n" + "="*80)
    print("TEST 3: Single File Upload")
    print("="*80)
    
    pdf_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
    
    if not pdf_files:
        print("⚠️  No PDF files found to test upload")
        print("   Please add a PDF file to the 'label' folder and run again")
        return False
    
    # Get first PDF file
    test_file = list(pdf_files)[0]
    local_path = os.path.join(LOCAL_LABEL_DIR, test_file)
    
    print(f"Testing upload of: {test_file}")
    print(f"File size: {os.path.getsize(local_path):,} bytes")
    
    success = upload_label_pdf_to_ftp(local_path)
    
    if success:
        print(f"✅ Test upload successful!")
        return True
    else:
        print(f"❌ Test upload failed")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("LABEL UPLOADER TEST SUITE")
    print("="*80)
    print("\nThis will test the label PDF uploader functionality:")
    print("1. SFTP connection and remote directory")
    print("2. Local label directory and file scanning")
    print("3. Single file upload to FTP")
    print("\n" + "="*80)
    
    results = {}
    
    # Test 1: SFTP Connection
    results['sftp_connection'] = test_sftp_connection()
    
    # Test 2: Local Directory
    results['local_directory'] = test_local_directory()
    
    # Test 3: Single File Upload (only if previous tests passed)
    if results['sftp_connection'] and results['local_directory']:
        results['single_upload'] = test_upload_single_file()
    else:
        print("\n⚠️  Skipping upload test due to previous failures")
        results['single_upload'] = False
    
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
        print("\n🎉 All tests passed! The label uploader is ready to use.")
        print("\nTo start monitoring:")
        print("  python run_label_monitor.py")
        print("or")
        print("  python label_uploader.py monitor")
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

