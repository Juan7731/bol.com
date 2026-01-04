"""
Test script to verify all imports work correctly
"""
import sys
import os

print("=" * 80)
print("TESTING IMPORTS")
print("=" * 80)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print()

# Test each import
modules_to_test = [
    'config_manager',
    'order_processing',
    'multi_account_processor',
    'bol_api_client',
    'bol_dtos',
    'order_database',
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")

print()
print("=" * 80)
print("TESTING CONFIG LOADING")
print("=" * 80)

try:
    from config_manager import load_config, get_active_bol_accounts
    config = load_config()
    print(f"✅ Config loaded")
    print(f"   Keys: {list(config.keys())}")
    
    if 'bol_accounts' in config:
        print(f"   Accounts: {len(config['bol_accounts'])}")
        for acc in config['bol_accounts']:
            print(f"     - {acc.get('name')}: active={acc.get('active')}")
    
    active = get_active_bol_accounts()
    print(f"✅ Active accounts: {len(active)}")
    for acc in active:
        print(f"     - {acc.get('name')}")
        
except Exception as e:
    print(f"❌ Config test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

