# 🚀 Production Deployment Guide

Este guia explica como executar o sistema de processamento de pedidos em **modo PRODUÇÃO**.

## ⚠️ Importante

**MODO PRODUÇÃO processa pedidos REAIS da Bol.com!**
- Gera etiquetas de envio reais
- Faz upload de arquivos CSV para o servidor SFTP
- Envia emails de notificação
- Marca pedidos como processados no banco de dados

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências instaladas**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuração correta** em `system_config.json`:
   - Contas Bol.com ativas (`"active": true`)
   - Credenciais corretas
   - `"test_mode": false` (já configurado)

## 🎯 Comando Único para Produção

### Windows (Recomendado)

**Duplo clique no arquivo:**
```
run_production.bat
```

**Ou execute no CMD/PowerShell:**
```cmd
run_production.bat
```

### Linux/Mac

```bash
python run_production.py
```

## 📝 O que o Script Faz

1. ✅ Verifica se há contas ativas configuradas
2. ✅ Processa pedidos de cada conta (Jean e Trivium)
3. ✅ Gera arquivos CSV com nomes de shop corretos
4. ✅ Baixa etiquetas de envio (PDF) reais
5. ✅ Faz upload de arquivos CSV para SFTP
6. ✅ Faz upload de etiquetas PDF para SFTP
7. ✅ Envia email de resumo
8. ✅ Marca pedidos como processados

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
- `"active": true` - Conta será processada
- `"active": false` - Conta será ignorada
- `"test_mode": false` - Modo PRODUÇÃO (pedidos reais)

## 📊 Saída Esperada

```
================================================================================
PRODUCTION MODE - Multi-Account Order Processing
================================================================================
⚠️  Running in PRODUCTION mode - real orders will be processed!
================================================================================

Found 2 active account(s):
  - Jean
  - Trivium

Processing account: Jean (Shop: Jean) - PRODUCTION MODE
...
✅ Successfully processed 5 orders for Jean

Processing account: Trivium (Shop: Trivium) - PRODUCTION MODE
...
✅ Successfully processed 6 orders for Trivium

================================================================================
PRODUCTION PROCESSING COMPLETE
================================================================================
  Accounts processed: 2
  Total orders processed: 11
================================================================================
✅ All accounts processed successfully
```

## 📁 Arquivos Gerados

Os arquivos CSV são salvos em:
```
batches/YYYYMMDD/S-001.csv
batches/YYYYMMDD/SL-001.csv
batches/YYYYMMDD/M-001.csv
```

As etiquetas PDF são salvas em:
```
label/{shipping-label-id}.pdf
```

## 🔍 Verificação

Após executar, verifique:

1. **Arquivos CSV gerados** na pasta `batches/`
2. **Etiquetas PDF baixadas** na pasta `label/`
3. **Upload SFTP bem-sucedido** (verifique logs)
4. **Email de resumo enviado** (verifique caixa de entrada)

## ⚠️ Troubleshooting

### Erro: "No active Bol.com accounts found"
- Verifique `system_config.json`
- Certifique-se de que pelo menos uma conta tem `"active": true`

### Erro: "Python is not installed"
- Instale Python 3.8+ do site oficial
- Adicione Python ao PATH do sistema

### Erro: "API request failed"
- Verifique credenciais em `system_config.json`
- Verifique conexão com internet
- Verifique se a API da Bol.com está disponível

### Erro: "SFTP upload failed"
- Verifique credenciais SFTP em `system_config.json`
- Verifique conexão com servidor SFTP
- Verifique se o diretório remoto existe

## 🔄 Agendamento Automático (Opcional)

Para executar automaticamente, use o Agendador de Tarefas do Windows:

1. Abra "Agendador de Tarefas"
2. Crie nova tarefa
3. Ação: Executar `run_production.bat`
4. Configure horários (ex: 08:00 e 15:01)

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs no console
2. Verifique arquivos de configuração
3. Teste conexão com API e SFTP

---

**Última atualização:** 2025-12-19

