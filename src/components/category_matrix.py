"""
Componente de Matriz Analítica para visualização de categorias vs meses.

Renders uma tabela interativa onde linhas são categorias e colunas são
meses. Cada célula contém a soma das transações daquela categoria naquele
mês. Os nomes das categorias funcionam como botões clicáveis para abrir
detalhes.
"""

from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import html


def format_currency(valor: float) -> str:
    """
    Formata um valor numérico para moeda brasileira (R$).

    Args:
        valor: Valor a ser formatado.

    Returns:
        String formatada como "R$ 1.234,56" ou "-" se valor é 0.

    Example:
        >>> format_currency(1234.56)
        'R$ 1.234,56'
        >>> format_currency(0.0)
        '-'
    """
    if valor == 0.0:
        return "-"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_month_header(mes_str: str) -> str:
    """
    Formata string de mês de "2026-01" para "Jan/26".

    Args:
        mes_str: Mês em formato "YYYY-MM".

    Returns:
        String formatada como "Jan/26".

    Example:
        >>> format_month_header("2026-01")
        'Jan/26'
    """
    meses_abrev = {
        "01": "Jan",
        "02": "Fev",
        "03": "Mar",
        "04": "Abr",
        "05": "Mai",
        "06": "Jun",
        "07": "Jul",
        "08": "Ago",
        "09": "Set",
        "10": "Out",
        "11": "Nov",
        "12": "Dez",
    }
    ano, mes = mes_str.split("-")
    mes_abrev = meses_abrev.get(mes, mes)
    ano_abrev = ano[-2:]
    return f"{mes_abrev}/{ano_abrev}"


def render_category_matrix(data: Dict[str, Any]) -> html.Div:
    """
    Renderiza tabela cruzada de categorias vs meses.

    Cria uma tabela interativa (dbc.Table) onde:
    - Linhas: Categorias (com ícones)
    - Colunas: Meses (formatados como "Jan/26")
    - Células: Soma de transações formatada em R$

    Os nomes das categorias são links que disparamevento clicável para
    abrir modal de detalhes. Categorias sem transações não aparecem.

    Args:
        data: Dict retornado por `get_category_matrix_data()` com
            estrutura:
            {
                "meses": ["2026-01", "2026-02", ...],
                "receitas": [
                    {"id": 1, "nome": "Salário", "icon": "💰",
                     "valores": {"2026-01": 5000.0, ...}},
                    ...
                ],
                "despesas": [
                    {"id": 5, "nome": "Alimentação", "icon": "🍔",
                     "valores": {"2026-01": 800.0, ...}},
                    ...
                ]
            }

    Returns:
        html.Div contendo a tabela responsiva com overflow horizontal.

    Example:
        >>> dados = get_category_matrix_data(months_past=3, months_future=3)
        >>> tabela = render_category_matrix(dados)
        >>> print(type(tabela))
        <class 'dash.html.Div'>
    """
    meses = data.get("meses", [])
    receitas = data.get("receitas", [])
    despesas = data.get("despesas", [])

    # Construir cabeçalho da tabela
    header_cells = [html.Th("Categoria", className="text-nowrap fw-bold")]
    for mes in meses:
        mes_formatado = format_month_header(mes)
        header_cells.append(
            html.Th(
                mes_formatado,
                className="text-center text-nowrap fw-bold",
                style={"minWidth": "80px"},
            )
        )

    cabecalho = html.Thead(html.Tr(header_cells, className="table-light"))

    # Construir corpo da tabela
    linhas_corpo = []

    # Seção RECEITAS
    if receitas:
        # Linha separadora visual para receitas
        linhas_corpo.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong("RECEITAS"),
                        colSpan=len(meses) + 1,
                        className="bg-success bg-opacity-10 text-success fw-bold",
                    )
                ],
                className="table-light",
            )
        )

        # Linhas de categorias de receita
        for categoria in receitas:
            categoria_id = categoria["id"]
            nome = categoria["nome"]
            icone = categoria["icon"]
            valores = categoria["valores"]

            # Célula com nome como botão clicável
            nome_cell = html.Td(
                html.A(
                    f"{icone} {nome}",
                    id={
                        "type": "btn-cat-detail",
                        "index": categoria_id,
                    },
                    href="#",
                    className="text-success text-decoration-none fw-bold",
                    style={
                        "cursor": "pointer",
                    },
                ),
            )

            # Células de valores dos meses
            valor_cells = [
                html.Td(
                    format_currency(valores.get(mes, 0.0)),
                    className="text-end text-success",
                    style={"minWidth": "80px"},
                )
                for mes in meses
            ]

            linhas_corpo.append(
                html.Tr(
                    [nome_cell] + valor_cells,
                    className="table-light",
                )
            )

    # Seção DESPESAS
    if despesas:
        # Linha separadora visual para despesas
        linhas_corpo.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong("DESPESAS"),
                        colSpan=len(meses) + 1,
                        className="bg-danger bg-opacity-10 text-danger fw-bold",
                    )
                ],
                className="table-light",
            )
        )

        # Linhas de categorias de despesa
        for categoria in despesas:
            categoria_id = categoria["id"]
            nome = categoria["nome"]
            icone = categoria["icon"]
            valores = categoria["valores"]

            # Célula com nome como botão clicável
            nome_cell = html.Td(
                html.A(
                    f"{icone} {nome}",
                    id={
                        "type": "btn-cat-detail",
                        "index": categoria_id,
                    },
                    href="#",
                    className="text-danger text-decoration-none fw-bold",
                    style={
                        "cursor": "pointer",
                    },
                ),
            )

            # Células de valores dos meses
            valor_cells = [
                html.Td(
                    format_currency(valores.get(mes, 0.0)),
                    className="text-end text-danger",
                    style={"minWidth": "80px"},
                )
                for mes in meses
            ]

            linhas_corpo.append(
                html.Tr(
                    [nome_cell] + valor_cells,
                    className="table-light",
                )
            )

    corpo = html.Tbody(linhas_corpo)

    # Tabela principal
    tabela = dbc.Table(
        [cabecalho, corpo],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
        className="mb-0 table-striped",
        style={
            "fontSize": "0.9rem",
        },
    )

    # Wrapper com scroll horizontal
    container = html.Div(
        tabela,
        style={
            "overflowX": "auto",
            "overflowY": "hidden",
            "borderRadius": "0.375rem",
        },
        className="border",
    )

    return container
