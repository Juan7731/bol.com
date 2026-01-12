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
    SFTP_REMOTE_LABEL_DIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory settings
LOCAL_LABEL_DIR = "label"
# SFTP_REMOTE_LABEL_DIR will be loaded from config or system_config.json


def ensure_remote_label_directory(sftp: paramiko.SFTPClient, remote_dir: str = None) -> bool:
    """
    Ensure the remote label directory exists, create if it doesn't.
    
    Args:
        sftp: Active SFTP client connection
        remote_dir: Remote directory path (defaults to SFTP_REMOTE_LABEL_DIR)
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    if remote_dir is None:
        remote_dir = SFTP_REMOTE_LABEL_DIR
    
    try:
        sftp.chdir(remote_dir)
        logger.debug(f"Remote label directory exists: {remote_dir}")
        return True
    except IOError:
        # Directory doesn't exist, create it
        logger.info(f"Creating remote label directory: {remote_dir}")
        try:
            parts = [p for p in remote_dir.strip("/").split("/") if p]
            current = "/"
            for part in parts:
                current = os.path.join(current, part).replace("\\", "/")
                try:
                    sftp.chdir(current)
                except IOError:
                    sftp.mkdir(current)
                    sftp.chdir(current)
            logger.info(f"✅ Created remote label directory: {remote_dir}")
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
        logger.error(f"❌ Arquivo não encontrado: {local_file_path}")
        return False
    
    if not local_file_path.lower().endswith('.pdf'):
        logger.warning(f"⚠️  Pulando arquivo não-PDF: {local_file_path}")
        return False
    
    # Try to get SFTP credentials from system_config.json first, fallback to config.py
    sftp_host = SFTP_HOST
    sftp_port = SFTP_PORT
    sftp_username = SFTP_USERNAME
    sftp_password = SFTP_PASSWORD
    sftp_remote_label_dir = SFTP_REMOTE_LABEL_DIR
    
    try:
        from config_manager import load_config
        config = load_config()
        if 'ftp' in config:
            ftp_config = config['ftp']
            sftp_host = ftp_config.get('host', SFTP_HOST)
            sftp_port = ftp_config.get('port', SFTP_PORT)
            sftp_username = ftp_config.get('username', SFTP_USERNAME)
            sftp_password = ftp_config.get('password', SFTP_PASSWORD)
            sftp_remote_label_dir = ftp_config.get('remote_label_dir', SFTP_REMOTE_LABEL_DIR)
            logger.debug("✅ Usando credenciais SFTP do system_config.json")
    except Exception as config_error:
        logger.debug(f"Não foi possível carregar credenciais do system_config.json: {config_error}")
    
    filename = os.path.basename(local_file_path)
    remote_path = os.path.join(sftp_remote_label_dir, filename).replace("\\", "/")
    
    transport = None
    try:
        # Connect to SFTP
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.banner_timeout = 30  # Increase banner timeout
        transport.auth_timeout = 30    # Increase auth timeout
        logger.debug(f"🔐 Tentando autenticação SFTP para {filename}...")
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Ensure remote directory exists
        if not ensure_remote_label_directory(sftp, sftp_remote_label_dir):
            logger.error(f"❌ Não foi possível acessar/criar diretório remoto: {sftp_remote_label_dir}")
            return False
        
        # Upload the file
        local_size = os.path.getsize(local_file_path)
        logger.info(f"📤 Enviando {filename} ({local_size} bytes) para {remote_path}")
        sftp.put(local_file_path, remote_path)
        
        # Verify upload
        try:
            remote_stat = sftp.stat(remote_path)
            remote_size = remote_stat.st_size
            
            if local_size == remote_size:
                logger.info(f"✅ Upload bem-sucedido: {filename} ({local_size} bytes)")
                return True
            else:
                logger.error(f"❌ Tamanho diferente após upload: {filename} (local={local_size}, remoto={remote_size})")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível verificar upload de {filename}: {e}")
            logger.warning("   Assumindo que o upload foi bem-sucedido")
            return True  # Assume success if we can't verify
            
    except paramiko.AuthenticationException as auth_error:
        logger.error(f"❌ Erro de autenticação SFTP ao enviar {filename}: {auth_error}")
        return False
    except paramiko.SSHException as ssh_error:
        logger.error(f"❌ Erro de conexão SSH/SFTP ao enviar {filename}: {ssh_error}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro ao enviar {filename} para FTP: {e}")
        logger.error(f"   Tipo de erro: {type(e).__name__}")
        import traceback
        logger.debug(f"Traceback completo: {traceback.format_exc()}")
        return False
    finally:
        if transport:
            try:
                transport.close()
            except:
                pass


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
    # Get SFTP credentials
    sftp_host = SFTP_HOST
    sftp_port = SFTP_PORT
    sftp_remote_label_dir = SFTP_REMOTE_LABEL_DIR
    
    try:
        from config_manager import load_config
        config = load_config()
        if 'ftp' in config:
            ftp_config = config['ftp']
            sftp_host = ftp_config.get('host', SFTP_HOST)
            sftp_port = ftp_config.get('port', SFTP_PORT)
            sftp_remote_label_dir = ftp_config.get('remote_label_dir', SFTP_REMOTE_LABEL_DIR)
    except Exception:
        pass
    
    logger.info("="*80)
    logger.info("📤 Upload de Todos os Labels PDF")
    logger.info("="*80)
    logger.info(f"Servidor: {sftp_host}:{sftp_port}")
    logger.info(f"Diretório remoto: {sftp_remote_label_dir}")
    logger.info(f"Diretório local: {LOCAL_LABEL_DIR}")
    logger.info("="*80)
    
    pdf_files = get_existing_pdf_files(LOCAL_LABEL_DIR)
    
    if not pdf_files:
        logger.info("⚠️  Nenhum arquivo PDF encontrado na pasta label")
        return
    
    logger.info(f"📋 Encontrados {len(pdf_files)} arquivo(s) PDF para upload")
    logger.info("")
    
    success_count = 0
    fail_count = 0
    
    for filename in pdf_files:
        local_path = os.path.join(LOCAL_LABEL_DIR, filename)
        if upload_label_pdf_to_ftp(local_path):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info("")
    logger.info("="*80)
    logger.info(f"📊 Upload concluído: {success_count} bem-sucedidos, {fail_count} falhas")
    logger.info("="*80)
    
    if fail_count > 0:
        logger.warning("⚠️  Alguns arquivos falharam no upload. Verifique os logs acima.")


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

