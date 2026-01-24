"""Quick integration test for importer."""

import sys
from pathlib import Path
from base64 import b64encode

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.components.importer import (
    render_importer_page,
    render_preview_table,
    render_import_success,
    render_import_error,
    render_import_info,
)
from src.utils.importers import parse_upload_content

# Test 1: Importer page
page = render_importer_page()
print("[OK] render_importer_page() works")

# Test 2: Preview table
dados = [
    {
        "data": "2025-01-15",
        "descricao": "Test",
        "valor": 45.5,
        "tipo": "despesa",
        "categoria": "Test",
    }
]
table = render_preview_table(dados)
print("[OK] render_preview_table() works")

# Test 3: Alerts
alert_ok = render_import_success(5)
alert_err = render_import_error("Test error")
alert_info = render_import_info("Test info")
print("[OK] Alert functions work")

# Test 4: CSV Parser
csv = "date,title,amount\n2025-01-15,Test,50.00\n"
encoded = b64encode(csv.encode("utf-8")).decode("utf-8")
result = parse_upload_content(encoded, "test.csv")
print(f"[OK] parse_upload_content() works ({len(result)} tx)")

print("[SUCCESS] All importer functionality integrated!")
