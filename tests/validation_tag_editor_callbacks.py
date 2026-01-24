"""
Validação de Callbacks do Editor de Tags (Modal).

Verifica:
1. Callback de ABRIR modal ao clicar na célula de tags
2. Callback de SALVAR tags de volta na tabela
3. Callback de CANCELAR modal
4. Sincronização de dados entre modal e tabela
"""

import os

os.environ["TESTING_MODE"] = "1"

import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch
from dash.exceptions import PreventUpdate
import pytest

# Import da aplicação
from src.app import (
    open_tag_editor_modal,
    save_tags_to_table,
    cancel_tag_editor_modal,
)
from src.database.operations import get_unique_tags_list


def test_open_tag_editor_modal_valid_cell():
    """
    Teste 1: Abre modal quando célula de tags é clicada.

    Verifica:
    - Modal abre (is_open=True)
    - Opções de dropdown carregadas
    - Tags atuais convertidas em lista
    - Índice de linha armazenado

    Utiliza column_id="tags" em vez de column=5
    """
    print("\n[TESTE 1] Abrindo modal na célula de tags...")

    # Dados de exemplo - usando column_id="tags" em vez de column=5
    active_cell = {"row": 0, "column_id": "tags"}
    table_data = [
        {
            "data": "23/01/2024",
            "tipo": "Despesa",
            "descricao": "Combustível",
            "categoria": "Transporte",
            "valor": "50.00",
            "tags": "Moto, Viagem",
            "conta": "Nubank",
        },
    ]

    # Mock de get_unique_tags_list
    with patch("src.app.get_unique_tags_list") as mock_get_tags:
        mock_get_tags.return_value = ["Casa", "Compras", "Moto", "Viagem", "Lazer"]

        # Mock de logger
        with patch("src.app.logger"):
            # Chamar callback
            modal_open, dropdown_opts, dropdown_val, row_idx = open_tag_editor_modal(
                active_cell, table_data
            )

    # Validações
    assert modal_open is True, "Modal deveria estar aberto"
    assert isinstance(dropdown_opts, list), "Opcoes devem ser lista"
    assert (
        len(dropdown_opts) == 5
    ), f"Deveria ter 5 opcoes de tags, obtidos: {len(dropdown_opts)}"
    # Validar que as tags da linha 0 foram extraídas corretamente
    assert "Moto" in dropdown_val, f"'Moto' deveria estar em {dropdown_val}"
    assert "Viagem" in dropdown_val, f"'Viagem' deveria estar em {dropdown_val}"
    assert len(dropdown_val) == 2, f"Deveria ter 2 tags, obtidas: {len(dropdown_val)}"
    assert row_idx == 0, "Indice de linha deveria ser 0"

    print("[OK] Modal aberto com sucesso")
    print(f"   - is_open: {modal_open}")
    print(f"   - dropdown_options: {len(dropdown_opts)} tags")
    print(f"   - dropdown_value: {dropdown_val}")
    print(f"   - row_index: {row_idx}")


def test_open_tag_editor_modal_wrong_column():
    """
    Teste 2: Não abre modal se célula clicada NÃO é na coluna de tags.

    Verifica:
    - PreventUpdate quando column_id != "tags"

    Agora testando com column_id correto
    """
    print("\n[TESTE 2] Evitando abertura em coluna errada...")

    # Clique em coluna "descricao" em vez de "tags"
    active_cell = {"row": 0, "column_id": "descricao"}
    table_data = [{"data": "23/01/2024", "tipo": "Despesa"}]

    with patch("src.app.logger"):
        try:
            open_tag_editor_modal(active_cell, table_data)
            assert False, "Deveria lancar PreventUpdate"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado corretamente para coluna errada")


def test_save_tags_to_table():
    """
    Teste 3: Salva tags selecionadas de volta na tabela.

    Verifica:
    - Tags são convertidas em string (formato CSV)
    - Linha correta é atualizada
    - Modal fecha (is_open=False)
    - Dados originais não são mutados
    """
    print("\n[TESTE 3] Salvando tags na tabela...")

    selected_tags = ["Moto", "Viagem", "Lazer"]
    row_index = 1
    table_data = [
        {
            "data": "23/01/2024",
            "tipo": "Despesa",
            "descricao": "Combustível",
            "tags": "Moto",
        },
        {
            "data": "24/01/2024",
            "tipo": "Despesa",
            "descricao": "Supermercado",
            "tags": "Casa",
        },
    ]

    with patch("src.app.logger"):
        updated_data, modal_open = save_tags_to_table(
            n_clicks=1,
            selected_tags=selected_tags,
            row_index=row_index,
            table_data=table_data,
        )

    # Validações
    assert modal_open is False, "Modal deveria estar fechado"
    assert len(updated_data) == 2, "Tabela deveria ter 2 linhas"
    assert (
        updated_data[1]["tags"] == "Moto, Viagem, Lazer"
    ), f"Tags não salvas corretamente: {updated_data[1]['tags']}"
    assert table_data[1]["tags"] == "Casa", "Dados originais foram mutados!"

    print("[OK] Tags salvas com sucesso")
    print(f"   - modal_open: {modal_open}")
    print(f"   - linha atualizada[1]['tags']: {updated_data[1]['tags']}")
    print(f"   - dados originais preservados: {table_data[1]['tags']}")


