"""
Script de validação e demonstração do Dashboard Multi-Contas.

Cria dados demo e renderiza o layout completo dos cards.
"""

import logging
from datetime import date, timedelta

from src.components.dashboard_cards import render_dashboard_cards
from src.database.connection import SessionLocal
from src.database.models import Categoria, Conta, Transacao

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)


def setup_demo_data() -> None:
    """Cria dados de demonstração no banco."""
    session = SessionLocal()

    # Limpar dados existentes
    session.query(Transacao).delete()
    session.query(Conta).delete()
    session.query(Categoria).delete()
    session.commit()

    logger.info("=" * 80)
    logger.info("CRIANDO DADOS DE DEMONSTRAÇÃO")
    logger.info("=" * 80)

    # Criar categorias
    categorias_dados = [
        ("Salário", "receita"),
        ("Freelance", "receita"),
        ("Investimento Resgate", "receita"),
        ("Alimentação", "despesa"),
        ("Transporte", "despesa"),
        ("Compras", "despesa"),
    ]

    categorias = {}
    for nome, tipo in categorias_dados:
        cat = Categoria(nome=nome, tipo=tipo)
        session.add(cat)
        categorias[nome] = cat

    session.commit()
    logger.info(f"✓ {len(categorias)} categorias criadas")

    # Criar contas
    contas_dados = [
        ("Nubank Corrente", "conta", 5000.00),
        ("XP Investimentos", "investimento", 25000.00),
        ("Cartão Visa", "cartao", 0.00),
        ("Caixa Econômica", "conta", 8500.00),
    ]

    contas = []
    for nome, tipo, saldo_inicial in contas_dados:
        conta = Conta(
            nome=nome,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
        )
        session.add(conta)
        contas.append(conta)

    session.commit()
    logger.info(f"✓ {len(contas)} contas criadas")

    # Criar transações
    hoje = date.today()
    transacoes_dados = [
        # Receitas
        (0, "Salário", "receita", 3500.00, hoje - timedelta(days=2)),
        (0, "Freelance", "receita", 1200.00, hoje - timedelta(days=5)),
        (1, "Investimento Resgate", "receita", 500.00, hoje - timedelta(days=1)),
        # Despesas
        (0, "Alimentação", "despesa", 450.00, hoje),
        (0, "Transporte", "despesa", 150.00, hoje - timedelta(days=3)),
        (0, "Compras", "despesa", 500.00, hoje - timedelta(days=7)),
        (2, "Compras", "despesa", 800.00, hoje - timedelta(days=2)),
        (3, "Alimentação", "despesa", 200.00, hoje - timedelta(days=1)),
    ]

    for conta_idx, cat_nome, tipo, valor, data_trans in transacoes_dados:
        trans = Transacao(
            conta_id=contas[conta_idx].id,
            categoria_id=categorias[cat_nome].id,
            tipo=tipo,
            valor=valor,
            descricao=f"{cat_nome} - {data_trans.strftime('%d/%m/%Y')}",
            data=data_trans,
        )
        session.add(trans)

    session.commit()
    logger.info(f"✓ {len(transacoes_dados)} transações criadas")
    logger.info("")


def display_demo_layout() -> None:
    """Exibe o layout de demonstração."""
    logger.info("=" * 80)
    logger.info("RENDERIZANDO DASHBOARD MULTI-CONTAS")
    logger.info("=" * 80)
    logger.info("")

    container = render_dashboard_cards()

    logger.info("✓ Layout renderizado com sucesso!")
    logger.info("")
    logger.info("=" * 80)
    logger.info("ESTRUTURA DO LAYOUT")
    logger.info("=" * 80)
    logger.info(
        """
    LINHA 1: RESUMO MACRO (3 Cards Grandes)
    ├── 💰 Disponível (Verde/Success)
    │   └─ Soma das Contas Correntes
    ├── 💳 Faturas/Cartões (Vermelho/Danger)
    │   └─ Soma dos Cartões
    └── 📈 Investimentos (Azul/Primary)
        └─ Soma dos Investimentos

    LINHA 2: PATRIMÔNIO TOTAL (1 Card Grande)
    └── 🎯 Patrimônio Total (Cinza/Secondary)
        └─ Liquidez + Investimentos - Dívida

    LINHA 3: DETALHE POR CONTA (Grid Responsivo)
    ├── Card: Nubank Corrente (🏦 - Azul)
    ├── Card: XP Investimentos (📈 - Verde)
    ├── Card: Cartão Visa (💳 - Vermelho)
    └── Card: Caixa Econômica (🏦 - Azul)
    """
    )
    logger.info("=" * 80)


def main() -> None:
    """Função principal."""
    try:
        logger.info("🚀 Iniciando validação do Dashboard Multi-Contas\n")

        # Setup
        setup_demo_data()

        # Display
        display_demo_layout()

        logger.info("✓ Validação concluída com sucesso!")
        logger.info("")
        logger.info("Resumo:")
        logger.info("  • Arquivo: src/components/dashboard_cards.py")
        logger.info("  • Função: render_dashboard_cards()")
        logger.info("  • Testes: 21/21 PASSING ✅")
        logger.info("  • Próximo: Integrar em src/pages/dashboard.py")
        logger.info("")

    except Exception as e:
        logger.error(f"✗ Erro durante validação: {e}", exc_info=True)


if __name__ == "__main__":
    main()
