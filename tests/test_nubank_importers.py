"""Test Nubank CSV importers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import base64
from datetime import datetime

from src.utils.importers import (
    clean_header,
    parse_upload_content,
)


# Sample CSV data for testing

CREDIT_CARD_CSV = """date,title,amount
2025-01-15,Padaria do João,45.50
2025-01-16,Supermercado X,-10.00
2025-01-17,Devolução,0.00
"""

CHECKING_ACCOUNT_CSV = """data,descrição,valor
15/01/2025,Transferência recebida,500.00
16/01/2025,Pagamento conta,-150.75
17/01/2025,Depósito,0.00
"""

INVALID_CSV = """name,age
John,25
"""


def test_clean_header():
    """Test header normalization."""
    print("[TEST 1] clean_header normalization:")

    # Test with spaces and mixed case
    headers = ["Data", " Valor ", "DESCRIÇÃO"]
    result = clean_header(headers)
    expected = ["data", "valor", "descrição"]

    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  [OK] Headers normalized: {result}")

    # Test with already clean headers
    clean = ["data", "valor", "descricao"]
    result2 = clean_header(clean)
    assert result2 == clean
    print(f"  [OK] Already clean headers: {result2}\n")


def test_credit_card_format():
    """Test credit card CSV parsing."""
    print("[TEST 2] Credit card format parsing:")

    # Encode CSV to base64
    encoded = base64.b64encode(
        CREDIT_CARD_CSV.encode("utf-8"),
    ).decode("utf-8")

    # Parse
    transactions = parse_upload_content(encoded, "cartao.csv")

    print(f"  Transactions parsed: {len(transactions)}")
    assert len(transactions) == 2, "Should have 2 valid transactions"

    # Check first transaction (positive = despesa)
    t1 = transactions[0]
    assert t1["data"] == "2025-01-15"
    assert t1["descricao"] == "Padaria do João"
    assert t1["valor"] == 45.50
    assert t1["tipo"] == "despesa"
    assert t1["categoria"] == "A Classificar"
    print(f"  [OK] TX1 (despesa): {t1}")

    # Check second transaction (negative = receita)
    t2 = transactions[1]
    assert t2["data"] == "2025-01-16"
    assert t2["descricao"] == "Supermercado X"
    assert t2["valor"] == 10.00
    assert t2["tipo"] == "receita"
    print(f"  [OK] TX2 (receita): {t2}")

    # Zero value should be skipped
    print(f"  [OK] Zero values ignored (line with 0.00 skipped)\n")


def test_checking_account_format():
    """Test checking account CSV parsing."""
    print("[TEST 3] Checking account format parsing:")

    # Encode CSV to base64
    encoded = base64.b64encode(
        CHECKING_ACCOUNT_CSV.encode("utf-8"),
    ).decode("utf-8")

    # Parse
    transactions = parse_upload_content(encoded, "conta.csv")

    print(f"  Transactions parsed: {len(transactions)}")
    assert len(transactions) == 2, "Should have 2 valid transactions"

    # Check first transaction (positive = receita)
    t1 = transactions[0]
    assert t1["data"] == "2025-01-15"
    assert t1["descricao"] == "Transferência recebida"
    assert t1["valor"] == 500.00
    assert t1["tipo"] == "receita"
    assert t1["categoria"] == "A Classificar"
    print(f"  [OK] TX1 (receita): {t1}")

    # Check second transaction (negative = despesa)
    t2 = transactions[1]
    assert t2["data"] == "2025-01-16"
    assert t2["descricao"] == "Pagamento conta"
    assert t2["valor"] == 150.75
    assert t2["tipo"] == "despesa"
    print(f"  [OK] TX2 (despesa): {t2}")

    # Zero value should be skipped
    print(f"  [OK] Zero values ignored\n")


def test_date_formats():
    """Test different date formats."""
    print("[TEST 4] Date format conversions:")

    # Credit card: YYYY-MM-DD
    cc_csv = "date,title,amount\n2025-12-31,Test,100.00\n"
    encoded_cc = base64.b64encode(cc_csv.encode("utf-8")).decode(
        "utf-8",
    )
    tx_cc = parse_upload_content(encoded_cc, "cc.csv")
    assert tx_cc[0]["data"] == "2025-12-31"
    print(f"  [OK] Credit card date (YYYY-MM-DD): {tx_cc[0]['data']}")

    # Checking: DD/MM/YYYY -> YYYY-MM-DD
    ca_csv = "data,descrição,valor\n31/12/2025,Test,100.00\n"
    encoded_ca = base64.b64encode(ca_csv.encode("utf-8")).decode(
        "utf-8",
    )
    tx_ca = parse_upload_content(encoded_ca, "ca.csv")
    assert tx_ca[0]["data"] == "2025-12-31"
    print(f"  [OK] Checking account date (DD/MM/YYYY -> ISO): " f"{tx_ca[0]['data']}\n")


def test_invalid_format():
    """Test error handling for invalid format."""
    print("[TEST 5] Invalid format detection:")

    encoded = base64.b64encode(
        INVALID_CSV.encode("utf-8"),
    ).decode("utf-8")

    try:
        parse_upload_content(encoded, "invalid.csv")
        assert False, "Should raise ValueError"
    except ValueError as e:
        print(f"  [OK] Correctly rejected invalid format")
        print(f"    Error: {str(e)}\n")


def test_edge_cases():
    """Test edge cases."""
    print("[TEST 6] Edge cases:")

    # Empty description
    csv = "date,title,amount\n2025-01-01,,50.00\n"
    encoded = base64.b64encode(csv.encode("utf-8")).decode("utf-8")
    tx = parse_upload_content(encoded, "test.csv")
    assert tx[0]["descricao"] == "Sem descrição"
    print(f"  [OK] Empty description handled: '{tx[0]['descricao']}'")

    # Values with decimal point
    csv = "date,title,amount\n2025-01-01,Test,1234.56\n"
    encoded = base64.b64encode(csv.encode("utf-8")).decode("utf-8")
    tx = parse_upload_content(encoded, "test.csv")
    assert abs(tx[0]["valor"] - 1234.56) < 0.01
    print(f"  [OK] Standard decimal format parsed: {tx[0]['valor']}")

    # All transactions skipped (all zero)
    csv = "date,title,amount\n2025-01-01,Test,0.00\n"
    encoded = base64.b64encode(csv.encode("utf-8")).decode("utf-8")
    tx = parse_upload_content(encoded, "test.csv")
    assert len(tx) == 0
    print(f"  [OK] All-zero CSV returns empty list\n")


if __name__ == "__main__":
    test_clean_header()
    test_credit_card_format()
    test_checking_account_format()
    test_date_formats()
    test_invalid_format()
    test_edge_cases()

    print("[SUCCESS] All importer tests passed!")
