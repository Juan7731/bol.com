# Configuração de Múltiplas Contas

## Status Atual

✅ **Ambas as contas estão configuradas e ativas:**
- **Jean**: Ativa
- **Trivium**: Ativa

## Mudanças Implementadas

### 1. Processamento Automático de Múltiplas Contas

O `order_processing.py` foi modificado para processar **automaticamente todas as contas ativas** configuradas no `system_config.json`.

#### Como Funciona:

1. **Verifica contas ativas**: Lê o `system_config.json` para encontrar todas as contas marcadas como `"active": true`
2. **Processa cada conta**: Para cada conta ativa, processa pedidos separadamente
3. **Gera arquivos separados**: Cada conta gera seus próprios arquivos CSV com o nome da loja correto
4. **Fallback**: Se o multi-account processor não estiver disponível, usa a conta única do `config.py`

### 2. Configuração

As contas são configuradas no arquivo `system_config.json`:

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
  ]
}
```

### 3. Verificar Contas Ativas

Para verificar quais contas estão ativas:

```bash
python3 -c "from config_manager import get_active_bol_accounts; accounts = get_active_bol_accounts(); print(f'Contas ativas: {len(accounts)}'); [print(f\"  - {acc['name']}\") for acc in accounts]"
```

## Execução

### Modo Contínuo (Recomendado)

O processamento roda continuamente e processa **ambas as contas** automaticamente:

```bash
python3 order_processing.py
```

### Execução Única

Para processar uma vez:

```bash
python3 order_processing.py --once
```

## Logs de Execução

Quando o processamento detecta múltiplas contas, você verá:

```
Starting Bol.com order processing run...
📋 Encontradas 2 conta(s) ativa(s): ['Jean', 'Trivium']
🔄 Processando todas as contas ativas...
================================================================================
MULTI-ACCOUNT ORDER PROCESSING
================================================================================
Processing account: Jean (Shop: Jean)
...
Processing account: Trivium (Shop: Trivium)
...
================================================================================
✅ Processamento concluído para todas as contas
   Contas processadas: 2
   Total de pedidos processados: X
================================================================================
   ✅ Jean: X pedido(s) processado(s)
   ✅ Trivium: X pedido(s) processado(s)
```

## Arquivos Gerados

Cada conta gera seus próprios arquivos CSV na pasta `batches/YYYYMMDD/`:

- **Jean**: `S-001.csv`, `SL-001.csv`, `M-001.csv` (com Shop="Jean")
- **Trivium**: `S-001.csv`, `SL-001.csv`, `M-001.csv` (com Shop="Trivium")

**Nota**: Os arquivos de diferentes contas podem ter o mesmo nome de batch, mas o campo "Shop" no CSV identifica a loja correta.

## Ativar/Desativar Contas

Para ativar ou desativar uma conta, edite o `system_config.json`:

```json
{
  "bol_accounts": [
    {
      "name": "Jean",
      "active": true   // true = ativa, false = desativada
    },
    {
      "name": "Trivium",
      "active": true   // true = ativa, false = desativada
    }
  ]
}
```

Ou use o `config_manager.py`:

```python
from config_manager import update_bol_account

# Ativar conta Jean
update_bol_account("Jean", active=True)

# Desativar conta Trivium
update_bol_account("Trivium", active=False)
```

## Verificação

### Verificar se está processando ambas as contas:

1. **Execute o processamento**:
   ```bash
   python3 order_processing.py --once
   ```

2. **Verifique os logs** - deve mostrar:
   - "📋 Encontradas 2 conta(s) ativa(s)"
   - "Processing account: Jean"
   - "Processing account: Trivium"

3. **Verifique os arquivos gerados** - cada conta deve gerar seus próprios arquivos CSV

## Troubleshooting

### Problema: Apenas uma conta está sendo processada

**Solução**: Verifique se ambas as contas estão marcadas como `"active": true` no `system_config.json`

### Problema: Erro "Multi-account processor não disponível"

**Solução**: Verifique se os arquivos `config_manager.py` e `multi_account_processor.py` existem e estão acessíveis

### Problema: Arquivos CSV não mostram o nome da loja correto

**Solução**: O nome da loja é definido pelo campo `"name"` da conta no `system_config.json`. Certifique-se de que está como "Jean" ou "Trivium"

## Benefícios

✅ **Processamento Automático**: Ambas as contas são processadas automaticamente  
✅ **Sem Configuração Manual**: Usa o `system_config.json` para determinar quais contas processar  
✅ **Flexível**: Pode ativar/desativar contas facilmente  
✅ **Logs Claros**: Mostra claramente qual conta está sendo processada  
✅ **Fallback Seguro**: Se multi-account não funcionar, usa conta única como fallback  

