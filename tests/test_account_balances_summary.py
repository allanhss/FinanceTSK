"""
Test module for get_account_balances_summary() function.

Tests the account balance calculation and grouping by account type
for multi-account dashboard.
"""

import pytest
from datetime import date
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Conta, Categoria, Transacao
from src.database.operations import get_account_balances_summary


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory test database with sample data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    # Create default categories
    categorias = [
        Categoria(nome="Salário", tipo="receita", icone="💰"),
        Categoria(nome="Compras", tipo="despesa", icone="🛍️"),
    ]
    session.add_all(categorias)
    session.commit()

    # Mock get_db
    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return session

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        yield session

    session.close()


def test_empty_accounts(test_db):
    """Test with no accounts - should return zeroed structure."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    assert resultado["total_disponivel"] == 0.0
    assert resultado["total_investido"] == 0.0
    assert resultado["total_cartoes"] == 0.0
    assert resultado["patrimonio_total"] == 0.0
    assert resultado["detalhe_por_conta"] == []


def test_single_account_with_saldo_inicial(test_db):
    """Test with single account and only saldo_inicial."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    # Create a single account
    conta = Conta(nome="Nubank", tipo="conta", saldo_inicial=1000.0)
    test_db.add(conta)
    test_db.commit()

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    assert resultado["total_disponivel"] == 1000.0
    assert resultado["total_investido"] == 0.0
    assert resultado["total_cartoes"] == 0.0
    assert resultado["patrimonio_total"] == 1000.0
    assert len(resultado["detalhe_por_conta"]) == 1

    conta_info = resultado["detalhe_por_conta"][0]
    assert conta_info["nome"] == "Nubank"
    assert conta_info["tipo"] == "conta"
    assert conta_info["saldo"] == 1000.0
    assert conta_info["cor_tipo"] == "#3B82F6"  # Azul para conta


def test_multiple_accounts_different_types(test_db):
    """Test with multiple accounts of different types."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    # Create accounts
    contas = [
        Conta(nome="Nubank", tipo="conta", saldo_inicial=5000.0),
        Conta(nome="XP", tipo="investimento", saldo_inicial=10000.0),
        Conta(nome="Visa", tipo="cartao", saldo_inicial=-500.0),  # Dívida negativa
    ]
    test_db.add_all(contas)
    test_db.commit()

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    assert resultado["total_disponivel"] == 5000.0
    assert resultado["total_investido"] == 10000.0
    assert resultado["total_cartoes"] == -500.0
    assert resultado["patrimonio_total"] == 14500.0  # 5000 + 10000 - 500
    assert len(resultado["detalhe_por_conta"]) == 3


def test_accounts_with_transactions(test_db):
    """Test balance calculation with transactions."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    # Create account
    conta = Conta(nome="Nubank", tipo="conta", saldo_inicial=1000.0)
    test_db.add(conta)
    test_db.flush()

    # Get category
    categoria = test_db.query(Categoria).filter_by(nome="Salário").first()

    # Create transactions
    transacoes = [
        Transacao(
            tipo="receita",
            descricao="Salário",
            valor=3000.0,
            data=date(2026, 1, 15),
            categoria_id=categoria.id,
            conta_id=conta.id,
        ),
        Transacao(
            tipo="despesa",
            descricao="Compras",
            valor=500.0,
            data=date(2026, 1, 20),
            categoria_id=categoria.id,
            conta_id=conta.id,
        ),
    ]
    test_db.add_all(transacoes)
    test_db.commit()

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    # Saldo = 1000 + 3000 - 500 = 3500
    assert resultado["total_disponivel"] == 3500.0
    assert resultado["patrimonio_total"] == 3500.0

    conta_info = resultado["detalhe_por_conta"][0]
    assert conta_info["saldo"] == 3500.0


def test_structure_keys(test_db):
    """Test that returned structure has all required keys."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    # Verify required keys
    required_keys = [
        "total_disponivel",
        "total_investido",
        "total_cartoes",
        "patrimonio_total",
        "detalhe_por_conta",
    ]

    for key in required_keys:
        assert key in resultado, f"Missing key: {key}"


def test_detalhe_per_conta_structure(test_db):
    """Test structure of detalhe_por_conta items."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    # Create account
    conta = Conta(nome="Test", tipo="conta", saldo_inicial=100.0)
    test_db.add(conta)
    test_db.commit()

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    assert len(resultado["detalhe_por_conta"]) == 1
    conta_info = resultado["detalhe_por_conta"][0]

    # Verify required fields in cada item
    required_fields = ["id", "nome", "tipo", "saldo", "cor_tipo"]
    for field in required_fields:
        assert field in conta_info, f"Missing field: {field}"

    # Verify data types
    assert isinstance(conta_info["id"], int)
    assert isinstance(conta_info["nome"], str)
    assert isinstance(conta_info["tipo"], str)
    assert isinstance(conta_info["saldo"], float)
    assert isinstance(conta_info["cor_tipo"], str)
    assert conta_info["cor_tipo"].startswith("#")  # Hex color


def test_color_mapping(test_db):
    """Test that correct colors are assigned to each account type."""
    from src.database.operations import get_account_balances_summary
    from unittest.mock import patch

    # Create accounts of each type
    contas = [
        Conta(nome="Conta", tipo="conta", saldo_inicial=1000.0),
        Conta(nome="Invest", tipo="investimento", saldo_inicial=2000.0),
        Conta(nome="Card", tipo="cartao", saldo_inicial=-100.0),
    ]
    test_db.add_all(contas)
    test_db.commit()

    def mock_get_db():
        class ContextManager:
            def __enter__(self):
                return test_db

            def __exit__(self, *args):
                pass

        return ContextManager()

    with patch("src.database.operations.get_db", side_effect=mock_get_db):
        resultado = get_account_balances_summary()

    cores_esperadas = {
        "conta": "#3B82F6",  # Azul
        "investimento": "#10B981",  # Verde
        "cartao": "#EF4444",  # Vermelho
    }

    for conta_info in resultado["detalhe_por_conta"]:
        tipo = conta_info["tipo"]
        cor_esperada = cores_esperadas[tipo]
        assert conta_info["cor_tipo"] == cor_esperada


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
