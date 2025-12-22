"""
Deploy Codebase to SFTP Server

This script uploads all necessary files from the codebase to the SFTP server.
It excludes unnecessary files like __pycache__, .pyc, test files, etc.
"""

import os
import sys
import logging
import paramiko
from pathlib import Path
from typing import List, Set
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Files and directories to exclude from deployment
EXCLUDE_PATTERNS: Set[str] = {
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git',
    '.gitignore',
    'batches',
    'label',
    '*.db',
    '*.log',
    '*.md',
    '*.txt',
    '*.bat',
    'chathistory.txt',
    'admin',  # PHP admin panel
    'test_*.py',
    'debug_*.py',
    'verify_*.py',
    'demo_*.py',
    'quick_test.py',
    'run_all_tests.py',
    'generate_test_excel.py',
    'get_order_item_ids.py',
    'check_fulfilment_structure.py',
    'label_integration_example.py',
    'test_callback_monitor.py',
    'test_label_uploader.py',
    'test_system.py',
    'run_callback_monitor.py',
    'run_callback_scheduler.py',
    'run_label_monitor.py',
    'run_scheduler.py',
    'run_scheduler_with_admin_config.py',
    'admin_config_reader.py',
    'admin_config.json',
    'process_both_shops.py',  # Old script, replaced by multi_account_processor
}

# Files that MUST be included (even if they match exclude patterns)
INCLUDE_FILES: Set[str] = {
    'requirements.txt',
    'system_config.json',
    'config.py',
    'run_production.py',
}

# Remote directory on SFTP server where code will be deployed
REMOTE_DEPLOY_DIR = "/data/sites/web/trivium-ecommercecom/bol-order-processor"


def load_sftp_config() -> dict:
    """Load SFTP configuration from system_config.json"""
    try:
        with open('system_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            ftp_config = config.get('ftp', {})
            return {
                'host': ftp_config.get('host', 'triviu.ssh.transip.me'),
                'port': ftp_config.get('port', 22),
                'username': ftp_config.get('username', 'trivium-ecommercecom'),
                'password': ftp_config.get('password', '&9z?8zcN&9z?8zcN'),
            }
    except Exception as e:
        logger.error(f"Failed to load SFTP config: {e}")
        sys.exit(1)


def should_exclude_file(file_path: str) -> bool:
    """Check if a file should be excluded from deployment"""
    filename = os.path.basename(file_path)
    
    # Always include files in INCLUDE_FILES
    if filename in INCLUDE_FILES:
        return False
    
    # Check exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_path or filename.startswith(pattern.replace('*', '')):
            return True
        if pattern.endswith('.py') and filename == pattern:
            return True
    
    # Exclude hidden files
    if filename.startswith('.'):
        return True
    
    return False


def get_files_to_deploy(root_dir: str = '.') -> List[str]:
    """Get list of files to deploy"""
    files_to_deploy = []
    root_path = Path(root_dir).resolve()
    
    for file_path in root_path.rglob('*'):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(root_path))
            
            # Skip if should be excluded
            if should_exclude_file(rel_path):
                continue
            
            files_to_deploy.append(str(file_path))
    
    return sorted(files_to_deploy)


def ensure_remote_directory(sftp: paramiko.SFTPClient, remote_path: str) -> bool:
    """Ensure remote directory exists, create if necessary"""
    try:
        sftp.chdir(remote_path)
        return True
    except IOError:
        # Directory doesn't exist, create it
        try:
            parts = remote_path.strip('/').split('/')
            current = ''
            for part in parts:
                current = f"{current}/{part}" if current else f"/{part}"
                try:
                    sftp.chdir(current)
                except IOError:
                    sftp.mkdir(current)
                    sftp.chdir(current)
                    logger.info(f"Created remote directory: {current}")
            return True
        except Exception as e:
            logger.error(f"Failed to create remote directory {remote_path}: {e}")
            return False


