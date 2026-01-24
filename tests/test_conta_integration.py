"""
Testes de integração para o novo sistema de contas.

Verifica que:
- Contas podem ser criadas com tipos válidos
- Transações podem ser associadas a contas
- Conta padrão é usada quando conta_id não é fornecido
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
from src.database.operations import create_transaction, create_category


class TestContaModel:
    """Testes do modelo Conta."""

    def test_create_conta_valida(self):
        """Verifica se uma conta válida pode ser criada."""
        with get_db() as session:
            conta = Conta(
                nome="Banco do Brasil",
                tipo="conta",
                saldo_inicial=1000.0,
            )
            session.add(conta)
            session.commit()

            assert conta.id is not None
            assert conta.nome == "Banco do Brasil"
            assert conta.tipo == "conta"
            assert conta.saldo_inicial == 1000.0

    def test_create_conta_cartao(self):
        """Verifica se um cartão pode ser criado."""
        with get_db() as session:
            conta = Conta(
                nome="Visa Infinite",
                tipo="cartao",
                saldo_inicial=0.0,
            )
            session.add(conta)
            session.commit()

            assert conta.tipo == "cartao"

    def test_create_conta_investimento(self):
        """Verifica se uma conta de investimento pode ser criada."""
        with get_db() as session:
            conta = Conta(
                nome="XP Investimentos",
                tipo="investimento",
                saldo_inicial=5000.0,
            )
            session.add(conta)
            session.commit()

            assert conta.tipo == "investimento"
            assert conta.saldo_inicial == 5000.0

    def test_conta_tipo_invalido(self):
        """Verifica que tipo inválido lança erro."""
        with pytest.raises(ValueError):
            Conta(
                nome="Conta Inválida",
                tipo="tipo_inválido",
                saldo_inicial=0.0,
            )

    def test_conta_to_dict(self):
        """Verifica conversão de conta para dicionário."""
        with get_db() as session:
            conta = Conta(
                nome="Teste",
                tipo="conta",
                saldo_inicial=123.45,
            )
            session.add(conta)
            session.commit()

            conta_dict = conta.to_dict()
            assert conta_dict["nome"] == "Teste"
            assert conta_dict["tipo"] == "conta"
            assert conta_dict["saldo_inicial"] == 123.45
            assert "id" in conta_dict
            assert "created_at" in conta_dict
            assert conta_dict["total_transacoes"] == 0


class TestTransacaoComConta:
    """Testes de transações com contas."""

    def test_create_transacao_com_conta_id(self):
        """Verifica se transação pode ser criada com conta_id."""
        with get_db() as session:
            # Create account
            conta = Conta(nome="Test", tipo="conta")
            session.add(conta)
            session.commit()
            conta_id = conta.id

            # Create category with unique name
            import uuid

            cat_name = f"Test Category {uuid.uuid4().hex[:8]}"
            categoria = Categoria(
                nome=cat_name, tipo="despesa", icone="📝", cor="#000000"
            )
            session.add(categoria)
            session.commit()
            categoria_id = categoria.id

            # Create transaction
            transacao = Transacao(
                tipo="despesa",
                descricao="Test",
                valor=100.0,
                data=date.today(),
                conta_id=conta_id,
                categoria_id=categoria_id,
            )
            session.add(transacao)
            session.commit()

            assert transacao.conta_id == conta_id
            assert transacao.categoria_id == categoria_id

    def test_transacao_relacionamento_conta(self):
        """Verifica relacionamento entre Transacao e Conta."""
        with get_db() as session:
            # Create account
            conta = Conta(nome="Test Account", tipo="conta")
            session.add(conta)
            session.commit()
            conta_id = conta.id

            # Create category with unique name
            import uuid

            cat_name = f"Test Category {uuid.uuid4().hex[:8]}"
            categoria = Categoria(
                nome=cat_name, tipo="despesa", icone="📝", cor="#000000"
            )
            session.add(categoria)
            session.commit()

            # Create transaction
            transacao = Transacao(
                tipo="despesa",
                descricao="Test",
                valor=100.0,
                data=date.today(),
                conta_id=conta_id,
                categoria_id=categoria.id,
            )
            session.add(transacao)
            session.commit()

            # Retrieve and check relationship
            retrieved_transacao = (
                session.query(Transacao).filter_by(id=transacao.id).first()
            )

            assert retrieved_transacao.conta_id == conta_id
            assert retrieved_transacao.conta.nome == "Test Account"


class TestContaDefaults:
    """Testes de contas padrão."""

    def test_default_accounts_exist(self):
        """Verifica que contas padrão foram criadas."""
        with get_db() as session:
            contas_padrao = (
                session.query(Conta)
                .filter(Conta.nome.in_(["Conta Padrão", "Investimentos"]))
                .all()
            )

            # We expect at least these 2 accounts to exist after init
            assert (
                len(contas_padrao) >= 2
            ), f"Expected at least 2 default accounts, found {len(contas_padrao)}"

    def test_conta_padrao_operations(self):
        """Verifica operações com conta padrão."""
        with get_db() as session:
            conta = session.query(Conta).filter_by(nome="Conta Padrão").first()
            assert conta is not None
            assert conta.tipo == "conta"

            conta_dict = conta.to_dict()
            assert conta_dict["nome"] == "Conta Padrão"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
