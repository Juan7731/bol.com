# 🚀 Deploy Codebase to SFTP Server

Este guia explica como fazer deploy do código para o servidor SFTP usando o terminal/console.

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências instaladas**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuração SFTP** em `system_config.json` (já configurado)

## 🎯 Comando Único para Deploy

### Windows (Recomendado)

**Duplo clique no arquivo:**
```
deploy_to_sftp.bat
```

**Ou execute no CMD/PowerShell:**
```cmd
deploy_to_sftp.bat
```

### Linux/Mac ou Terminal Python

```bash
python deploy_to_sftp.py
```

## 📝 O que o Script Faz

1. ✅ Carrega configuração SFTP de `system_config.json`
2. ✅ Escaneia arquivos do projeto
3. ✅ Exclui arquivos desnecessários:
   - `__pycache__/`, `*.pyc` (arquivos compilados)
   - `batches/`, `label/` (dados locais)
   - `*.db` (banco de dados local)
   - Arquivos de teste (`test_*.py`, `debug_*.py`)
   - Documentação (`*.md`, `*.txt`)
   - Scripts antigos e temporários
4. ✅ Inclui arquivos essenciais:
   - Todos os arquivos `.py` principais
   - `requirements.txt`
   - `system_config.json`
   - `config.py`
   - `run_production.py`
5. ✅ Cria estrutura de diretórios no servidor
6. ✅ Faz upload de todos os arquivos
7. ✅ Verifica upload bem-sucedido

## 📁 Diretório Remoto

Os arquivos serão enviados para:
```
/data/sites/web/trivium-ecommercecom/bol-order-processor/
```

## 📊 Arquivos Incluídos no Deploy

### ✅ Incluídos:
- `bol_api_client.py`
- `bol_dtos.py`
- `config.py`
- `config_manager.py`
- `label_uploader.py`
- `multi_account_processor.py`
- `order_database.py`
- `order_processing.py`
- `run_production.py`
- `status_callback_handler.py`
- `requirements.txt`
- `system_config.json`

### ❌ Excluídos:
- `__pycache__/` - Arquivos compilados Python
- `batches/` - Dados locais de processamento
- `label/` - PDFs de etiquetas locais
- `*.db` - Banco de dados local
- `test_*.py` - Scripts de teste
- `debug_*.py` - Scripts de debug
- `*.md`, `*.txt` - Documentação
- `*.bat` - Scripts batch locais
- `admin/` - Painel admin PHP

## 🔍 Verificação

Após o deploy, você pode verificar os arquivos no servidor:

1. **Conecte-se via SFTP** ao servidor
2. **Navegue até**: `/data/sites/web/trivium-ecommercecom/bol-order-processor/`
3. **Verifique** se todos os arquivos foram enviados

## ⚠️ Troubleshooting

### Erro: "Failed to load SFTP config"
- Verifique se `system_config.json` existe
- Verifique se a seção `ftp` está configurada

### Erro: "SFTP connection failed"
- Verifique credenciais em `system_config.json`
- Verifique conexão com internet
- Verifique se o servidor SFTP está acessível

### Erro: "Failed to create remote directory"
- Verifique permissões no servidor SFTP
- Verifique se o usuário tem permissão para criar diretórios

### Erro: "No files to deploy"
- Verifique se você está no diretório correto do projeto
- Verifique se há arquivos Python no projeto

## 🔄 Deploy Incremental

O script faz deploy de **todos os arquivos** a cada execução. Se você modificou apenas alguns arquivos, o script ainda funcionará, mas pode demorar mais.

## 📞 Próximos Passos Após Deploy

Após fazer deploy:

1. **Conecte-se ao servidor** via SSH
2. **Navegue até o diretório**:
   ```bash
   cd /data/sites/web/trivium-ecommercecom/bol-order-processor
   ```
3. **Instale dependências** (se necessário):
   ```bash
   pip install -r requirements.txt
   ```
4. **Teste o script**:
   ```bash
   python run_production.py
   ```

## 🔐 Segurança

⚠️ **IMPORTANTE**: O script faz upload de `system_config.json` e `config.py` que contêm credenciais sensíveis. Certifique-se de que:
- O servidor SFTP está seguro
- As permissões de arquivo estão corretas
- Apenas usuários autorizados têm acesso

---

**Última atualização:** 2025-12-21

