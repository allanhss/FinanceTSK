"""
Validacao: get_unique_tags_list() retorna lista unica ordenada de tags

Testa:
1. Cria transacoes com tags diferentes
2. Chama get_unique_tags_list()
3. Valida que retorna lista unica e ordenada
"""

import os

os.environ["TESTING_MODE"] = "1"

import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import engine, SessionLocal, TESTING_MODE
from src.database.models import Base, Conta, Categoria, Transacao
from src.database.operations import create_transaction, get_unique_tags_list


def setup():
    """Setup test database."""
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        # Create test account
        conta = session.query(Conta).filter_by(nome="TagTest").first()
        if not conta:
            conta = Conta(nome="TagTest", tipo="conta", saldo_inicial=5000.0)
            session.add(conta)

        # Create test category
        categoria = session.query(Categoria).filter_by(nome="TagTestCat").first()
        if not categoria:
            categoria = Categoria(nome="TagTestCat", tipo="despesa")
            session.add(categoria)

        session.commit()
        return conta.id, categoria.id


def create_test_transactions():
    """Create test transactions with various tags."""
    print("\n[SETUP] Criando transacoes de teste com tags...")

    conta_id, categoria_id = setup()

    test_cases = [
        ("Compra 1", "Compras,Lazer", 50.0),
        ("Compra 2", "Compras,Casa", 75.0),
        ("Compra 3", "Lazer,Viagem", 100.0),
        ("Compra 4", "Casa,Manutencao", 150.0),
        ("Compra 5", "Viagem", 200.0),
    ]

    for desc, tags, valor in test_cases:
        success, msg = create_transaction(
            tipo="despesa",
            descricao=desc,
            valor=valor,
            data=date(2026, 1, 24),
            categoria_id=categoria_id,
            conta_id=conta_id,
            tags=tags,
        )
        if success:
            print(f"   [OK] {desc:<15} com tags: {tags}")
        else:
            print(f"   [ERRO] Falha ao criar {desc}: {msg}")
            return False

    return True


def test_get_unique_tags_list():
    """Test the get_unique_tags_list() function."""
    print("\n[TESTE] Recuperando lista unica de tags...")

    tags_list = get_unique_tags_list()

    print(f"   [INFO] Total de tags unicas: {len(tags_list)}")
    print(f"   [INFO] Tags recuperadas: {tags_list}")

    # Expected tags (from test data)
    expected_tags = {"Compras", "Lazer", "Casa", "Viagem", "Manutencao"}
    actual_tags = set(tags_list)

    # Check if all expected tags are in the list
    if expected_tags.issubset(actual_tags):
        print(f"   [OK] Todas as tags esperadas foram encontradas")
    else:
        missing = expected_tags - actual_tags
        print(f"   [ERRO] Tags faltando: {missing}")
        return False

    # Check if list is sorted
    if tags_list == sorted(tags_list):
        print(f"   [OK] Lista esta ordenada alfabeticamente")
    else:
        print(f"   [ERRO] Lista nao esta ordenada")
        print(f"       Esperado: {sorted(tags_list)}")
        print(f"       Obtido: {tags_list}")
        return False

    # Check for duplicates
    if len(tags_list) == len(set(tags_list)):
        print(f"   [OK] Nao ha duplicatas")
    else:
        print(f"   [ERRO] Existem duplicatas na lista")
        return False

    return True


def test_dropdown_format():
    """Test that the list is suitable for dropdown."""
    print("\n[TESTE] Validacao do formato para dropdown...")

    tags_list = get_unique_tags_list()

    # Should be a list of strings
    if not isinstance(tags_list, list):
        print(f"   [ERRO] Nao eh uma lista")
        return False

    if not all(isinstance(tag, str) for tag in tags_list):
        print(f"   [ERRO] Nem todos sao strings")
        return False

    # Each tag should be stripped (no leading/trailing spaces)
    for tag in tags_list:
        if tag != tag.strip():
            print(f"   [ERRO] Tag com espacos: '{tag}'")
            return False

    print(f"   [OK] Formato valido para dropdown (list[str], {len(tags_list)} items)")
    return True


def main():
    """Run all tests."""
    print("=" * 80)
    print("[VALIDACAO] get_unique_tags_list() - Lista para Dropdown")
    print("=" * 80)

    print(f"\n[INFO] TESTING_MODE: {TESTING_MODE}")
    print(f"[INFO] Engine URL: {engine.url}")

    if not TESTING_MODE:
        print(f"[ERRO] Este teste requer TESTING_MODE=1")
        sys.exit(1)

    # Setup and create test data
    if not create_test_transactions():
        print("\n[ERRO] Falha na criacao de dados de teste")
        sys.exit(1)

    # Run tests
    test1 = test_get_unique_tags_list()
    test2 = test_dropdown_format()

    print("\n" + "=" * 80)
    if test1 and test2:
        print("[RESULTADO] TODOS OS TESTES PASSARAM!")
        print("   Funcao get_unique_tags_list() esta pronta para dropdown.")
        print("=" * 80)
    else:
        print("[RESULTADO] ALGUNS TESTES FALHARAM")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
