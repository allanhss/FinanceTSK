"""
Componente para renderização de Fluxo de Caixa.

Transforma dados brutos de receitas e despesas mensais em uma tabela
visual com meses nas colunas e tipos de movimento (receitas, despesas, saldo)
nas linhas.
"""

from typing import List, Dict, Any
import pandas as pd
import dash_bootstrap_components as dbc
from dash import html


def format_currency(value: float) -> str:
    """
    Formata um valor numérico como moeda brasileira.

    Args:
        value: Valor a ser formatado.

    Returns:
        String formatada como "R$ 1.234,56" ou "-R$ 1.234,56".

    Example:
        >>> format_currency(1234.56)
        'R$ 1.234,56'
        >>> format_currency(-500.0)
        '-R$ 500,00'
    """
    sinal = "-" if value < 0 else ""
    valor_abs = abs(value)
    return f"{sinal}R$ {valor_abs:,.2f}".replace(",", "|").replace(".", ",").replace("|", ".")


def format_mes_display(mes_str: str) -> str:
    """
    Converte "2026-01" para "Jan/26".

    Args:
        mes_str: String no formato "YYYY-MM".

    Returns:
        String formatada como "Mmm/YY".

    Example:
        >>> format_mes_display("2026-01")
        'Jan/26'
    """
    meses = {
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
    mes_abrev = meses.get(mes, mes)
    ano_curto = ano[-2:]
    return f"{mes_abrev}/{ano_curto}"


def render_cash_flow_table(data: List[Dict[str, Any]]) -> dbc.Card:
    """
    Renderiza tabela de Fluxo de Caixa com transposição (meses em colunas).

    Transforma dados brutos em matriz onde:
    - Colunas: Meses (Janeiro/26, Fevereiro/26, etc)
    - Linhas: Receitas, Despesas, Saldo
    - Formatação: Valores em moeda, saldo colorido (vermelho se negativo)

    Args:
        data: Lista de dicts com chaves 'mes', 'receitas', 'despesas', 'saldo'.

    Returns:
        dbc.Card contendo a tabela ou alerta se dados vazios.

    Example:
        >>> data = [
        ...     {'mes': '2026-01', 'receitas': 1000, 'despesas': 500, 'saldo': 500},
        ...     {'mes': '2026-02', 'receitas': 1200, 'despesas': 1300, 'saldo': -100},
        ... ]
        >>> card = render_cash_flow_table(data)
        >>> isinstance(card, dbc.Card)
        True
    """
    if not data:
        return dbc.Card(
            [
                dbc.CardHeader(html.H5("💰 Fluxo de Caixa")),
                dbc.CardBody(
                    dbc.Alert(
                        "Nenhum dado de transações disponível.",
                        color="info",
                        className="mb-0",
                    )
                ),
            ],
            className="shadow-sm",
        )

    try:
        # Converter para DataFrame
        df = pd.DataFrame(data)

        # Construir tabela manualmente para maior controle
        # Colunas serão os meses
        meses = df["mes"].tolist()
        meses_display = [format_mes_display(m) for m in meses]

        # Linhas fixas: Receitas, Despesas, Saldo
        linhas_dados = []

        # Linha de Receitas
        linha_receitas = [
            html.Tr(
                [
                    html.Th("Receitas", className="bg-light"),
                    *[
                        html.Td(
                            format_currency(row["receitas"]),
                            className="text-end text-nowrap",
                        )
                        for _, row in df.iterrows()
                    ],
                ],
                className="table-success",
            )
        ]

        # Linha de Despesas
        linha_despesas = [
            html.Tr(
                [
                    html.Th("Despesas", className="bg-light"),
                    *[
                        html.Td(
                            format_currency(row["despesas"]),
                            className="text-end text-nowrap",
                        )
                        for _, row in df.iterrows()
                    ],
                ],
                className="table-danger",
            )
        ]

        # Linha de Saldo (com coloração dinâmica)
        linha_saldo = []
        for _, row in df.iterrows():
            saldo = row["saldo"]
            cor_texto = "text-danger" if saldo < 0 else "text-success"
            linha_saldo.append(
                html.Td(
                    format_currency(saldo),
                    className=f"text-end text-nowrap fw-bold {cor_texto}",
                )
            )

        linha_saldo_tr = html.Tr(
            [html.Th("Saldo", className="bg-light"), *linha_saldo],
            className="table-info",
        )

        # Montar cabeçalho com meses
        cabecalho = html.Thead(
            html.Tr(
                [
                    html.Th("", className="bg-light"),
                    *[
                        html.Th(
                            mes_display,
                            className="text-center text-nowrap bg-light",
                        )
                        for mes_display in meses_display
                    ],
                ]
            )
        )

        # Montar corpo da tabela
        corpo = html.Tbody([*linha_receitas, *linha_despesas, linha_saldo_tr])

        # Construir tabela
        tabela = dbc.Table(
            [cabecalho, corpo],
            bordered=True,
            striped=True,
            responsive=True,
            className="mb-0",
        )

        return dbc.Card(
            [
                dbc.CardHeader(html.H5("💰 Fluxo de Caixa Mensal")),
                dbc.CardBody(tabela),
            ],
            className="shadow-sm",
        )

    except Exception as e:
        return dbc.Card(
            [
                dbc.CardHeader(html.H5("💰 Fluxo de Caixa")),
                dbc.CardBody(
                    dbc.Alert(
                        f"Erro ao renderizar tabela: {str(e)}",
                        color="danger",
                        className="mb-0",
                    )
                ),
            ],
            className="shadow-sm",
        )
