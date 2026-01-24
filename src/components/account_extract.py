"""
Extrato de Conta - Visualização completa de movimentações.

Fornece interface para visualizar todas as transações de uma conta específica,
permitindo conciliação e análise detalhada do histórico.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import date

import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dash_table import DataTable

from src.database.operations import get_transactions, get_account_by_id

logger = logging.getLogger(__name__)


def render_account_extract(conta_id: int) -> dbc.Container:
    """
    Renderiza página de extrato detalhado de uma conta.

    Exibe todas as transações da conta com cálculo de saldo acumulado linha a linha,
    permitindo conciliação e análise histórica.

    Args:
        conta_id: ID da conta a exibir.

    Returns:
        Componente dbc.Container com extrato completo.

    Example:
        >>> extract = render_account_extract(conta_id=1)
        >>> isinstance(extract, dbc.Container)
        True
    """
    try:
        # Recuperar dados da conta
        conta = get_account_by_id(conta_id)
        if not conta:
            return dbc.Alert(
                f"❌ Conta com ID {conta_id} não encontrada.",
                color="danger",
                className="mt-4",
            )

        # Recuperar todas as transações (sem filtros)
        transacoes = get_transactions()

        # Filtrar apenas transações dessa conta
        transacoes_conta = [t for t in transacoes if t.get("conta_id") == conta_id]

        logger.info(
            f"[EXTRATO] Carregando extrato da conta {conta.nome}: "
            f"{len(transacoes_conta)} transações"
        )

        # Preparar dados para tabela com saldo acumulado
        dados_extrato = _prepare_extract_data(transacoes_conta, conta.saldo_inicial)

        # Emoji por tipo
        tipo_emoji = {
            "conta": "🏦",
            "cartao": "💳",
            "investimento": "📈",
        }.get(conta.tipo, "💰")

        # Renderizar layout
        return dbc.Container(
            [
                # Breadcrumb / Voltar
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Link(
                                    "← Voltar para Contas",
                                    href="/contas",
                                    className="text-muted text-decoration-none mb-3 d-inline-block",
                                )
                            ],
                            width=12,
                        )
                    ],
                    className="mb-3",
                ),
                # Cabeçalho
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(
                                    f"{tipo_emoji} Extrato: {conta.nome}",
                                    className="mb-1 fw-bold",
                                ),
                                html.P(
                                    f"Saldo Inicial: R$ {conta.saldo_inicial:,.2f}".replace(
                                        ",", "#"
                                    )
                                    .replace(".", ",")
                                    .replace("#", "."),
                                    className="text-muted small",
                                ),
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
                # Tabela de extrato
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                _render_extract_table(dados_extrato),
                            ],
                            width=12,
                        )
                    ],
                    className="mb-4",
                ),
            ],
            fluid=True,
            className="py-4",
        )

    except Exception as e:
        logger.error(
            f"[EXTRATO] Erro ao carregar extrato da conta {conta_id}: {e}",
            exc_info=True,
        )
        return dbc.Alert(
            f"❌ Erro ao carregar extrato: {str(e)}",
            color="danger",
            className="mt-4",
        )


def _prepare_extract_data(
    transacoes: List[Dict[str, Any]], saldo_inicial: float
) -> List[Dict[str, Any]]:
    """
    Prepara dados para exibição na tabela de extrato com saldo acumulado.

    Args:
        transacoes: Lista de transações da conta.
        saldo_inicial: Saldo inicial da conta.

    Returns:
        Lista de dicionários com dados formatados e saldo acumulado.
    """
    dados_formatados = []
    saldo_acumulado = saldo_inicial

    for tx in transacoes:
        # Extrair categoria nome
        categoria_nome = "Sem categoria"
        if isinstance(tx.get("categoria"), dict):
            categoria_nome = tx.get("categoria", {}).get("nome", "Sem categoria")
        else:
            categoria_nome = tx.get("categoria", "Sem categoria")

        # Determinar cor e sinal do valor
        tipo = tx.get("tipo", "")
        valor = float(tx.get("valor", 0))

        if tipo == "receita":
            saldo_acumulado += valor
            cor_valor = "#22C55E"  # Verde
            sinal = "+"
        elif tipo == "despesa":
            saldo_acumulado -= valor
            cor_valor = "#EF4444"  # Vermelho
            sinal = "-"
        else:
            cor_valor = "#6B7280"  # Cinza
            sinal = ""

        # Formatar data
        data_str = tx.get("data", "")
        if isinstance(data_str, str):
            # Converte ISO para DD/MM/YYYY
            if "T" in data_str:
                data_str = data_str.split("T")[0]
            if "-" in data_str:
                parts = data_str.split("-")
                data_str = f"{parts[2]}/{parts[1]}/{parts[0]}"

        dados_formatados.append(
            {
                "data": data_str,
                "tipo_emoji": "💰" if tipo == "receita" else "💸",
                "categoria": categoria_nome,
                "descricao": tx.get("descricao", ""),
                "valor": f"R$ {valor:,.2f}".replace(",", "#")
                .replace(".", ",")
                .replace("#", "."),
                "valor_num": valor,
                "sinal": sinal,
                "cor_valor": cor_valor,
                "saldo": f"R$ {saldo_acumulado:,.2f}".replace(",", "#")
                .replace(".", ",")
                .replace("#", "."),
                "saldo_num": saldo_acumulado,
            }
        )

    return dados_formatados


def _render_extract_table(dados: List[Dict[str, Any]]) -> Any:
    """
    Renderiza tabela de extrato em DataTable ou dbc.Table.

    Args:
        dados: Dados preparados para a tabela.

    Returns:
        Componente DataTable com estilização condicional.
    """
    if not dados:
        return dbc.Alert(
            "📭 Nenhuma transação registrada para esta conta.",
            color="info",
            className="text-center",
        )

    # Usar DataTable para melhor funcionalidade
    return DataTable(
        columns=[
            {
                "name": "Data",
                "id": "data",
                "type": "text",
            },
            {
                "name": "",
                "id": "tipo_emoji",
                "type": "text",
            },
            {
                "name": "Categoria",
                "id": "categoria",
                "type": "text",
            },
            {
                "name": "Descrição",
                "id": "descricao",
                "type": "text",
            },
            {
                "name": "Valor",
                "id": "valor",
                "type": "text",
            },
            {
                "name": "Saldo",
                "id": "saldo",
                "type": "text",
            },
        ],
        data=dados,
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontSize": "13px",
            "fontFamily": "monospace",
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold",
            "padding": "12px",
            "fontSize": "13px",
        },
        style_data_conditional=[
            # Linhas pares com fundo claro
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 249, 250)",
            },
            # Hover
            {
                "if": {"state": "hover"},
                "backgroundColor": "rgb(240, 245, 250)",
            },
            # Coluna de data em negrito
            {
                "if": {"column_id": "data"},
                "fontWeight": "bold",
                "minWidth": "100px",
            },
            # Coluna de valor em cor (positivo/negativo)
            {
                "if": {
                    "column_id": "valor",
                    "filter_query": "{sinal} contains '+'",
                },
                "color": "#22C55E",
                "fontWeight": "bold",
            },
            {
                "if": {
                    "column_id": "valor",
                    "filter_query": "{sinal} contains '-'",
                },
                "color": "#EF4444",
                "fontWeight": "bold",
            },
            # Coluna de saldo
            {
                "if": {"column_id": "saldo"},
                "fontWeight": "bold",
                "minWidth": "120px",
                "backgroundColor": "#f0f9ff",
            },
        ],
        style_cell_conditional=[
            {
                "if": {"column_id": "data"},
                "minWidth": "100px",
                "textAlign": "center",
            },
            {
                "if": {"column_id": "tipo_emoji"},
                "minWidth": "40px",
                "textAlign": "center",
                "width": "40px",
            },
            {
                "if": {"column_id": "categoria"},
                "minWidth": "120px",
            },
            {
                "if": {"column_id": "descricao"},
                "minWidth": "200px",
            },
            {
                "if": {"column_id": "valor"},
                "minWidth": "100px",
                "textAlign": "right",
            },
            {
                "if": {"column_id": "saldo"},
                "minWidth": "120px",
                "textAlign": "right",
            },
        ],
    )


def add_extract_link_to_card(card_component: Any, conta_id: int) -> Any:
    """
    Adiciona link de extrato ao card da conta.

    Modifica o card para incluir um link "Ver Extrato" que leva
    para a página de extrato da conta.

    Args:
        card_component: Componente dbc.Card original.
        conta_id: ID da conta.

    Returns:
        Componente modificado com link adicionado.

    Note:
        Esta função é para ser usada como helper se necessário.
        A modificação principal é feita diretamente em account_manager.py.
    """
    return card_component
