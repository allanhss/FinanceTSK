import logging
from datetime import date

import dash_bootstrap_components as dbc
from dash import html

from src.database.operations import get_dashboard_summary

logger = logging.getLogger(__name__)


def _formatar_moeda(valor: float) -> str:
    """
    Formata um valor numérico como moeda brasileira.

    Args:
        valor: Valor em ponto flutuante a ser formatado.

    Returns:
        String formatada como R$ X.XXX,XX (padrão brasileiro).
    """
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_summary_cards(
    month: int | None = None,
    year: int | None = None,
    total_receitas: float | None = None,
    total_despesas: float | None = None,
    saldo: float | None = None,
) -> dbc.Row:
    """
    Renderiza três cards com indicadores principais (KPIs).

    Exibe Total Receitas, Total Despesas e Saldo do período.
    Formata valores em moeda brasileira (R$ 1.234,56).

    Args:
        month: Mês para resumo (1-12). Se None, usa mês atual.
        year: Ano para resumo. Se None, usa ano atual.
        total_receitas: Valor pré-calculado de receitas. Se None,
            calcula via get_dashboard_summary.
        total_despesas: Valor pré-calculado de despesas. Se None,
            calcula via get_dashboard_summary.
        saldo: Valor pré-calculado de saldo. Se None, calcula
            como receitas - despesas.

    Returns:
        dbc.Row contendo 3 dbc.Card com os KPIs formatados.

    Example:
        >>> cards = render_summary_cards(month=1, year=2026)
        >>> cards = render_summary_cards()  # Mês/ano atual
        >>> cards = render_summary_cards(
        ...     total_receitas=1000, total_despesas=500, saldo=500
        ... )
    """
    try:
        # Se valores pré-calculados foram passados, usar eles
        if total_receitas is not None and total_despesas is not None:
            valor_receitas = total_receitas
            valor_despesas = total_despesas
            valor_saldo = (
                saldo if saldo is not None else total_receitas - total_despesas
            )
            logger.info(
                f"💳 Cards com valores pré-calculados: "
                f"Receitas={valor_receitas}, Despesas={valor_despesas}"
            )
        else:
            # Caso contrário, buscar do banco
            hoje = date.today()
            mes_consulta = month if month else hoje.month
            ano_consulta = year if year else hoje.year

            logger.info(
                f"📊 Carregando resumo dashboard para " f"{mes_consulta}/{ano_consulta}"
            )

            resumo = get_dashboard_summary(mes_consulta, ano_consulta)
            valor_receitas = resumo.get("total_receitas", 0.0)
            valor_despesas = resumo.get("total_despesas", 0.0)
            valor_saldo = valor_receitas - valor_despesas
            logger.info(
                f"✓ Resumo carregado: Receitas=R${valor_receitas:.2f}, "
                f"Despesas=R${valor_despesas:.2f}"
            )

        # Determinar cor do saldo
        cor_saldo = "success" if valor_saldo >= 0 else "danger"

        # Card: Receitas
        card_receitas = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                "💰 Receitas",
                                className="card-title text-success",
                            ),
                            html.P(
                                _formatar_moeda(valor_receitas),
                                className="display-6 text-success fw-bold",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm",
            ),
            width=12,
            md=4,
            className="mb-3",
        )

        # Card: Despesas
        card_despesas = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                "💸 Despesas",
                                className="card-title text-danger",
                            ),
                            html.P(
                                _formatar_moeda(valor_despesas),
                                className="display-6 text-danger fw-bold",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm",
            ),
            width=12,
            md=4,
            className="mb-3",
        )

        # Card: Saldo
        card_saldo = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(
                                "📊 Saldo",
                                className=f"card-title text-{cor_saldo}",
                            ),
                            html.P(
                                _formatar_moeda(abs(valor_saldo)),
                                className=(f"display-6 text-{cor_saldo} fw-bold"),
                            ),
                            html.Small(
                                "Superávit" if valor_saldo >= 0 else "Déficit",
                                className=f"text-{cor_saldo}",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm",
            ),
            width=12,
            md=4,
            className="mb-3",
        )

        logger.info(
            f"✓ Cards carregados: R$ {valor_receitas:.2f} | "
            f"R$ {valor_despesas:.2f} | Saldo: R$ {valor_saldo:.2f}"
        )

        return dbc.Row(
            [card_receitas, card_despesas, card_saldo],
            className="g-3 mt-4",
        )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar cards de resumo: {e}")
        return dbc.Row(
            dbc.Col(
                dbc.Alert(
                    "Erro ao carregar resumo. Tente novamente.",
                    color="danger",
                    className="mt-3",
                ),
                width=12,
            )
        )
