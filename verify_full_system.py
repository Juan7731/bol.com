"""
Script para verificar se todo o sistema está funcionando corretamente:
1. Verificação de tempo/scheduler
2. Processamento de pedidos
3. Upload de arquivos gerados para o servidor
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_1_configuration():
    """Teste 1: Verificar configurações"""
    logger.info("="*80)
    logger.info("TESTE 1: Verificação de Configurações")
    logger.info("="*80)
    
    try:
        from config import (
            BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE,
            PROCESS_INTERVAL, PROCESS_TIMES,
            SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD,
            SFTP_REMOTE_BATCH_DIR, SFTP_REMOTE_LABEL_DIR,
            EMAIL_ENABLED
        )
        
        logger.info("✅ Configurações do config.py carregadas")
        logger.info(f"   TEST_MODE: {TEST_MODE}")
        logger.info(f"   PROCESS_INTERVAL: {PROCESS_INTERVAL} segundos")
        logger.info(f"   SFTP_HOST: {SFTP_HOST}")
        logger.info(f"   SFTP_USERNAME: {SFTP_USERNAME}")
        
        # Verificar system_config.json
        from config_manager import get_active_bol_accounts, load_config
        config = load_config()
        active_accounts = get_active_bol_accounts()
        
        logger.info(f"✅ {len(active_accounts)} conta(s) ativa(s) no system_config.json")
        for acc in active_accounts:
            logger.info(f"   - {acc['name']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao verificar configurações: {e}")
        return False

def test_2_sftp_connection():
    """Teste 2: Verificar conexão SFTP"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 2: Verificação de Conexão SFTP")
    logger.info("="*80)
    
    try:
        import paramiko
        from config_manager import load_config
        
        config = load_config()
        ftp_config = config.get('ftp', {})
        
        sftp_host = ftp_config.get('host')
        sftp_port = ftp_config.get('port', 22)
        sftp_username = ftp_config.get('username')
        sftp_password = ftp_config.get('password')
        
        logger.info(f"Conectando a {sftp_host}:{sftp_port}...")
        
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        logger.info("✅ Conexão SFTP bem-sucedida")
        
        # Testar diretórios
        batch_dir = ftp_config.get('remote_batch_dir')
        label_dir = ftp_config.get('remote_label_dir')
        
        try:
            sftp.chdir(batch_dir)
            files = sftp.listdir(".")
            logger.info(f"✅ Diretório Batches acessível: {len(files)} arquivo(s)")
        except Exception as e:
            logger.error(f"❌ Erro ao acessar diretório Batches: {e}")
            return False
        
        try:
            sftp.chdir(label_dir)
            files = sftp.listdir(".")
            logger.info(f"✅ Diretório Label acessível: {len(files)} arquivo(s)")
        except Exception as e:
            logger.error(f"❌ Erro ao acessar diretório Label: {e}")
            return False
        
        transport.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na conexão SFTP: {e}")
        return False

def test_3_order_processing():
    """Teste 3: Verificar processamento de pedidos"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 3: Verificação de Processamento de Pedidos")
    logger.info("="*80)
    
    try:
        from order_processing import (
            run_processing_once,
            classify_orders,
            generate_excel_batches,
            upload_files_sftp
        )
        from bol_api_client import BolAPIClient
        from bol_dtos import Order
        from config import BOL_CLIENT_ID, BOL_CLIENT_SECRET, TEST_MODE
        from config_manager import get_active_bol_accounts
        
        logger.info("✅ Funções de processamento importadas com sucesso")
        
        # Verificar se multi-account está funcionando
        active_accounts = get_active_bol_accounts()
        logger.info(f"✅ Sistema multi-conta configurado: {len(active_accounts)} conta(s)")
        
        # Testar uma conexão API rápida
        if active_accounts:
            first_account = active_accounts[0]
            logger.info(f"Testando conexão API com conta: {first_account['name']}")
            client = BolAPIClient(
                first_account['client_id'],
                first_account['client_secret'],
                test_mode=TEST_MODE
            )
            # Apenas testar obtenção de token
            token = client._get_access_token()
            if token:
                logger.info("✅ Conexão com API Bol.com bem-sucedida")
            else:
                logger.error("❌ Falha ao obter token da API")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar processamento: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_4_file_generation():
    """Teste 4: Verificar geração de arquivos"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 4: Verificação de Geração de Arquivos")
    logger.info("="*80)
    
    try:
        import os
        from order_processing import _batch_dir

        batch_dir = _batch_dir()
        label_dir = "label"
        
        logger.info(f"Diretório de batches: {batch_dir}")
        logger.info(f"Diretório de labels: {label_dir}")
        
        # Verificar se diretórios existem
        if os.path.exists(batch_dir):
            csv_files = [f for f in os.listdir(batch_dir) if f.endswith('.csv')]
            logger.info(f"✅ Diretório batches existe: {len(csv_files)} arquivo(s) CSV")
            for f in csv_files[:5]:  # Mostrar primeiros 5
                logger.info(f"   - {f}")
        else:
            logger.warning("⚠️  Diretório batches não existe (será criado automaticamente)")
        
        if os.path.exists(label_dir):
            pdf_files = [f for f in os.listdir(label_dir) if f.endswith('.pdf')]
            logger.info(f"✅ Diretório label existe: {len(pdf_files)} arquivo(s) PDF")
            for f in pdf_files[:5]:  # Mostrar primeiros 5
                logger.info(f"   - {f}")
        else:
            logger.warning("⚠️  Diretório label não existe (será criado automaticamente)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar geração de arquivos: {e}")
        return False

