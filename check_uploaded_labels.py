"""
Script to check uploaded label PDF files on SFTP server
"""

import paramiko
import logging
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
    SFTP_REMOTE_LABEL_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_uploaded_labels():
    """Check uploaded label PDF files on SFTP server"""
    logger.info("="*80)
    logger.info("📋 CHECKING UPLOADED LABEL PDF FILES")
    logger.info("="*80)
    logger.info("")
    logger.info(f"SFTP Server: {SFTP_HOST}:{SFTP_PORT}")
    logger.info(f"Remote Directory: {SFTP_REMOTE_LABEL_DIR}")
    logger.info("")
    
    transport = None
    try:
        # Connect to SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        logger.info("✅ Successfully connected to SFTP server")
        logger.info("")
        
        # Try to access the label directory
        try:
            sftp.chdir(SFTP_REMOTE_LABEL_DIR)
            logger.info(f"✅ Successfully accessed directory: {SFTP_REMOTE_LABEL_DIR}")
        except IOError as e:
            logger.error(f"❌ Cannot access directory {SFTP_REMOTE_LABEL_DIR}")
            logger.error(f"   Error: {e}")
            logger.info("")
            logger.info("Attempting to list current directory...")
            try:
                current_dir = sftp.getcwd()
                logger.info(f"Current directory: {current_dir}")
                files = sftp.listdir(current_dir)
                logger.info(f"Files in current directory: {files[:10]}")
            except Exception as e2:
                logger.error(f"Error listing directory: {e2}")
            finally:
                transport.close()
                return
        
        # List all PDF files in the remote directory
        try:
            files = sftp.listdir(SFTP_REMOTE_LABEL_DIR)
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            
            logger.info(f"📁 Total files in directory: {len(files)}")
            logger.info(f"📄 PDF files found: {len(pdf_files)}")
            logger.info("")
            
            if pdf_files:
                logger.info("✅ Uploaded Label PDF Files:")
                logger.info("-" * 80)
                for i, filename in enumerate(sorted(pdf_files), 1):
                    try:
                        # Get file stats
                        file_path = f"{SFTP_REMOTE_LABEL_DIR}/{filename}"
                        file_stat = sftp.stat(file_path)
                        size_kb = file_stat.st_size / 1024
                        # Get modification time
                        import datetime
                        mtime = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                        logger.info(f"{i:3d}. {filename:50s} ({size_kb:.2f} KB) - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                    except Exception as e:
                        logger.info(f"{i:3d}. {filename:50s} (Error getting stats: {e})")
                logger.info("-" * 80)
                logger.info("")
                logger.info(f"✅ Total: {len(pdf_files)} PDF file(s) uploaded")
            else:
                logger.warning("⚠️  No PDF files found in the remote directory")
                logger.info("")
                logger.info("Available files:")
                for f in files[:20]:  # Show first 20 files
                    logger.info(f"  - {f}")
                if len(files) > 20:
                    logger.info(f"  ... and {len(files) - 20} more files")
            
        except Exception as e:
            logger.error(f"❌ Error listing files: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if transport:
            transport.close()
        logger.info("")
        logger.info("="*80)
        logger.info("Verification complete")
        logger.info("="*80)


if __name__ == "__main__":
    check_uploaded_labels()
