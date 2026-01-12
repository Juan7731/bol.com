# Instruções para Corrigir Upload SFTP

## Problema Identificado

O upload de arquivos CSV e labels PDF para o servidor SFTP está falhando com erro de autenticação:
```
❌ Erro de autenticação SFTP: Authentication failed.
```

## Correções Implementadas

✅ **Código atualizado para usar credenciais do `system_config.json`**
- O código agora tenta usar as credenciais do `system_config.json` primeiro
- Se não encontrar, usa as credenciais do `config.py` como fallback

✅ **Melhor tratamento de erros**
- Logs mais detalhados
- Mensagens de erro mais claras

✅ **Diretório de labels adicionado ao `system_config.json`**
- Campo `remote_label_dir` adicionado

## Verificação de Credenciais

### 1. Verificar Credenciais no system_config.json

As credenciais estão em `/home/triviumecom/projects/bol/bol.com/system_config.json`:

```json
{
  "ftp": {
    "host": "triviu.ssh.transip.me",
    "port": 22,
    "username": "trivium-ecommercecom",
    "password": "&9z?8zcN&9z?8zcN",
    "remote_batch_dir": "/data/sites/web/trivium-ecommercecom/FTP/Batches",
    "remote_label_dir": "/data/sites/web/trivium-ecommercecom/FTP/Label",
    "remote_callback_dir": "/data/sites/web/trivium-ecommercecom/FTP/Callbacks"
  }
}
```

### 2. Testar Conexão Manualmente

Teste a conexão SFTP manualmente para verificar se as credenciais estão corretas:

```bash
# Teste via linha de comando
sftp trivium-ecommercecom@triviu.ssh.transip.me

# Ou usando o script de teste
cd /home/triviumecom/projects/bol/bol.com
python3 test_sftp_fix.py
```

### 3. Verificar Senha

A senha contém caracteres especiais: `&9z?8zcN&9z?8zcN`

**Importante**: Certifique-se de que:
- A senha está correta no `system_config.json`
- Não há espaços extras no início ou fim
- Os caracteres especiais (`&`, `?`) estão corretos

### 4. Possíveis Soluções

#### Solução 1: Verificar se a senha está correta

1. Acesse o painel de controle do servidor TransIP
2. Verifique a senha SFTP atual
3. Atualize o `system_config.json` se necessário

#### Solução 2: Resetar senha SFTP

Se a senha estiver incorreta:
1. Acesse o painel TransIP
2. Gere uma nova senha SFTP
3. Atualize o `system_config.json` com a nova senha

#### Solução 3: Verificar se a conta está ativa

1. Verifique se a conta SFTP está ativa no painel TransIP
2. Verifique se não há restrições de IP
3. Verifique se a conta não está bloqueada

## Como Atualizar Credenciais

### Opção 1: Editar system_config.json diretamente

```bash
nano /home/triviumecom/projects/bol/bol.com/system_config.json
```

Edite a seção `ftp` com as credenciais corretas.

### Opção 2: Usar config_manager.py

```python
from config_manager import load_config, save_config

config = load_config()
config['ftp']['password'] = 'nova_senha_aqui'
save_config(config)
```

## Teste Após Correção

Após atualizar as credenciais, teste novamente:

```bash
# Teste de conexão
python3 test_sftp_fix.py

# Teste de upload manual
python3 upload_existing_files.py all
```

## Status Atual

- ✅ **Código corrigido**: Usa credenciais do `system_config.json`
- ✅ **Tratamento de erros melhorado**: Logs mais detalhados
- ❌ **Autenticação falhando**: Credenciais precisam ser verificadas/corrigidas

## Próximos Passos

1. **Verificar credenciais SFTP** no painel TransIP
2. **Atualizar `system_config.json`** com credenciais corretas
3. **Testar conexão** com `test_sftp_fix.py`
4. **Testar upload** com `upload_existing_files.py all`

## Nota Importante

Os arquivos CSV e labels PDF estão sendo gerados corretamente localmente. O único problema é o upload para o servidor SFTP devido à autenticação. Após corrigir as credenciais, o upload funcionará automaticamente.

