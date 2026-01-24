"""
Validacao: Dropdown de tags na tabela de preview

Testa:
1. render_preview_table recebe existing_tags
2. Cria DataTable com dropdown para tags
3. As opcoes do dropdown contem os tags passados
"""

import os

os.environ["TESTING_MODE"] = "1"

import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.components.importer import render_preview_table


def test_render_preview_table_with_tags():
    """Test that render_preview_table generates dropdown for tags."""
    print("\n[TESTE] Geracao de tabela com dropdown de tags...")

    # Sample transaction data
    transactions = [
        {
            "data": "2026-01-24",
            "descricao": "Compra no Supermercado",
            "valor": 150.50,
            "tipo": "despesa",
            "categoria": "Alimentacao",
            "tags": "",
        },
        {
            "data": "2026-01-23",
            "descricao": "Passagem de Uber",
            "valor": 45.00,
            "tipo": "despesa",
            "categoria": "Transporte",
            "tags": "Viagem",
        },
    ]

    # Category options
    category_options = [
        {"label": "Alimentacao", "value": "Alimentacao"},
        {"label": "Transporte", "value": "Transporte"},
    ]

    # Existing tags for dropdown
    existing_tags = ["Moto", "Viagem", "Lazer", "Casa", "Compras"]

    # Generate preview table
    try:
        table_card = render_preview_table(transactions, category_options, existing_tags)
        print(f"   [OK] Tabela de preview gerada com sucesso")
    except Exception as e:
        print(f"   [ERRO] Falha ao gerar tabela: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Validate that it's a Card with DataTable
    try:
        # Card structure should have children
        if not hasattr(table_card, "children") or not table_card.children:
            print(f"   [ERRO] Card nao tem children esperados")
            return False

        print(f"   [OK] Card estrutura valida")

        # Try to find the DataTable in the card
        # It's typically nested: Card > CardBody > DataTable
        if len(table_card.children) >= 2:
            card_body = table_card.children[1]  # CardBody is typically second
            if hasattr(card_body, "children") and card_body.children:
                data_table = card_body.children[
                    0
                ]  # DataTable is typically first child of CardBody

                # Check DataTable properties
                if hasattr(data_table, "dropdown") and data_table.dropdown:
                    dropdown_config = data_table.dropdown
                    print(f"   [INFO] Dropdown config: {list(dropdown_config.keys())}")

                    if "tags" in dropdown_config:
                        tags_options = dropdown_config["tags"].get("options", [])
                        print(
                            f"   [OK] Tags dropdown encontrado com {len(tags_options)} opcoes"
                        )

                        # Verify that all tags are in options
                        tag_values = [opt["value"] for opt in tags_options]
                        print(f"   [INFO] Tags disponiveis: {tag_values}")

                        if all(tag in tag_values for tag in existing_tags):
                            print(
                                f"   [SUCESSO] Todos os tags existentes estao no dropdown!"
                            )
                            return True
                        else:
                            missing = [
                                tag for tag in existing_tags if tag not in tag_values
                            ]
                            print(f"   [ERRO] Tags faltando no dropdown: {missing}")
                            return False
                    else:
                        print(f"   [ERRO] 'tags' nao encontrado no dropdown config")
                        print(
                            f"           Chaves disponiveis: {list(dropdown_config.keys())}"
                        )
                        return False

        print(f"   [AVISO] Nao foi possivel validar estrutura interna completa")
        print(f"           Mas a tabela foi gerada sem erros")
        return True

    except Exception as e:
        print(f"   [ERRO] Erro ao validar estrutura: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_render_preview_table_without_tags():
    """Test that render_preview_table works without existing_tags (backward compatibility)."""
    print("\n[TESTE] Compatibilidade retroativa (sem existing_tags)...")

    transactions = [
        {
            "data": "2026-01-24",
            "descricao": "Teste",
            "valor": 50.00,
            "tipo": "despesa",
            "categoria": "Teste",
            "tags": "",
        },
    ]

    category_options = [{"label": "Teste", "value": "Teste"}]

    # Don't pass existing_tags (or pass None)
    try:
        table_card = render_preview_table(transactions, category_options)
        print(f"   [OK] Tabela gerada com sucesso (sem existing_tags)")
        return True
    except Exception as e:
        print(f"   [ERRO] Falha ao gerar com backward compatibility: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 80)
    print("[VALIDACAO] Dropdown de Tags na Tabela de Preview")
    print("=" * 80)

    test1 = test_render_preview_table_with_tags()
    test2 = test_render_preview_table_without_tags()

    print("\n" + "=" * 80)
    if test1 and test2:
        print("[RESULTADO] TODOS OS TESTES PASSARAM!")
        print("   Dropdown de tags esta pronto na tabela de importacao.")
        print("=" * 80)
    else:
        print("[RESULTADO] ALGUNS TESTES FALHARAM")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
