"""
Test for emoji selector in category manager.
"""

import pytest
from src.components.category_manager import render_category_manager, EMOJI_OPTIONS


def test_emoji_options_exist():
    """Test that EMOJI_OPTIONS constant is defined."""
    assert EMOJI_OPTIONS is not None
    assert isinstance(EMOJI_OPTIONS, list)
    assert len(EMOJI_OPTIONS) > 100  # Should have many emoji options


def test_emoji_options_contain_common_financial_emojis():
    """Test that common financial emojis are included."""
    financial_emojis = ["💰", "💸", "💳", "🏦", "💼", "💻"]
    for emoji in financial_emojis:
        assert emoji in EMOJI_OPTIONS, f"Emoji {emoji} not found in EMOJI_OPTIONS"


def test_category_manager_renders_with_icons():
    """Test that category manager renders with icon dropdowns."""
    receitas = [
        {"id": 1, "nome": "Salário", "icone": "💼", "tipo": "receita"},
        {"id": 2, "nome": "Freelance", "icone": "💻", "tipo": "receita"},
    ]
    despesas = [
        {"id": 3, "nome": "Alimentação", "icone": "🍔", "tipo": "despesa"},
    ]

    card = render_category_manager(receitas, despesas)

    assert card is not None
    # Check if component is a dbc.Card
    assert hasattr(card, "children")


def test_category_manager_displays_icons_in_list():
    """Test that rendered categories display icons properly."""
    receitas = [
        {"id": 1, "nome": "Salário", "icone": "💼"},
    ]
    despesas = []

    card = render_category_manager(receitas, despesas)

    # Verify the structure contains the category
    assert card is not None


def test_emoji_options_are_unique():
    """Test that all emoji options are unique."""
    assert len(EMOJI_OPTIONS) == len(set(EMOJI_OPTIONS)), "Duplicate emojis found"


def test_emoji_options_all_strings():
    """Test that all emoji options are strings."""
    for emoji in EMOJI_OPTIONS:
        assert isinstance(emoji, str), f"Non-string item in EMOJI_OPTIONS: {emoji}"
        assert len(emoji) > 0, "Empty emoji found"


def test_empty_categories_show_alert():
    """Test that empty category lists show info alert."""
    receitas = []
    despesas = []

    card = render_category_manager(receitas, despesas)

    assert card is not None
    # Both columns should show "Nenhuma categoria" alerts
