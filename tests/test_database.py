"""
Testes para operações de banco de dados.

Cobre modelos, operações CRUD e validações do sistema FinanceTSK.
"""

import pytest
from datetime import date
from pathlib import Path
import sys

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import init_database, get_db
from src.database.models import Categoria, Transacao, Conta
from src.database.operations import (
    create_category,
    get_categories,
    create_transaction,
    get_transactions,
    get_dashboard_summary,
)


def _get_default_account_id():
    """Get default account ID for tests."""
    with get_db() as session:
        conta = session.query(Conta).filter_by(nome="Conta Padrão").first()
        return conta.id if conta else 1


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Inicializa banco de dados antes de cada teste."""
    init_database()
    yield
    # Cleanup se necessário
    with get_db() as session:
        session.query(Transacao).delete()
        session.query(Categoria).delete()
        session.commit()


class TestTransacao:
    """Testes para operações de transação."""

    def test_criar_transacao_despesa(self):
        """Testa criação de transação de despesa."""
        # Criar categoria
        create_category("Alimentação", "despesa")
        categorias = get_categories(tipo="despesa")
        cat_id = next(c["id"] for c in categorias if c["nome"] == "Alimentação")
        conta_id = _get_default_account_id()

        # Criar transação
        success, msg = create_transaction(
            tipo="despesa",
            descricao="Compra no mercado",
            valor=150.50,
            data=date(2026, 1, 19),
            categoria_id=cat_id,
            conta_id=conta_id,
        )
        assert success
        assert "sucesso" in msg.lower()

    def test_criar_transacao_receita(self):
        """Testa criação de transação de receita."""
        # Criar categoria
        create_category("Salário", "receita")
        categorias = get_categories(tipo="receita")
        cat_id = next(c["id"] for c in categorias if c["nome"] == "Salário")
        conta_id = _get_default_account_id()

        # Criar transação
        success, msg = create_transaction(
            tipo="receita",
            descricao="Salário de janeiro",
            valor=5000.00,
            data=date(2026, 1, 19),
            categoria_id=cat_id,
            conta_id=conta_id,
        )
        assert success

    def test_transacao_tipo_invalido(self):
        """Testa validação de tipo de transação."""
        create_category("Test", "despesa")
        cat_id = get_categories()[0]["id"]
        conta_id = _get_default_account_id()

        success, msg = create_transaction(
            tipo="invalido",
            descricao="Test",
            valor=100.0,
            data=date(2026, 1, 19),
            categoria_id=cat_id,
            conta_id=conta_id,
        )
        assert not success

    def test_transacao_valor_negativo(self):
        """Testa validação de valor negativo."""
        create_category("Test", "despesa")
        cat_id = get_categories()[0]["id"]
        conta_id = _get_default_account_id()

        success, msg = create_transaction(
            tipo="despesa",
            descricao="Test",
            valor=-100.0,
            data=date(2026, 1, 19),
            categoria_id=cat_id,
            conta_id=conta_id,
        )
        assert not success

    def test_get_transactions(self):
        """Testa recuperação de transações."""
        create_category("Test", "despesa")
        cat_id = get_categories()[0]["id"]
        conta_id = _get_default_account_id()

        create_transaction(
            tipo="despesa",
            descricao="T1",
            valor=100.0,
            data=date(2026, 1, 15),
            categoria_id=cat_id,
            conta_id=conta_id,
        )
        create_transaction(
            tipo="despesa",
            descricao="T2",
            valor=200.0,
            data=date(2026, 1, 18),
            categoria_id=cat_id,
            conta_id=conta_id,
        )

        transacoes = get_transactions()
        assert len(transacoes) >= 2

    def test_get_dashboard_summary(self):
        """Testa resumo do dashboard."""
        from src.database.models import Conta

        # Criar categorias
        create_category("Salário", "receita")
        create_category("Alimentação", "despesa")

        # Get default account
        with get_db() as session:
            conta = session.query(Conta).filter_by(nome="Conta Padrão").first()
            conta_id = conta.id if conta else 1

        categorias = get_categories()
        cat_receita = next(c for c in categorias if c["tipo"] == "receita")
        cat_despesa = next(c for c in categorias if c["tipo"] == "despesa")

        # Criar transações
        create_transaction(
            tipo="receita",
            descricao="Renda",
            valor=5000.0,
            data=date(2026, 1, 19),
            categoria_id=cat_receita["id"],
            conta_id=conta_id,
        )
        create_transaction(
            tipo="despesa",
            descricao="Comida",
            valor=500.0,
            data=date(2026, 1, 19),
            categoria_id=cat_despesa["id"],
            conta_id=conta_id,
        )

        resumo = get_dashboard_summary(month=1, year=2026)

        assert resumo["total_receitas"] == 5000.0
        assert resumo["total_despesas"] == 500.0
        assert resumo["saldo"] == 4500.0
