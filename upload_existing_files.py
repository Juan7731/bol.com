"""
Script para fazer upload manual de arquivos CSV e labels PDF existentes para o servidor SFTP
"""

import os
import logging
from pathlib import Path
from order_processing import upload_files_sftp, _today_batch_dir
from label_uploader import upload_all_labels

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def upload_existing_batch_files():
    """Fazer upload de todos os arquivos CSV existentes na pasta batches"""
    logger.info("="*80)
    logger.info("📤 Upload de Arquivos CSV Existentes")
    logger.info("="*80)
    
    # Encontrar todos os arquivos CSV na pasta batches
    batch_dir = _today_batch_dir()
    if not os.path.exists(batch_dir):
        logger.error(f"❌ Diretório de batches não encontrado: {batch_dir}")
        return
    
    csv_files = []
    for root, dirs, files in os.walk(batch_dir):
        for file in files:
            if file.endswith('.csv'):
                full_path = os.path.join(root, file)
                csv_files.append(full_path)
                logger.info(f"Encontrado: {file}")
    
    if not csv_files:
        logger.warning("⚠️  Nenhum arquivo CSV encontrado na pasta batches")
        return
    
    logger.info(f"\n📋 Total de arquivos CSV encontrados: {len(csv_files)}")
    logger.info("Iniciando upload...\n")
    
    # Fazer upload
    upload_files_sftp(csv_files)
    
    logger.info("="*80)
    logger.info("✅ Upload de arquivos CSV concluído")
    logger.info("="*80)


def upload_existing_labels():
    """Fazer upload de todos os arquivos PDF existentes na pasta label"""
    logger.info("="*80)
    logger.info("📤 Upload de Labels PDF Existentes")
    logger.info("="*80)
    
    upload_all_labels()


def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "batches" or command == "csv":
            upload_existing_batch_files()
        elif command == "labels" or command == "pdf":
            upload_existing_labels()
        elif command == "all":
            upload_existing_batch_files()
            print("\n")
            upload_existing_labels()
        else:
            print("Uso: python upload_existing_files.py [batches|labels|all]")
            print("  batches - Upload apenas arquivos CSV")
            print("  labels  - Upload apenas labels PDF")
            print("  all     - Upload ambos (padrão)")
    else:
        # Padrão: upload de tudo
        upload_existing_batch_files()
        print("\n")
        upload_existing_labels()


if __name__ == "__main__":
    main()

