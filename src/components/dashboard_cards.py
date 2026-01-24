"""
Dashboard Multi-Contas: Cards dinâmicos com resumo de saldos.

Módulo responsável por renderizar cards dinâmicos que exibem:
  - Resumo macro: Disponível (Contas), Faturas (Cartões), Investimentos
  - Detalhe por conta: Grid de cards menores com saldo de cada conta
"""

import logging
from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import html

from src.database.operations import get_account_balances_summary

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


def _get_emoji_por_tipo(tipo_conta: str) -> str:
    """
    Retorna emoji correspondente ao tipo de conta.

    Args:
        tipo_conta: Tipo da conta ('conta', 'cartao', 'investimento').

    Returns:
        Emoji correspondente ao tipo.
    """
    emojis = {
        "conta": "🏦",
        "cartao": "💳",
        "investimento": "📈",
    }
    return emojis.get(tipo_conta, "💰")


def _get_cor_classe_bootstrap(cor_hex: str) -> str:
    """
    Mapeia cor hexadecimal para classe Bootstrap.

    Args:
        cor_hex: Cor em formato hexadecimal (ex: #3B82F6).

    Returns:
        Nome da classe Bootstrap (primary, success, danger).
    """
    cores_map = {
        "#3B82F6": "primary",  # Azul (Contas)
        "#10B981": "success",  # Verde (Investimentos)
        "#EF4444": "danger",  # Vermelho (Cartões)
    }
    return cores_map.get(cor_hex, "secondary")


