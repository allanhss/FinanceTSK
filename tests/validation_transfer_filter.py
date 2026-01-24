"""
Validação: Filtro de Exclusão de "Transferência Interna" nos Relatórios Analíticos

Este script testa se as funções de análise corretamente excluem transações
categorizadas como "Transferência Interna" dos cálculos, mas as mantêm
no saldo das contas.

Cenário de teste:
1. Criar categorias: Salário (receita), Alimentação (despesa), Transfer. Interna (despesa)
2. Criar transações de ambos os tipos
3. Verificar que:
   - get_dashboard_summary exclui transferências
   - get_cash_flow_data exclui transferências
   - get_category_matrix_data exclui transferências
   - Saldo das contas NOT é afetado
"""

import os
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Configurar modo teste
os.environ["TESTING_MODE"] = "1"

from src.database.connection import SessionLocal, Base, engine
from src.database.models import Categoria, Transacao, Conta
from src.database.operations import (
    get_dashboard_summary,
    get_cash_flow_data,
    get_category_matrix_data,
    get_account_balance,
)


def setup_test_data():
    """Criar dados de teste com transações reais e transferências."""
    session = SessionLocal()

    # Limpar dados anteriores
    session.query(Transacao).delete()
    session.query(Categoria).delete()
    session.query(Conta).delete()

    # Criar categorias
    cat_salario = Categoria(
        nome="Salário",
        tipo="receita",
        icone="💰",
        cor="#22C55E",
    )
    cat_alimentacao = Categoria(
        nome="Alimentação",
        tipo="despesa",
        icone="🍔",
        cor="#F97316",
    )
    cat_transferencia = Categoria(
        nome="Transferência Interna",
        tipo="despesa",
        icone="🔄",
        cor="#6B7280",
    )

    session.add_all([cat_salario, cat_alimentacao, cat_transferencia])
    session.flush()

    # Criar conta
    conta = Conta(
        nome="Conta Corrente",
        tipo="conta",
        saldo_inicial=1000.0,
    )
    session.add(conta)
    session.flush()

    today = date.today()
    primeiro_dia = today.replace(day=1)

    # ===== TRANSAÇÕES DO MÊS =====
    # Receita real: Salário
    t1 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_salario.id,
        tipo="receita",
        valor=5000.0,
        descricao="Salário Mensal",
        data=primeiro_dia + timedelta(days=1),
    )

    # Despesa real: Alimentação
    t2 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        tipo="despesa",
        valor=500.0,
        descricao="Supermercado",
        data=primeiro_dia + timedelta(days=5),
    )

    # Transferência interna: Pagamento de fatura (NÃO deve contar na análise)
    t3 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transferencia.id,
        tipo="despesa",
        valor=2000.0,
        descricao="Pagamento fatura cartão",
        data=primeiro_dia + timedelta(days=10),
    )

    # Transferência interna: Resgate PIX (NÃO deve contar na análise)
    t4 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transferencia.id,
        tipo="receita",
        valor=1000.0,
        descricao="Resgate aplicação",
        data=primeiro_dia + timedelta(days=15),
    )

    session.add_all([t1, t2, t3, t4])
    session.commit()

    print("✅ Dados de teste criados:")
    print(f"   - Categoria Salário (receita)")
    print(f"   - Categoria Alimentação (despesa)")
    print(f"   - Categoria Transferência Interna (despesa)")
    print(f"   - Conta Corrente com saldo inicial R$ 1.000,00")
    print()

    return conta, session


def test_dashboard_summary_excludes_transfers():
    """Verificar se get_dashboard_summary exclui transferências."""
    conta, session = setup_test_data()

    today = date.today()
    month = today.month
    year = today.year

    resumo = get_dashboard_summary(month, year)

    # ===== VERIFICAÇÕES =====
    # Receitas REAIS devem ser apenas o salário (5000)
    # NÃO deve incluir o resgate (1000)
    receitas_esperadas = 5000.0
    receitas_reais = resumo["total_receitas"]

    # Despesas REAIS devem ser apenas alimentação (500)
    # NÃO deve incluir o pagamento de fatura (2000)
    despesas_esperadas = 500.0
    despesas_reais = resumo["total_despesas"]

    # Saldo do mês = receitas - despesas (sem transferências)
    saldo_mes_esperado = receitas_esperadas - despesas_esperadas
    saldo_mes_real = resumo["saldo"]

    # Saldo total da conta DEVE incluir TUDO (saldo_inicial + receitas - despesas)
    # = 1000 + 5000 + 1000 - 500 - 2000 = 4500
    saldo_total_esperado = 4500.0
    saldo_total_real = resumo["saldo_total"]

    print("📊 get_dashboard_summary() - Teste de Exclusão de Transferências")
    print(f"   Receitas esperadas (sem transferências): R$ {receitas_esperadas:.2f}")
    print(f"   Receitas calculadas: R$ {receitas_reais:.2f}")
    print(f"   ✓ PASS" if receitas_reais == receitas_esperadas else f"   ✗ FAIL")
    print()

    print(f"   Despesas esperadas (sem transferências): R$ {despesas_esperadas:.2f}")
    print(f"   Despesas calculadas: R$ {despesas_reais:.2f}")
    print(f"   ✓ PASS" if despesas_reais == despesas_esperadas else f"   ✗ FAIL")
    print()

    print(f"   Saldo mês esperado: R$ {saldo_mes_esperado:.2f}")
    print(f"   Saldo mês calculado: R$ {saldo_mes_real:.2f}")
    print(f"   ✓ PASS" if saldo_mes_real == saldo_mes_esperado else f"   ✗ FAIL")
    print()

    print(
        f"   Saldo total esperado (inclui transferências): R$ {saldo_total_esperado:.2f}"
    )
    print(f"   Saldo total calculado: R$ {saldo_total_real:.2f}")
    print(f"   ✓ PASS" if saldo_total_real == saldo_total_esperado else f"   ✗ FAIL")
    print()

    assert (
        receitas_reais == receitas_esperadas
    ), f"Receitas incorretas: {receitas_reais}"
    assert (
        despesas_reais == despesas_esperadas
    ), f"Despesas incorretas: {despesas_reais}"
    assert (
        saldo_mes_real == saldo_mes_esperado
    ), f"Saldo do mês incorreto: {saldo_mes_real}"
    assert (
        saldo_total_real == saldo_total_esperado
    ), f"Saldo total incorreto: {saldo_total_real}"

    session.close()


