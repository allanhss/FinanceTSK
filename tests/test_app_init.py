#!/usr/bin/env python3
"""Script rápido para testar inicialização da aplicação"""
import sys
import os
from pathlib import Path

# Adicionar raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("TESTE: Inicialização da Aplicação Real")
print("=" * 70 + "\n")

print("1️⃣  Importando módulos...")
try:
    from src.app import app
    from src.database.connection import init_database, CAMINHO_BANCO
    print("   ✅ Módulos importados\n")
except Exception as e:
    print(f"   ❌ Erro ao importar: {e}\n")
    sys.exit(1)

print("2️⃣  Verificando banco atual...")
if os.path.exists(CAMINHO_BANCO):
    size = os.path.getsize(CAMINHO_BANCO)
    print(f"   ✓ Arquivo existe: {size} bytes")
else:
    print(f"   ✓ Arquivo não existe (será criado)")
print()

print("3️⃣  Inicializando banco...")
try:
    init_database()
    print("   ✅ Banco inicializado com sucesso\n")
except Exception as e:
    print(f"   ❌ Erro: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("4️⃣  Verificando arquivo finance.db...")
if os.path.exists(CAMINHO_BANCO):
    size = os.path.getsize(CAMINHO_BANCO)
    print(f"   ✅ Arquivo criado: {CAMINHO_BANCO}")
    print(f"   📦 Tamanho: {size} bytes\n")
else:
    print(f"   ❌ Arquivo não foi criado!\n")
    sys.exit(1)

print("5️⃣  Testando Dash app...")
try:
    # Acessar callbacks sem executar server
    print(f"   ✓ App está pronto para rodar")
    print(f"   ✓ Callbacks: {len(app.callback_map)} registrados\n")
except Exception as e:
    print(f"   ❌ Erro ao acessar app: {e}\n")
    sys.exit(1)

print("=" * 70)
print("✅ TESTE DE INICIALIZAÇÃO PASSOU!")
print("=" * 70)
print("\nA aplicação está pronta. Para iniciar o servidor:\n")
print("   python src/app.py\n")
print("Depois acesse: http://localhost:8050")
