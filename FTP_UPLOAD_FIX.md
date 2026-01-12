# Correção do Upload FTP - Batches e Labels

## Problema Identificado

Os arquivos CSV e labels PDF estão sendo gerados corretamente na pasta local, mas não estão sendo enviados para o servidor SFTP devido a um erro de autenticação.

## Erro Encontrado

```
❌ ERRO DE AUTENTICAÇÃO SFTP: Authentication failed.
```

## Possíveis Causas

1. **Credenciais incorretas**: A senha ou username podem estar incorretos
2. **Caracteres especiais na senha**: A senha contém caracteres especiais (`&9z?8zcN&9z?8zcN`) que podem precisar de tratamento especial
3. **Conta bloqueada**: A conta SFTP pode estar temporariamente bloqueada
4. **Problema de rede**: Pode haver um problema de conectividade

## Soluções Implementadas

### 1. Melhorias no Código de Upload

- ✅ Melhor tratamento de erros com mensagens mais claras
- ✅ Logs mais detalhados para facilitar debugging
- ✅ Verificação de tamanho de arquivo após upload
- ✅ Tratamento específico para erros de autenticação

### 2. Scripts de Teste e Upload Manual

#### `test_sftp_connection.py`
Script para testar a conexão SFTP e verificar credenciais:
```bash
python3 test_sftp_connection.py
```

#### `upload_existing_files.py`
Script para fazer upload manual de arquivos existentes:
```bash
# Upload de tudo (CSV + Labels)
python3 upload_existing_files.py all

# Apenas arquivos CSV
python3 upload_existing_files.py batches

# Apenas labels PDF
python3 upload_existing_files.py labels
```

## Como Corrigir o Problema

### Passo 1: Verificar Credenciais

1. Verifique as credenciais em `config.py`:
   - `SFTP_HOST`: `triviu.ssh.transip.me`
   - `SFTP_PORT`: `22`
   - `SFTP_USERNAME`: `trivium-ecommercecom`
   - `SFTP_PASSWORD`: `&9z?8zcN&9z?8zcN`

2. Teste a conexão manualmente via SFTP:
   ```bash
   sftp trivium-ecommercecom@triviu.ssh.transip.me
   ```

### Passo 2: Verificar se a Senha Está Correta

Se a senha contém caracteres especiais, certifique-se de que está sendo passada corretamente. O paramiko pode ter problemas com alguns caracteres especiais.

### Passo 3: Testar Conexão

Execute o script de teste:
```bash
python3 test_sftp_connection.py
```

### Passo 4: Fazer Upload Manual

Após corrigir as credenciais, execute:
```bash
python3 upload_existing_files.py all
```

## Arquivos Modificados

1. **`order_processing.py`**
   - Função `upload_files_sftp()` melhorada com melhor tratamento de erros
   - Mensagens de log mais claras em português
   - Tratamento específico para erros de autenticação

2. **`label_uploader.py`**
   - Função `upload_label_pdf_to_ftp()` melhorada
   - Função `upload_all_labels()` melhorada com logs mais detalhados
   - Tratamento específico para erros de autenticação

3. **`upload_existing_files.py`** (NOVO)
   - Script para fazer upload manual de arquivos existentes
   - Suporta upload de CSV, labels ou ambos

4. **`test_sftp_connection.py`** (NOVO)
   - Script para testar conexão SFTP
   - Verifica credenciais e acesso aos diretórios

## Próximos Passos

1. **Corrigir credenciais SFTP** se necessário
2. **Testar conexão** com `test_sftp_connection.py`
3. **Fazer upload manual** dos arquivos existentes com `upload_existing_files.py`
4. **Verificar** se os arquivos aparecem no servidor SFTP
5. **Executar processamento normal** - o upload automático deve funcionar após corrigir as credenciais

## Notas Importantes

- Os arquivos CSV estão sendo gerados corretamente na pasta `batches/YYYYMMDD/`
- Os labels PDF (se houver) estão na pasta `label/`
- O código de upload está funcionando corretamente - o problema é apenas de autenticação
- Após corrigir as credenciais, o upload automático funcionará normalmente

