"""
Validação: Exclusão de "Transferência Interna" da Listagem de Despesas

Verifica que:
1. get_transactions() com exclude_transfers=False retorna todas as transações
2. get_transactions() com exclude_transfers=True retorna sem "Transferência Interna"
3. Parámetro é opcional e padrão é False (backward compatible)
"""

import os
from datetime import date

os.environ["TESTING_MODE"] = "1"

from src.database.connection import SessionLocal
from src.database.models import Categoria, Transacao, Conta
from src.database.operations import get_transactions


def setup_test_data():
    """Criar dados de teste com despesas reais e transferências."""
    session = SessionLocal()

    # Limpar dados anteriores
    session.query(Transacao).delete()
    session.query(Categoria).delete()
    session.query(Conta).delete()

    # Criar categorias
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

    session.add_all([cat_alimentacao, cat_transferencia])
    session.flush()

    # Criar conta
    conta = Conta(
        nome="Conta Corrente",
        tipo="conta",
        saldo_inicial=1000.0,
    )
    session.add(conta)
    session.flush()

    # Criar transações
    # Despesa real
    t1 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        tipo="despesa",
        valor=500.0,
        descricao="Supermercado",
        data=date(2026, 1, 20),
    )

    # Despesa real
    t2 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_alimentacao.id,
        tipo="despesa",
        valor=150.0,
        descricao="Restaurante",
        data=date(2026, 1, 15),
    )

    # Transferência interna (despesa)
    t3 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transferencia.id,
        tipo="despesa",
        valor=2000.0,
        descricao="Pagamento fatura cartão",
        data=date(2026, 1, 10),
    )

    # Transferência interna (despesa)
    t4 = Transacao(
        conta_id=conta.id,
        categoria_id=cat_transferencia.id,
        tipo="despesa",
        valor=500.0,
        descricao="Resgate PIX",
        data=date(2026, 1, 5),
    )

    session.add_all([t1, t2, t3, t4])
    session.commit()

    print("✅ Dados de teste criados:")
    print("   - 2 Despesas reais (Alimentação)")
    print("   - 2 Transferências internas (despesa)")
    print()

    return session


def test_exclude_transfers_false():
    """Verificar que exclude_transfers=False retorna todas as despesas."""
    session = setup_test_data()

    # Recuperar com exclude_transfers=False (padrão)
    transacoes = get_transactions(exclude_transfers=False)
    despesas = [t for t in transacoes if t.get("tipo") == "despesa"]

    print("✅ TESTE 1: exclude_transfers=False (Padrão)")
    print(f"   Total de despesas: {len(despesas)}")
    print()

    # Deve ter 4 despesas (2 reais + 2 transferências)
    assert len(despesas) == 4, f"Esperava 4 despesas, obteve {len(despesas)}"

    # Verificar que contém "Transferência Interna"
    tem_transferencia = any(
        (
            isinstance(t.get("categoria"), dict)
            and t.get("categoria", {}).get("nome") == "Transferência Interna"
        )
        or t.get("categoria") == "Transferência Interna"
        for t in despesas
    )
    assert tem_transferencia, "Deveria conter 'Transferência Interna'"

    print("   ✓ Contém 2 despesas reais")
    print("   ✓ Contém 2 transferências internas")
    print()


def test_exclude_transfers_true():
    """Verificar que exclude_transfers=True exclui "Transferência Interna"."""
    session = setup_test_data()

    # Recuperar com exclude_transfers=True
    transacoes = get_transactions(exclude_transfers=True)
    despesas = [t for t in transacoes if t.get("tipo") == "despesa"]

    print("✅ TESTE 2: exclude_transfers=True")
    print(f"   Total de despesas: {len(despesas)}")
    print()

    # Deve ter apenas 2 despesas (sem transferências)
    assert len(despesas) == 2, f"Esperava 2 despesas, obteve {len(despesas)}"

    # Verificar que NÃO contém "Transferência Interna"
    tem_transferencia = any(
        (
            isinstance(t.get("categoria"), dict)
            and t.get("categoria", {}).get("nome") == "Transferência Interna"
        )
        or t.get("categoria") == "Transferência Interna"
        for t in despesas
    )
    assert not tem_transferencia, "NÃO deveria conter 'Transferência Interna'"

    # Verificar que contém as despesas reais
    categorias_nomes = []
    for t in despesas:
        cat = t.get("categoria")
        if isinstance(cat, dict):
            categorias_nomes.append(cat.get("nome"))
        else:
            categorias_nomes.append(cat)

    assert (
        "Alimentação" in categorias_nomes
    ), f"Deveria conter 'Alimentação', obteve: {categorias_nomes}"

    print("   ✓ Contém apenas 2 despesas reais")
    print("   ✓ Excluiu 'Transferência Interna'")
    print()


def test_backward_compatibility():
    """Verificar que get_transactions() sem parâmetros mantém comportamento antigo."""
    session = setup_test_data()

    # Chamar sem parâmetro exclude_transfers
    transacoes = get_transactions()

    print("✅ TESTE 3: Backward Compatibility")
    print()

    # Deve retornar todas as transações (comportamento antigo)
    assert len(transacoes) > 0, "Deveria retornar transações"

    # Verificar que inclui transferências (comportamento padrão)
    despesas = [t for t in transacoes if t.get("tipo") == "despesa"]
    tem_transferencia = any(
        (
            isinstance(t.get("categoria"), dict)
            and t.get("categoria", {}).get("nome") == "Transferência Interna"
        )
        or t.get("categoria") == "Transferência Interna"
        for t in despesas
    )
    assert tem_transferencia, "Padrão deveria incluir 'Transferência Interna'"

    print("   ✓ get_transactions() sem parâmetro funciona")
    print("   ✓ Padrão mantém comportamento antigo (inclui transferências)")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("🔬 VALIDAÇÃO: Exclusão de 'Transferência Interna' de Despesas")
    print("=" * 70)
    print()

    try:
        test_exclude_transfers_false()
        test_exclude_transfers_true()
        test_backward_compatibility()

        print("=" * 70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print()
        print("Resumo:")
        print("  ✓ exclude_transfers=False retorna todas as despesas")
        print("  ✓ exclude_transfers=True exclui 'Transferência Interna'")
        print("  ✓ Backward compatibility mantido")
        print()
        print("Resultado: Listagem de despesas limpa e focada em consumo real!")
        print()

    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TESTE FALHOU: {e}")
        print("=" * 70)
        exit(1)
