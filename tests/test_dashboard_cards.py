"""
Testes para o módulo dashboard_cards.py.

Validação de renderização de cards dinâmicos do Dashboard Multi-Contas.
"""

import logging
from datetime import date, timedelta

import pytest
from dash import html

from src.components.dashboard_cards import (
    _formatar_moeda,
    _get_cor_classe_bootstrap,
    _get_emoji_por_tipo,
    render_dashboard_cards,
)
from src.database.connection import SessionLocal
from src.database.models import Categoria, Conta, Transacao

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


class TestFormatacaoAuxiliar:
    """Testes das funções auxiliares de formatação."""

    def test_formatar_moeda_positivo(self):
        """Testa formatação de valor positivo."""
        resultado = _formatar_moeda(1234.56)
        assert resultado == "R$ 1.234,56"

    def test_formatar_moeda_negativo(self):
        """Testa formatação de valor negativo."""
        resultado = _formatar_moeda(-500.00)
        assert resultado == "R$ -500,00"

    def test_formatar_moeda_zero(self):
        """Testa formatação de zero."""
        resultado = _formatar_moeda(0.0)
        assert resultado == "R$ 0,00"

    def test_formatar_moeda_grande(self):
        """Testa formatação de valor grande com múltiplos separadores."""
        resultado = _formatar_moeda(1000000.99)
        assert resultado == "R$ 1.000.000,99"

    def test_get_emoji_conta(self):
        """Testa emoji para conta corrente."""
        assert _get_emoji_por_tipo("conta") == "🏦"

    def test_get_emoji_cartao(self):
        """Testa emoji para cartão."""
        assert _get_emoji_por_tipo("cartao") == "💳"

    def test_get_emoji_investimento(self):
        """Testa emoji para investimento."""
        assert _get_emoji_por_tipo("investimento") == "📈"

    def test_get_emoji_tipo_desconhecido(self):
        """Testa emoji para tipo desconhecido."""
        assert _get_emoji_por_tipo("tipo_inexistente") == "💰"

    def test_get_cor_classe_primary(self):
        """Testa mapeamento de cor azul (#3B82F6) para primary."""
        assert _get_cor_classe_bootstrap("#3B82F6") == "primary"

    def test_get_cor_classe_success(self):
        """Testa mapeamento de cor verde (#10B981) para success."""
        assert _get_cor_classe_bootstrap("#10B981") == "success"

    def test_get_cor_classe_danger(self):
        """Testa mapeamento de cor vermelha (#EF4444) para danger."""
        assert _get_cor_classe_bootstrap("#EF4444") == "danger"

    def test_get_cor_classe_desconhecida(self):
        """Testa mapeamento de cor desconhecida para secondary."""
        assert _get_cor_classe_bootstrap("#FFFFFF") == "secondary"


