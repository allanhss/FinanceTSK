"""Validation tests for get_classification_history function."""

import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.models import Conta, Transacao, Categoria
from src.database.connection import SessionLocal
from src.database.operations import get_classification_history
import logging

logger = logging.getLogger(__name__)
os.environ["TESTING_MODE"] = "true"


def setup_test_data():
    """Create test data with multiple transactions for classification learning.

    Returns:
        Tuple of (session, conta) for testing.
    """
    session = SessionLocal()

    # Clean up existing test data
    session.query(Transacao).delete()
    session.query(Conta).delete()
    session.query(Categoria).delete()
    session.commit()

    # Create test categories
    cat_transporte = Categoria(nome="Transporte", tipo="despesa")
    cat_alimentacao = Categoria(nome="Alimentação", tipo="despesa")
    cat_lazer = Categoria(nome="Lazer", tipo="despesa")
    session.add_all([cat_transporte, cat_alimentacao, cat_lazer])
    session.commit()

    # Create test account
    conta = Conta(
        nome="Conta Teste",
        tipo="conta",
        saldo_inicial=5000.0,
    )
    session.add(conta)
    session.commit()

    # Create test transactions with various classifications
    # Transaction 1: Posto Ipiranga (Transporte)
    tx1 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transporte.id,
        data=date(2024, 1, 10),
        descricao="Posto Ipiranga",
        valor=150.0,
        tipo="despesa",
        tags="Carro,Gasolina",
    )

    # Transaction 2: Same place, different date (should not override due to ordering)
    tx2 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_lazer.id,
        data=date(2024, 1, 5),
        descricao="Posto Ipiranga",
        valor=100.0,
        tipo="despesa",
        tags="Lazer",
    )

    # Transaction 3: Restaurant (Alimentação)
    tx3 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        data=date(2024, 1, 12),
        descricao="Restaurant XYZ",
        valor=80.0,
        tipo="despesa",
        tags="Lazer,Comida",
    )

    # Transaction 4: Duplicate with different case
    tx4 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        data=date(2024, 1, 15),
        descricao="RESTAURANT XYZ",
        valor=120.0,
        tipo="despesa",
        tags="Saúde",
    )

    # Transaction 5: No tags
    tx5 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transporte.id,
        data=date(2024, 1, 18),
        descricao="Uber",
        valor=45.0,
        tipo="despesa",
        tags=None,
    )

    session.add_all([tx1, tx2, tx3, tx4, tx5])
    session.commit()

    return session, conta


def test_classification_history_basic():
    """Test basic classification history learning."""
    session, _ = setup_test_data()

    history = get_classification_history()

    # Verify structure
    assert isinstance(history, dict), f"Expected dict, got {type(history)}"
    assert len(history) > 0, "Expected non-empty history"

    # Verify key normalization (lowercase)
    assert "posto ipiranga" in history, "Expected normalized key for Posto Ipiranga"
    assert "restaurant xyz" in history, "Expected normalized key for Restaurant XYZ"
    assert "uber" in history, "Expected normalized key for Uber"

    logger.info("✅ test_classification_history_basic PASSED")
    session.close()


def test_classification_history_most_recent():
    """Test that most recent classification is retained for duplicates."""
    session, _ = setup_test_data()

    history = get_classification_history()

    # "Posto Ipiranga" appears twice:
    # - 2024-01-10 as Transporte with tags "Carro,Gasolina"
    # - 2024-01-05 as Lazer with tags "Lazer"
    # Should keep the 2024-01-10 version (most recent)
    entry = history.get("posto ipiranga")
    assert entry is not None, "Expected entry for Posto Ipiranga"
    assert (
        entry["categoria"] == "Transporte"
    ), f"Expected 'Transporte', got {entry['categoria']}"
    assert (
        entry["tags"] == "Carro,Gasolina"
    ), f"Expected 'Carro,Gasolina', got {entry['tags']}"

    logger.info("✅ test_classification_history_most_recent PASSED")
    session.close()


def test_classification_history_normalization():
    """Test that case-insensitive normalization works correctly."""
    session, _ = setup_test_data()

    history = get_classification_history()

    # "Restaurant XYZ" and "RESTAURANT XYZ" should both map to same key
    normalized_key = "restaurant xyz"
    entry = history.get(normalized_key)
    assert entry is not None, f"Expected entry for {normalized_key}"
    # Should keep the one with later date (2024-01-15 > 2024-01-12)
    assert (
        entry["categoria"] == "Alimentação"
    ), f"Expected 'Alimentação', got {entry['categoria']}"
    assert entry["tags"] == "Saúde", f"Expected 'Saúde', got {entry['tags']}"

    logger.info("✅ test_classification_history_normalization PASSED")
    session.close()


def test_classification_history_none_tags():
    """Test that None tags are handled gracefully."""
    session, _ = setup_test_data()

    history = get_classification_history()

    # Uber has no tags
    entry = history.get("uber")
    assert entry is not None, "Expected entry for Uber"
    assert entry["categoria"] == "Transporte"
    assert entry["tags"] == "", "Expected empty string for None tags"

    logger.info("✅ test_classification_history_none_tags PASSED")
    session.close()


def test_classification_history_lookup():
    """Test that history can be used for classification lookup."""
    session, _ = setup_test_data()

    history = get_classification_history()

    # Simulate import scenario: new transaction with description
    novo_descricao = "Posto Ipiranga"
    normalized = novo_descricao.lower().strip()

    # Lookup in history
    suggestion = history.get(normalized)
    assert suggestion is not None, "Expected suggestion for Posto Ipiranga"
    assert suggestion["categoria"] == "Transporte"
    assert suggestion["tags"] == "Carro,Gasolina"

    # Simulate a description not in history
    nao_existente = history.get("nova_loja_desconhecida")
    assert nao_existente is None, "Expected None for unknown description"

    logger.info("✅ test_classification_history_lookup PASSED")
    session.close()


if __name__ == "__main__":
    test_classification_history_basic()
    test_classification_history_most_recent()
    test_classification_history_normalization()
    test_classification_history_none_tags()
    test_classification_history_lookup()
    print("\n✅ All classification history validation tests PASSED!")
