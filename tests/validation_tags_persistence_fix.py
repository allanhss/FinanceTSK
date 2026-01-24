"""
Script de Validacao: Verifica que create_transaction salva tags corretamente

Testa:
1. Criar transacao com tags via parametro 'tags'
2. Verificar que tags sao salvas no banco
3. Verificar que get_classification_history recupera as tags
"""

import os

os.environ["TESTING_MODE"] = "1"

import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import engine, SessionLocal, TESTING_MODE
from src.database.models import Base, Conta, Categoria, Transacao
from src.database.operations import create_transaction, get_classification_history


def setup():
    """Setup database."""
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        # Create test account
        conta = session.query(Conta).filter_by(nome="Debug").first()
        if not conta:
            conta = Conta(nome="Debug", tipo="conta", saldo_inicial=1000.0)
            session.add(conta)

        # Create test category
        categoria = session.query(Categoria).filter_by(nome="Teste").first()
        if not categoria:
            categoria = Categoria(nome="Teste", tipo="despesa")
            session.add(categoria)

        session.commit()
        return conta.id, categoria.id


def test_create_transaction_with_tags():
    """Test creating a transaction with tags parameter."""
    print("\n[TESTE1] Criar transacao com parametro tags")

    conta_id, categoria_id = setup()

    # Create transaction with tags parameter (not tag parameter!)
    success, message = create_transaction(
        tipo="despesa",
        descricao="Teste Tags Persistencia",
        valor=50.0,
        data=date(2026, 1, 24),
        categoria_id=categoria_id,
        conta_id=conta_id,
        tags="Debug,Teste,Tags",  # Using 'tags' parameter!
    )

    if success:
        print(f"   [OK] Transacao criada: {message}")
    else:
        print(f"   [ERRO] Falha ao criar: {message}")
        return False

    # Verify in database
    with SessionLocal() as session:
        transacao = (
            session.query(Transacao)
            .filter_by(descricao="Teste Tags Persistencia")
            .first()
        )

        if transacao:
            print(f"   [OK] Transacao encontrada no banco")
            print(f"       - ID: {transacao.id}")
            print(f"       - Tags no banco: '{transacao.tags}'")

            if transacao.tags == "Debug,Teste,Tags":
                print(f"   [SUCESSO] Tags salvas corretamente!")
                return True
            else:
                print(f"   [ERRO] Tags salvas incorretamente")
                print(f"       Esperado: 'Debug,Teste,Tags'")
                print(f"       Obtido: '{transacao.tags}'")
                return False
        else:
            print(f"   [ERRO] Transacao NAO encontrada no banco")
            return False


def test_classification_history():
    """Test that get_classification_history retrieves the tags."""
    print("\n[TESTE2] Recuperar tags do historico")

    historico = get_classification_history()

    # Look for normalized description
    chave = "teste tags persistencia"

    if chave in historico:
        entry = historico[chave]
        print(f"   [OK] Entrada encontrada no historico")
        print(f"       - Categoria: {entry.get('categoria')}")
        print(f"       - Tags: {entry.get('tags')}")

        if entry.get("tags") == "Debug,Teste,Tags":
            print(f"   [SUCESSO] Tags recuperadas corretamente do historico!")
            return True
        else:
            print(f"   [ERRO] Tags nao correspondem no historico")
            return False
    else:
        print(f"   [ERRO] Chave '{chave}' nao encontrada no historico")
        print(f"       Chaves disponiveis: {list(historico.keys())}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("[VALIDACAO] Persistencia de Tags - Correcao do Bug")
    print("=" * 80)

    print(f"\n[INFO] TESTING_MODE: {TESTING_MODE}")
    print(f"[INFO] Engine URL: {engine.url}")

    if not TESTING_MODE:
        print(f"[ERRO] Este teste requer TESTING_MODE=1")
        sys.exit(1)

    test1 = test_create_transaction_with_tags()
    test2 = test_classification_history()

    print("\n" + "=" * 80)
    if test1 and test2:
        print("[RESULTADO] TODOS OS TESTES PASSARAM!")
        print("   Tags sao agora persistidas corretamente no banco.")
        print("=" * 80)
    else:
        print("[RESULTADO] ALGUNS TESTES FALHARAM")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
