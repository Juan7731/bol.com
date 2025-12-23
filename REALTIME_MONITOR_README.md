# ⏰ Real-Time Order Monitor - Multi-Account

Sistema de monitoramento em tempo real que verifica novos pedidos a cada minuto e processa automaticamente.

## 🎯 Recursos

- ✅ **Monitoramento contínuo** - Verifica novos pedidos a cada 60 segundos
- ✅ **Multi-conta** - Processa Jean e Trivium automaticamente
- ✅ **Modo produção** - Processa pedidos reais
- ✅ **Processamento automático** - Gera CSVs, baixa etiquetas, faz upload
- ✅ **Um único comando** - Execute e deixe rodando
- ✅ **Shutdown gracioso** - Ctrl+C para parar com segurança

## 🚀 Comando Único

### Windows (Recomendado)

**Duplo clique no arquivo:**
```
run_realtime_monitor.bat
```

**Ou execute no CMD/PowerShell:**
```cmd
run_realtime_monitor.bat
```

### Linux/Mac

```bash
python run_realtime_monitor.py
```

## 📝 Como Funciona

1. **Inicialização**
   - Carrega configuração de `system_config.json`
   - Verifica contas ativas (Jean e Trivium)
   - Entra em loop de monitoramento

2. **A cada minuto (60 segundos)**
   - Verifica conta Jean para novos pedidos
   - Verifica conta Trivium para novos pedidos
   - Se encontrar pedidos novos:
     - Gera arquivos CSV com shop names corretos
     - Baixa etiquetas de envio (PDF)
     - Faz upload de CSVs para SFTP
     - Faz upload de etiquetas para SFTP
     - Envia email de resumo
     - Marca pedidos como processados

3. **Loop contínuo**
   - Aguarda 60 segundos
   - Repete processo
   - Continua até Ctrl+C

## 📊 Saída Esperada

```
================================================================================
REAL-TIME ORDER MONITOR - Multi-Account Processing
================================================================================
⚠️  Running in PRODUCTION mode
⏰  Checking for new orders every 60 seconds
⌨️  Press Ctrl+C to stop
================================================================================

────────────────────────────────────────────────────────────────────────────────
CHECK #1 - 2025-12-21 10:00:00
────────────────────────────────────────────────────────────────────────────────
Checking account: Jean (Shop: Jean)
ℹ️  No new orders for Jean

Checking account: Trivium (Shop: Trivium)
✅ Processed 3 order(s) for Trivium

✅ Check #1 complete: 3 order(s) processed
📊 Total orders processed since start: 3

⏳ Next check in 60 seconds... (Ctrl+C to stop)

────────────────────────────────────────────────────────────────────────────────
CHECK #2 - 2025-12-21 10:01:00
────────────────────────────────────────────────────────────────────────────────
Checking account: Jean (Shop: Jean)
ℹ️  No new orders for Jean

Checking account: Trivium (Shop: Trivium)
ℹ️  No new orders for Trivium

ℹ️  Check #2 complete: No new orders
📊 Total orders processed since start: 3

⏳ Next check in 60 seconds... (Ctrl+C to stop)
```

## ⏹️ Parar o Monitor

Para parar o monitor com segurança:

1. Pressione **Ctrl+C** na janela do terminal
2. O script finalizará a verificação atual
3. Mostrará resumo final:
   ```
   ================================================================================
   REAL-TIME MONITOR STOPPED
   ================================================================================
     Total checks performed: 45
     Total orders processed: 127
   ================================================================================
   ```

## 🔧 Configuração

### Arquivo: `system_config.json`

```json
{
  "bol_accounts": [
    {
      "name": "Jean",
      "client_id": "...",
      "client_secret": "...",
      "active": true
    },
    {
      "name": "Trivium",
      "client_id": "...",
      "client_secret": "...",
      "active": true
    }
  ],
  "test_mode": false
}
```

**Importante:**
- `"active": true` - Conta será monitorada
- `"active": false` - Conta será ignorada
- `"test_mode": false` - Modo PRODUÇÃO

## 📁 Arquivos Gerados

### CSVs (a cada processamento):
```
batches/YYYYMMDD/S-001.csv  (primeira execução do dia)
batches/YYYYMMDD/S-002.csv  (segunda execução)
batches/YYYYMMDD/SL-001.csv
...
```

### Etiquetas PDF:
```
label/{shipping-label-id}.pdf
```

## 🎯 Casos de Uso

### 1. Monitoramento contínuo durante horário comercial
```cmd
REM Iniciar às 8h da manhã
run_realtime_monitor.bat

REM Deixar rodando até 18h
REM Pressionar Ctrl+C para parar
```

### 2. Monitoramento 24/7
```cmd
REM Executar como serviço do Windows
REM Ou deixar rodando continuamente em servidor
run_realtime_monitor.bat
```

### 3. Teste rápido
```cmd
REM Rodar por alguns minutos para testar
run_realtime_monitor.bat
REM Ctrl+C após alguns checks
```

## ⚠️ Importante

### Desempenho
- O script verifica pedidos a cada 60 segundos
- Cada verificação leva ~2-5 segundos por conta
- Uso de memória: ~50-100 MB
- Uso de CPU: Baixo (apenas durante verificações)

### Banco de Dados
- Pedidos processados são salvos em `bol_orders.db`
- Previne processamento duplicado
- Arquivo cresce ~1 KB por 10 pedidos

### Upload SFTP
- Cada pedido processado gera upload de CSV e PDF
- Conexão SFTP é aberta/fechada a cada verificação
- Falhas de upload são logadas mas não param o monitor

### Email
- Um email é enviado por conta com pedidos novos
- Se nenhum pedido novo, não envia email
- Falha de email não para o processamento

## ⚠️ Troubleshooting

### Monitor não inicia
- Verifique se Python está instalado
- Verifique dependências: `pip install -r requirements.txt`
- Verifique `system_config.json` existe

### Monitor para sozinho
- Verifique logs para erros
- Verifique conexão com API Bol.com
- Verifique conexão com SFTP

### Pedidos não são processados
- Verifique se contas estão `"active": true`
- Verifique credenciais das contas
- Verifique se pedidos são realmente novos (não processados antes)

### Monitor muito lento
- Normal: cada verificação leva alguns segundos
- Se muito lento (>30s por verificação), verifique:
  - Conexão com internet
  - Resposta da API Bol.com
  - Conexão SFTP

## 🔄 Diferença vs Execução Única

| Característica | Execução Única (`run_production.bat`) | Monitor em Tempo Real (`run_realtime_monitor.bat`) |
|---|---|---|
| Execução | Uma vez, depois para | Contínua (loop infinito) |
| Frequência | Manual (quando você executar) | Automática (a cada 60s) |
| Parar | Automático após processar | Manual (Ctrl+C) |
| Uso | Processamento sob demanda | Monitoramento contínuo |

## 📞 Suporte

Em caso de problemas:
1. Verifique logs no console
2. Verifique arquivos de configuração
3. Teste conexão com API e SFTP
4. Verifique se há pedidos novos realmente

## 🚀 Executar como Serviço do Windows (Opcional)

Para rodar 24/7 como serviço:

1. Use **NSSM** (Non-Sucking Service Manager)
2. Instale o serviço:
   ```cmd
   nssm install BolOrderMonitor "C:\xampp\htdocs\github\run_realtime_monitor.bat"
   ```
3. Configure para iniciar automaticamente
4. Inicie o serviço:
   ```cmd
   net start BolOrderMonitor
   ```

---

**Última atualização:** 2025-12-21