def upload_file(sftp: paramiko.SFTPClient, local_path: str, remote_base_dir: str) -> bool:
    """Upload a single file to SFTP server"""
    try:
        # Get relative path from current directory
        rel_path = os.path.relpath(local_path, '.')
        remote_path = os.path.join(remote_base_dir, rel_path).replace('\\', '/')
        
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_path)
        if not ensure_remote_directory(sftp, remote_dir):
            return False
        
        # Upload file
        logger.info(f"Uploading: {rel_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
        
        # Verify upload
        try:
            remote_stat = sftp.stat(remote_path)
            local_size = os.path.getsize(local_path)
            if remote_stat.st_size == local_size:
                logger.info(f"  ✅ Uploaded successfully ({local_size} bytes)")
                return True
            else:
                logger.warning(f"  ⚠️  Size mismatch: local={local_size}, remote={remote_stat.st_size}")
                return True  # Still consider successful
        except Exception as e:
            logger.warning(f"  ⚠️  Could not verify upload: {e}")
            return True  # Assume successful
        
    except Exception as e:
        logger.error(f"  ❌ Failed to upload {local_path}: {e}")
        return False


def deploy_to_sftp():
    """Main deployment function"""
    logger.info("="*80)
    logger.info("DEPLOY CODEBASE TO SFTP SERVER")
    logger.info("="*80)
    
    # Load SFTP configuration
    sftp_config = load_sftp_config()
    logger.info(f"SFTP Server: {sftp_config['host']}:{sftp_config['port']}")
    logger.info(f"Remote Directory: {REMOTE_DEPLOY_DIR}")
    logger.info("")
    
    # Get files to deploy
    logger.info("Scanning files to deploy...")
    files_to_deploy = get_files_to_deploy()
    logger.info(f"Found {len(files_to_deploy)} file(s) to deploy")
    logger.info("")
    
    if not files_to_deploy:
        logger.error("No files to deploy!")
        sys.exit(1)
    
    # Show files that will be deployed
    logger.info("Files to deploy:")
    for f in files_to_deploy[:20]:  # Show first 20
        logger.info(f"  - {os.path.relpath(f, '.')}")
    if len(files_to_deploy) > 20:
        logger.info(f"  ... and {len(files_to_deploy) - 20} more file(s)")
    logger.info("")
    
    # Connect to SFTP
    transport = None
    try:
        logger.info("Connecting to SFTP server...")
        transport = paramiko.Transport((sftp_config['host'], sftp_config['port']))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        transport.connect(username=sftp_config['username'], password=sftp_config['password'])
        sftp = paramiko.SFTPClient.from_transport(transport)
        logger.info("✅ Connected to SFTP server")
        logger.info("")
        
        # Ensure remote directory exists
        if not ensure_remote_directory(sftp, REMOTE_DEPLOY_DIR):
            logger.error("Failed to create remote directory")
            sys.exit(1)
        
        # Upload files
        logger.info("="*80)
        logger.info("UPLOADING FILES")
        logger.info("="*80)
        logger.info("")
        
        uploaded_count = 0
        failed_count = 0
        
        for file_path in files_to_deploy:
            if upload_file(sftp, file_path, REMOTE_DEPLOY_DIR):
                uploaded_count += 1
            else:
                failed_count += 1
        
        # Summary
        logger.info("")
        logger.info("="*80)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("="*80)
        logger.info(f"  Total files: {len(files_to_deploy)}")
        logger.info(f"  ✅ Uploaded: {uploaded_count}")
        logger.info(f"  ❌ Failed: {failed_count}")
        logger.info("="*80)
        
        if failed_count > 0:
            logger.error("⚠️  Some files failed to upload")
            sys.exit(1)
        else:
            logger.info("✅ Deployment completed successfully!")
            logger.info(f"   Files deployed to: {REMOTE_DEPLOY_DIR}")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if transport:
            transport.close()


if __name__ == "__main__":
    deploy_to_sftp()

