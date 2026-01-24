"""
Tests for payment filtering in credit card imports.

Validates that "Pagamento recebido" lines are correctly filtered
out during CSV parsing to prevent duplicate or incorrect classifications.
"""

import pytest
import logging
from io import StringIO

from src.utils.importers import _parse_credit_card


logger = logging.getLogger(__name__)


class TestPaymentFiltering:
    """Test suite for payment line filtering."""

    def test_filter_pagamento_recebido_exact(self):
        """Verify exact 'Pagamento recebido' is filtered."""
        csv_content = """date,title,amount
2026-01-20,Padaria Pão Quente,-25.50
2026-01-21,Pagamento recebido,100.00
2026-01-22,Mercado XYZ,-150.00
"""
        reader_dict = {}
        lines = csv_content.strip().split("\n")

        # Manually create DictReader-like structure
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should only have 2 transactions (padaria and mercado)
        assert len(result) == 2
        assert result[0]["descricao"] == "Padaria Pão Quente"
        assert result[1]["descricao"] == "Mercado XYZ"

    def test_filter_pagamento_recebido_case_insensitive(self):
        """Verify filtering is case-insensitive."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-20,Mercado ABC,-50.00
2026-01-21,PAGAMENTO RECEBIDO,200.00
2026-01-22,Lanchonete,-30.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should only have 2 transactions
        assert len(result) == 2
        assert result[0]["descricao"] == "Mercado ABC"
        assert result[1]["descricao"] == "Lanchonete"

    def test_filter_pagamento_recebido_with_spaces(self):
        """Verify filtering works with leading/trailing spaces."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-20,Restaurante,-80.00
2026-01-21,  Pagamento recebido  ,150.00
2026-01-22,Cinema,-45.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should only have 2 transactions
        assert len(result) == 2
        assert result[0]["descricao"] == "Restaurante"
        assert result[1]["descricao"] == "Cinema"

    def test_partial_match_not_filtered(self):
        """Verify partial matches like 'Pagamento recebido de X' are also filtered."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-20,Despesa Normal,-25.00
2026-01-21,Pagamento recebido de João,500.00
2026-01-22,Outra Despesa,-15.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should only have 2 transactions (both start with "Pagamento recebido" filtered)
        assert len(result) == 2
        assert result[0]["descricao"] == "Despesa Normal"
        assert result[1]["descricao"] == "Outra Despesa"

    def test_normal_descriptions_not_affected(self):
        """Verify normal descriptions containing 'pagamento' are not filtered."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-20,Pagamento de Conta,-100.00
2026-01-21,Boleto Pagamento,-50.00
2026-01-22,Pagamento de Crédito,-75.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # All should be included (none start with "Pagamento recebido")
        assert len(result) == 3
        assert result[0]["descricao"] == "Pagamento de Conta"
        assert result[1]["descricao"] == "Boleto Pagamento"
        assert result[2]["descricao"] == "Pagamento de Crédito"

    def test_mixed_transactions_with_payment(self):
        """Verify mixed transactions are handled correctly."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-15,Supermercado,-200.50
2026-01-18,Padaria,-45.00
2026-01-20,Pagamento recebido,500.00
2026-01-22,Restaurante,-120.00
2026-01-25,Pagamento recebido,600.00
2026-01-28,Farmácia,-85.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should have 4 transactions (only those without "Pagamento recebido")
        assert len(result) == 4
        descriptions = [t["descricao"] for t in result]
        assert "Supermercado" in descriptions
        assert "Padaria" in descriptions
        assert "Restaurante" in descriptions
        assert "Farmácia" in descriptions
        # Payment lines should NOT be in descriptions
        assert "Pagamento recebido" not in str(descriptions)

    def test_logging_on_payment_filter(self):
        """Verify logging occurs when payment is filtered."""
        import csv
        from io import StringIO
        from unittest.mock import patch

        csv_content = """date,title,amount
2026-01-20,Pagamento recebido,100.00
2026-01-21,Despesa Normal,-50.00
"""
        with patch("src.utils.importers.logger") as mock_logger:
            reader = csv.DictReader(StringIO(csv_content))
            result = _parse_credit_card(reader, ["date", "title", "amount"])

            # Check that logger.info was called for the filtered line
            assert mock_logger.info.called
            call_args = str(mock_logger.info.call_args_list).lower()
            assert "pagamento recebido" in call_args

    def test_empty_description_not_affected(self):
        """Verify empty descriptions don't cause issues."""
        import csv
        from io import StringIO

        csv_content = """date,title,amount
2026-01-20,Despesa Normal,-25.00
2026-01-21,,-50.00
2026-01-22,Outra Despesa,-15.00
"""
        reader = csv.DictReader(StringIO(csv_content))
        result = _parse_credit_card(reader, ["date", "title", "amount"])

        # Should have transactions (empty descriptions won't match filter)
        assert len(result) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
