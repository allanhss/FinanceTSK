"""
Componente para renderização de Fluxo de Caixa.

Transforma dados brutos de receitas e despesas mensais em uma tabela
visual com meses nas colunas e tipos de movimento (receitas, despesas, saldo)
nas linhas.
"""

from typing import List, Dict, Any
from datetime import date
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
    return (
        f"{sinal}R$ {valor_abs:,.2f}".replace(",", "|")
        .replace(".", ",")
        .replace("|", ".")
    )


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
    - Formatação: Valores em moeda, cores pastéis, mês atual destacado

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

        # Obter mês/ano atual para destaque
        data_atual = date.today()
        mes_atual_str = f"{data_atual.year:04d}-{data_atual.month:02d}"

        # Construir tabela manualmente para maior controle
        # Colunas serão os meses
        meses = df["mes"].tolist()
        meses_display = [format_mes_display(m) for m in meses]

        # Helper para criar células com valor zero apagado
        def criar_celula_valor(valor: float) -> html.Td:
            """Cria célula com estilo especial para zeros."""
            if valor == 0:
                return html.Td(
                    format_currency(valor),
                    className="text-end text-nowrap",
                    style={"background-color": "#ffffff", "color": "#cccccc"},
                )
            return html.Td(
                format_currency(valor),
                className="text-end text-nowrap",
            )

        # Linha de Receitas
        linha_receitas = [
            html.Tr(
                [
                    html.Th(
                        "Receitas",
                        className="bg-light",
                        style={"background-color": "#ffffff"},
                    ),
                    *[
                        html.Td(
                            format_currency(row["receitas"]),
                            className="text-end text-nowrap",
                            style={
                                "background-color": (
                                    "#93c47d" if row["receitas"] != 0 else "#ffffff"
                                ),
                                "color": (
                                    "#000000" if row["receitas"] != 0 else "#cccccc"
                                ),
                            },
                        )
                        for _, row in df.iterrows()
                    ],
                ],
            )
        ]

        # Linha de Despesas
        linha_despesas = [
            html.Tr(
                [
                    html.Th(
                        "Despesas",
                        className="bg-light",
                        style={"background-color": "#ffffff"},
                    ),
                    *[
                        html.Td(
                            format_currency(row["despesas"]),
                            className="text-end text-nowrap",
                            style={
                                "background-color": (
                                    "#ea9999" if row["despesas"] != 0 else "#ffffff"
                                ),
                                "color": (
                                    "#000000" if row["despesas"] != 0 else "#cccccc"
                                ),
                            },
                        )
                        for _, row in df.iterrows()
                    ],
                ],
            )
        ]

        # Linha de Saldo (com coloração dinâmica por valor)
        linha_saldo = []
        for _, row in df.iterrows():
            saldo = row["saldo"]
            if saldo == 0:
                estilo = {"background-color": "#ffffff", "color": "#cccccc"}
            elif saldo > 0:
                estilo = {"background-color": "#93c47d", "color": "#000000"}
            else:
                estilo = {"background-color": "#ea9999", "color": "#000000"}

            linha_saldo.append(
                html.Td(
                    format_currency(saldo),
                    className="text-end text-nowrap fw-bold",
                    style=estilo,
                )
            )

        linha_saldo_tr = html.Tr(
            [
                html.Th(
                    "Saldo", className="bg-light", style={"background-color": "#ffffff"}
                ),
                *linha_saldo,
            ],
        )

        # Montar cabeçalho com meses (com destaque para mês atual)
        cabecalhos_meses = []
        for mes_str, mes_display in zip(meses, meses_display):
            if mes_str == mes_atual_str:
                # Destaque do mês atual
                cabecalhos_meses.append(
                    html.Th(
                        mes_display,
                        className="text-center text-nowrap fw-bold",
                        style={
                            "border": "2px solid #000",
                            "font-weight": "bold",
                            "background-color": "#fff3cd",
                        },
                    )
                )
            else:
                cabecalhos_meses.append(
                    html.Th(
                        mes_display,
                        className="text-center text-nowrap",
                        style={"background-color": "#ffffff"},
                    )
                )

        cabecalho = html.Thead(
            html.Tr(
                [
                    html.Th(
                        "", className="bg-light", style={"background-color": "#ffffff"}
                    ),
                    *cabecalhos_meses,
                ]
            )
        )

        # Montar corpo da tabela
        corpo = html.Tbody([*linha_receitas, *linha_despesas, linha_saldo_tr])

        # Construir tabela
        tabela = dbc.Table(
            [cabecalho, corpo],
            bordered=True,
            striped=False,
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
