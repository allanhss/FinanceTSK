"""
Testes para CRUD de Contas e validações de regra de negócio.

Verifica:
- Criação, leitura, atualização e deleção de contas
- Validações de regra de negócio em transações por tipo de conta
- Cálculo de saldo de conta
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
    create_account,
    get_accounts,
    get_account_by_id,
    update_account,
    delete_account,
    get_account_balance,
    create_transaction,
)


class TestCRUDContas:
    """Testes para CRUD de Contas."""

    def test_create_account_success(self):
        """Verifica criação de conta com sucesso."""
        import uuid

        nome = f"Test Account {uuid.uuid4().hex[:8]}"

        success, message = create_account(
            nome=nome,
            tipo="conta",
            saldo_inicial=1000.0,
        )

        assert success, f"Failed to create account: {message}"
        assert "sucesso" in message.lower()

    def test_create_account_tipo_invalido(self):
        """Verifica erro com tipo inválido."""
        success, message = create_account(
            nome="Test",
            tipo="invalid_type",
            saldo_inicial=0.0,
        )

        assert not success
        assert "Tipo" in message

    def test_create_account_saldo_negativo(self):
        """Verifica erro com saldo negativo."""
        success, message = create_account(
            nome="Test",
            tipo="conta",
            saldo_inicial=-100.0,
        )

        assert not success
        assert "negativo" in message.lower()

    def test_get_accounts_all(self):
        """Verifica recuperação de todas as contas."""
        contas = get_accounts()
        assert isinstance(contas, list)
        assert len(contas) >= 2  # At least Conta Padrão and Investimentos

    def test_get_accounts_filtered_by_tipo(self):
        """Verifica filtro de contas por tipo."""
        contas_conta = get_accounts(tipo="conta")
        assert isinstance(contas_conta, list)
        for conta in contas_conta:
            assert conta.tipo == "conta"

    def test_get_account_by_id(self):
        """Verifica recuperação de conta por ID."""
        contas = get_accounts()
        if contas:
            primeira_conta = contas[0]
            conta = get_account_by_id(primeira_conta.id)
            assert conta is not None
            assert conta.id == primeira_conta.id

    def test_get_account_by_id_not_found(self):
        """Verifica retorno None para conta não encontrada."""
        conta = get_account_by_id(99999)
        assert conta is None

    def test_update_account(self):
        """Verifica atualização de conta."""
        # Create account first
        import uuid

        nome = f"Test Account {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome, tipo="conta", saldo_inicial=100.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome).first()
            if conta:
                # Update
                novo_nome = f"Updated {uuid.uuid4().hex[:8]}"
                success, message = update_account(
                    conta_id=conta.id,
                    nome=novo_nome,
                    saldo_inicial=500.0,
                )
                assert success, f"Update failed: {message}"

    def test_delete_account_success(self):
        """Verifica deleção de conta sem transações."""
        import uuid

        nome = f"Test Account {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome, tipo="conta", saldo_inicial=0.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome).first()
            if conta:
                success, message = delete_account(conta_id=conta.id)
                assert success, f"Delete failed: {message}"

    def test_delete_account_with_transactions_fails(self):
        """Verifica que deleção de conta com transações falha."""
        # Get an account with transactions
        with get_db() as session:
            # Find any account with transactions
            conta_com_transacao = session.query(Conta).join(Transacao).first()

            if conta_com_transacao:
                success, message = delete_account(conta_id=conta_com_transacao.id)
                assert not success
                assert "transação" in message.lower()


class TestValidacaoRegraNegogio:
    """Testes para validação de regra de negócio."""

    def test_receita_em_conta_permitida(self):
        """Verifica que receita é permitida em conta corrente."""
        import uuid

        # Create conta
        nome_conta = f"Test Conta {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome_conta, tipo="conta", saldo_inicial=0.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome_conta).first()
            categoria = session.query(Categoria).filter_by(tipo="receita").first()

            if conta and categoria:
                success, message = create_transaction(
                    tipo="receita",
                    descricao="Test Income",
                    valor=100.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=conta.id,
                )
                assert success, f"Receita em conta deveria ser permitida: {message}"

    def test_receita_em_cartao_proibida(self):
        """Verifica que receita é PROIBIDA em cartão de crédito."""
        import uuid

        # Create cartão
        nome_cartao = f"Test Cartao {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome_cartao, tipo="cartao", saldo_inicial=0.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            cartao = session.query(Conta).filter_by(nome=nome_cartao).first()
            categoria = session.query(Categoria).filter_by(tipo="receita").first()

            if cartao and categoria:
                success, message = create_transaction(
                    tipo="receita",
                    descricao="Test Income on Card",
                    valor=100.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=cartao.id,
                )
                assert not success, "Receita em cartão deveria ser proibida"
                assert (
                    "receita" in message.lower() or "não permitida" in message.lower()
                )

    def test_receita_em_investimento_permitida(self):
        """Verifica que receita é permitida em investimento."""
        import uuid

        # Create investimento
        nome_inv = f"Test Inv {uuid.uuid4().hex[:8]}"
        success, _ = create_account(
            nome=nome_inv, tipo="investimento", saldo_inicial=0.0
        )

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            investimento = session.query(Conta).filter_by(nome=nome_inv).first()
            categoria = session.query(Categoria).filter_by(tipo="receita").first()

            if investimento and categoria:
                success, message = create_transaction(
                    tipo="receita",
                    descricao="Investment Income",
                    valor=100.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=investimento.id,
                )
                assert (
                    success
                ), f"Receita em investimento deveria ser permitida: {message}"

    def test_despesa_em_conta_permitida(self):
        """Verifica que despesa é permitida em conta corrente."""
        import uuid

        # Create conta
        nome_conta = f"Test Conta {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome_conta, tipo="conta", saldo_inicial=0.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome_conta).first()
            categoria = session.query(Categoria).filter_by(tipo="despesa").first()

            if conta and categoria:
                success, message = create_transaction(
                    tipo="despesa",
                    descricao="Test Expense",
                    valor=50.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=conta.id,
                )
                assert success, f"Despesa em conta deveria ser permitida: {message}"

    def test_despesa_em_cartao_permitida(self):
        """Verifica que despesa é permitida em cartão de crédito."""
        import uuid

        # Create cartão
        nome_cartao = f"Test Cartao {uuid.uuid4().hex[:8]}"
        success, _ = create_account(nome=nome_cartao, tipo="cartao", saldo_inicial=0.0)

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            cartao = session.query(Conta).filter_by(nome=nome_cartao).first()
            categoria = session.query(Categoria).filter_by(tipo="despesa").first()

            if cartao and categoria:
                success, message = create_transaction(
                    tipo="despesa",
                    descricao="Credit Card Expense",
                    valor=75.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=cartao.id,
                )
                assert success, f"Despesa em cartão deveria ser permitida: {message}"

    def test_despesa_em_investimento_proibida(self):
        """Verifica que despesa é PROIBIDA em investimento."""
        import uuid

        # Create investimento
        nome_inv = f"Test Inv {uuid.uuid4().hex[:8]}"
        success, _ = create_account(
            nome=nome_inv, tipo="investimento", saldo_inicial=0.0
        )

        if not success:
            pytest.skip("Could not create test account")

        with get_db() as session:
            investimento = session.query(Conta).filter_by(nome=nome_inv).first()
            categoria = session.query(Categoria).filter_by(tipo="despesa").first()

            if investimento and categoria:
                success, message = create_transaction(
                    tipo="despesa",
                    descricao="Investment Expense",
                    valor=50.0,
                    data=date.today(),
                    categoria_id=categoria.id,
                    conta_id=investimento.id,
                )
                assert not success, "Despesa em investimento deveria ser proibida"
                assert (
                    "despesa" in message.lower() or "não permitida" in message.lower()
                )


class TestCalculoSaldoConta:
    """Testes para cálculo de saldo de conta."""

    def test_get_account_balance_inicial(self):
        """Verifica saldo inicial de nova conta."""
        import uuid

        nome = f"Test Account {uuid.uuid4().hex[:8]}"

        create_account(nome=nome, tipo="conta", saldo_inicial=500.0)

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome).first()
            if conta:
                saldo = get_account_balance(conta.id)
                assert saldo == 500.0

    def test_get_account_balance_com_transacoes(self):
        """Verifica saldo com transações."""
        import uuid

        nome = f"Test Account {uuid.uuid4().hex[:8]}"

        create_account(nome=nome, tipo="conta", saldo_inicial=1000.0)

        conta_id = None
        categoria_id = None

        with get_db() as session:
            conta = session.query(Conta).filter_by(nome=nome).first()
            categoria = session.query(Categoria).filter_by(tipo="receita").first()
            conta_id = conta.id
            categoria_id = categoria.id

        if conta_id and categoria_id:
            # Add receita
            create_transaction(
                tipo="receita",
                descricao="Salary",
                valor=500.0,
                data=date.today(),
                categoria_id=categoria_id,
                conta_id=conta_id,
            )

        # Recalculate balance
        saldo_final = get_account_balance(conta_id)
        # Expected: 1000 (initial) + 500 (receita) - 0 (despesa) = 1500
        assert saldo_final == 1500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
