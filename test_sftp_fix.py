"""
Script para testar e corrigir problemas de autenticação SFTP
"""

import paramiko
import sys
import json
import os

def test_sftp_with_config():
    """Testa conexão SFTP usando credenciais do system_config.json"""
    print("="*80)
    print("🔍 Teste de Conexão SFTP - system_config.json")
    print("="*80)
    
    # Load from system_config.json
    try:
        with open('system_config.json', 'r') as f:
            config = json.load(f)
        
        ftp_config = config.get('ftp', {})
        sftp_host = ftp_config.get('host')
        sftp_port = ftp_config.get('port', 22)
        sftp_username = ftp_config.get('username')
        sftp_password = ftp_config.get('password')
        
        print(f"Host: {sftp_host}")
        print(f"Port: {sftp_port}")
        print(f"Username: {sftp_username}")
        print(f"Password length: {len(sftp_password)} caracteres")
        print(f"Password (first 3 chars): {sftp_password[:3]}...")
        print("="*80)
        print()
        
        if not all([sftp_host, sftp_username, sftp_password]):
            print("❌ Credenciais incompletas no system_config.json")
            return False
        
        # Try connection
        print("📡 Conectando ao servidor SFTP...")
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.banner_timeout = 30
        transport.auth_timeout = 30
        
        print("🔐 Tentando autenticação...")
        try:
            transport.connect(username=sftp_username, password=sftp_password)
            print("✅ Autenticação bem-sucedida!")
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            print("✅ Cliente SFTP criado com sucesso")
            
            # Test directories
            print()
            print("📁 Testando acesso aos diretórios...")
            
            # Test Batches directory
            batch_dir = ftp_config.get('remote_batch_dir', '/data/sites/web/trivium-ecommercecom/FTP/Batches')
            try:
                sftp.chdir(batch_dir)
                print(f"✅ Diretório Batches acessível: {batch_dir}")
                files = sftp.listdir(".")
                print(f"   Arquivos encontrados: {len(files)}")
            except Exception as e:
                print(f"⚠️  Erro ao acessar diretório Batches: {e}")
            
            # Test Label directory
            label_dir = ftp_config.get('remote_label_dir', '/data/sites/web/trivium-ecommercecom/FTP/Label')
            try:
                sftp.chdir(label_dir)
                print(f"✅ Diretório Label acessível: {label_dir}")
                files = sftp.listdir(".")
                print(f"   Arquivos encontrados: {len(files)}")
            except Exception as e:
                print(f"⚠️  Erro ao acessar diretório Label: {e}")
            
            transport.close()
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
            print("1. Username ou senha incorretos no system_config.json")
            print("2. Caracteres especiais na senha podem precisar de escape")
            print("3. Conta pode estar bloqueada ou desabilitada")
            print()
            print("Sugestões:")
            print("- Verifique as credenciais no system_config.json")
            print("- Tente fazer login manual via SFTP para verificar")
            print("- Verifique se a senha contém caracteres especiais que precisam ser tratados")
            print("="*80)
            return False
            
    except FileNotFoundError:
        print("❌ Arquivo system_config.json não encontrado")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao ler system_config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_sftp_with_config()
    sys.exit(0 if success else 1)

