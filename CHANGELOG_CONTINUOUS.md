# Changelog - Modo Contínuo

## Data: 2026-01-05

### Mudanças Implementadas

#### 1. Modo Contínuo de Processamento
- ✅ Adicionado modo contínuo que roda sem verificação de horários
- ✅ Processamento verifica novos pedidos a cada intervalo configurável
- ✅ Ideal para execução em servidor 24/7

#### 2. Configuração
- ✅ Adicionado `PROCESS_INTERVAL` em `config.py` (padrão: 300 segundos = 5 minutos)
- ✅ Mantida compatibilidade com `PROCESS_TIMES` para modo scheduler

#### 3. Opções de Execução
- ✅ **Padrão**: Modo contínuo (sem argumentos)
- ✅ `--continuous, -c`: Modo contínuo explícito
- ✅ `--once, -o`: Execução única
- ✅ `--scheduler, -s`: Modo baseado em horários (antigo)
- ✅ `--help, -h`: Ajuda

#### 4. Scripts e Documentação
- ✅ Criado `start_processing.sh` para facilitar inicialização
- ✅ Criado `CONTINUOUS_MODE.md` com documentação completa
- ✅ Melhorado tratamento de erros e logs

### Arquivos Modificados

1. **config.py**
   - Adicionado `PROCESS_INTERVAL = 300`

2. **order_processing.py**
   - Adicionada função `run_continuous()`
   - Modificado `__main__` para suportar múltiplas opções
   - Melhorado tratamento de erros em modo contínuo

### Arquivos Criados

1. **start_processing.sh** - Script de inicialização
2. **CONTINUOUS_MODE.md** - Documentação completa
3. **CHANGELOG_CONTINUOUS.md** - Este arquivo

### Como Usar

#### Execução Simples (Recomendado)
```bash
python3 order_processing.py
```

#### Com Script
```bash
./start_processing.sh
```

#### Em Background
```bash
nohup python3 order_processing.py > processing.log 2>&1 &
```

### Benefícios

- ✅ **Sem espera**: Processa pedidos imediatamente
- ✅ **Automático**: Roda 24/7 sem intervenção
- ✅ **Configurável**: Ajuste o intervalo conforme necessário
- ✅ **Resiliente**: Continua após erros
- ✅ **Logs claros**: Acompanhe cada execução

### Compatibilidade

- ✅ Mantida compatibilidade com modo scheduler antigo
- ✅ Todas as funcionalidades existentes preservadas
- ✅ Uploads SFTP e emails continuam funcionando

