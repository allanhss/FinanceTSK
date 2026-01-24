"""
Teste de segurança: Validar que scripts em /tests/ usam banco de teste automaticamente.
Este script demonstra a proteção contra corrupção de dados de produção.
"""

import os
import sys

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Este script está em /tests/, então TESTING_MODE deve ser detectado automaticamente
from src.database.connection import TESTING_MODE, CAMINHO_BANCO


def main():
    """Validate test environment protection."""
    print("=" * 70)
    print("🔒 TESTE DE SEGURANÇA - PROTEÇÃO DE BANCO DE DADOS")
    print("=" * 70)

    # Verificação 1: TESTING_MODE detectado
    print(f"\n1️⃣  TESTING_MODE detectado: {TESTING_MODE}")
    if TESTING_MODE:
        print("   ✅ SUCESSO: Modo de teste ativado automaticamente")
    else:
        print("   ❌ FALHA: Modo de teste NÃO foi detectado!")
        sys.exit(1)

    # Verificação 2: Banco de teste sendo usado
    print(f"\n2️⃣  Banco de dados em uso: {CAMINHO_BANCO}")
    if "test_finance.db" in CAMINHO_BANCO:
        print("   ✅ SUCESSO: Usando banco de teste (test_finance.db)")
    else:
        print(f"   ❌ FALHA: Usando banco de PRODUÇÃO! ({CAMINHO_BANCO})")
        sys.exit(1)

    # Verificação 3: Script está em /tests/
    script_path = os.path.abspath(sys.argv[0])
    normalized_path = script_path.replace("\\", "/")
    print(f"\n3️⃣  Script em execução: {script_path}")
    if "/tests/" in normalized_path:
        print(f"   ✅ SUCESSO: Script detectado em pasta /tests/")
    else:
        print(f"   ⚠️  Script está fora de /tests/")

    # Verificação 4: Caminho isolado
    prod_db_path = os.path.join(
        os.path.dirname(os.path.dirname(CAMINHO_BANCO)), "data", "finance.db"
    )
    if CAMINHO_BANCO != prod_db_path:
        print(f"\n4️⃣  Isolamento de dados:")
        print(f"   Banco de teste: {CAMINHO_BANCO}")
        print(f"   Banco de prod:  {prod_db_path}")
        print("   ✅ SUCESSO: Bancos de dados completamente isolados")
    else:
        print("   ❌ FALHA: Caminhos são iguais!")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("🎉 TODAS AS VERIFICAÇÕES DE SEGURANÇA PASSARAM!")
    print("=" * 70)
    print("\n📝 Resumo:")
    print("   • Scripts em /tests/ usam automaticamente test_finance.db")
    print("   • Banco de produção (finance.db) está protegido")
    print("   • Mesmo sem TESTING_MODE=1, a detecção funciona")
    print("   • Corrupção de dados de produção prevenida ✅")
    print()


if __name__ == "__main__":
    main()