def test_save_tags_empty_list():
    """
    Teste 4: Salva com lista vazia (limpa tags).

    Verifica:
    - String vazia quando nenhuma tag selecionada
    """
    print("\n[TESTE 4] Salvando com lista vazia...")

    selected_tags = []  # Nenhuma tag
    row_index = 0
    table_data = [
        {
            "data": "23/01/2024",
            "tags": "Moto, Viagem",
        },
    ]

    with patch("src.app.logger"):
        updated_data, modal_open = save_tags_to_table(
            n_clicks=1,
            selected_tags=selected_tags,
            row_index=row_index,
            table_data=table_data,
        )

    assert updated_data[0]["tags"] == "", "Tags deveria estar vazia"
    print("[OK] Lista vazia salva com sucesso (tags limpas)")


def test_cancel_tag_editor_modal():
    """
    Teste 5: Cancela editor sem salvar.

    Verifica:
    - Modal fecha (is_open=False)
    - Dropdown é resetado (value=[])
    """
    print("\n[TESTE 5] Cancelando editor...")

    with patch("src.app.logger"):
        modal_open, dropdown_val = cancel_tag_editor_modal(n_clicks=1)

    assert modal_open is False, "Modal deveria estar fechado"
    assert dropdown_val == [], "Dropdown deveria estar vazio"

    print("[OK] Editor cancelado com sucesso")
    print(f"   - modal_open: {modal_open}")
    print(f"   - dropdown_value: {dropdown_val}")


def test_callbacks_integration():
    """
    Teste 6: Integração completa (abrir -> selecionar -> salvar).

    Simula fluxo completo:
    1. Usuário clica na célula de tags
    2. Modal abre com tags atuais
    3. Usuário seleciona novas tags
    4. Clica em Salvar
    5. Tabela é atualizada e modal fecha
    """
    print("\n[TESTE 6] Fluxo completo de edição...")

    # Passo 1: Dados iniciais
    table_data = [
        {
            "data": "23/01/2024",
            "tipo": "Despesa",
            "tags": "Moto",
        },
    ]
    active_cell = {"row": 0, "column_id": "tags"}

    # Passo 2: Abrir modal
    with patch("src.app.get_unique_tags_list") as mock_get_tags:
        mock_get_tags.return_value = ["Casa", "Moto", "Viagem"]
        with patch("src.app.logger"):
            modal_open, opts, vals, row_idx = open_tag_editor_modal(
                active_cell, table_data
            )

    assert modal_open is True
    assert vals == ["Moto"]
    print("  [OK] Passo 1-2: Modal aberto com tags atuais")

    # Passo 3: Selecionar novas tags
    selected_tags = ["Moto", "Viagem"]  # User selects more tags

    # Passo 4-5: Salvar
    with patch("src.app.logger"):
        updated_data, modal_closed = save_tags_to_table(
            n_clicks=1,
            selected_tags=selected_tags,
            row_index=row_idx,
            table_data=table_data,
        )

    assert modal_closed is False
    assert updated_data[0]["tags"] == "Moto, Viagem"
    print("  [OK] Passo 3-5: Tags atualizadas e modal fechado")
    print("[OK] Fluxo completo executado com sucesso")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTES DO EDITOR DE TAGS - CALLBACKS")
    print("=" * 70)

    try:
        test_open_tag_editor_modal_valid_cell()
        test_open_tag_editor_modal_wrong_column()
        test_save_tags_to_table()
        test_save_tags_empty_list()
        test_cancel_tag_editor_modal()
        test_callbacks_integration()

        print("\n" + "=" * 70)
        print("[OK] TODOS OS 6 TESTES PASSARAM")
        print("=" * 70)
        print("\nCallbacks de edicao de tags estao prontos para producao!")

    except AssertionError as e:
        print(f"\n[ERRO] FALHA NA VALIDACAO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] ERRO INESPERADO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
