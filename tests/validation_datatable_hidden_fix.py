"""
Validação: Remoção de Colunas 'hidden' da DataTable

Verifica que:
1. Colunas 'skipped' e 'disable_edit' foram removidas da definição de columns
2. Os dados ainda contêm skipped e disable_edit (para style_data_conditional)
3. style_data_conditional continua funcionando corretamente
"""

import os

os.environ["TESTING_MODE"] = "1"

from src.components.importer import render_preview_table


def test_preview_table_no_hidden_columns():
    """Verificar que colunas hidden foram removidas."""

    # Dados de teste
    data = [
        {
            "data": "2026-01-20",
            "descricao": "Compra Normal",
            "valor": 100.0,
            "tipo": "despesa",
            "categoria": "Alimentação",
            "tags": "",
            "skipped": False,
            "disable_edit": False,
        },
        {
            "data": "2026-01-19",
            "descricao": "Pagamento de Fatura",
            "valor": 500.0,
            "tipo": "despesa",
            "categoria": "Transferência Interna",
            "tags": "",
            "skipped": True,
            "disable_edit": True,
        },
    ]

    category_options = [
        {"label": "🍔 Alimentação", "value": "Alimentação"},
        {"label": "🔄 Transferência Interna", "value": "Transferência Interna"},
    ]

    # Renderizar tabela
    card = render_preview_table(data, category_options)

    # Extrair DataTable
    table = None
    for child in card.children:
        if hasattr(child, "children"):
            for subchild in child.children:
                if hasattr(subchild, "id") and subchild.id == "table-import-preview":
                    table = subchild
                    break

    assert table is not None, "DataTable não encontrada"

    # Extrair coluna IDs
    column_ids = [col["id"] for col in table.columns]

    print("✅ TESTE 1: Colunas Removidas")
    print(f"   Colunas visíveis: {column_ids}")
    print()

    # Verificações
    assert "data" in column_ids, "Coluna 'data' faltando"
    assert "descricao" in column_ids, "Coluna 'descricao' faltando"
    assert "valor" in column_ids, "Coluna 'valor' faltando"
    assert "tipo" in column_ids, "Coluna 'tipo' faltando"
    assert "categoria" in column_ids, "Coluna 'categoria' faltando"
    assert "tags" in column_ids, "Coluna 'tags' faltando"

    # As colunas metadata devem estar AUSENTES
    assert "skipped" not in column_ids, "❌ Coluna 'skipped' ainda está presente!"
    assert (
        "disable_edit" not in column_ids
    ), "❌ Coluna 'disable_edit' ainda está presente!"

    print("   ✓ 'skipped' removida corretamente")
    print("   ✓ 'disable_edit' removida corretamente")
    print()


def test_preview_table_data_preserved():
    """Verificar que os dados ainda contêm skipped e disable_edit."""

    data = [
        {
            "data": "2026-01-20",
            "descricao": "Compra Normal",
            "valor": 100.0,
            "tipo": "despesa",
            "categoria": "Alimentação",
            "tags": "",
            "skipped": False,
            "disable_edit": False,
        },
        {
            "data": "2026-01-19",
            "descricao": "Pagamento de Fatura",
            "valor": 500.0,
            "tipo": "despesa",
            "categoria": "Transferência Interna",
            "tags": "",
            "skipped": True,
            "disable_edit": True,
        },
    ]

    category_options = [
        {"label": "🍔 Alimentação", "value": "Alimentação"},
        {"label": "🔄 Transferência Interna", "value": "Transferência Interna"},
    ]

    # Renderizar tabela
    card = render_preview_table(data, category_options)

    # Extrair DataTable
    table = None
    for child in card.children:
        if hasattr(child, "children"):
            for subchild in child.children:
                if hasattr(subchild, "id") and subchild.id == "table-import-preview":
                    table = subchild
                    break

    assert table is not None, "DataTable não encontrada"

    # Verificar dados
    table_data = table.data

    print("✅ TESTE 2: Dados Preservados para style_data_conditional")
    print()

    assert len(table_data) == 2, "Dados não foram preparados corretamente"

    # Primeiro registro (normal)
    assert table_data[0]["skipped"] == False, "skipped não preservado na linha 1"
    assert (
        table_data[0]["disable_edit"] == False
    ), "disable_edit não preservado na linha 1"
    print("   ✓ Linha 1 (normal): skipped=False, disable_edit=False")

    # Segundo registro (desabilitado)
    assert table_data[1]["skipped"] == True, "skipped não preservado na linha 2"
    assert (
        table_data[1]["disable_edit"] == True
    ), "disable_edit não preservado na linha 2"
    print("   ✓ Linha 2 (desabilitada): skipped=True, disable_edit=True")
    print()


def test_style_data_conditional_intact():
    """Verificar que style_data_conditional continua funcionando."""

    data = [
        {
            "data": "2026-01-20",
            "descricao": "Compra Normal",
            "valor": 100.0,
            "tipo": "despesa",
            "categoria": "Alimentação",
            "tags": "",
            "skipped": False,
            "disable_edit": False,
        },
    ]

    category_options = []

    # Renderizar tabela
    card = render_preview_table(data, category_options)

    # Extrair DataTable
    table = None
    for child in card.children:
        if hasattr(child, "children"):
            for subchild in child.children:
                if hasattr(subchild, "id") and subchild.id == "table-import-preview":
                    table = subchild
                    break

    assert table is not None, "DataTable não encontrada"

    # Verificar style_data_conditional
    style_conditions = table.style_data_conditional

    print("✅ TESTE 3: style_data_conditional Intacto")
    print()

    # Deve ter pelo menos 2 condições
    assert len(style_conditions) >= 2, "style_data_conditional não está completo"

    # Procurar pela condição disable_edit
    disable_edit_condition = None
    for condition in style_conditions:
        if condition.get("if", {}).get("filter_query") == "{disable_edit} = true":
            disable_edit_condition = condition
            break

    assert (
        disable_edit_condition is not None
    ), "Condição disable_edit não encontrada em style_data_conditional"
    print("   ✓ Condição {disable_edit} = true está presente")

    # Verificar styling
    assert "color" in disable_edit_condition, "Cor não definida"
    assert "backgroundColor" in disable_edit_condition, "backgroundColor não definida"
    assert "fontStyle" in disable_edit_condition, "fontStyle não definida"
    print("   ✓ Estilos (cor, fundo, fonte) definidos corretamente")
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("🔬 VALIDAÇÃO: Remoção de Colunas 'hidden' da DataTable")
    print("=" * 70)
    print()

    try:
        test_preview_table_no_hidden_columns()
        test_preview_table_data_preserved()
        test_style_data_conditional_intact()

        print("=" * 70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print()
        print("Resumo:")
        print("  ✓ Colunas 'skipped' e 'disable_edit' removidas da definição")
        print("  ✓ Dados ainda contêm skipped e disable_edit")
        print("  ✓ style_data_conditional continua funcionando")
        print()
        print("Resultado: Erro 'Invalid component prop columns key hidden' corrigido!")
        print()

    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"❌ TESTE FALHOU: {e}")
        print("=" * 70)
        exit(1)
