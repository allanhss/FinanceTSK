"""Validation tests for intelligent categorization based on classification history."""

import os
import sys
import csv
import io
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.importers import _parse_credit_card, _apply_history
import logging

logger = logging.getLogger(__name__)


def test_apply_history_basic():
    """Test basic history application to a transaction."""
    history = {
        "restaurant xyz": {"categoria": "Alimentação", "tags": "Lazer,Comida"},
        "posto ipiranga": {"categoria": "Transporte", "tags": "Carro,Gasolina"},
    }

    # Test 1: Exact match (case-insensitive)
    row = {"descricao": "Restaurant XYZ", "categoria": "A Classificar", "tags": ""}
    _apply_history(row, history)
    assert (
        row["categoria"] == "Alimentação"
    ), f"Expected 'Alimentação', got {row['categoria']}"
    assert (
        row["tags"] == "Lazer,Comida"
    ), f"Expected tags 'Lazer,Comida', got {row['tags']}"

    # Test 2: Current description contains history match
    row2 = {
        "descricao": "RESTAURANT XYZ - LOJA 01",
        "categoria": "A Classificar",
        "tags": "",
    }
    _apply_history(row2, history)
    assert row2["categoria"] == "Alimentação"
    assert row2["tags"] == "Lazer,Comida"

    logger.info("✅ test_apply_history_basic PASSED")


def test_apply_history_bidirectional_match():
    """Test bidirectional substring matching in history."""
    history = {"uber": {"categoria": "Transporte", "tags": "Viagem"}}

    # Historical key "uber" should match current description "Uber * Viagem"
    row = {
        "descricao": "Uber * Viagem Saída 123",
        "categoria": "A Classificar",
        "tags": "",
    }
    _apply_history(row, history)
    assert (
        row["categoria"] == "Transporte"
    ), f"Expected 'Transporte', got {row['categoria']}"
    assert row["tags"] == "Viagem"

    logger.info("✅ test_apply_history_bidirectional_match PASSED")


def test_apply_history_no_overwrite():
    """Test that history does not overwrite existing category."""
    history = {"restaurant": {"categoria": "Alimentação", "tags": "Comida"}}

    # Row already has category, should not be overwritten
    row = {
        "descricao": "Restaurant XYZ",
        "categoria": "Lazer",  # Already set
        "tags": "",
    }
    _apply_history(row, history)
    assert row["categoria"] == "Lazer", "Should not overwrite existing category"

    logger.info("✅ test_apply_history_no_overwrite PASSED")


def test_apply_history_none_input():
    """Test that None history is handled gracefully."""
    row = {"descricao": "Some transaction", "categoria": "A Classificar", "tags": ""}
    _apply_history(row, None)
    assert (
        row["categoria"] == "A Classificar"
    ), "Should remain unchanged with None history"

    logger.info("✅ test_apply_history_none_input PASSED")


def test_parse_credit_card_with_history():
    """Test that classification history is applied during CSV parsing."""
    history = {"restaurant xyz": {"categoria": "Alimentação", "tags": "Lazer"}}

    csv_content = """Date,Amount,Title
2024-01-15,50.00,Restaurant XYZ
2024-01-16,100.00,New Store ABC
"""
    reader = csv.DictReader(io.StringIO(csv_content))
    transactions = _parse_credit_card(
        reader, ["date", "amount", "title"], classification_history=history
    )

    assert len(transactions) == 2, f"Expected 2 transactions, got {len(transactions)}"

    # First transaction should have category from history
    tx1 = transactions[0]
    assert (
        tx1["categoria"] == "Alimentação"
    ), f"Expected 'Alimentação', got {tx1['categoria']}"
    assert tx1["tags"] == "Lazer", f"Expected 'Lazer', got {tx1['tags']}"

    # Second transaction should remain unclassified
    tx2 = transactions[1]
    assert (
        tx2["categoria"] == "A Classificar"
    ), f"Expected 'A Classificar', got {tx2['categoria']}"

    logger.info("✅ test_parse_credit_card_with_history PASSED")


def test_parse_credit_card_history_priority_over_tags():
    """Test that history fills tags even when category is auto-categorized."""
    history = {
        "transferência": {"categoria": "Transferência Interna", "tags": "Interna"}
    }

    csv_content = """Date,Amount,Title
2024-01-15,1000.00,Transferência Interna
"""
    reader = csv.DictReader(io.StringIO(csv_content))
    transactions = _parse_credit_card(
        reader, ["date", "amount", "title"], classification_history=history
    )

    assert len(transactions) == 1
    tx = transactions[0]
    assert tx["categoria"] == "Transferência Interna"
    # Tags from history should be applied
    assert tx["tags"] == "Interna", f"Expected tags 'Interna', got {tx['tags']}"

    logger.info("✅ test_parse_credit_card_history_priority_over_tags PASSED")


def test_parse_credit_card_without_history():
    """Test that parsing works correctly without history (backward compatibility)."""
    csv_content = """Date,Amount,Title
2024-01-15,50.00,Restaurant XYZ
2024-01-16,-100.00,Pagamento de fatura
"""
    reader = csv.DictReader(io.StringIO(csv_content))
    transactions = _parse_credit_card(
        reader, ["date", "amount", "title"], classification_history=None
    )

    assert len(transactions) == 2

    # First transaction: no category (not in AUTO_CATEGORIES)
    assert transactions[0]["categoria"] == "A Classificar"

    # Second transaction: matched by AUTO_CATEGORIES
    assert transactions[1]["categoria"] == "Transferência Interna"

    logger.info("✅ test_parse_credit_card_without_history PASSED")


if __name__ == "__main__":
    test_apply_history_basic()
    test_apply_history_bidirectional_match()
    test_apply_history_no_overwrite()
    test_apply_history_none_input()
    test_parse_credit_card_with_history()
    test_parse_credit_card_history_priority_over_tags()
    test_parse_credit_card_without_history()
    print("\n✅ All intelligent categorization validation tests PASSED!")
