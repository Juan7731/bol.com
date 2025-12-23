# 🚀 Guia Rápido - Sistema de Processamento de Pedidos Bol.com

## 📋 Comandos Disponíveis

### ⏰ MONITOR EM TEMPO REAL (Recomendado para uso diário)
**Verifica novos pedidos a cada minuto automaticamente**

```cmd
run_realtime_monitor.bat
```

✅ Processa ambas as contas (Jean e Trivium)  
✅ Verifica novos pedidos a cada 60 segundos  
✅ Processamento automático  
✅ Modo PRODUÇÃO  
⏹️ Pressione Ctrl+C para parar  

---

### 🎯 PROCESSAMENTO ÚNICO (Execução sob demanda)
**Processa pedidos uma vez e para**

```cmd
run_production.bat
```

✅ Processa ambas as contas (Jean e Trivium)  
✅ Executa uma vez  
✅ Modo PRODUÇÃO  
✅ Para automaticamente após processar  

---

### 🚀 DEPLOY PARA SERVIDOR SFTP
**Envia código para o servidor**

```cmd
deploy_to_sftp.bat
```

✅ Faz upload de todos os arquivos Python  
✅ Envia para `/data/sites/web/trivium-ecommercecom/bol-order-processor/`  
✅ Exclui arquivos desnecessários (testes, cache, etc.)  
✅ Verifica uploads bem-sucedidos  

---

## 🎯 Qual Comando Usar?

### Para uso diário/contínuo:
```cmd
run_realtime_monitor.bat
```
**Use este para monitoramento contínuo durante o dia.**

### Para processamento pontual:
```cmd
run_production.bat
```
**Use este quando quiser processar pedidos manualmente.**

### Para atualizar código no servidor:
```cmd
deploy_to_sftp.bat
```
**Use este após fazer alterações no código.**

---

## 📊 Comparação

| Recurso | Monitor em Tempo Real | Processamento Único |
|---------|----------------------|---------------------|
| **Execução** | Contínua (loop) | Uma vez |
| **Frequência** | A cada 60 segundos | Manual |
| **Parar** | Ctrl+C | Automático |
| **Uso** | Monitoramento diário | Sob demanda |
| **Contas** | Jean + Trivium | Jean + Trivium |
| **Modo** | PRODUÇÃO | PRODUÇÃO |

---

## 🔧 Configuração

### Ativar/Desativar Contas

Edite `system_config.json`:

```json
{
  "bol_accounts": [
    {
      "name": "Jean",
      "active": true    ← true = ativo, false = desativado
    },
    {
      "name": "Trivium",
      "active": true    ← true = ativo, false = desativado
    }
  ]
}
```

---

## 📁 Arquivos Gerados

### CSVs de Pedidos:
```
batches/20251221/S-001.csv     ← Pedidos single
batches/20251221/SL-001.csv    ← Pedidos single-line
batches/20251221/M-001.csv     ← Pedidos multi
```

### Etiquetas PDF:
```
label/7764dbd5-5129-4b4c-a722-89508b92c191.pdf
label/ada3c787-bd6c-48fd-892a-a714876dab4b.pdf
...
```

### Banco de Dados:
```
bol_orders.db                  ← Histórico de pedidos processados
```

---

## ⚠️ Troubleshooting

### Erro: "Python is not installed"
```cmd
# Baixe e instale Python 3.8+ de python.org
# Adicione ao PATH do sistema
```

### Erro: "No active accounts found"
```cmd
# Edite system_config.json
# Certifique-se de que pelo menos uma conta tem "active": true
```

### Erro: "SFTP connection failed"
```cmd
# Verifique credenciais em system_config.json
# Verifique conexão com internet
```

### Monitor muito lento
```cmd
# Normal: 2-5 segundos por verificação
# Se > 30 segundos, verifique conexão com API Bol.com
```

---

## 📖 Documentação Completa

- `PRODUCTION_README.md` - Guia de produção
- `REALTIME_MONITOR_README.md` - Guia de monitoramento em tempo real
- `DEPLOY_README.md` - Guia de deploy
- `README.md` - Documentação técnica completa

---

## 🚀 Início Rápido

1. **Primeira vez:**
   ```cmd
   # Instale dependências
   pip install -r requirements.txt
   ```

2. **Uso diário:**
   ```cmd
   # Inicie o monitor em tempo real
   run_realtime_monitor.bat
   
   # Deixe rodando
   # Pressione Ctrl+C quando quiser parar
   ```

3. **Verificar resultados:**
   - Veja CSVs em `batches/YYYYMMDD/`
   - Veja etiquetas em `label/`
   - Verifique logs no console

---

## 📞 Suporte

Em caso de problemas:
1. ✅ Verifique logs no console
2. ✅ Verifique `system_config.json`
3. ✅ Verifique conexão com internet
4. ✅ Teste API Bol.com manualmente

---

**Sistema pronto para uso! Execute `run_realtime_monitor.bat` para começar.**

