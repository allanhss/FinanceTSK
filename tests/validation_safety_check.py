"""
Script de validação de segurança: Prova que a trava de proteção funciona.

Este script DEVE estar em /tests/ para validar automaticamente a proteção.
Se a detecção de ambiente funcionar, deve conectar ao test_finance.db.
Se conectar ao finance.db de produção, a validação FALHA (indicando corrupção de dados).
"""

import os
import sys

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import engine, TESTING_MODE, CAMINHO_BANCO


def main():
    """Validate safety lock is working correctly."""
    print("=" * 80)
    print("[SEGURANCA] VALIDANDO PROTECAO DE BANCO DE DADOS")
    print("=" * 80)

    # Get database URL from engine
    db_url = str(engine.url)
    print(f"\n[INFO] Engine URL detectada: {db_url}")

    # Extract database name from path
    db_path = CAMINHO_BANCO
    db_filename = os.path.basename(db_path)

    print(f"[INFO] Caminho do banco: {db_path}")
    print(f"[INFO] Nome do arquivo: {db_filename}")
    print(f"[INFO] TESTING_MODE: {TESTING_MODE}")

    # Validation 1: This script is in /tests/ folder
    script_location = os.path.abspath(__file__)
    normalized_location = script_location.replace("\\", "/")
    in_tests_folder = "/tests/" in normalized_location

    print(f"\n[OK] Script localizado em: {script_location}")
    print(f"[OK] Em pasta /tests/: {in_tests_folder}")

    # Validation 2: Should be using test database
    print(f"\n[VALIDACAO] VALIDACAO DE SEGURANCA:")

    if in_tests_folder:
        print(f"   [OK] Script esta em /tests/")

        # Must use test_finance.db
        if "test_finance.db" in db_filename:
            print(f"   [SUCESSO] Usando banco de teste ({db_filename})")
        else:
            print(f"   [ERRO] FALHA CRITICA: Usando banco de PRODUCAO ({db_filename})")
            print(f"\n   [ERRO] Script em /tests/ conectou em producao!")
            print(f"   [ERRO] Isso significa a trava de protecao NAO esta funcionando!")
            sys.exit(1)
    else:
        print(f"   [AVISO] Script NAO esta em /tests/")
        print(
            f"   [INFO] (Este teste deve ser executado como: python tests/validation_safety_check.py)"
        )

    # Validation 3: URL must contain test_finance.db
    print(f"\n[VALIDACAO] VALIDACAO DE URL:")
    if "test_finance.db" in db_url:
        print(f"   [SUCESSO] URL contem 'test_finance.db'")
    else:
        print(f"   [ERRO] FALHA: URL nao contem 'test_finance.db'")
        print(f"   [INFO] URL: {db_url}")
        sys.exit(1)

    # Validation 4: Ensure finance.db (production) is NOT being used
    print(f"\n[VALIDACAO] PROTECAO CONTRA PRODUCAO:")
    if "finance.db" in db_url and "test_finance.db" not in db_url:
        print(f"   [ERRO] FALHA CRITICA: Conectando a banco de PRODUCAO (finance.db)")
        sys.exit(1)
    else:
        print(f"   [SUCESSO] Banco de producao nao foi acessado")

    # Final summary
    print("\n" + "=" * 80)
    print("[SUCESSO] TODAS AS VALIDACOES DE SEGURANCA PASSARAM!")
    print("=" * 80)
    print("\n[RESUMO]")
    print(f"   * Script em: {script_location}")
    print(f"   * Banco em uso: {db_filename}")
    print(f"   * TESTING_MODE: {TESTING_MODE}")
    print(f"   * Engine URL: {db_url}")
    print("\n[PROTECAO] A trava de protecao esta funcionando corretamente!")
    print("   Banco de producao esta seguro contra scripts de teste.")
    print()


if __name__ == "__main__":
    main()
