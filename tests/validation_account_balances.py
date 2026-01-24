"""
Validation script for get_account_balances_summary() function.

Demonstrates how the function is used in a multi-account dashboard context.
Run this script to see the function in action with real data.

Usage:
    python tests/validation_account_balances.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import init_database
from src.database.operations import (
    create_account,
    create_category,
    create_transaction,
    get_account_balances_summary,
)


def setup_demo_data():
    """Create demo accounts and transactions for testing."""
    print("\n" + "=" * 70)
    print("[SETUP] Criando dados de demonstracao...")
    print("=" * 70)

    # Create demo categories
    print("\n[CATEGORIAS] Criando categorias...")
    categories = [
        ("Salario", "receita", "S", 0.0),
        ("Freelance", "receita", "F", 0.0),
        ("Alimentacao", "despesa", "A", 1500.0),
        ("Transporte", "despesa", "T", 800.0),
        ("Diversao", "despesa", "D", 500.0),
    ]

    for nome, tipo, icone, teto in categories:
        success, msg = create_category(nome, tipo=tipo, icone=icone, teto_mensal=teto)
        if success:
            print(f"  [OK] {icone} {nome}")

    # Create demo accounts
    print("\n[CONTAS] Criando contas...")
    accounts_config = [
        ("Conta Corrente Nubank", "conta", 5000.0),
        ("Investimentos XP", "investimento", 25000.0),
        ("Cartao Credito Visa", "cartao", 0.0),
    ]

    account_ids = {}
    for nome, tipo, saldo in accounts_config:
        success, msg = create_account(nome, tipo, saldo)
        if success:
            # Extract ID from message if needed or use latest
            print(f"  [OK] {nome} (tipo: {tipo}, saldo inicial: R$ {saldo:,.2f})")
            # Get accounts to find the IDs
            from src.database.operations import get_accounts

            contas = get_accounts()
            for c in contas:
                if c.nome == nome:
                    account_ids[tipo] = c.id

    # Create demo transactions
    print("\n[TRANSACOES] Criando transacoes...")

    today = date.today()

    transactions = [
        # Receitas
        {
            "tipo": "receita",
            "descricao": "Salario Mensal",
            "valor": 5000.0,
            "data": today,
            "categoria": "Salario",
            "conta_tipo": "conta",
        },
        {
            "tipo": "receita",
            "descricao": "Freelance - Projeto Web",
            "valor": 1500.0,
            "data": today - timedelta(days=5),
            "categoria": "Freelance",
            "conta_tipo": "conta",
        },
        {
            "tipo": "receita",
            "descricao": "Juros de Investimento",
            "valor": 120.0,
            "data": today - timedelta(days=10),
            "categoria": "Salario",
            "conta_tipo": "investimento",
        },
        # Despesas
        {
            "tipo": "despesa",
            "descricao": "Supermercado - Compras",
            "valor": 250.0,
            "data": today,
            "categoria": "Alimentacao",
            "conta_tipo": "conta",
        },
        {
            "tipo": "despesa",
            "descricao": "Uber - Deslocamento",
            "valor": 45.0,
            "data": today - timedelta(days=1),
            "categoria": "Transporte",
            "conta_tipo": "conta",
        },
        {
            "tipo": "despesa",
            "descricao": "Compra na Steam",
            "valor": 89.90,
            "data": today - timedelta(days=3),
            "categoria": "Diversao",
            "conta_tipo": "cartao",
        },
    ]

    for trans in transactions:
        conta_id = account_ids.get(trans["conta_tipo"])
        if not conta_id:
            print(f"  [ERRO] Conta nao encontrada para tipo {trans['conta_tipo']}")
            continue

        # Get category ID
        from src.database.operations import get_categories

        cats = get_categories()
        cat_id = None
        for c in cats:
            # Handle both dict and object returns
            c_nome = c.get("nome") if isinstance(c, dict) else c.nome
            if c_nome == trans["categoria"]:
                cat_id = c.get("id") if isinstance(c, dict) else c.id
                break

        if not cat_id:
            print(f"  [ERRO] Categoria '{trans['categoria']}' nao encontrada")
            continue

        success, msg = create_transaction(
            tipo=trans["tipo"],
            descricao=trans["descricao"],
            valor=trans["valor"],
            data=trans["data"],
            categoria_id=cat_id,
            conta_id=conta_id,
        )

        if success:
            emoji = "[+]" if trans["tipo"] == "receita" else "[-]"
            print(f"  {emoji} {trans['descricao']}: R$ {trans['valor']:.2f}")


def display_summary():
    """Display the account balances summary in a formatted way."""
    print("\n" + "=" * 70)
    print("[RESULTADO] Resumo de Saldos Multi-Conta")
    print("=" * 70)

    resumo = get_account_balances_summary()

    # Display total by type
    print("\n[RESUMO POR TIPO DE CONTA]:")
    print(f"  Liquidez (Contas):        R$ {resumo['total_disponivel']:>12,.2f}")
    print(f"  Investimentos:            R$ {resumo['total_investido']:>12,.2f}")
    print(f"  Divida (Cartoes):         R$ {resumo['total_cartoes']:>12,.2f}")
    print(f"  {'─' * 50}")
    print(f"  Patrimonio Total:         R$ {resumo['patrimonio_total']:>12,.2f}")

    # Display details per account
    print("\n[DETALHE POR CONTA]:")

    if not resumo["detalhe_por_conta"]:
        print("  (nenhuma conta registrada)")
        return

    # Group by type for better visualization
    por_tipo = {}
    for conta in resumo["detalhe_por_conta"]:
        tipo = conta["tipo"]
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append(conta)

    tipo_labels = {
        "conta": ("CONTAS CORRENTES", "#3B82F6"),
        "investimento": ("INVESTIMENTOS", "#10B981"),
        "cartao": ("CARTOES DE CREDITO", "#EF4444"),
    }

    for tipo, (label, _cor) in tipo_labels.items():
        if tipo in por_tipo:
            print(f"\n  {label}:")
            for conta in por_tipo[tipo]:
                # Format saldo with sign for cartao
                saldo_str = f"R$ {conta['saldo']:>12,.2f}"
                print(f"    * {conta['nome']:<30} {saldo_str}")


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("VALIDACAO: get_account_balances_summary()")
    print("=" * 70)
    print("\nEste script demonstra o funcionamento da funcao de calculo")
    print("de saldos para o Dashboard Multi-Contas.")

    # Initialize database
    print("\n[INIT] Inicializando banco de dados...")
    try:
        init_database()
        print("[OK] Banco de dados inicializado")
    except Exception as e:
        print(f"[ERRO] Erro ao inicializar banco: {e}")
        return

    # Setup demo data
    try:
        setup_demo_data()
    except Exception as e:
        print(f"\n[ERRO] Erro ao criar dados de demonstracao: {e}")
        import traceback

        traceback.print_exc()
        return

    # Display summary
    try:
        display_summary()
    except Exception as e:
        print(f"\n[ERRO] Erro ao exibir resumo: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n" + "=" * 70)
    print("[SUCESSO] Validacao concluida!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
