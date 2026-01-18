from datetime import date
from typing import List, Dict
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from src.database.operations import get_category_options

"""
Formulários reutilizáveis para transações (receitas e despesas).

Este módulo contém funções que geram layouts de formulários usando
Dash Bootstrap Components, permitindo a reutilização para múltiplos
tipos de transações.
"""


def transaction_form(tipo: str) -> dbc.Card:
    """
    Cria um formulário dinâmico para entrada de receitas ou despesas.

    Args:
        tipo: Tipo de transação - 'receita' ou 'despesa'.

    Returns:
        Card Bootstrap contendo o formulário completo com campos
        e botão de submissão.

    Raises:
        ValueError: Se tipo não for 'receita' ou 'despesa'.

    Example:
        >>> form = transaction_form('despesa')
        >>> isinstance(form, dbc.Card)
        True
    """
    if tipo not in ["receita", "despesa"]:
        raise ValueError(f"tipo deve ser 'receita' ou 'despesa', recebido: {tipo}")

    cor_botao = "success" if tipo == "receita" else "danger"
    titulo = "Nova Receita" if tipo == "receita" else "Nova Despesa"
    opcoes_categoria = get_category_options()

    # Row 1: Valor e Data
    linha_valor_data = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label("Valor (R$)", html_for=f"input-{tipo}-valor"),
                    dbc.Input(
                        id=f"input-{tipo}-valor",
                        type="number",
                        placeholder="R$ 0.00",
                        step=0.01,
                        min=0,
                    ),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    dbc.Label("Data", html_for=f"dcc-{tipo}-data"),
                    dcc.DatePickerSingle(
                        id=f"dcc-{tipo}-data",
                        date=date.today(),
                        display_format="DD/MM/YYYY",
                        placeholder="DD/MM/YYYY",
                    ),
                ],
                md=6,
            ),
        ],
        className="mb-3",
    )

    # Row 2: Descrição
    linha_descricao = dbc.Row(
        dbc.Col(
            [
                dbc.Label("Descrição", html_for=f"input-{tipo}-descricao"),
                dbc.Input(
                    id=f"input-{tipo}-descricao",
                    type="text",
                    placeholder="Ex: Salário, Compra no supermercado",
                ),
            ],
            md=12,
        ),
        className="mb-3",
    )

    # Row 3: Categoria e Tags
    linha_categoria_tags = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label("Categoria", html_for=f"dcc-{tipo}-categoria"),
                    dcc.Dropdown(
                        id=f"dcc-{tipo}-categoria",
                        options=opcoes_categoria,
                        placeholder="Selecione uma categoria",
                    ),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    dbc.Label("Tags", html_for=f"input-{tipo}-tags"),
                    dbc.Input(
                        id=f"input-{tipo}-tags",
                        type="text",
                        placeholder="Ex: mercado, jantar (separadas por vírgula)",
                    ),
                ],
                md=6,
            ),
        ],
        className="mb-3",
    )

    # Row 4: Pessoa Origem (apenas para receita)
    linhas_formulario = [
        linha_valor_data,
        linha_descricao,
        linha_categoria_tags,
    ]

    if tipo == "receita":
        linha_pessoa_origem = dbc.Row(
            dbc.Col(
                [
                    dbc.Label(
                        "Pessoa Origem",
                        html_for=f"input-{tipo}-pessoa-origem",
                    ),
                    dbc.Input(
                        id=f"input-{tipo}-pessoa-origem",
                        type="text",
                        placeholder="Ex: Chefe, Cliente",
                    ),
                ],
                md=12,
            ),
            className="mb-3",
        )
        linhas_formulario.append(linha_pessoa_origem)

    # Row 5: Botão Salvar
    linha_botao = dbc.Row(
        dbc.Col(
            dbc.Button(
                f"Salvar {titulo.split()[1]}",
                id=f"btn-salvar-{tipo}",
                color=cor_botao,
                className="w-100",
            ),
            md=12,
        ),
        className="mt-4",
    )
    linhas_formulario.append(linha_botao)

    return dbc.Card(
        [
            dbc.CardHeader(html.H5(titulo)),
            dbc.CardBody(linhas_formulario),
        ],
        className="shadow-sm",
    )
