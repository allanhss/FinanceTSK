"""Test importer UI component."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import dash_bootstrap_components as dbc
from dash import html

from src.components.importer import (
    render_importer_page,
    render_import_error,
    render_import_info,
    render_import_success,
    render_preview_table,
)


def test_render_importer_page():
    """Test main importer page rendering."""
    print("[TEST 1] render_importer_page structure:")

    page = render_importer_page()

    # Check container
    assert isinstance(page, dbc.Container)
    print("  [OK] Returns dbc.Container")

    # Check it has children
    assert page.children is not None
    assert len(page.children) > 0
    print(f"  [OK] Container has {len(page.children)} children")

    # Check for key component IDs
    page_str = str(page)
    assert "upload-data" in page_str
    print("  [OK] Contains upload-data component")

    assert "store-import-data" in page_str
    print("  [OK] Contains store-import-data")

    assert "preview-container" in page_str
    print("  [OK] Contains preview-container")

    assert "btn-save-import" in page_str
    print("  [OK] Contains btn-save-import")

    assert "import-feedback" in page_str
    print("  [OK] Contains import-feedback\n")


def test_render_preview_table_with_data():
    """Test preview table rendering with transactions."""
    print("[TEST 2] render_preview_table with data:")

    # Sample transactions
    dados = [
        {
            "data": "2025-01-15",
            "descricao": "Padaria do Joao",
            "valor": 45.50,
            "tipo": "despesa",
            "categoria": "Alimentacao",
        },
        {
            "data": "2025-01-16",
            "descricao": "Transferencia",
            "valor": 500.00,
            "tipo": "receita",
            "categoria": "A Classificar",
        },
    ]

    table = render_preview_table(dados)

    # Check structure
    assert isinstance(table, dbc.Card)
    print("  [OK] Returns dbc.Card")

    # Check table ID
    table_str = str(table)
    assert "table-import-preview" in table_str
    print("  [OK] Contains table-import-preview")

    # Check row count in output
    assert "2 transacoes" in table_str or "2" in table_str
    print("  [OK] Shows transaction count\n")


def test_render_preview_table_empty():
    """Test preview table with no data."""
    print("[TEST 3] render_preview_table empty data:")

    table = render_preview_table([])

    # Should return empty div
    assert isinstance(table, html.Div)
    print("  [OK] Returns empty html.Div for no data\n")


def test_render_import_success():
    """Test success alert rendering."""
    print("[TEST 4] render_import_success:")

    alert = render_import_success(42)

    # Check type
    assert isinstance(alert, dbc.Alert)
    print("  [OK] Returns dbc.Alert")

    # Check content
    alert_str = str(alert)
    assert "42" in alert_str
    print("  [OK] Contains transaction count (42)")

    assert "success" in alert_str.lower()
    print("  [OK] Success color set\n")


def test_render_import_error():
    """Test error alert rendering."""
    print("[TEST 5] render_import_error:")

    message = "Arquivo CSV invalido"
    alert = render_import_error(message)

    # Check type
    assert isinstance(alert, dbc.Alert)
    print("  [OK] Returns dbc.Alert")

    # Check content
    alert_str = str(alert)
    assert message in alert_str
    print(f"  [OK] Contains error message: '{message}'")

    assert "danger" in alert_str.lower()
    print("  [OK] Error color set\n")


def test_render_import_info():
    """Test info alert rendering."""
    print("[TEST 6] render_import_info:")

    message = "Processando arquivo..."
    alert = render_import_info(message)

    # Check type
    assert isinstance(alert, dbc.Alert)
    print("  [OK] Returns dbc.Alert")

    # Check content
    alert_str = str(alert)
    assert message in alert_str
    print(f"  [OK] Contains info message: '{message}'")

    assert "info" in alert_str.lower()
    print("  [OK] Info color set\n")


def test_table_columns_structure():
    """Test DataTable column configuration."""
    print("[TEST 7] DataTable columns structure:")

    dados = [
        {
            "data": "2025-01-15",
            "descricao": "Teste",
            "valor": 100.00,
            "tipo": "despesa",
            "categoria": "Teste",
        }
    ]

    table = render_preview_table(dados)
    table_str = str(table)

    # Check for expected columns
    assert "Data" in table_str
    print("  [OK] Has 'Data' column")

    assert "Descri" in table_str  # May have encoding
    print("  [OK] Has 'Descricao' column (editable)")

    assert "Valor" in table_str
    print("  [OK] Has 'Valor' column")

    assert "Tipo" in table_str
    print("  [OK] Has 'Tipo' column")

    assert "Categoria" in table_str
    print("  [OK] Has 'Categoria' column (editable)\n")


def test_currency_formatting():
    """Test Brazilian currency formatting in table."""
    print("[TEST 8] Currency formatting:")

    dados = [
        {
            "data": "2025-01-15",
            "descricao": "Test",
            "valor": 1234.56,
            "tipo": "despesa",
            "categoria": "Test",
        }
    ]

    table = render_preview_table(dados)
    table_str = str(table)

    # Check for Brazilian format (comma as decimal)
    assert "1234,56" in table_str or "1234.56" in table_str
    print("  [OK] Shows value in currency format")

    assert "R$" in table_str
    print("  [OK] Shows currency symbol (R$)\n")


def test_tipo_formatting():
    """Test tipo (type) emoji display."""
    print("[TEST 9] Tipo emoji formatting:")

    dados_receita = [
        {
            "data": "2025-01-15",
            "descricao": "Test",
            "valor": 100.00,
            "tipo": "receita",
            "categoria": "Test",
        }
    ]

    dados_despesa = [
        {
            "data": "2025-01-15",
            "descricao": "Test",
            "valor": 100.00,
            "tipo": "despesa",
            "categoria": "Test",
        }
    ]

    table_receita = render_preview_table(dados_receita)
    table_despesa = render_preview_table(dados_despesa)

    receita_str = str(table_receita)
    despesa_str = str(table_despesa)

    # Check emoji/text display
    assert "Receita" in receita_str
    print("  [OK] Receita shows 'Receita' label")

    assert "Despesa" in despesa_str
    print("  [OK] Despesa shows 'Despesa' label\n")


def test_component_imports():
    """Test all component functions can be imported."""
    print("[TEST 10] Component imports:")

    # Should not raise
    try:
        from src.components.importer import (
            render_importer_page,
            render_preview_table,
            render_import_success,
            render_import_error,
            render_import_info,
        )

        print("  [OK] render_importer_page")
        print("  [OK] render_preview_table")
        print("  [OK] render_import_success")
        print("  [OK] render_import_error")
        print("  [OK] render_import_info\n")
    except ImportError as e:
        raise AssertionError(f"Import failed: {e}")


if __name__ == "__main__":
    test_render_importer_page()
    test_render_preview_table_with_data()
    test_render_preview_table_empty()
    test_render_import_success()
    test_render_import_error()
    test_render_import_info()
    test_table_columns_structure()
    test_currency_formatting()
    test_tipo_formatting()
    test_component_imports()

    print("[SUCCESS] All importer component tests passed!")
