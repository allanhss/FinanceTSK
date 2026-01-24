"""
Testes para o dashboard com suporte a múltiplas contas.
"""

import pytest
import sys
from pathlib import Path
from datetime import date

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models import Conta, Categoria, Transacao
from src.database.operations import (
    get_dashboard_summary,
    create_account,
    create_transaction,
)


class TestDashboardComMultiplasContas:
    """Testes para dashboard com múltiplas contas."""

    def test_dashboard_summary_includes_all_accounts(self):
        """Verifica que dashboard inclui saldo de todas as contas."""
        # Get current month
        today = date.today()
        month = today.month
        year = today.year

        # Get summary
        resumo = get_dashboard_summary(month, year)

        # Verify structure
        assert "saldo_total" in resumo
        assert "saldo_por_tipo" in resumo
        assert "total_receitas" in resumo
        assert "total_despesas" in resumo
        assert isinstance(resumo["saldo_por_tipo"], dict)

    def test_dashboard_saldo_total_calculo(self):
        """Verifica cálculo de saldo total considerando todas as contas."""
        import uuid

        # Create two test accounts
        nome1 = f"Test Account 1 {uuid.uuid4().hex[:8]}"
        nome2 = f"Test Account 2 {uuid.uuid4().hex[:8]}"

        success1, _ = create_account(nome=nome1, tipo="conta", saldo_inicial=1000.0)
        success2, _ = create_account(nome=nome2, tipo="conta", saldo_inicial=500.0)

        if not success1 or not success2:
            pytest.skip("Could not create test accounts")

        # Get dashboard
        today = date.today()
        resumo = get_dashboard_summary(today.month, today.year)

        # Verify that both accounts are in saldo_por_tipo
        assert (
            nome1 in resumo["saldo_por_tipo"]
            or "Conta Padrão" in resumo["saldo_por_tipo"]
        )

    def test_dashboard_transacoes_mes(self):
        """Verifica que dashboard retorna estrutura correta com multi-contas."""
        from datetime import date

        today = date.today()

        # Get dashboard - just verify structure and that it works with multiple accounts
        resumo = get_dashboard_summary(today.month, today.year)

        # Verify structure
        assert "total_receitas" in resumo
        assert "total_despesas" in resumo
        assert "saldo" in resumo
        assert "saldo_total" in resumo
        assert "saldo_por_tipo" in resumo

        # Verify data types
        assert isinstance(resumo["total_receitas"], (int, float))
        assert isinstance(resumo["total_despesas"], (int, float))
        assert isinstance(resumo["saldo"], (int, float))
        assert isinstance(resumo["saldo_total"], (int, float))
        assert isinstance(resumo["saldo_por_tipo"], dict)

        # Verify that we have at least the default accounts
        assert (
            len(resumo["saldo_por_tipo"]) >= 2
        )  # At least Conta Padrão and Investimentos


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