def test_5_upload_functionality():
    """Teste 5: Verificar funcionalidade de upload"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 5: Verificação de Funcionalidade de Upload")
    logger.info("="*80)
    
    try:
        from order_processing import upload_files_sftp
        from label_uploader import upload_all_labels, upload_label_pdf_to_ftp
        
        logger.info("✅ Funções de upload importadas")
        logger.info("   - upload_files_sftp: Disponível")
        logger.info("   - upload_all_labels: Disponível")
        logger.info("   - upload_label_pdf_to_ftp: Disponível")
        
        # Verificar se há arquivos para testar upload
        import os
        from order_processing import _batch_dir

        batch_dir = _batch_dir()
        if os.path.exists(batch_dir):
            csv_files = [f for f in os.listdir(batch_dir) if f.endswith('.csv')]
            if csv_files:
                logger.info(f"✅ {len(csv_files)} arquivo(s) CSV disponível(is) para upload")
            else:
                logger.info("ℹ️  Nenhum arquivo CSV para testar upload")
        
        label_dir = "label"
        if os.path.exists(label_dir):
            pdf_files = [f for f in os.listdir(label_dir) if f.endswith('.pdf')]
            if pdf_files:
                logger.info(f"✅ {len(pdf_files)} arquivo(s) PDF disponível(is) para upload")
            else:
                logger.info("ℹ️  Nenhum arquivo PDF para testar upload")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar upload: {e}")
        return False

def test_6_continuous_mode():
    """Teste 6: Verificar modo contínuo"""
    logger.info("")
    logger.info("="*80)
    logger.info("TESTE 6: Verificação de Modo Contínuo")
    logger.info("="*80)
    
    try:
        from order_processing import run_continuous, run_processing_once, run_scheduler
        from config import PROCESS_INTERVAL, PROCESS_TIMES
        
        logger.info("✅ Funções de modo contínuo importadas")
        logger.info(f"   - run_continuous: Disponível")
        logger.info(f"   - run_processing_once: Disponível")
        logger.info(f"   - run_scheduler: Disponível")
        logger.info(f"   - PROCESS_INTERVAL: {PROCESS_INTERVAL} segundos")
        logger.info(f"   - PROCESS_TIMES: {[t for t in PROCESS_TIMES if t]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar modo contínuo: {e}")
        return False

def main():
    """Executar todos os testes"""
    logger.info("")
    logger.info("="*80)
    logger.info("🔍 VERIFICAÇÃO COMPLETA DO SISTEMA")
    logger.info("="*80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    results = {}
    
    # Executar testes
    results['config'] = test_1_configuration()
    results['sftp'] = test_2_sftp_connection()
    results['processing'] = test_3_order_processing()
    results['files'] = test_4_file_generation()
    results['upload'] = test_5_upload_functionality()
    results['continuous'] = test_6_continuous_mode()
    
    # Resumo
    logger.info("")
    logger.info("="*80)
    logger.info("📊 RESUMO DOS TESTES")
    logger.info("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"   {status}: {test_name.upper()}")
    
    logger.info("")
    logger.info(f"Total: {total} testes")
    logger.info(f"✅ Passou: {passed}")
    logger.info(f"❌ Falhou: {failed}")
    logger.info("="*80)
    
    if failed == 0:
        logger.info("")
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        logger.info("✅ O sistema está pronto para uso")
        logger.info("")
        logger.info("Para iniciar o processamento contínuo:")
        logger.info("   python3 order_processing.py")
        logger.info("")
        return 0
    else:
        logger.warning("")
        logger.warning("⚠️  ALGUNS TESTES FALHARAM")
        logger.warning("Verifique os erros acima e corrija antes de usar o sistema")
        logger.warning("")
        return 1

if __name__ == "__main__":
    sys.exit(main())

