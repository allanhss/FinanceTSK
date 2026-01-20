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

    Suporta campos opcionais para parcelamento, forma de pagamento e recorrência.

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

    # Row 3: Categoria
    linha_categoria = dbc.Row(
        dbc.Col(
            [
                dbc.Label("Categoria", html_for=f"dcc-{tipo}-categoria"),
                dcc.Dropdown(
                    id=f"dcc-{tipo}-categoria",
                    options=opcoes_categoria,
                    placeholder="Selecione uma categoria",
                ),
            ],
            md=12,
        ),
        className="mb-3",
    )

    # Row 3.5: Tag (Opcional - ex: Mãe, Trabalho)
    linha_tag = dbc.Row(
        dbc.Col(
            [
                dbc.Label(
                    "Tag (Opcional - ex: Mãe, Trabalho)",
                    html_for=f"dropdown-{tipo}-tag",
                ),
                dcc.Dropdown(
                    id=f"dropdown-{tipo}-tag",
                    placeholder="Selecione ou digite tags",
                    searchable=True,
                    clearable=True,
                    multi=True,
                ),
            ],
            md=12,
        ),
        className="mb-3",
    )

    linhas_formulario = [
        linha_valor_data,
        linha_descricao,
        linha_categoria,
        linha_tag,
    ]

    # Row 4: Específicos por tipo (Despesa vs Receita)
    if tipo == "despesa":
        # Forma de Pagamento e Número de Parcelas para Despesas
        linha_pagamento_parcelas = dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Forma de Pagamento",
                            html_for=f"select-{tipo}-pagamento",
                        ),
                        dcc.Dropdown(
                            id=f"select-{tipo}-pagamento",
                            options=[
                                {"label": "Dinheiro", "value": "dinheiro"},
                                {"label": "Pix", "value": "pix"},
                                {"label": "Crédito", "value": "credito"},
                                {"label": "Débito", "value": "debito"},
                                {"label": "Transferência", "value": "transferencia"},
                                {"label": "Boleto", "value": "boleto"},
                            ],
                            placeholder="Selecione a forma",
                        ),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        dbc.Label(
                            "Número de Parcelas",
                            html_for=f"input-{tipo}-parcelas",
                        ),
                        dbc.Input(
                            id=f"input-{tipo}-parcelas",
                            type="number",
                            placeholder="Qtd Parcelas (ex: 10)",
                            min=1,
                            value=1,
                        ),
                    ],
                    md=6,
                ),
            ],
            className="mb-3",
        )
        linhas_formulario.append(linha_pagamento_parcelas)

    elif tipo == "receita":
        # Pessoa Origem para Receitas
        linha_pessoa_origem = dbc.Row(
            dbc.Col(
                [
                    dbc.Label(
                        "Pessoa Origem",
                        html_for=f"input-{tipo}-origem",
                    ),
                    dbc.Input(
                        id=f"input-{tipo}-origem",
                        type="text",
                        placeholder="Ex: Chefe, Cliente, Banco X",
                    ),
                ],
                md=12,
            ),
            className="mb-3",
        )
        linhas_formulario.append(linha_pessoa_origem)

    # Row 5: Recorrência (para ambos)
    linha_recorrencia = dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Checklist(
                        id=f"check-{tipo}-recorrente",
                        options=[{"label": " É recorrente?", "value": 1}],
                        value=[],
                        switch=True,
                    ),
                ],
                md=4,
            ),
            dbc.Col(
                [
                    dbc.Label(
                        "Frequência",
                        html_for=f"select-{tipo}-frequencia",
                    ),
                    dcc.Dropdown(
                        id=f"select-{tipo}-frequencia",
                        options=[
                            {"label": "Mensal", "value": "mensal"},
                            {"label": "Quinzenal", "value": "quinzenal"},
                            {"label": "Semanal", "value": "semanal"},
                        ],
                        placeholder="Selecione a frequência",
                        disabled=True,
                    ),
                ],
                md=8,
            ),
        ],
        className="mb-3",
    )
    linhas_formulario.append(linha_recorrencia)

    # Row 6: Botão Salvar
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