def render_dashboard_cards(
    transaction_data: Dict[str, Any] | None = None,
) -> dbc.Container:
    """
    Renderiza layout completo de cards do Dashboard Multi-Contas.

    Layout com 2 linhas:
      - Linha 1: 3 cards grandes (Disponível, Faturas, Investimentos)
      - Linha 2: Grid de cards menores com detalhe por conta

    Args:
        transaction_data: Dados opcionais de transações (não usado,
            mantido por compatibilidade com assinatura anterior).

    Returns:
        dbc.Container com o layout completo dos cards.
    """
    try:
        logger.info("📊 Inicializando renderização de Dashboard Multi-Contas")

        # Buscar dados de contas
        resumo = get_account_balances_summary()

        total_disponivel = resumo.get("total_disponivel", 0.0)
        total_investido = resumo.get("total_investido", 0.0)
        total_cartoes = resumo.get("total_cartoes", 0.0)
        patrimonio_total = resumo.get("patrimonio_total", 0.0)
        detalhe_por_conta = resumo.get("detalhe_por_conta", [])

        logger.info(
            f"✓ Dados carregados: Disponível=R${total_disponivel:.2f}, "
            f"Investido=R${total_investido:.2f}, "
            f"Cartões=R${total_cartoes:.2f}, "
            f"Patrimônio=R${patrimonio_total:.2f}"
        )

        # ===== LINHA 1: RESUMO MACRO (3 CARDS GRANDES) =====

        # Card 1: Disponível (Contas Correntes)
        card_disponivel = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                "💰 Disponível",
                                className="card-title text-primary fw-bold",
                            ),
                            html.P(
                                _formatar_moeda(total_disponivel),
                                className="display-5 text-primary fw-bold",
                            ),
                            html.Small(
                                "Contas Correntes",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm border-start border-primary border-5",
            ),
            width=12,
            md=4,
            className="mb-4",
        )

        # Card 2: Faturas (Cartões)
        cor_cartoes = "text-danger" if total_cartoes < 0 else "text-warning"
        card_faturas = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                "💳 Faturas/Cartões",
                                className="card-title text-danger fw-bold",
                            ),
                            html.P(
                                _formatar_moeda(total_cartoes),
                                className=f"display-5 {cor_cartoes} fw-bold",
                            ),
                            html.Small(
                                "Débito (negativo = a pagar)",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm border-start border-danger border-5",
            ),
            width=12,
            md=4,
            className="mb-4",
        )

        # Card 3: Investimentos
        card_investimentos = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                "📈 Investimentos",
                                className="card-title text-success fw-bold",
                            ),
                            html.P(
                                _formatar_moeda(total_investido),
                                className="display-5 text-success fw-bold",
                            ),
                            html.Small(
                                "Aplicações & Ativos",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm border-start border-success border-5",
            ),
            width=12,
            md=4,
            className="mb-4",
        )

        linha_1 = dbc.Row(
            [card_disponivel, card_faturas, card_investimentos],
            className="g-3",
        )

        # ===== LINHA 2: PATRIMÔNIO TOTAL =====

        card_patrimonio = dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(
                                "🎯 Patrimônio Total",
                                className="card-title text-secondary fw-bold",
                            ),
                            html.P(
                                _formatar_moeda(patrimonio_total),
                                className="display-4 text-secondary fw-bold",
                            ),
                            html.Small(
                                "Liquidez + Investimentos - Dívida",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="shadow-sm border-start border-secondary border-5",
            ),
            width=12,
            className="mb-4",
        )

        linha_patrimonio = dbc.Row(
            card_patrimonio,
            className="g-3",
        )

        # ===== LINHA 3: DETALHE POR CONTA (GRID) =====

        cards_contas = []
        if detalhe_por_conta:
            logger.info(f"📋 Renderizando {len(detalhe_por_conta)} contas no detalhe")

            for conta in detalhe_por_conta:
                conta_id = conta.get("id", "?")
                conta_nome = conta.get("nome", "Conta Desconhecida")
                conta_tipo = conta.get("tipo", "conta")
                conta_saldo = conta.get("saldo", 0.0)
                conta_cor_hex = conta.get("cor_tipo", "#6B7280")

                emoji = _get_emoji_por_tipo(conta_tipo)
                cor_classe = _get_cor_classe_bootstrap(conta_cor_hex)

                card_conta = dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.Div(
                                    [
                                        html.Span(
                                            f"{emoji} {conta_nome}",
                                            className="fw-bold",
                                        ),
                                    ],
                                    className=f"text-{cor_classe}",
                                ),
                                className="bg-light",
                            ),
                            dbc.CardBody(
                                [
                                    html.P(
                                        _formatar_moeda(conta_saldo),
                                        className=f"text-{cor_classe} fw-bold mb-0",
                                    ),
                                    html.Small(
                                        conta_tipo.capitalize(),
                                        className="text-muted",
                                    ),
                                ],
                                className="py-2",
                            ),
                        ],
                        className="shadow-sm h-100",
                    ),
                    width=12,
                    sm=6,
                    md=4,
                    lg=3,
                    className="mb-3",
                )

                cards_contas.append(card_conta)

            linha_contas = dbc.Row(
                cards_contas,
                className="g-3",
            )
        else:
            logger.warning("⚠️ Nenhuma conta encontrada")
            linha_contas = dbc.Row(
                dbc.Col(
                    dbc.Alert(
                        "Nenhuma conta cadastrada. Crie uma conta para visualizar saldos.",
                        color="info",
                        className="mt-3",
                    ),
                    width=12,
                )
            )

        # ===== CONTAINER FINAL =====

        container = dbc.Container(
            [
                html.H4(
                    "📊 Dashboard Financeiro",
                    className="mb-4 mt-4 fw-bold text-dark",
                ),
                linha_1,
                html.Hr(className="my-4"),
                linha_patrimonio,
                html.Hr(className="my-4"),
                html.H5(
                    "Detalhes por Conta",
                    className="mb-3 fw-bold text-dark",
                ),
                linha_contas,
            ],
            fluid=True,
            className="py-4",
        )

        logger.info("✓ Dashboard Multi-Contas renderizado com sucesso")
        return container

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar Dashboard Multi-Contas: {e}")
        return dbc.Container(
            dbc.Row(
                dbc.Col(
                    dbc.Alert(
                        f"Erro ao carregar Dashboard: {str(e)}",
                        color="danger",
                        className="mt-3",
                    ),
                    width=12,
                )
            )
        )
