"""Validation tests for improved tag application from classification history."""

import os
import sys
import csv
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.importers import _apply_history
import logging

logger = logging.getLogger(__name__)


def test_apply_history_tags_application():
    """Test that tags from history are applied to transactions without tags."""
    history = {
        "restaurant xyz": {"categoria": "Alimentação", "tags": "Lazer,Comida,Grupo"},
        "uber": {"categoria": "Transporte", "tags": "Viagem,Carro"},
    }

    # Test 1: Transaction without tags should receive historical tags
    row1 = {
        "descricao": "Restaurant XYZ Downtown",
        "categoria": "A Classificar",
        "tags": "",
    }
    _apply_history(row1, history)
    assert row1["categoria"] == "Alimentação", "Category should be applied"
    assert (
        row1["tags"] == "Lazer,Comida,Grupo"
    ), f"Expected tags 'Lazer,Comida,Grupo', got '{row1['tags']}'"

    # Test 2: Transaction with existing tags should not be overwritten
    row2 = {
        "descricao": "Restaurant XYZ Downtown",
        "categoria": "Alimentação",
        "tags": "Próprio",  # Already has tags
    }
    _apply_history(row2, history)
    assert row2["tags"] == "Próprio", "Existing tags should not be overwritten"

    # Test 3: Multiple matches - should use first one
    row3 = {"descricao": "Uber * Viagem", "categoria": "A Classificar", "tags": ""}
    _apply_history(row3, history)
    assert row3["categoria"] == "Transporte", "Category from history"
    assert row3["tags"] == "Viagem,Carro", "Tags from history"

    logger.info("✅ test_apply_history_tags_application PASSED")


def test_apply_history_empty_tags_not_applied():
    """Test that empty tags from history are not applied."""
    history = {"store abc": {"categoria": "Compras", "tags": ""}}  # No tags

    row = {"descricao": "Store ABC", "categoria": "A Classificar", "tags": ""}
    _apply_history(row, history)
    assert row["categoria"] == "Compras", "Category should be applied"
    assert row["tags"] == "", "Tags should remain empty if history has no tags"

    logger.info("✅ test_apply_history_empty_tags_not_applied PASSED")


def test_apply_history_none_tags_in_history():
    """Test handling of None tags values from history."""
    history = {
        "transaction test": {"categoria": "Varia", "tags": None}  # Explicitly None
    }

    row = {"descricao": "Transaction Test", "categoria": "A Classificar", "tags": ""}
    _apply_history(row, history)
    assert row["categoria"] == "Varia", "Category should be applied"
    # Should not crash and tags should remain empty
    assert row.get("tags") == "", "Tags should remain empty with None history tags"

    logger.info("✅ test_apply_history_none_tags_in_history PASSED")


def test_apply_history_preserves_category_adds_tags():
    """Test that tags are added even when category already exists."""
    history = {"restaurant": {"categoria": "Alimentação", "tags": "Comida,Grupo"}}

    # Row has category but no tags
    row = {
        "descricao": "Restaurant Premium",
        "categoria": "Alimentação",  # Already has category (not "A Classificar")
        "tags": "",
    }
    _apply_history(row, history)
    assert row["categoria"] == "Alimentação", "Category unchanged"
    assert row["tags"] == "Comida,Grupo", "Tags should still be applied"

    logger.info("✅ test_apply_history_preserves_category_adds_tags PASSED")


def test_apply_history_bidirectional_with_tags():
    """Test bidirectional matching with tag application."""
    history = {"uber": {"categoria": "Transporte", "tags": "Uber,Viagem"}}

    # Test 1: Historical key is substring of current description
    row1 = {
        "descricao": "Uber - Viagem São Paulo",
        "categoria": "A Classificar",
        "tags": "",
    }
    _apply_history(row1, history)
    assert row1["categoria"] == "Transporte"
    assert (
        row1["tags"] == "Uber,Viagem"
    ), "Tags should be applied on bidirectional match"

    # Test 2: Current description is substring of historical key? (less common but possible)
    history2 = {
        "uber black premium service": {
            "categoria": "Transporte",
            "tags": "Premium,Luxo",
        }
    }
    row2 = {"descricao": "Uber Black", "categoria": "A Classificar", "tags": ""}
    _apply_history(row2, history2)
    assert row2["categoria"] == "Transporte"
    assert (
        row2["tags"] == "Premium,Luxo"
    ), "Tags should be applied with reverse matching"

    logger.info("✅ test_apply_history_bidirectional_with_tags PASSED")


def test_apply_history_csv_import_with_tags():
    """Test that tags are preserved during CSV import with history."""
    from src.utils.importers import _parse_credit_card

    history = {
        "restaurant xyz": {"categoria": "Alimentação", "tags": "Lazer,Comida"},
        "transferência": {
            "categoria": "Transferência Interna",
            "tags": "Interna,Pessoal",
        },
    }

    csv_content = """Date,Amount,Title
2024-01-15,50.00,Restaurant XYZ
2024-01-16,-100.00,Transferência Interna
2024-01-17,30.00,New Store
"""
    reader = csv.DictReader(io.StringIO(csv_content))
    transactions = _parse_credit_card(
        reader, ["date", "amount", "title"], classification_history=history
    )

    assert len(transactions) == 3

    # First: Restaurant - should have tags from history
    assert transactions[0]["categoria"] == "Alimentação"
    assert (
        transactions[0]["tags"] == "Lazer,Comida"
    ), f"Expected 'Lazer,Comida', got '{transactions[0]['tags']}'"

    # Second: Transferência - should have tags from history
    assert transactions[1]["categoria"] == "Transferência Interna"
    assert transactions[1]["tags"] == "Interna,Pessoal"

    # Third: New Store - no history match, no tags
    assert transactions[2]["categoria"] == "A Classificar"
    assert transactions[2]["tags"] == ""

    logger.info("✅ test_apply_history_csv_import_with_tags PASSED")


if __name__ == "__main__":
    test_apply_history_tags_application()
    test_apply_history_empty_tags_not_applied()
    test_apply_history_none_tags_in_history()
    test_apply_history_preserves_category_adds_tags()
    test_apply_history_bidirectional_with_tags()
    test_apply_history_csv_import_with_tags()
    print("\n✅ All improved tag application validation tests PASSED!")
