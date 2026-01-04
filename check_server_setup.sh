#!/bin/bash
# Script para verificar setup do servidor

echo "================================================================================"
echo "BOL.COM ORDER PROCESSOR - SERVER SETUP CHECK"
echo "================================================================================"
echo ""

# Verificar diretório atual
echo "📁 Current Directory:"
pwd
echo ""

# Verificar arquivos Python necessários
echo "📄 Checking Python Files:"
required_files=(
    "run_realtime_monitor.py"
    "multi_account_processor.py"
    "order_processing.py"
    "config_manager.py"
    "bol_api_client.py"
    "bol_dtos.py"
    "order_database.py"
    "config.py"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
        all_present=false
    fi
done
echo ""

# Verificar system_config.json
echo "⚙️  Checking Configuration:"
if [ -f "system_config.json" ]; then
    echo "  ✅ system_config.json exists"
    
    # Verificar se é JSON válido
    if python3 -c "import json; json.load(open('system_config.json'))" 2>/dev/null; then
        echo "  ✅ system_config.json is valid JSON"
        
        # Contar contas ativas
        active_count=$(python3 -c "import json; config=json.load(open('system_config.json')); print(sum(1 for acc in config.get('bol_accounts', []) if acc.get('active', False)))")
        echo "  ✅ Active accounts: $active_count"
    else
        echo "  ❌ system_config.json is INVALID JSON"
    fi
else
    echo "  ❌ system_config.json (MISSING)"
    all_present=false
fi
echo ""

# Verificar Python
echo "🐍 Checking Python:"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "  ✅ $python_version"
else
    echo "  ❌ Python 3 not found"
fi
echo ""

# Verificar diretórios
echo "📂 Checking Directories:"
for dir in "batches" "label"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ⚠️  $dir/ (creating...)"
        mkdir -p "$dir"
    fi
done
echo ""

# Verificar permissões
echo "🔐 Checking Permissions:"
if [ -w "." ]; then
    echo "  ✅ Write permission in current directory"
else
    echo "  ❌ No write permission in current directory"
fi
echo ""

# Testar importações Python
echo "🔬 Testing Python Imports:"
python3 -c "
import sys
try:
    import config_manager
    print('  ✅ config_manager')
except Exception as e:
    print(f'  ❌ config_manager: {e}')

try:
    import order_processing
    print('  ✅ order_processing')
except Exception as e:
    print(f'  ❌ order_processing: {e}')

try:
    import multi_account_processor
    print('  ✅ multi_account_processor')
except Exception as e:
    print(f'  ❌ multi_account_processor: {e}')
"
echo ""

# Resumo
echo "================================================================================"
if [ "$all_present" = true ]; then
    echo "✅ ALL CHECKS PASSED - Ready to run!"
    echo ""
    echo "To start the processor:"
    echo "  python3 run_realtime_monitor.py"
else
    echo "❌ SOME CHECKS FAILED - Please fix the issues above"
    echo ""
    echo "Missing files need to be uploaded to this directory"
fi
echo "================================================================================"

