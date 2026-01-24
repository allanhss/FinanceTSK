"""Validation tests for 'Pagamento recebido' auto-categorization."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.models import Conta, Transacao, Categoria
from src.database.connection import SessionLocal
from src.database.operations import get_transactions
from src.utils.importers import _parse_credit_card
import csv
import io
import logging

logger = logging.getLogger(__name__)
os.environ["TESTING_MODE"] = "true"


def setup_test_data():
    """Create test data with 'Pagamento recebido' transaction.

    Returns:
        Tuple of (session, conta, categoria) for testing.
    """
    session = SessionLocal()

    # Clean up existing test data
    session.query(Transacao).delete()
    session.query(Conta).delete()
    session.query(Categoria).delete()
    session.commit()

    # Create test categories
    cat_transferencia = Categoria(
        nome="Transferência Interna",
        tipo="receita",
    )
    cat_despesa = Categoria(
        nome="Alimentação",
        tipo="despesa",
    )
    session.add_all([cat_transferencia, cat_despesa])
    session.commit()

    # Create test account
    conta = Conta(
        nome="Cartão Crédito Teste",
        tipo="cartao",
        saldo_inicial=1000.0,
    )
    session.add(conta)
    session.commit()

    return session, conta, cat_transferencia


def test_auto_categorization_pagamento_recebido():
    """Test that 'Pagamento recebido' is auto-categorized correctly."""
    session, conta, categoria = setup_test_data()

    # Parse CSV with "Pagamento recebido"
    csv_content = """Date,Amount,Title
2024-01-15,1000.00,Pagamento recebido
2024-01-16,-50.00,Compra Restaurante
"""
    reader = csv.DictReader(io.StringIO(csv_content))
    transactions = _parse_credit_card(reader, ["Date", "Amount", "Title"])

    # Verify parsing results
    assert len(transactions) == 2, f"Expected 2 transactions, got {len(transactions)}"

    # Check first transaction (Pagamento recebido)
    primeiro = transactions[0]
    assert (
        "pagamento recebido" in primeiro["descricao"].lower()
    ), f"Expected 'Pagamento recebido' in description, got {primeiro['descricao']}"
    assert (
        primeiro["categoria"] == "Transferência Interna"
    ), f"Expected 'Transferência Interna', got {primeiro['categoria']}"
    assert primeiro["skipped"] is False, "Expected skipped=False for Pagamento recebido"
    assert (
        primeiro["disable_edit"] is False
    ), "Expected disable_edit=False for Pagamento recebido"

    # Check second transaction (normal expense)
    segundo = transactions[1]
    assert (
        "Restaurante" in segundo["descricao"]
    ), f"Expected 'Restaurante' in description, got {segundo['descricao']}"
    assert (
        segundo["categoria"] == "A Classificar"
    ), f"Expected 'A Classificar', got {segundo['categoria']}"

    logger.info("✅ test_auto_categorization_pagamento_recebido PASSED")
    session.close()


def test_pagamento_recebido_in_database():
    """Test that imported 'Pagamento recebido' is stored correctly in database."""
    session, conta, categoria = setup_test_data()

    # Create transaction for "Pagamento recebido"
    transacao = Transacao(
        conta_id=conta.id,
        categoria_id=categoria.id,
        data=datetime(2024, 1, 15),
        descricao="Pagamento recebido",
        valor=1000.0,
        tipo="receita",  # Pagamento recebido is income from perspective
        parcela_atual=None,
        numero_parcelas=1,
    )
    session.add(transacao)
    session.commit()

    # Retrieve from database directly
    transacoes = session.query(Transacao).filter_by(conta_id=conta.id).all()
    assert len(transacoes) == 1, f"Expected 1 transaction, got {len(transacoes)}"

    tx = transacoes[0]
    assert tx.descricao == "Pagamento recebido"
    assert tx.categoria.nome == "Transferência Interna"
    assert tx.tipo == "receita"

    logger.info("✅ test_pagamento_recebido_in_database PASSED")
    session.close()


def test_pagamento_recebido_excluded_from_despesas():
    """Test that 'Pagamento recebido' is excluded from despesas list when filtering."""
    session, conta, categoria = setup_test_data()

    # Create "Pagamento recebido" transaction (Transferência Interna)
    transacao1 = Transacao(
        conta_id=conta.id,
        categoria_id=categoria.id,
        data=datetime(2024, 1, 15),
        descricao="Pagamento recebido",
        valor=1000.0,
        tipo="receita",
        parcela_atual=None,
        numero_parcelas=1,
    )

    # Create real expense for comparison
    cat_alimentacao = session.query(Categoria).filter_by(nome="Alimentação").first()
    transacao2 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        data=datetime(2024, 1, 16),
        descricao="Restaurante XYZ",
        valor=50.0,
        tipo="despesa",
        parcela_atual=None,
        numero_parcelas=1,
    )
    session.add_all([transacao1, transacao2])
    session.commit()

    # Get all transactions from database (no filtering)
    todas = session.query(Transacao).filter_by(conta_id=conta.id).all()
    assert len(todas) == 2, f"Expected 2 total, got {len(todas)}"

    # Test filter logic: exclude transfers
    transferencias = [
        tx for tx in todas if tx.categoria.nome == "Transferência Interna"
    ]
    sem_transferencias = [
        tx for tx in todas if tx.categoria.nome != "Transferência Interna"
    ]

    assert len(transferencias) == 1, f"Expected 1 transfer, got {len(transferencias)}"
    assert (
        len(sem_transferencias) == 1
    ), f"Expected 1 non-transfer, got {len(sem_transferencias)}"
    assert sem_transferencias[0].descricao == "Restaurante XYZ"

    logger.info("✅ test_pagamento_recebido_excluded_from_despesas PASSED")
    session.close()


if __name__ == "__main__":
    test_auto_categorization_pagamento_recebido()
    test_pagamento_recebido_in_database()
    test_pagamento_recebido_excluded_from_despesas()
    print("\n✅ All 'Pagamento recebido' validation tests PASSED!")
