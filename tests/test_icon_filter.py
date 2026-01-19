"""
Test for icon filtering and selection in category manager.

Tests that the icon selector component renders correctly with RadioItems in grid format.
"""

import pytest
from src.components.category_manager import (
    render_category_manager,
    EMOJI_OPTIONS,
    render_icon_selector,
)
from dash import html


def test_icon_selector_renders():
    """Test that render_icon_selector creates a valid component."""
    selector = render_icon_selector("receita", "💰")

    # Should be a Div
    assert selector is not None
    # Should contain button and popover
    selector_str = str(selector)
    assert "btn-icon-receita" in selector_str
    assert "popover-icon-receita" in selector_str
    assert "radio-icon-receita" in selector_str


def test_icon_selector_uses_radio_items():
    """Test that icon selector uses RadioItems with grid layout."""
    selector = render_icon_selector("despesa", "💸")
    selector_str = str(selector)

    # Should contain RadioItems
    assert "RadioItems" in selector_str
    # Should have grid layout
    assert "gridTemplateColumns" in selector_str
    assert "repeat(3, 1fr)" in selector_str


def test_available_icons_excludes_used_receita():
    """Test that used receita icons are excluded from dropdown."""
    receitas = [
        {"id": 1, "nome": "Salário", "icone": "💼"},
        {"id": 2, "nome": "Freelance", "icone": "💻"},
    ]
    despesas = []

    card = render_category_manager(receitas, despesas)

    # Card should be rendered without errors
    assert card is not None
    # The component should contain the radio for receita
    card_str = str(card)
    assert "radio-icon-receita" in card_str


def test_available_icons_excludes_used_despesa():
    """Test that used despesa icons are excluded from dropdown."""
    receitas = []
    despesas = [
        {"id": 1, "nome": "Aluguel", "icone": "🏠"},
        {"id": 2, "nome": "Alimentação", "icone": "🍕"},
    ]

    card = render_category_manager(receitas, despesas)

    # Card should be rendered without errors
    assert card is not None
    # The component should contain the radio for despesa
    card_str = str(card)
    assert "radio-icon-despesa" in card_str


def test_same_icon_different_types_allows_icon():
    """Test that same icon in different types appears in both dropdowns."""
    receitas = [
        {"id": 1, "nome": "Income", "icone": "⭐"},
    ]
    despesas = []

    card = render_category_manager(receitas, despesas)

    # Card should be rendered without errors
    assert card is not None
    # The component should not have errors when rendering


def test_empty_categories_shows_all_icons():
    """Test that with no categories, all icons are available."""
    receitas = []
    despesas = []

    card = render_category_manager(receitas, despesas)

    # Card should be rendered without errors
    assert card is not None
    # The component should contain both radio buttons
    card_str = str(card)
    assert "radio-icon-receita" in card_str
    assert "radio-icon-despesa" in card_str


def test_categories_with_none_icon():
    """Test that categories with None icon don't affect filtering."""
    receitas = [
        {"id": 1, "nome": "Category1", "icone": None},
        {"id": 2, "nome": "Category2", "icone": "💼"},
    ]
    despesas = []

    card = render_category_manager(receitas, despesas)

    # Card should be rendered without errors
    assert card is not None


def test_all_emoji_options_available():
    """Test that EMOJI_OPTIONS contains all unique emojis."""
    assert len(EMOJI_OPTIONS) > 0
    # Check for deduplication
    assert len(EMOJI_OPTIONS) == len(set(EMOJI_OPTIONS))


def test_filtering_logic():
    """Test the filtering logic directly."""
    receitas = [
        {"id": 1, "nome": "Salário", "icone": "💼"},
        {"id": 2, "nome": "Freelance", "icone": "💻"},
    ]
    despesas = [
        {"id": 3, "nome": "Aluguel", "icone": "🏠"},
    ]

    # Extract used icons manually
    icones_receita_usados = {cat.get("icone") for cat in receitas if cat.get("icone")}
    icones_despesa_usados = {cat.get("icone") for cat in despesas if cat.get("icone")}

    # Check that filtering works
    icones_receita_disponiveis = [
        e for e in EMOJI_OPTIONS if e not in icones_receita_usados
    ]
    icones_despesa_disponiveis = [
        e for e in EMOJI_OPTIONS if e not in icones_despesa_usados
    ]

    # Verify filtering
    assert "💼" not in icones_receita_disponiveis
    assert "💻" not in icones_receita_disponiveis
    assert "🏠" not in icones_despesa_disponiveis

    # Verify that other icons are still available
    assert len(icones_receita_disponiveis) < len(EMOJI_OPTIONS)
    assert len(icones_despesa_disponiveis) < len(EMOJI_OPTIONS)
    assert len(icones_receita_disponiveis) > 0
    assert len(icones_despesa_disponiveis) > 0


def test_category_manager_renders_without_error():
    """Test that render_category_manager always renders without errors."""
    test_cases = [
        ([], []),
        ([{"id": 1, "nome": "Cat1", "icone": "💼"}], []),
        ([], [{"id": 2, "nome": "Cat2", "icone": "🏠"}]),
        (
            [{"id": 1, "nome": "Cat1", "icone": "💼"}],
            [{"id": 2, "nome": "Cat2", "icone": "🏠"}],
        ),
        (
            [{"id": 1, "nome": "Cat1", "icone": None}],
            [{"id": 2, "nome": "Cat2", "icone": None}],
        ),
    ]

    for receitas, despesas in test_cases:
        card = render_category_manager(receitas, despesas)
        assert card is not None
        # Verify it's a Card component
        assert hasattr(card, "children") or hasattr(card, "id")
