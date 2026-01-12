# Scripts que Executam Diretamente sem Verificação de Tempo

## Resumo da Verificação

Este documento lista os scripts que podem ser executados diretamente no servidor **sem verificação de tempo agendado**. Estes scripts processam pedidos imediatamente quando chamados.

## Scripts Identificados

### 1. `run_production.py`
**Localização:** `/home/triviumecom/projects/bol/bol.com/run_production.py`

**Descrição:**
- Executa processamento de pedidos em modo PRODUÇÃO
- Processa todas as contas ativas imediatamente
- **NÃO verifica horários agendados** - executa assim que chamado
- Usa `test_mode=False` (modo produção)

**Como é chamado:**
```bash
python3 run_production.py
# ou
python run_production.py
```

**Risco:** ⚠️ **ALTO** - Pode processar pedidos fora dos horários agendados se executado manualmente

---

### 2. `process_both_shops.py`
**Localização:** `/home/triviumecom/projects/bol/bol.com/process_both_shops.py`

**Descrição:**
- Processa pedidos de AMBAS as lojas (Jean e Trivium)
- Processa TODOS os pedidos abertos (não apenas novos)
- **NÃO verifica horários agendados** - executa assim que chamado
- Usa `process_all=True` (processa todos os pedidos abertos)

**Como é chamado:**
```bash
python3 process_both_shops.py
# ou
python process_both_shops.py
```

**Risco:** ⚠️ **ALTO** - Pode processar pedidos fora dos horários agendados se executado manualmente

---

### 3. `multi_account_processor.py`
**Localização:** `/home/triviumecom/projects/bol/bol.com/multi_account_processor.py`

**Descrição:**
- Processa pedidos de todas as contas ativas
- Quando executado diretamente (via `if __name__ == "__main__"`), chama `process_all_accounts()`
- **NÃO verifica horários agendados** - executa assim que chamado
- Filtra apenas pedidos não processados (não processa todos os abertos)

**Como é chamado:**
```bash
python3 multi_account_processor.py
# ou
python multi_account_processor.py
```

**Risco:** ⚠️ **MÉDIO** - Pode processar pedidos fora dos horários agendados, mas pelo menos filtra pedidos já processados

---

## Scripts com Verificação de Tempo (CORRETOS)

### `run_realtime_monitor.py` ✅
**Status:** Rodando no servidor (PID: 7448)

**Descrição:**
- Verifica horários agendados em `system_config.json`
- Processa pedidos APENAS nos horários configurados
- Loop contínuo verificando se é hora de processar
- **CORRETO** - tem verificação de tempo

**Horários configurados em `system_config.json`:**
- 02:00, 04:00, 06:00, 08:00, 15:01, 16:01, 17:01, 18:01, 20:01, 23:01

---

## Verificações Realizadas

### Processos em Execução
- ✅ `run_realtime_monitor.py` está rodando (PID 7448) - **CORRETO**
- ❌ Nenhum processo de `run_production.py` encontrado
- ❌ Nenhum processo de `process_both_shops.py` encontrado
- ❌ Nenhum processo de `multi_account_processor.py` encontrado

### Cron Jobs
- ❌ Nenhum crontab configurado para o usuário atual

### Systemd Services
- ❌ Nenhum serviço systemd configurado

---

## Recomendações

### 1. Proteger Scripts de Execução Direta
Adicionar verificação de tempo nos scripts que executam diretamente, ou adicionar um flag de confirmação:

```python
# Exemplo para run_production.py
import sys
from datetime import datetime

def check_scheduled_time():
    """Verifica se está em um horário agendado"""
    current_time = datetime.now().strftime("%H:%M")
    scheduled_times = ["02:00", "04:00", "06:00", "08:00", "15:01", "16:01", "17:01", "18:01", "20:01", "23:01"]
    return current_time in scheduled_times

if __name__ == "__main__":
    # Permitir execução direta apenas se for horário agendado ou com flag --force
    if "--force" not in sys.argv and not check_scheduled_time():
        print("⚠️  ATENÇÃO: Este script deve ser executado apenas nos horários agendados!")
        print("   Use --force para executar mesmo assim (não recomendado)")
        sys.exit(1)
    main()
```

### 2. Documentar Uso
Adicionar avisos claros nos scripts sobre quando devem ser executados.

### 3. Monitoramento
Verificar logs regularmente para detectar execuções não agendadas.

---

## Conclusão

**Status Atual:** ✅ **SEGURO**
- Apenas `run_realtime_monitor.py` está rodando no servidor
- Este script tem verificação de tempo correta
- Nenhum script sem verificação de tempo está sendo executado automaticamente

**Atenção:** Os scripts `run_production.py`, `process_both_shops.py` e `multi_account_processor.py` podem ser executados manualmente sem verificação de tempo. Certifique-se de que não há cron jobs ou outros agendadores configurados para executá-los diretamente.