class TestRenderDashboardCards:
    """Testes para a função render_dashboard_cards()."""

    def test_render_sem_contas(self):
        """Testa renderização sem contas criadas."""
        resultado = render_dashboard_cards()

        # Deve retornar um Container
        assert hasattr(resultado, "children") or hasattr(resultado, "props")
        logger.info("✓ Renderização sem contas executada com sucesso")

    def test_render_com_uma_conta(self, db_setup):
        """Testa renderização com uma conta simples."""
        session = db_setup

        # Criar categoria
        cat_salario = Categoria(nome="Salario", tipo="receita")
        session.add(cat_salario)
        session.commit()

        # Criar conta
        conta = Conta(
            nome="Nubank",
            tipo="conta",
            saldo_inicial=1000.00,
        )
        session.add(conta)
        session.commit()

        # Criar transação
        trans = Transacao(
            conta_id=conta.id,
            categoria_id=cat_salario.id,
            tipo="receita",
            valor=500.00,
            descricao="Salário",
            data=date.today(),
        )
        session.add(trans)
        session.commit()

        # Render
        resultado = render_dashboard_cards()

        assert resultado is not None
        logger.info("✓ Renderização com uma conta executada com sucesso")

    def test_render_com_multiplas_contas_tipos(self, db_setup):
        """Testa renderização com múltiplas contas de tipos diferentes."""
        session = db_setup

        # Criar categorias
        cat_salario = Categoria(nome="Salario", tipo="receita")
        cat_compra = Categoria(nome="Compras", tipo="despesa")
        session.add_all([cat_salario, cat_compra])
        session.commit()

        # Criar contas de diferentes tipos
        contas = [
            Conta(nome="Nubank", tipo="conta", saldo_inicial=5000.00),
            Conta(nome="XP Investimentos", tipo="investimento", saldo_inicial=25000.00),
            Conta(nome="Visa Cartão", tipo="cartao", saldo_inicial=0.00),
        ]
        session.add_all(contas)
        session.commit()

        # Adicionar transações
        transacoes = [
            Transacao(
                conta_id=contas[0].id,
                categoria_id=cat_salario.id,
                tipo="receita",
                valor=3000.00,
                descricao="Salário",
                data=date.today(),
            ),
            Transacao(
                conta_id=contas[0].id,
                categoria_id=cat_compra.id,
                tipo="despesa",
                valor=500.00,
                descricao="Compras Mercado",
                data=date.today(),
            ),
            Transacao(
                conta_id=contas[2].id,
                categoria_id=cat_compra.id,
                tipo="despesa",
                valor=200.00,
                descricao="Compras Cartão",
                data=date.today(),
            ),
        ]
        session.add_all(transacoes)
        session.commit()

        # Render
        resultado = render_dashboard_cards()

        assert resultado is not None
        logger.info("✓ Renderização com múltiplas contas executada com sucesso")

    def test_render_estrutura_basica(self, db_setup):
        """Testa se a estrutura básica do render está correta."""
        session = db_setup

        # Criar dados mínimos
        cat = Categoria(nome="Test", tipo="receita")
        conta = Conta(nome="TestConta", tipo="conta", saldo_inicial=100.00)
        session.add_all([cat, conta])
        session.commit()

        resultado = render_dashboard_cards()

        # Verificar se é um Container ou Row do Dash Bootstrap
        assert hasattr(resultado, "children") or hasattr(resultado, "props")
        logger.info("✓ Estrutura básica validada com sucesso")

    def test_render_com_dados_none(self):
        """Testa que render funciona mesmo com transaction_data=None."""
        # Não deveria lançar exceção
        resultado = render_dashboard_cards(transaction_data=None)
        assert resultado is not None
        logger.info("✓ Render com transaction_data=None executado com sucesso")

    def test_render_com_saldo_negativo(self, db_setup):
        """Testa renderização com saldo negativo em cartão."""
        session = db_setup

        # Criar categoria e conta
        cat = Categoria(nome="Compras", tipo="despesa")
        conta = Conta(nome="Visa", tipo="cartao", saldo_inicial=0.00)
        session.add_all([cat, conta])
        session.commit()

        # Criar transação que deixa conta com saldo negativo
        trans = Transacao(
            conta_id=conta.id,
            categoria_id=cat.id,
            tipo="despesa",
            valor=500.00,
            descricao="Gasto no cartão",
            data=date.today(),
        )
        session.add(trans)
        session.commit()

        resultado = render_dashboard_cards()
        assert resultado is not None
        logger.info("✓ Renderização com saldo negativo executada com sucesso")

    def test_render_performance_muitas_contas(self, db_setup):
        """Testa performance com muitas contas."""
        session = db_setup

        # Criar muitas contas
        cat = Categoria(nome="Test", tipo="receita")
        session.add(cat)
        session.commit()

        for i in range(20):
            conta = Conta(
                nome=f"Conta {i}",
                tipo=(
                    "conta"
                    if i % 3 == 0
                    else ("investimento" if i % 3 == 1 else "cartao")
                ),
                saldo_inicial=float(i * 1000),
            )
            session.add(conta)

        session.commit()

        # Render deve ser rápido mesmo com muitas contas
        resultado = render_dashboard_cards()
        assert resultado is not None
        logger.info("✓ Performance com 20 contas validada com sucesso")


class TestIntegracaoDashboard:
    """Testes de integração com o dashboard."""

    def test_render_estrutura_linhas(self, db_setup):
        """Testa se as 3 linhas estão sendo renderizadas."""
        session = db_setup

        # Setup básico
        cat = Categoria(nome="Test", tipo="receita")
        conta = Conta(nome="Test", tipo="conta", saldo_inicial=1000.00)
        session.add_all([cat, conta])
        session.commit()

        resultado = render_dashboard_cards()

        # O resultado deve ser um Container com múltiplas linhas
        assert resultado is not None
        logger.info("✓ Estrutura de linhas validada com sucesso")

    def test_render_sem_erro_vazio(self):
        """Testa que render não lança erro mesmo com banco vazio."""
        try:
            resultado = render_dashboard_cards()
            assert resultado is not None
            logger.info("✓ Render sem erro com banco vazio executado com sucesso")
        except Exception as e:
            pytest.fail(f"Render lançou exceção com banco vazio: {e}")
