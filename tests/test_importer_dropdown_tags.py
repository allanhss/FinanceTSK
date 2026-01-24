"""
Tests for importer component category dropdown and tags column.

Validates that the preview table correctly renders with category
dropdown options and editable tags column.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.components.importer import render_preview_table
from dash.dash_table import DataTable


class TestImporterDropdownAndTags:
    """Test suite for category dropdown and tags functionality."""

    def test_render_preview_table_with_category_options(self):
        """Verify preview table accepts and uses category_options."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        category_options = [
            {"label": "Alimentação", "value": "Alimentação"},
            {"label": "Transporte", "value": "Transporte"},
            {"label": "A Classificar", "value": "A Classificar"},
        ]

        result = render_preview_table(data, category_options)

        # Verify it's a Card
        assert result is not None
        assert hasattr(result, "children")

    def test_render_preview_table_default_category_options(self):
        """Verify default empty list for category_options."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Teste",
                "valor": 100.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        # Call without category_options
        result = render_preview_table(data)

        # Should not raise an error
        assert result is not None

    def test_preview_table_contains_tags_column(self):
        """Verify tags column is present in the DataTable."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        result = render_preview_table(data, [])

        # Find the DataTable in the Card children
        assert result is not None
        assert hasattr(result, "children")
        # The second child should be CardBody with the DataTable
        card_body = result.children[1]
        assert hasattr(card_body, "children")

    def test_preview_table_columns_structure(self):
        """Verify all expected columns exist with correct properties."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        category_options = [
            {"label": "Alimentação", "value": "Alimentação"},
        ]

        result = render_preview_table(data, category_options)

        # Extract DataTable from Card
        card_body = result.children[1]
        data_table = card_body.children[0]

        assert isinstance(data_table, DataTable)
        assert (
            len(data_table.columns) == 6
        )  # Data + Descricao + Valor + Tipo + Categoria + Tags

        # Verify column IDs
        column_ids = [col["id"] for col in data_table.columns]
        assert "data" in column_ids
        assert "descricao" in column_ids
        assert "valor" in column_ids
        assert "tipo" in column_ids
        assert "categoria" in column_ids
        assert "tags" in column_ids

    def test_tags_column_is_editable(self):
        """Verify tags column is marked as editable."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        result = render_preview_table(data, [])

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Find tags column
        tags_col = next(
            (col for col in data_table.columns if col["id"] == "tags"), None
        )
        assert tags_col is not None
        assert tags_col.get("editable") is True

    def test_categoria_column_has_dropdown_presentation(self):
        """Verify categoria column has dropdown presentation."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        category_options = [
            {"label": "Alimentação", "value": "Alimentação"},
        ]

        result = render_preview_table(data, category_options)

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Find categoria column
        cat_col = next(
            (col for col in data_table.columns if col["id"] == "categoria"), None
        )
        assert cat_col is not None
        assert cat_col.get("presentation") == "dropdown"

    def test_datatable_has_dropdown_config(self):
        """Verify DataTable dropdown configuration is set."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        category_options = [
            {"label": "Alimentação", "value": "Alimentação"},
            {"label": "Transporte", "value": "Transporte"},
        ]

        result = render_preview_table(data, category_options)

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Check dropdown property
        assert hasattr(data_table, "dropdown")
        assert data_table.dropdown is not None
        assert "categoria" in data_table.dropdown
        assert data_table.dropdown["categoria"]["clearable"] is False
        assert len(data_table.dropdown["categoria"]["options"]) == 2

    def test_preview_table_with_tags_data(self):
        """Verify tags are properly displayed in table data."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
                "tags": "compras,supermercado",
            }
        ]

        result = render_preview_table(data, [])

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Verify table data includes tags
        assert len(data_table.data) == 1
        assert data_table.data[0].get("tags") == "compras,supermercado"

    def test_preview_table_tags_empty_by_default(self):
        """Verify tags field is empty string by default."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        result = render_preview_table(data, [])

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Verify tags default to empty string
        assert data_table.data[0].get("tags") == ""

    def test_category_options_ordering(self):
        """Verify category options maintain their order in dropdown."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        category_options = [
            {"label": "Transporte", "value": "Transporte"},
            {"label": "Alimentação", "value": "Alimentação"},
            {"label": "Lazer", "value": "Lazer"},
        ]

        result = render_preview_table(data, category_options)

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Verify options are in same order
        dropdown_options = data_table.dropdown["categoria"]["options"]
        assert len(dropdown_options) == 3
        assert dropdown_options[0]["value"] == "Transporte"
        assert dropdown_options[1]["value"] == "Alimentação"
        assert dropdown_options[2]["value"] == "Lazer"

    def test_categoria_and_tags_column_widths(self):
        """Verify categoria and tags columns have appropriate min widths."""
        data = [
            {
                "data": "2026-01-20",
                "descricao": "Mercado",
                "valor": 150.00,
                "tipo": "despesa",
                "categoria": "Alimentação",
            }
        ]

        result = render_preview_table(data, [])

        card_body = result.children[1]
        data_table = card_body.children[0]

        # Check style_cell_conditional
        assert hasattr(data_table, "style_cell_conditional")
        widths = {
            item["if"]["column_id"]: item["minWidth"]
            for item in data_table.style_cell_conditional
            if "minWidth" in item
        }
        assert widths.get("categoria") == "150px"
        assert widths.get("tags") == "120px"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