def test_cash_flow_excludes_transfers():
    """Verificar se get_cash_flow_data exclui transferências."""
    conta, session = setup_test_data()

    fluxo = get_cash_flow_data(months_past=1, months_future=1)

    # Encontrar o mês atual nos dados
    today = date.today()
    mes_atual = today.strftime("%Y-%m")

    mes_data = None
    for mes_info in fluxo:
        if mes_info["mes"] == mes_atual:
            mes_data = mes_info
            break

    assert mes_data is not None, f"Dados do mês {mes_atual} não encontrados"

    receitas_esperadas = 5000.0  # Apenas salário
    despesas_esperadas = 500.0  # Apenas alimentação
    saldo_esperado = receitas_esperadas - despesas_esperadas

    print("💹 get_cash_flow_data() - Teste de Exclusão de Transferências")
    print(f"   Mês analisado: {mes_atual}")
    print()

    print(f"   Receitas esperadas: R$ {receitas_esperadas:.2f}")
    print(f"   Receitas calculadas: R$ {mes_data['receitas']:.2f}")
    print(f"   ✓ PASS" if mes_data["receitas"] == receitas_esperadas else f"   ✗ FAIL")
    print()

    print(f"   Despesas esperadas: R$ {despesas_esperadas:.2f}")
    print(f"   Despesas calculadas: R$ {mes_data['despesas']:.2f}")
    print(f"   ✓ PASS" if mes_data["despesas"] == despesas_esperadas else f"   ✗ FAIL")
    print()

    print(f"   Saldo esperado: R$ {saldo_esperado:.2f}")
    print(f"   Saldo calculado: R$ {mes_data['saldo']:.2f}")
    print(f"   ✓ PASS" if mes_data["saldo"] == saldo_esperado else f"   ✗ FAIL")
    print()

    assert mes_data["receitas"] == receitas_esperadas
    assert mes_data["despesas"] == despesas_esperadas
    assert mes_data["saldo"] == saldo_esperado

    session.close()


def test_category_matrix_excludes_transfers():
    """Verificar se get_category_matrix_data exclui transferências."""
    conta, session = setup_test_data()

    matriz = get_category_matrix_data(months_past=1, months_future=1)

    # Verificar que "Transferência Interna" NÃO aparece na matriz
    nomes_despesas = [cat["nome"] for cat in matriz["despesas"]]
    nomes_receitas = [cat["nome"] for cat in matriz["receitas"]]

    print("📈 get_category_matrix_data() - Teste de Exclusão de Transferências")
    print()

    print(f"   Categorias de Receita: {nomes_receitas}")
    print(
        f"   ✓ PASS: Salário presente" if "Salário" in nomes_receitas else "   ✗ FAIL"
    )
    print(
        f"   ✓ PASS: Transfer. Interna ausente"
        if "Transferência Interna" not in nomes_receitas
        else "   ✗ FAIL"
    )
    print()

    print(f"   Categorias de Despesa: {nomes_despesas}")
    print(
        f"   ✓ PASS: Alimentação presente"
        if "Alimentação" in nomes_despesas
        else "   ✗ FAIL"
    )
    print(
        f"   ✓ PASS: Transfer. Interna ausente"
        if "Transferência Interna" not in nomes_despesas
        else "   ✗ FAIL"
    )
    print()

    assert "Salário" in nomes_receitas, "Salário não encontrado em receitas"
    assert "Alimentação" in nomes_despesas, "Alimentação não encontrada em despesas"
    assert (
        "Transferência Interna" not in nomes_receitas
    ), "Transferência Interna deveria estar ausente de receitas"
    assert (
        "Transferência Interna" not in nomes_despesas
    ), "Transferência Interna deveria estar ausente de despesas"

    session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("🔬 VALIDAÇÃO: Filtro de 'Transferência Interna' em Relatórios")
    print("=" * 70)
    print()

    try:
        test_dashboard_summary_excludes_transfers()
        test_cash_flow_excludes_transfers()
        test_category_matrix_excludes_transfers()

        print("=" * 70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print()
        print("Resumo:")
        print("  ✓ get_dashboard_summary() exclui transferências corretamente")
        print("  ✓ get_cash_flow_data() exclui transferências corretamente")
        print("  ✓ get_category_matrix_data() exclui transferências corretamente")
        print("  ✓ Saldo total das contas INCLUI transferências (como esperado)")
        print()
        print(
            "Garantido: KPIs refletem consumo e ganho REAL, ignorando movimentações internas!"
        )
        print()

    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TESTE FALHOU: {e}")
        print("=" * 70)
        exit(1)
