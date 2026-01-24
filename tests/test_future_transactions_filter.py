"""
Teste específico para validar o filtro de transações futuras.

Verifica que transações futuras são ignoradas no cálculo de saldo.
"""

import logging
from datetime import date, timedelta

import pytest

from src.database.connection import SessionLocal
from src.database.models import Categoria, Conta, Transacao
from src.database.operations import get_account_balances_summary

logger = logging.getLogger(__name__)


@pytest.fixture
def db_setup():
    """Fixture para configurar banco de dados limpo."""
    session = SessionLocal()

    # Limpar dados existentes
    session.query(Transacao).delete()
    session.query(Conta).delete()
    session.query(Categoria).delete()
    session.commit()

    yield session

    # Limpeza
    session.query(Transacao).delete()
    session.query(Conta).delete()
    session.query(Categoria).delete()
    session.commit()
    session.close()


class TestTransacoesFuturas:
    """Testes para validar filtro de transações futuras."""

    def test_ignora_transacoes_futuras(self, db_setup):
        """
        Testa que transações futuras não são incluídas no saldo atual.

        Cenário:
        - Saldo inicial: R$ 1000
        - Transação hoje (passada): +R$ 500 (receita)
        - Transação futura: +R$ 5000 (receita)
        - Resultado esperado: R$ 1500 (não inclui os 5000)
        """
        session = db_setup

        # Criar categoria
        cat_salario = Categoria(nome="Salario", tipo="receita")
        session.add(cat_salario)
        session.commit()

        # Criar conta
        conta = Conta(
            nome="Conta Teste",
            tipo="conta",
            saldo_inicial=1000.00,
        )
        session.add(conta)
        session.commit()

        hoje = date.today()

        # Transação passada (deve ser incluída)
        trans_hoje = Transacao(
            conta_id=conta.id,
            categoria_id=cat_salario.id,
            tipo="receita",
            valor=500.00,
            descricao="Salário hoje",
            data=hoje,
        )

        # Transação futura (NÃO deve ser incluída)
        trans_futura = Transacao(
            conta_id=conta.id,
            categoria_id=cat_salario.id,
            tipo="receita",
            valor=5000.00,
            descricao="Salário futuro (recorrente)",
            data=hoje + timedelta(days=30),
        )

        session.add_all([trans_hoje, trans_futura])
        session.commit()

        # Obter resumo
        resumo = get_account_balances_summary()

        # Validações
        conta_info = resumo["detalhe_por_conta"][0]

        # Saldo deve ser: 1000 (inicial) + 500 (hoje) - 0 (futura ignorada) = 1500
        assert conta_info["saldo"] == 1500.00, (
            f"Saldo incorreto. Esperado 1500.00, obtido {conta_info['saldo']}. "
            f"Transação futura foi incluída indevidamente."
        )

        logger.info(
            f"✓ Transações futuras ignoradas corretamente: R$ {conta_info['saldo']}"
        )

    def test_inclui_transacoes_passadas(self, db_setup):
        """
        Testa que transações passadas JSOU incluídas no saldo.

        Cenário:
        - Saldo inicial: R$ 1000
        - Transação 10 dias atrás: +R$ 500
        - Transação ontem: +R$ 200
        - Resultado esperado: R$ 1700
        """
        session = db_setup

        # Criar categoria
        cat_salario = Categoria(nome="Salario", tipo="receita")
        session.add(cat_salario)
        session.commit()

        # Criar conta
        conta = Conta(
            nome="Conta Teste",
            tipo="conta",
            saldo_inicial=1000.00,
        )
        session.add(conta)
        session.commit()

        hoje = date.today()

        # Transações passadas
        trans_10_dias_atras = Transacao(
            conta_id=conta.id,
            categoria_id=cat_salario.id,
            tipo="receita",
            valor=500.00,
            descricao="Salário 10 dias atrás",
            data=hoje - timedelta(days=10),
        )

        trans_ontem = Transacao(
            conta_id=conta.id,
            categoria_id=cat_salario.id,
            tipo="receita",
            valor=200.00,
            descricao="Salário ontem",
            data=hoje - timedelta(days=1),
        )

        session.add_all([trans_10_dias_atras, trans_ontem])
        session.commit()

        # Obter resumo
        resumo = get_account_balances_summary()

        # Validações
        conta_info = resumo["detalhe_por_conta"][0]

        # Saldo deve ser: 1000 (inicial) + 500 + 200 = 1700
        assert conta_info["saldo"] == 1700.00, (
            f"Saldo incorreto. Esperado 1700.00, obtido {conta_info['saldo']}. "
            f"Transações passadas não foram incluídas."
        )

        logger.info(
            f"✓ Transações passadas incluídas corretamente: R$ {conta_info['saldo']}"
        )

    def test_despesas_futuras_nao_afetam_saldo(self, db_setup):
        """
        Testa que despesas futuras não reduzem o saldo atual.

        Cenário:
        - Saldo inicial: R$ 1000
        - Despesa hoje: -R$ 100
        - Despesa futura: -R$ 500
        - Resultado esperado: R$ 900 (não inclui a despesa futura)
        """
        session = db_setup

        # Criar categoria
        cat_despesa = Categoria(nome="Compras", tipo="despesa")
        session.add(cat_despesa)
        session.commit()

        # Criar conta
        conta = Conta(
            nome="Conta Teste",
            tipo="conta",
            saldo_inicial=1000.00,
        )
        session.add(conta)
        session.commit()

        hoje = date.today()

        # Despesa hoje (deve ser incluída)
        trans_hoje = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=100.00,
            descricao="Compra hoje",
            data=hoje,
        )

        # Despesa futura (NÃO deve ser incluída)
        trans_futura = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=500.00,
            descricao="Compra futura",
            data=hoje + timedelta(days=7),
        )

        session.add_all([trans_hoje, trans_futura])
        session.commit()

        # Obter resumo
        resumo = get_account_balances_summary()

        # Validações
        conta_info = resumo["detalhe_por_conta"][0]

        # Saldo deve ser: 1000 (inicial) - 100 (hoje) - 0 (futura ignorada) = 900
        assert conta_info["saldo"] == 900.00, (
            f"Saldo incorreto. Esperado 900.00, obtido {conta_info['saldo']}. "
            f"Despesa futura foi incluída indevidamente."
        )

        logger.info(
            f"✓ Despesas futuras ignoradas corretamente: R$ {conta_info['saldo']}"
        )

    def test_saldo_com_mix_passadas_futuras(self, db_setup):
        """
        Testa cenário misto com múltiplas transações passadas e futuras.

        Cenário:
        - Saldo inicial: R$ 5000
        - Receitas passadas: +R$ 1000
        - Despesas passadas: -R$ 200
        - Receitas futuras: +R$ 3000 (devem ser ignoradas)
        - Despesas futuras: -R$ 500 (devem ser ignoradas)
        - Resultado esperado: R$ 5800 (5000 + 1000 - 200)
        """
        session = db_setup

        # Criar categorias
        cat_receita = Categoria(nome="Receita", tipo="receita")
        cat_despesa = Categoria(nome="Despesa", tipo="despesa")
        session.add_all([cat_receita, cat_despesa])
        session.commit()

        # Criar conta
        conta = Conta(
            nome="Conta Mista",
            tipo="conta",
            saldo_inicial=5000.00,
        )
        session.add(conta)
        session.commit()

        hoje = date.today()

        # Transações passadas
        trans_receita_passada = Transacao(
            conta_id=conta.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=1000.00,
            descricao="Receita passada",
            data=hoje - timedelta(days=5),
        )

        trans_despesa_passada = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=200.00,
            descricao="Despesa passada",
            data=hoje - timedelta(days=3),
        )

        # Transações futuras (devem ser ignoradas)
        trans_receita_futura = Transacao(
            conta_id=conta.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=3000.00,
            descricao="Receita futura",
            data=hoje + timedelta(days=30),
        )

        trans_despesa_futura = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=500.00,
            descricao="Despesa futura",
            data=hoje + timedelta(days=15),
        )

        session.add_all(
            [
                trans_receita_passada,
                trans_despesa_passada,
                trans_receita_futura,
                trans_despesa_futura,
            ]
        )
        session.commit()

        # Obter resumo
        resumo = get_account_balances_summary()

        # Validações
        conta_info = resumo["detalhe_por_conta"][0]

        # Saldo esperado: 5000 + 1000 - 200 = 5800
        expected_saldo = 5800.00
        assert conta_info["saldo"] == expected_saldo, (
            f"Saldo incorreto. Esperado {expected_saldo}, obtido {conta_info['saldo']}. "
            f"Transações futuras podem ter sido incluídas."
        )

        logger.info(f"✓ Saldo misto calculado corretamente: R$ {conta_info['saldo']}")

    def test_patrimonio_ignora_futuras(self, db_setup):
        """
        Testa que o patrimônio total também ignora transações futuras.

        Cenário:
        - Conta corrente: R$ 1000 (inicial) + R$ 500 (passada) + R$ 5000 (futura)
        - Investimento: R$ 10000 (inicial) + R$ 1000 (futura)
        - Cartão: R$ 0 (inicial) - R$ 100 (passada) - R$ 500 (futura)
        - Total esperado: (1500) + (10000) + (-100) = 11400
          (não inclui 5000 + 1000 - 500 = 5500 em transações futuras)
        """
        session = db_setup

        # Criar categorias
        cat_receita = Categoria(nome="Receita", tipo="receita")
        cat_despesa = Categoria(nome="Despesa", tipo="despesa")
        session.add_all([cat_receita, cat_despesa])
        session.commit()

        # Criar contas de diferentes tipos
        conta_corrente = Conta(nome="Corrente", tipo="conta", saldo_inicial=1000.00)
        conta_investimento = Conta(
            nome="Investimento", tipo="investimento", saldo_inicial=10000.00
        )
        conta_cartao = Conta(nome="Cartão", tipo="cartao", saldo_inicial=0.00)

        session.add_all([conta_corrente, conta_investimento, conta_cartao])
        session.commit()

        hoje = date.today()

        # Transações para conta corrente
        trans_corrente_passada = Transacao(
            conta_id=conta_corrente.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=500.00,
            data=hoje - timedelta(days=1),
            descricao="Receita passada",
        )
        trans_corrente_futura = Transacao(
            conta_id=conta_corrente.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=5000.00,
            data=hoje + timedelta(days=30),
            descricao="Receita futura",
        )

        # Transações para investimento
        trans_investimento_futura = Transacao(
            conta_id=conta_investimento.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=1000.00,
            data=hoje + timedelta(days=15),
            descricao="Investimento futuro",
        )

        # Transações para cartão
        trans_cartao_passada = Transacao(
            conta_id=conta_cartao.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=100.00,
            data=hoje - timedelta(days=2),
            descricao="Despesa passada",
        )
        trans_cartao_futura = Transacao(
            conta_id=conta_cartao.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=500.00,
            data=hoje + timedelta(days=7),
            descricao="Despesa futura",
        )

        session.add_all(
            [
                trans_corrente_passada,
                trans_corrente_futura,
                trans_investimento_futura,
                trans_cartao_passada,
                trans_cartao_futura,
            ]
        )
        session.commit()

        # Obter resumo
        resumo = get_account_balances_summary()

        # Validações
        # Corrente: 1000 + 500 = 1500
        # Investimento: 10000
        # Cartão: -100
        # Total esperado: 1500 + 10000 - 100 = 11400
        expected_patrimonio = 11400.00

        assert resumo["patrimonio_total"] == expected_patrimonio, (
            f"Patrimônio incorreto. Esperado {expected_patrimonio}, "
            f"obtido {resumo['patrimonio_total']}. "
            f"Transações futuras podem ter afetado o cálculo."
        )

        logger.info(
            f"✓ Patrimônio calculado corretamente (sem futuras): R$ {resumo['patrimonio_total']}"
        )
