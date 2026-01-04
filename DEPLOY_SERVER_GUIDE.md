# 🚀 Guia de Deploy no Servidor VPS

## Problema Identificado

O erro "No module named" indica que os módulos Python não estão sendo encontrados no servidor. Isso acontece porque:
1. Os arquivos podem não estar no mesmo diretório
2. O Python não está encontrando os módulos locais
3. Falta configuração do PYTHONPATH

## ✅ Solução Completa

### 1. Estrutura de Arquivos no Servidor

Todos os arquivos Python devem estar no MESMO diretório:

```
/root/bol.com/  (ou seu diretório)
├── run_realtime_monitor.py
├── multi_account_processor.py
├── order_processing.py
├── config_manager.py
├── bol_api_client.py
├── bol_dtos.py
├── order_database.py
├── label_uploader.py
├── system_config.json
├── config.py
├── bol_orders.db
├── batches/
└── label/
```

### 2. Verificar Arquivos no Servidor

```bash
# Entre no diretório
cd /root/bol.com

# Liste todos os arquivos Python
ls -la *.py

# Deve mostrar TODOS estes arquivos:
# - run_realtime_monitor.py
# - multi_account_processor.py
# - order_processing.py
# - config_manager.py
# - bol_api_client.py
# - bol_dtos.py
# - order_database.py
# - label_uploader.py
# - config.py
```

### 3. Testar Importações

```bash
# Execute o script de teste
python3 test_imports.py

# Deve mostrar:
# ✅ config_manager
# ✅ order_processing
# ✅ multi_account_processor
# ✅ bol_api_client
# ✅ bol_dtos
# ✅ order_database
```

### 4. Verificar system_config.json

```bash
# Verificar se o arquivo existe
cat system_config.json

# Deve mostrar as configurações com:
# - "active": true para ambas as contas
# - processing_times configurados
```

### 5. Executar o Processador

```bash
# Execute a partir do diretório correto
cd /root/bol.com
python3 run_realtime_monitor.py
```

## 🔧 Comandos de Deploy

### Upload de Arquivos via SFTP

```bash
# Conectar via SFTP
sftp trivium-ecommercecom@triviu.ssh.transip.me

# Entrar no diretório
cd /data/sites/web/trivium-ecommercecom/bol-order-processor

# Upload de todos os arquivos Python
put run_realtime_monitor.py
put multi_account_processor.py
put order_processing.py
put config_manager.py
put bol_api_client.py
put bol_dtos.py
put order_database.py
put label_uploader.py
put config.py
put system_config.json
put test_imports.py
```

### Ou usar o script de deploy

```bash
# No Windows
deploy_to_sftp.bat

# Verifica e faz upload de todos os arquivos
```

## 🐛 Troubleshooting

### Erro: "No module named 'multi_account_processor'"

**Causa**: Arquivo não está no diretório ou PYTHONPATH incorreto

**Solução**:
```bash
# Verificar se o arquivo existe
ls -la multi_account_processor.py

# Se não existir, fazer upload
# Se existir, adicionar diretório ao PYTHONPATH
export PYTHONPATH="/root/bol.com:$PYTHONPATH"
python3 run_realtime_monitor.py
```

### Erro: "No active accounts"

**Causa**: system_config.json não tem contas ativas

**Solução**:
```bash
# Editar o arquivo
nano system_config.json

# Garantir que ambas as contas tenham:
# "active": true
```

### Erro: "Configuration loading error"

**Causa**: system_config.json não existe ou está corrompido

**Solução**:
```bash
# Verificar se existe
cat system_config.json

# Se estiver corrompido, fazer upload novamente
```

## 📝 Checklist de Deploy

- [ ] Todos os arquivos .py estão no servidor
- [ ] system_config.json está no servidor
- [ ] Ambas as contas têm "active": true
- [ ] test_imports.py executa sem erros
- [ ] Diretórios batches/ e label/ existem
- [ ] Permissões de escrita nos diretórios
- [ ] Python 3.8+ instalado
- [ ] Dependências instaladas (paramiko, requests, etc.)

## 🚀 Executar em Background

### Opção 1: nohup

```bash
cd /root/bol.com
nohup python3 run_realtime_monitor.py > monitor.log 2>&1 &

# Ver o PID
echo $!

# Ver os logs
tail -f monitor.log
```

### Opção 2: screen

```bash
# Criar sessão
screen -S bol_monitor

# Executar
cd /root/bol.com
python3 run_realtime_monitor.py

# Desconectar: Ctrl+A, depois D

# Reconectar
screen -r bol_monitor
```

### Opção 3: systemd service

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/bol-processor.service
```

Conteúdo:
```ini
[Unit]
Description=Bol.com Order Processor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bol.com
ExecStart=/usr/bin/python3 /root/bol.com/run_realtime_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl enable bol-processor
sudo systemctl start bol-processor
sudo systemctl status bol-processor
```

## 📊 Monitorar Logs

```bash
# Ver logs em tempo real
tail -f monitor.log

# Ver últimas 100 linhas
tail -n 100 monitor.log

# Procurar por erros
grep ERROR monitor.log
grep "❌" monitor.log
```

## ✅ Verificação Final

Após o deploy, você deve ver nos logs:

```
📁 Current working directory: /root/bol.com
📁 Script directory: /root/bol.com
✅ Loaded 2 account(s) from config
✅ 2 account(s) marked as active
✅ Found 2 active account(s): ['Jean', 'Trivium']
================================================================================
SCHEDULED ORDER PROCESSOR - Multi-Account Processing
================================================================================
⚠️  Running in PRODUCTION mode
📅 Processing times (auto-run):
   1. 08:00
   2. 15:01
   3. 16:01
   4. 17:01
   5. 18:01

ℹ️  The system will process BOTH accounts (Jean & Trivium) at these times
```

Se você ver "0 account(s)", há um problema de configuração.
Se você ver "No module named", há um problema de importação.

