#!/bin/bash
# Script para iniciar o processamento de pedidos Bol.com em modo contínuo
# Uso: ./start_processing.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 Iniciando Processamento Bol.com"
echo "=========================================="
echo "Diretório: $SCRIPT_DIR"
echo "Modo: Contínuo (sem verificação de horários)"
echo "Pressione Ctrl+C para parar"
echo "=========================================="
echo ""

# Verificar se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: python3 não encontrado"
    exit 1
fi

# Verificar se o arquivo principal existe
if [ ! -f "order_processing.py" ]; then
    echo "❌ Erro: order_processing.py não encontrado"
    exit 1
fi

# Executar em modo contínuo
python3 order_processing.py --continuous

