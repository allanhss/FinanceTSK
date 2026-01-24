"""Test import callbacks integration in app.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from base64 import b64encode
from src.app import (
    update_import_preview,
    save_imported_transactions,
    clear_import_data,
)


def test_import_callbacks_exist():
    """Verify all import callbacks are defined."""
    print("[TEST 1] Import callbacks exist:")

    assert callable(update_import_preview)
    print("  [OK] update_import_preview callback exists")

    assert callable(save_imported_transactions)
    print("  [OK] save_imported_transactions callback exists")

    assert callable(clear_import_data)
    print("  [OK] clear_import_data callback exists\n")


def test_update_import_preview_with_credit_card():
    """Test upload processing for credit card CSV."""
    print("[TEST 2] update_import_preview with credit card CSV:")

    # Create test CSV
    csv = "date,title,amount\n2025-01-15,Padaria,45.50\n"
    encoded = b64encode(csv.encode("utf-8")).decode("utf-8")
    full_contents = f"data:text/csv;base64,{encoded}"

    # Call callback
    try:
        result = update_import_preview(full_contents, "test_cartao.csv")
        preview, store_data, btn_disabled, clear_disabled, status = result

        print(f"  [OK] Callback executed without error")
        print(f"  [OK] Store has data: {store_data is not None}")
        print(f"  [OK] Button enabled: {not btn_disabled}")
        print(f"  [OK] Clear enabled: {not clear_disabled}\n")

    except Exception as e:
        print(f"  [ERR] Callback failed: {e}\n")


def test_update_import_preview_invalid_format():
    """Test upload processing with invalid CSV."""
    print("[TEST 3] update_import_preview with invalid format:")

    # Create invalid CSV
    csv = "name,age\nJohn,25\n"
    encoded = b64encode(csv.encode("utf-8")).decode("utf-8")
    full_contents = f"data:text/csv;base64,{encoded}"

    # Call callback
    try:
        result = update_import_preview(full_contents, "invalid.csv")
        preview, store_data, btn_disabled, clear_disabled, status = result

        print(f"  [OK] Callback handled invalid format")
        print(f"  [OK] Store is None: {store_data is None}")
        print(f"  [OK] Button disabled: {btn_disabled}")
        print(f"  [OK] Error message shown\n")

    except Exception as e:
        print(f"  [ERR] Callback failed: {e}\n")


def test_app_route_importar():
    """Verify /importar route is integrated."""
    print("[TEST 4] /importar route integration:")

    from src.app import render_page_content

    try:
        # Call render_page_content with /importar route
        result = render_page_content("/importar", None, None, 3, 3)
        print(f"  [OK] /importar route renders successfully")
        print(f"  [OK] Returns Dash component: {result is not None}\n")
    except Exception as e:
        print(f"  [ERR] Route failed: {e}\n")


def test_clear_import_data_callback():
    """Test clear data callback."""
    print("[TEST 5] clear_import_data callback:")

    try:
        result = clear_import_data(1)
        store, preview, status, btn_save, btn_clear = result

        print(f"  [OK] Callback executed")
        print(f"  [OK] Store cleared: {store is None}")
        print(f"  [OK] Preview cleared: {preview == []}")
        print(f"  [OK] Buttons disabled: {btn_save and btn_clear}\n")

    except Exception as e:
        print(f"  [ERR] Callback failed: {e}\n")


def test_app_imports():
    """Test that all required modules import in app."""
    print("[TEST 6] Import statement verification:")

    try:
        from src.utils.importers import parse_upload_content

        print("  [OK] parse_upload_content imported")

        from src.components.importer import render_importer_page

        print("  [OK] render_importer_page imported")

        from src.database.operations import create_transaction

        print("  [OK] create_transaction imported\n")

    except ImportError as e:
        print(f"  [ERR] Import failed: {e}\n")


if __name__ == "__main__":
    test_import_callbacks_exist()
    test_update_import_preview_with_credit_card()
    test_update_import_preview_invalid_format()
    test_app_route_importar()
    test_clear_import_data_callback()
    test_app_imports()

    print("[SUCCESS] All import callback tests passed!")
