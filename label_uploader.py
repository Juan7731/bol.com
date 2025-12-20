"""
Label PDF Monitor and Auto-Uploader to FTP
Monitors the 'label' subfolder and automatically uploads PDF files to FTP/label directory when created
"""

import os
import time
import logging
import paramiko
from pathlib import Path
from typing import Set
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory settings
LOCAL_LABEL_DIR = "label"
SFTP_REMOTE_LABEL_DIR = "/data/sites/web/trivium-ecommercecom/FTP/Label"


def ensure_remote_label_directory(sftp: paramiko.SFTPClient) -> bool:
    """
    Ensure the remote label directory exists, create if it doesn't.
    
    Args:
        sftp: Active SFTP client connection
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        sftp.chdir(SFTP_REMOTE_LABEL_DIR)
        logger.info(f"Remote label directory exists: {SFTP_REMOTE_LABEL_DIR}")
        return True
    except IOError:
        # Directory doesn't exist, create it
        logger.info(f"Creating remote label directory: {SFTP_REMOTE_LABEL_DIR}")
        try:
            parts = SFTP_REMOTE_LABEL_DIR.strip("/").split("/")
            current = "/"
            for part in parts:
                current = os.path.join(current, part).replace("\\", "/")
                try:
                    sftp.chdir(current)
                except IOError:
                    sftp.mkdir(current)
                    sftp.chdir(current)
            logger.info(f"✅ Created remote label directory: {SFTP_REMOTE_LABEL_DIR}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create remote label directory: {e}")
            return False


def upload_label_pdf_to_ftp(local_file_path: str) -> bool:
    """
    Upload a single PDF label file to the FTP label directory.
    
    Args:
        local_file_path: Path to the local PDF file
        
    Returns:
        bool: True if upload was successful, False otherwise
    """
    if not os.path.exists(local_file_path):
        logger.error(f"❌ File not found: {local_file_path}")
        return False
    
    if not local_file_path.lower().endswith('.pdf'):
        logger.warning(f"⚠️  Skipping non-PDF file: {local_file_path}")
        return False
    
    filename = os.path.basename(local_file_path)
    remote_path = os.path.join(SFTP_REMOTE_LABEL_DIR, filename).replace("\\", "/")
    
    transport = None
    try:
        # Connect to SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Ensure remote directory exists
        if not ensure_remote_label_directory(sftp):
            return False
        
        # Upload the file
        logger.info(f"📤 Uploading {filename} to {remote_path}")
        sftp.put(local_file_path, remote_path)
        
        # Verify upload
        try:
            remote_stat = sftp.stat(remote_path)
            local_size = os.path.getsize(local_file_path)
            remote_size = remote_stat.st_size
            
            if local_size == remote_size:
                logger.info(f"✅ Successfully uploaded {filename} ({local_size} bytes)")
                return True
            else:
                logger.error(f"❌ Size mismatch for {filename}: local={local_size}, remote={remote_size}")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Could not verify upload for {filename}: {e}")
            return True  # Assume success if we can't verify
            
    except Exception as e:
        logger.error(f"❌ Error uploading {filename} to FTP: {e}")
        return False
    finally:
        if transport:
            transport.close()


def get_existing_pdf_files(directory: str) -> Set[str]:
    """
    Get a set of all PDF files currently in the directory.
    
    Args:
        directory: Path to the directory to scan
        
    Returns:
        Set of PDF filenames
    """
    if not os.path.exists(directory):
        logger.warning(f"⚠️  Directory does not exist: {directory}")
        return set()
    
    pdf_files = set()
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith('.pdf'):
                pdf_files.add(filename)
    except Exception as e:
        logger.error(f"❌ Error scanning directory {directory}: {e}")
    
    return pdf_files


def monitor_label_folder(check_interval: int = 5, upload_existing: bool = False):
    """
    Monitor the label folder for new PDF files and upload them to FTP.
    
    Args:
        check_interval: Time in seconds between directory checks (default: 5)
        upload_existing: If True, upload existing PDF files on startup (default: False)
    """
    logger.info("="*80)
    logger.info("📁 Label PDF Monitor Started")
    logger.info("="*80)
    logger.info(f"Local directory: {LOCAL_LABEL_DIR}")
    logger.info(f"Remote FTP directory: {SFTP_REMOTE_LABEL_DIR}")
    logger.info(f"Check interval: {check_interval} seconds")
    logger.info(f"Upload existing files: {upload_existing}")
    logger.info("="*80)
    
    # Create local directory if it doesn't exist
    os.makedirs(LOCAL_LABEL_DIR, exist_ok=True)
    
    # Track known files
    known_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
    logger.info(f"Found {len(known_files)} existing PDF files in label folder")
    
    # Upload existing files if requested
    if upload_existing and known_files:
        logger.info(f"Uploading {len(known_files)} existing PDF files...")
        for filename in known_files:
            local_path = os.path.join(LOCAL_LABEL_DIR, filename)
            upload_label_pdf_to_ftp(local_path)
    
    # Start monitoring loop
    logger.info("\n🔍 Monitoring for new PDF files... (Press Ctrl+C to stop)\n")
    
    try:
        while True:
            current_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
            new_files = current_files - known_files
            
            if new_files:
                logger.info(f"🆕 Detected {len(new_files)} new PDF file(s)")
                for filename in new_files:
                    local_path = os.path.join(LOCAL_LABEL_DIR, filename)
                    # Small delay to ensure file is fully written
                    time.sleep(0.5)
                    if upload_label_pdf_to_ftp(local_path):
                        known_files.add(filename)
            
            # Check for deleted files
            deleted_files = known_files - current_files
            if deleted_files:
                logger.info(f"🗑️  Removed {len(deleted_files)} file(s) from tracking")
                known_files = current_files
            
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("\n\n" + "="*80)
        logger.info("🛑 Monitor stopped by user")
        logger.info("="*80)


def upload_all_labels():
    """
    Upload all existing PDF files in the label folder to FTP.
    Useful for batch uploads or manual sync.
    """
    logger.info("="*80)
    logger.info("📤 Uploading All Label PDFs")
    logger.info("="*80)
    
    pdf_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
    
    if not pdf_files:
        logger.info("No PDF files found in label folder")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to upload")
    
    success_count = 0
    fail_count = 0
    
    for filename in pdf_files:
        local_path = os.path.join(LOCAL_LABEL_DIR, filename)
        if upload_label_pdf_to_ftp(local_path):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info("="*80)
    logger.info(f"✅ Upload complete: {success_count} successful, {fail_count} failed")
    logger.info("="*80)


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "upload-all":
            # Upload all existing files
            upload_all_labels()
        elif command == "monitor":
            # Monitor with optional existing file upload
            upload_existing = "--upload-existing" in sys.argv
            monitor_label_folder(check_interval=5, upload_existing=upload_existing)
        elif command == "test":
            # Test upload with a single file
            if len(sys.argv) < 3:
                print("Usage: python label_uploader.py test <filename>")
                sys.exit(1)
            filename = sys.argv[2]
            local_path = os.path.join(LOCAL_LABEL_DIR, filename)
            upload_label_pdf_to_ftp(local_path)
        else:
            print("Unknown command. Available commands:")
            print("  monitor              - Start monitoring for new PDF files")
            print("  monitor --upload-existing - Monitor and upload existing files first")
            print("  upload-all           - Upload all existing PDF files")
            print("  test <filename>      - Test upload a specific file")
    else:
        # Default: start monitoring
        monitor_label_folder(check_interval=5, upload_existing=False)

