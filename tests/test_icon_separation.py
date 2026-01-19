"""
Test suite for icon/name separation in categories.

Tests for the icon field uniqueness, separation from name,
and proper serialization in API responses.
"""

import pytest
from src.database.models import Categoria
from src.database.connection import get_db
from src.database.operations import (
    create_category,
    get_categories,
    initialize_default_categories,
    delete_category,
)


@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up categories before each test."""
    with get_db() as session:
        session.query(Categoria).delete()
        session.commit()
    yield
    with get_db() as session:
        session.query(Categoria).delete()
        session.commit()


class TestIconSeparation:
    """Test icon/name separation implementation."""

    def test_create_category_with_icon(self) -> None:
        """Test creating a category with icon."""
        sucesso, mensagem = create_category(
            nome="Freelance",
            tipo="receita",
            cor="#3B82F6",
            icone="💻",
        )

        assert sucesso is True
        assert "sucesso" in mensagem.lower()

        categorias = get_categories(tipo="receita")
        assert len(categorias) >= 1
        assert any(c["nome"] == "Freelance" and c["icone"] == "💻" for c in categorias)

    def test_icon_uniqueness_per_type(self) -> None:
        """Test that icons must be unique within the same category type."""
        # Create first category with icon
        sucesso1, mensagem1 = create_category(
            nome="Freelance",
            tipo="receita",
            cor="#3B82F6",
            icone="💻",
        )
        assert sucesso1 is True

        # Try to create different category with same icon and type
        sucesso2, mensagem2 = create_category(
            nome="Consultoria",
            tipo="receita",
            cor="#6366F1",
            icone="💻",  # Same icon
        )

        assert sucesso2 is False
        assert "ícone" in mensagem2.lower() and "uso" in mensagem2.lower()

    def test_same_icon_different_types_allowed(self) -> None:
        """Test that same icon is allowed in different category types."""
        # Create income category with icon
        sucesso1, _ = create_category(
            nome="Ganho",
            tipo="receita",
            cor="#10B981",
            icone="⭐",
        )
        assert sucesso1 is True

        # Create expense category with same icon (different type)
        sucesso2, _ = create_category(
            nome="Bônus",
            tipo="despesa",
            cor="#EF4444",
            icone="⭐",  # Same icon, different type
        )
        assert sucesso2 is True

        # Both should exist
        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        assert any(c["icone"] == "⭐" for c in receitas)
        assert any(c["icone"] == "⭐" for c in despesas)

    def test_icon_returned_in_to_dict(self) -> None:
        """Test that icon field is properly serialized in to_dict()."""
        sucesso, _ = create_category(
            nome="Premium",
            tipo="receita",
            cor="#F59E0B",
            icone="👑",
        )
        assert sucesso is True

        categorias = get_categories(tipo="receita")
        categoria = next((c for c in categorias if c["nome"] == "Premium"), None)

        assert categoria is not None
        assert "icone" in categoria
        assert categoria["icone"] == "👑"
        assert categoria["nome"] == "Premium"

    def test_get_categories_includes_icon_field(self) -> None:
        """Test that get_categories returns icon field for all categories."""
        categorias = get_categories()

        # Each category should have icon field
        for cat in categorias:
            assert "icone" in cat
            assert "nome" in cat
            assert "tipo" in cat
            assert "cor" in cat

    def test_initialize_default_categories_with_icons(self) -> None:
        """Test that default categories are initialized with icons."""
        # Initialize defaults
        sucesso, mensagem = initialize_default_categories()
        assert sucesso is True

        # Get all categories
        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        # Should have default categories
        assert len(receitas) == 5  # Salário, Mesada, Vendas, Investimentos, Outros
        assert (
            len(despesas) == 7
        )  # Alimentação, Moradia, Transporte, Lazer, Saúde, Educação, Outros

        # All should have icons
        for cat in receitas + despesas:
            assert cat["icone"] is not None
            assert len(cat["icone"]) > 0

    def test_default_categories_have_unique_icons_per_type(self) -> None:
        """Test that default categories have unique icons within each type."""
        initialize_default_categories()

        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        # Check uniqueness within each type
        icons_receita = [c["icone"] for c in receitas]
        icons_despesa = [c["icone"] for c in despesas]

        assert len(icons_receita) == len(
            set(icons_receita)
        ), "Duplicate icons in receitas"
        assert len(icons_despesa) == len(
            set(icons_despesa)
        ), "Duplicate icons in despesas"

    def test_category_dict_structure(self) -> None:
        """Test that to_dict returns all expected fields."""
        sucesso, _ = create_category(
            nome="TestCat",
            tipo="receita",
            cor="#FFFFFF",
            icone="🧪",
        )
        assert sucesso is True

        categorias = get_categories()
        cat_dict = next((c for c in categorias if c["nome"] == "TestCat"), None)

        assert cat_dict is not None
        assert set(cat_dict.keys()) == {
            "id",
            "nome",
            "tipo",
            "cor",
            "icone",
            "created_at",
            "total_transacoes",
        }

    def test_icon_can_be_none(self) -> None:
        """Test that icon field can be None/null."""
        sucesso, _ = create_category(
            nome="NoIcon",
            tipo="despesa",
            cor="#999999",
            icone=None,
        )
        assert sucesso is True

        categorias = get_categories(tipo="despesa")
        cat = next((c for c in categorias if c["nome"] == "NoIcon"), None)

        assert cat is not None
        assert cat["icone"] is None


class TestIconValidationErrors:
    """Test error handling for icon operations."""

    def test_error_on_duplicate_icon_same_type(self) -> None:
        """Test proper error message when icon already exists."""
        create_category("Cat1", "receita", "#111111", "🎯")

        sucesso, mensagem = create_category("Cat2", "receita", "#222222", "🎯")

        assert sucesso is False
        assert "ícone" in mensagem.lower()
        assert "em uso" in mensagem.lower() or "existe" in mensagem.lower()

    def test_can_update_same_category_with_same_name(self) -> None:
        """Test that we can create same name with different icon if in different type."""
        # Create in receita
        sucesso1, _ = create_category("Teste", "receita", "#111111", "🔴")
        assert sucesso1 is True

        # Create same name in despesa with different icon (should work)
        sucesso2, _ = create_category("Teste", "despesa", "#222222", "🔵")
        assert sucesso2 is True

        receita_cat = get_categories(tipo="receita")
        despesa_cat = get_categories(tipo="despesa")

        assert any(c["nome"] == "Teste" and c["icone"] == "🔴" for c in receita_cat)
        assert any(c["nome"] == "Teste" and c["icone"] == "🔵" for c in despesa_cat)
