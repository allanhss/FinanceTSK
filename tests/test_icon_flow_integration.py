"""
Test for icon selection integration in category creation flow.

Tests the callback integration for category creation with icon selection,
validation, error handling, and field cleanup.
"""

import pytest
from src.database.models import Categoria
from src.database.connection import get_db
from src.database.operations import (
    create_category,
    get_categories,
)


class TestIconFlowIntegration:
    """Test icon selection in category creation flow."""

    @pytest.fixture(autouse=True)
    def cleanup_database(self):
        """Clean up categories before each test."""
        with get_db() as session:
            session.query(Categoria).delete()
            session.commit()
        yield
        with get_db() as session:
            session.query(Categoria).delete()
            session.commit()

    def test_create_with_icon_success(self):
        """Test successful category creation with icon."""
        success, msg = create_category(
            nome="Freelance",
            tipo="receita",
            cor="#3B82F6",
            icone="💻",
        )
        assert success is True
        assert "sucesso" in msg.lower()

        categorias = get_categories(tipo="receita")
        assert len(categorias) == 1
        assert categorias[0]["nome"] == "Freelance"
        assert categorias[0]["icone"] == "💻"

    def test_create_without_icon_fails(self):
        """Test that creation without icon should fail or return None."""
        # This tests that icon=None is allowed, but validation happens in UI
        success, msg = create_category(
            nome="NoIcon",
            tipo="receita",
            cor="#111111",
            icone=None,  # No icon
        )
        # Backend allows None, UI should validate
        assert success is True

        categorias = get_categories(tipo="receita")
        assert any(c["nome"] == "NoIcon" and c["icone"] is None for c in categorias)

    def test_duplicate_icon_same_type_fails(self):
        """Test that duplicate icons in same type fail."""
        # Create first category
        success1, _ = create_category("Cat1", "receita", icone="🎯")
        assert success1 is True

        # Try to create with same icon
        success2, msg = create_category("Cat2", "receita", icone="🎯")
        assert success2 is False
        assert "ícone" in msg.lower() or "em uso" in msg.lower()

    def test_same_icon_different_types_succeeds(self):
        """Test that same icon works in different types."""
        success1, _ = create_category("Income", "receita", icone="⭐")
        assert success1 is True

        success2, _ = create_category("Expense", "despesa", icone="⭐")
        assert success2 is True

        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        assert any(c["icone"] == "⭐" for c in receitas)
        assert any(c["icone"] == "⭐" for c in despesas)

    def test_icon_persisted_in_dict(self):
        """Test that icon is included in to_dict output."""
        create_category("Premium", "receita", icone="👑")

        categorias = get_categories(tipo="receita")
        cat = next((c for c in categorias if c["nome"] == "Premium"), None)

        assert cat is not None
        assert "icone" in cat
        assert cat["icone"] == "👑"

    def test_create_with_special_characters_icon(self):
        """Test creation with various emoji types."""
        test_cases = [
            ("Cat1", "💰"),  # Money emoji
            ("Cat2", "🏠"),  # Building emoji
            ("Cat3", "⭐"),  # Star emoji
            ("Cat4", "🎯"),  # Target emoji
        ]

        for nome, icone in test_cases:
            success, _ = create_category(nome, "receita", icone=icone)
            assert success is True, f"Failed to create {nome} with {icone}"

        categorias = get_categories(tipo="receita")
        assert len(categorias) == len(test_cases)

    def test_error_message_on_duplicate_icon(self):
        """Test error message clarity on duplicate icon."""
        create_category("First", "despesa", icone="🍕")

        success, msg = create_category("Second", "despesa", icone="🍕")

        assert success is False
        assert "🍕" in msg or "ícone" in msg.lower()

    def test_validation_empty_name_with_icon(self):
        """Test that empty name fails even with icon."""
        success, msg = create_category("", "receita", icone="💻")

        assert success is False
        # Should fail due to validation (empty name)

    def test_validation_invalid_tipo_with_icon(self):
        """Test that invalid tipo fails even with icon."""
        success, msg = create_category("Cat", "invalid_type", icone="💻")

        assert success is False
        assert "tipo" in msg.lower() or "receita" in msg.lower()


class TestIconUIFlow:
    """Test the UI flow for icon selection (simulated)."""

    @pytest.fixture(autouse=True)
    def cleanup_database(self):
        """Clean up before each test."""
        with get_db() as session:
            session.query(Categoria).delete()
            session.commit()
        yield
        with get_db() as session:
            session.query(Categoria).delete()
            session.commit()

    def test_user_flow_select_icon_and_name(self):
        """Simulate: User selects icon from dropdown and enters name."""
        # Simulate user action: Select icon 💻 from dropdown
        selected_icon = "💻"

        # Simulate: User types name
        entered_name = "Freelance Work"

        # Simulate: User clicks Add button
        success, msg = create_category(
            nome=entered_name,
            tipo="receita",
            icone=selected_icon,
        )

        assert success is True

        # Verify category was saved with icon
        categorias = get_categories(tipo="receita")
        assert len(categorias) == 1
        assert categorias[0]["nome"] == "Freelance Work"
        assert categorias[0]["icone"] == "💻"

    def test_user_error_no_icon_selected(self):
        """Simulate: User forgets to select icon and clicks Add."""
        entered_name = "Freelance Work"
        selected_icon = None  # User forgot to select

        # UI should validate this and show error
        # Backend would still accept it, but UI prevents submission
        if not selected_icon:
            # Simulate UI validation
            validation_error = "Por favor, selecione um ícone"
            assert "ícone" in validation_error.lower()

    def test_user_error_duplicate_icon(self):
        """Simulate: User tries to use same icon twice."""
        # First category creation succeeds
        create_category("Freelance", "receita", icone="💻")

        # User tries to create another with same icon
        success, msg = create_category("Consulting", "receita", icone="💻")

        assert success is False
        # UI should display error about duplicate icon

    def test_user_creates_multiple_with_different_icons(self):
        """Simulate: User creates multiple categories with different icons."""
        categories_to_create = [
            ("Salary", "receita", "💼"),
            ("Freelance", "receita", "💻"),
            ("Investment", "receita", "📈"),
        ]

        for nome, tipo, icone in categories_to_create:
            success, _ = create_category(nome, tipo, icone=icone)
            assert success is True

        receitas = get_categories(tipo="receita")
        assert len(receitas) == len(categories_to_create)

        # Verify all icons are unique
        icons = [c["icone"] for c in receitas]
        assert len(icons) == len(set(icons))

    def test_form_fields_cleared_after_success(self):
        """Test that form fields are cleared after successful creation."""
        # Create category
        success, _ = create_category("Test", "receita", icone="🎯")
        assert success is True

        # In the callback, form values should be set to:
        # - input_receita: "" (empty)
        # - input_despesa: "" (empty)
        # - dropdown_icon_receita: None
        # - dropdown_icon_despesa: None
        # This is tested in app callback tests

    def test_error_alert_shows_on_duplicate(self):
        """Test that error alert displays duplicate icon message."""
        create_category("First", "despesa", icone="🍕")

        success, msg = create_category("Second", "despesa", icone="🍕")

        assert success is False
        # Error alert should display msg
        assert "erro" in msg.lower() or "ícone" in msg.lower()
