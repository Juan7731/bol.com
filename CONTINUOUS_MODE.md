# Modo Contínuo de Processamento

## Mudanças Implementadas

O projeto foi modificado para rodar **continuamente sem verificação de horários**, ideal para execução em servidor.

### O que mudou:

1. **Modo Contínuo (Padrão)**: O processamento roda continuamente, verificando novos pedidos a cada intervalo configurado
2. **Sem verificação de horários**: Não precisa mais esperar horários específicos
3. **Configurável**: Intervalo de verificação pode ser ajustado em `config.py`

## Configuração

### Intervalo de Processamento

No arquivo `config.py`, configure o intervalo:

```python
# Intervalo em segundos (padrão: 300 = 5 minutos)
PROCESS_INTERVAL = 300  # 5 minutos
```

### Opções de Execução

#### 1. Modo Contínuo (Padrão - Recomendado para Servidor)
```bash
python3 order_processing.py
# ou
python3 order_processing.py --continuous
# ou
python3 order_processing.py -c
```

Roda continuamente, verificando novos pedidos a cada `PROCESS_INTERVAL` segundos.

#### 2. Execução Única
```bash
python3 order_processing.py --once
# ou
python3 order_processing.py -o
```

Executa um único ciclo de processamento e encerra.

#### 3. Modo Scheduler (Baseado em Horários)
```bash
python3 order_processing.py --scheduler
# ou
python3 order_processing.py -s
```

Roda baseado nos horários configurados em `PROCESS_TIMES` (modo antigo).

#### 4. Script de Inicialização
```bash
chmod +x start_processing.sh
./start_processing.sh
```

## Execução no Servidor

### Opção 1: Executar Diretamente
```bash
cd /home/triviumecom/projects/bol/bol.com
python3 order_processing.py
```

### Opção 2: Usar o Script
```bash
cd /home/triviumecom/projects/bol/bol.com
chmod +x start_processing.sh
./start_processing.sh
```

### Opção 3: Usar nohup (executar em background)
```bash
cd /home/triviumecom/projects/bol/bol.com
nohup python3 order_processing.py > processing.log 2>&1 &
```

### Opção 4: Usar systemd (Recomendado para Produção)

Crie um arquivo `/etc/systemd/system/bol-processing.service`:

```ini
[Unit]
Description=Bol.com Order Processing Service
After=network.target

[Service]
Type=simple
User=triviumecom
WorkingDirectory=/home/triviumecom/projects/bol/bol.com
ExecStart=/usr/bin/python3 /home/triviumecom/projects/bol/bol.com/order_processing.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Depois:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bol-processing
sudo systemctl start bol-processing
sudo systemctl status bol-processing
```

## Logs

Os logs são exibidos no console. Para salvar em arquivo:

```bash
python3 order_processing.py 2>&1 | tee processing.log
```

Ou com nohup:
```bash
nohup python3 order_processing.py > processing.log 2>&1 &
tail -f processing.log
```

## Parar o Processamento

- **Console**: Pressione `Ctrl+C`
- **Background**: Use `kill` ou `systemctl stop bol-processing`

## Vantagens do Modo Contínuo

✅ **Sem espera por horários**: Processa pedidos assim que aparecem  
✅ **Ideal para servidor**: Roda 24/7 sem intervenção  
✅ **Configurável**: Ajuste o intervalo conforme necessário  
✅ **Resiliente**: Continua rodando mesmo após erros  
✅ **Logs detalhados**: Acompanhe cada execução  

## Exemplo de Saída

```
================================================================================
🚀 Modo Contínuo de Processamento
================================================================================
Intervalo de verificação: 300 segundos (5.0 minutos)
O processamento rodará continuamente, verificando novos pedidos a cada intervalo
Pressione Ctrl+C para parar
================================================================================

================================================================================
🔄 Execução #1 - 2026-01-05 12:00:00
================================================================================
Starting Bol.com order processing run...
Processing 5 new orders (filtered from 10 total)
...
Processing run completed. Orders processed: 5

⏳ Aguardando 300 segundos até próxima verificação...
```

## Notas Importantes

- O processamento verifica apenas pedidos **não processados** (evita duplicatas)
- Arquivos CSV são gerados na pasta `batches/YYYYMMDD/`
- Labels PDF são salvos na pasta `label/`
- Uploads para SFTP são feitos automaticamente após geração
- Emails de resumo são enviados após cada processamento

