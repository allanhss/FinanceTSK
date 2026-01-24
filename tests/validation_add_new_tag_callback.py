# -*- coding: utf-8 -*-
"""
Validacao - Callback de Criacao de Novas Tags.

Verifica:
1. Criacao de novas tags digitando no dropdown
2. Rejeicao de tags duplicadas (case-insensitive)
3. Validacao de entrada vazia
"""

import os

os.environ["TESTING_MODE"] = "1"

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch
from dash.exceptions import PreventUpdate

# Import da aplicacao
from src.app import add_new_tag_option


def test_create_new_tag():
    """
    Teste 1: Cria uma nova tag ao digitar.

    Verifica:
    - Tag nova eh criada
    - Adicionada a lista de opcoes
    - Estrutura {'label': ..., 'value': ...} correta
    """
    print("\n[TESTE 1] Criando nova tag ao digitar...")

    # Dados iniciais
    search_value = "Novo Tag"
    existing_options = [
        {"label": "Casa", "value": "Casa"},
        {"label": "Moto", "value": "Moto"},
    ]

    with patch("src.app.logger"):
        updated_options = add_new_tag_option(search_value, existing_options)

    # Validacoes
    assert (
        len(updated_options) == 3
    ), f"Deveria ter 3 opcoes, obtidas: {len(updated_options)}"
    assert updated_options[-1] == {
        "label": "Novo Tag",
        "value": "Novo Tag",
    }, f"Nova tag nao foi adicionada corretamente: {updated_options[-1]}"

    print("[OK] Nova tag criada com sucesso")
    print(f"   - search_value: '{search_value}'")
    print(f"   - opcoes antes: 2")
    print(f"   - opcoes depois: {len(updated_options)}")
    print(f"   - nova opcao: {updated_options[-1]}")


def test_duplicate_tag_exact_case():
    """
    Teste 2: Rejeita tag duplicada (case exato).

    Verifica:
    - PreventUpdate se tag existe com mesmo case
    """
    print("\n[TESTE 2] Rejeitando tag duplicada (case exato)...")

    search_value = "Moto"
    existing_options = [
        {"label": "Casa", "value": "Casa"},
        {"label": "Moto", "value": "Moto"},
    ]

    with patch("src.app.logger"):
        try:
            add_new_tag_option(search_value, existing_options)
            assert False, "Deveria lancar PreventUpdate para tag duplicada"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado para tag duplicada")


def test_duplicate_tag_case_insensitive():
    """
    Teste 3: Rejeita tag duplicada (case-insensitive).

    Verifica:
    - PreventUpdate se tag existe com case diferente
    """
    print("\n[TESTE 3] Rejeitando tag duplicada (case-insensitive)...")

    search_value = "MOTO"  # Maiuscula
    existing_options = [
        {"label": "Casa", "value": "Casa"},
        {"label": "Moto", "value": "Moto"},  # Minuscula
    ]

    with patch("src.app.logger"):
        try:
            add_new_tag_option(search_value, existing_options)
            assert (
                False
            ), "Deveria lancar PreventUpdate para tag duplicada (case-insensitive)"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado para tag duplicada (case-insensitive)")


def test_empty_search_value():
    """
    Teste 4: Rejeita entrada vazia.

    Verifica:
    - PreventUpdate se search_value eh vazio
    """
    print("\n[TESTE 4] Rejeitando entrada vazia...")

    search_value = ""
    existing_options = [
        {"label": "Casa", "value": "Casa"},
    ]

    with patch("src.app.logger"):
        try:
            add_new_tag_option(search_value, existing_options)
            assert False, "Deveria lancar PreventUpdate para entrada vazia"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado para entrada vazia")


def test_none_search_value():
    """
    Teste 5: Rejeita None.

    Verifica:
    - PreventUpdate se search_value eh None
    """
    print("\n[TESTE 5] Rejeitando None...")

    search_value = None
    existing_options = [
        {"label": "Casa", "value": "Casa"},
    ]

    with patch("src.app.logger"):
        try:
            add_new_tag_option(search_value, existing_options)
            assert False, "Deveria lancar PreventUpdate para None"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado para None")


def test_whitespace_only():
    """
    Teste 6: Rejeita string com apenas espacos.

    Verifica:
    - PreventUpdate se search_value eh somente espacos
    """
    print("\n[TESTE 6] Rejeitando espacos em branco...")

    search_value = "   "
    existing_options = [
        {"label": "Casa", "value": "Casa"},
    ]

    with patch("src.app.logger"):
        try:
            add_new_tag_option(search_value, existing_options)
            assert False, "Deveria lancar PreventUpdate para espacos apenas"
        except PreventUpdate:
            print("[OK] PreventUpdate lancado para espacos apenas")


def test_tag_with_spaces():
    """
    Teste 7: Cria tag com espacos internos.

    Verifica:
    - Tag com multiplas palavras pode ser criada
    """
    print("\n[TESTE 7] Criando tag com espacos internos...")

    search_value = "Tag com Espacos"
    existing_options = [
        {"label": "Casa", "value": "Casa"},
    ]

    with patch("src.app.logger"):
        updated_options = add_new_tag_option(search_value, existing_options)

    assert len(updated_options) == 2, f"Deveria ter 2 opcoes"
    assert (
        updated_options[-1]["value"] == "Tag com Espacos"
    ), f"Tag com espacos nao foi criada corretamente"

    print("[OK] Tag com espacos criada com sucesso")
    print(f"   - search_value: '{search_value}'")
    print(f"   - nova opcao: {updated_options[-1]}")


def test_multiple_new_tags_sequencially():
    """
    Teste 8: Cria multiplas tags em sequencia.

    Simula usuario criando varias tags uma apos outra.
    """
    print("\n[TESTE 8] Criando multiplas tags em sequencia...")

    options = [
        {"label": "Casa", "value": "Casa"},
    ]

    tags_to_create = ["Moto", "Viagem", "Lazer", "Compras"]

    with patch("src.app.logger"):
        for tag in tags_to_create:
            options = add_new_tag_option(tag, options)
            print(f"   - Criada tag '{tag}' (total: {len(options)})")

    assert len(options) == 5, f"Deveria ter 5 opcoes (1 inicial + 4 novas)"
    print("[OK] Multiplas tags criadas com sucesso")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTES - CRIACAO DE NOVAS TAGS VIA DROPDOWN")
    print("=" * 70)

    try:
        test_create_new_tag()
        test_duplicate_tag_exact_case()
        test_duplicate_tag_case_insensitive()
        test_empty_search_value()
        test_none_search_value()
        test_whitespace_only()
        test_tag_with_spaces()
        test_multiple_new_tags_sequencially()

        print("\n" + "=" * 70)
        print("[OK] TODOS OS 8 TESTES PASSARAM")
        print("=" * 70)
        print("\nCallback de criacao de tags esta pronto para producao!")

    except AssertionError as e:
        print(f"\n[ERRO] FALHA NA VALIDACAO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] ERRO INESPERADO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
