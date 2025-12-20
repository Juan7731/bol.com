"""
Verify that Excel files are actually uploaded to the SFTP server
"""

import paramiko
import os
import sys
from config import (
    SFTP_HOST,
    SFTP_PORT,
    SFTP_USERNAME,
    SFTP_PASSWORD,
    SFTP_REMOTE_BATCH_DIR,
)

def verify_ftp_files():
    """Connect to SFTP and list files in the remote directory"""
    print("="*80)
    print("SFTP Upload Verification")
    print("="*80)
    print(f"\nConnecting to: {SFTP_HOST}:{SFTP_PORT}")
    print(f"Username: {SFTP_USERNAME}")
    print(f"Remote directory: {SFTP_REMOTE_BATCH_DIR}\n")
    
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.banner_timeout = 30  # Increase banner timeout
    transport.auth_timeout = 30    # Increase auth timeout
    try:
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        print("✅ Successfully connected to SFTP server\n")
        
        # Try to change to remote directory
        try:
            sftp.chdir(SFTP_REMOTE_BATCH_DIR)
            print(f"✅ Successfully accessed directory: {SFTP_REMOTE_BATCH_DIR}\n")
        except IOError as e:
            print(f"❌ Cannot access directory {SFTP_REMOTE_BATCH_DIR}")
            print(f"   Error: {e}\n")
            print("Attempting to list current directory...")
            try:
                current_dir = sftp.getcwd()
                print(f"Current directory: {current_dir}")
                files = sftp.listdir(current_dir)
                print(f"Files in current directory: {files[:10]}...")  # Show first 10
            except Exception as e2:
                print(f"Error listing directory: {e2}")
            finally:
                transport.close()
                return
        
        # List all files in the remote directory
        try:
            files = sftp.listdir(SFTP_REMOTE_BATCH_DIR)
            csv_files = [f for f in files if f.endswith('.csv')]
            
            print(f"📁 Total files in directory: {len(files)}")
            print(f"📊 CSV files found: {len(csv_files)}\n")
            
            if csv_files:
                print("✅ Excel files found on SFTP server:")
                print("-" * 80)
                for i, filename in enumerate(sorted(xlsx_files), 1):
                    try:
                        # Get file stats
                        file_path = f"{SFTP_REMOTE_BATCH_DIR}/{filename}"
                        file_stat = sftp.stat(file_path)
                        size_kb = file_stat.st_size / 1024
                        print(f"{i:3d}. {filename:30s} ({size_kb:.2f} KB)")
                    except Exception as e:
                        print(f"{i:3d}. {filename:30s} (Error getting stats: {e})")
                print("-" * 80)
            else:
                print("❌ No CSV files found in the remote directory")
                print("\nAvailable files:")
                for f in files[:20]:  # Show first 20 files
                    print(f"  - {f}")
                if len(files) > 20:
                    print(f"  ... and {len(files) - 20} more files")
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        transport.close()
        print("\n" + "="*80)
        print("Verification complete")
        print("="*80)

if __name__ == "__main__":
    verify_ftp_files()

