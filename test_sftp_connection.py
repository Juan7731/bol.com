"""
Script para testar a conexão SFTP e verificar credenciais
"""

import paramiko
import sys
from config import SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD

def test_sftp_connection():
    """Testa a conexão SFTP"""
    print("="*80)
    print("🔍 Teste de Conexão SFTP")
    print("="*80)
    print(f"Host: {SFTP_HOST}")
    print(f"Port: {SFTP_PORT}")
    print(f"Username: {SFTP_USERNAME}")
    print(f"Password length: {len(SFTP_PASSWORD)} caracteres")
    print(f"Password (first 3 chars): {SFTP_PASSWORD[:3]}...")
    print("="*80)
    print()
    
    transport = None
    try:
        print("📡 Conectando ao servidor SFTP...")
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        
        print("🔐 Tentando autenticação...")
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        
        print("✅ Autenticação bem-sucedida!")
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        print("✅ Cliente SFTP criado com sucesso")
        
        # Testar acesso aos diretórios
        print()
        print("📁 Testando acesso aos diretórios...")
        
        # Testar diretório de batches
        try:
            sftp.chdir("/data/sites/web/trivium-ecommercecom/FTP/Batches")
            print("✅ Diretório Batches acessível")
            files = sftp.listdir(".")
            print(f"   Arquivos encontrados: {len(files)}")
            if files:
                print(f"   Primeiros arquivos: {files[:5]}")
        except Exception as e:
            print(f"⚠️  Erro ao acessar diretório Batches: {e}")
        
        # Testar diretório de labels
        try:
            sftp.chdir("/data/sites/web/trivium-ecommercecom/FTP/Label")
            print("✅ Diretório Label acessível")
            files = sftp.listdir(".")
            print(f"   Arquivos encontrados: {len(files)}")
            if files:
                print(f"   Primeiros arquivos: {files[:5]}")
        except Exception as e:
            print(f"⚠️  Erro ao acessar diretório Label: {e}")
        
        print()
        print("="*80)
        print("✅ Teste de conexão concluído com sucesso!")
        print("="*80)
        return True
        
    except paramiko.AuthenticationException as e:
        print()
        print("="*80)
        print("❌ ERRO DE AUTENTICAÇÃO")
        print("="*80)
        print(f"Erro: {e}")
        print()
        print("Possíveis causas:")
        print("1. Username ou senha incorretos")
        print("2. Caracteres especiais na senha podem precisar de escape")
        print("3. Conta pode estar bloqueada ou desabilitada")
        print()
        print("Sugestões:")
        print("- Verifique as credenciais em config.py")
        print("- Tente fazer login manual via SFTP para verificar")
        print("="*80)
        return False
        
    except paramiko.SSHException as e:
        print()
        print("="*80)
        print("❌ ERRO DE CONEXÃO SSH")
        print("="*80)
        print(f"Erro: {e}")
        print("="*80)
        return False
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ ERRO INESPERADO")
        print("="*80)
        print(f"Erro: {e}")
        print(f"Tipo: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        print("="*80)
        return False
        
    finally:
        if transport:
            try:
                transport.close()
            except:
                pass

if __name__ == "__main__":
    success = test_sftp_connection()
    sys.exit(0 if success else 1)

