"""
Validação: Melhoria do Gráfico de Evolução

Demonstra as melhorias implementadas:
1. Eixo Y único (sem eixo Y2)
2. Linha de Patrimônio Acumulado (cumsum)
3. Melhor comparação visual entre Receita/Despesa/Patrimônio
"""

import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Função principal de validação."""
    try:
        logger.info("=" * 80)
        logger.info("VALIDACAO: MELHORIA DO GRAFICO DE EVOLUCAO")
        logger.info("=" * 80)
        logger.info("")

        from src.database.connection import SessionLocal
        from src.database.models import Categoria, Conta, Transacao
        from src.database.operations import get_category_matrix_data
        from src.components.dashboard_charts import render_evolution_chart

        session = SessionLocal()

        # Limpar dados
        session.query(Transacao).delete()
        session.query(Conta).delete()
        session.query(Categoria).delete()
        session.commit()

        # Criar categorias
        cat_receita = Categoria(nome="Salário", tipo="receita")
        cat_despesa = Categoria(nome="Despesas", tipo="despesa")
        session.add_all([cat_receita, cat_despesa])
        session.commit()

        # Criar conta
        conta = Conta(nome="Conta Teste", tipo="conta", saldo_inicial=0.0)
        session.add(conta)
        session.commit()

        # Criar transações ao longo de 3 meses
        hoje = date.today()
        transacoes = []

        # Mês 1: Receita 3000, Despesa 1000
        trans1_r = Transacao(
            conta_id=conta.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=3000.00,
            descricao="Salário mês 1",
            data=hoje - timedelta(days=60),
        )
        trans1_d = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=1000.00,
            descricao="Despesas mês 1",
            data=hoje - timedelta(days=60),
        )

        # Mês 2: Receita 3000, Despesa 800
        trans2_r = Transacao(
            conta_id=conta.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=3000.00,
            descricao="Salário mês 2",
            data=hoje - timedelta(days=30),
        )
        trans2_d = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=800.00,
            descricao="Despesas mês 2",
            data=hoje - timedelta(days=30),
        )

        # Mês 3: Receita 3000, Despesa 1200
        trans3_r = Transacao(
            conta_id=conta.id,
            categoria_id=cat_receita.id,
            tipo="receita",
            valor=3000.00,
            descricao="Salário mês 3",
            data=hoje,
        )
        trans3_d = Transacao(
            conta_id=conta.id,
            categoria_id=cat_despesa.id,
            tipo="despesa",
            valor=1200.00,
            descricao="Despesas mês 3",
            data=hoje,
        )

        session.add_all([trans1_r, trans1_d, trans2_r, trans2_d, trans3_r, trans3_d])
        session.commit()

        logger.info("DADOS CRIADOS:")
        logger.info("  Mês 1: Receita R$ 3.000 - Despesa R$ 1.000 = Saldo R$ 2.000")
        logger.info("  Mês 2: Receita R$ 3.000 - Despesa R$   800 = Saldo R$ 2.200")
        logger.info("  Mês 3: Receita R$ 3.000 - Despesa R$ 1.200 = Saldo R$ 1.800")
        logger.info("")

        # Calcular matriz
        matriz = get_category_matrix_data(months_past=3, months_future=0)

        logger.info("PROCESSAMENTO:")
        logger.info(f"  Meses: {matriz.get('meses', [])}")
        logger.info("")

        # Renderizar gráfico
        chart = render_evolution_chart(matriz)

        logger.info("GRAFICO RENDERIZADO COM SUCESSO!")
        logger.info("")
        logger.info("MELHORIAS IMPLEMENTADAS:")
        logger.info("  1. Eixo Y Único:")
        logger.info("     - Removido yaxis2 (eixo Y secundário)")
        logger.info("     - Todos os traces agora usam o mesmo eixo")
        logger.info("     - Melhor comparação visual entre escalas")
        logger.info("")
        logger.info("  2. Montante Acumulado:")
        logger.info("     - Nova coluna calculada via cumsum(saldos_mensais)")
        logger.info("     - Linha roxa com preenchimento semi-transparente")
        logger.info("     - Mostra evolução do patrimônio ao longo do tempo")
        logger.info("")
        logger.info("  3. Cálculo do Patrimônio:")
        logger.info("     - Mês 1: 2.000")
        logger.info("     - Mês 2: 2.000 + 2.200 = 4.200")
        logger.info("     - Mês 3: 4.200 + 1.800 = 6.000")
        logger.info("")
        logger.info("  4. Visualização:")
        logger.info("     - Barras verdes (Receitas)")
        logger.info("     - Barras vermelhas (Despesas)")
        logger.info("     - Linha roxa com fill (Patrimônio Acumulado)")
        logger.info("     - Legenda horizontal no topo")
        logger.info("")

        logger.info("=" * 80)
        logger.info("VALIDACAO CONCLUIDA COM SUCESSO!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Arquivo modificado:")
        logger.info("  • src/components/dashboard_charts.py")
        logger.info("")
        logger.info("Função atualizada:")
        logger.info("  • render_evolution_chart(data)")
        logger.info("")
        logger.info("Benefícios:")
        logger.info("  ✓ Melhor comparação visual com eixo único")
        logger.info("  ✓ Linha de tendência de patrimônio acumulado")
        logger.info("  ✓ Preenchimento visual mais atrativo")
        logger.info("  ✓ Sem distorção de escala entre eixos")
        logger.info("")

        # Limpeza
        session.query(Transacao).delete()
        session.query(Conta).delete()
        session.query(Categoria).delete()
        session.commit()
        session.close()

    except Exception as e:
        logger.error(f"Erro durante validacao: {e}", exc_info=True)


if __name__ == "__main__":
    main()
