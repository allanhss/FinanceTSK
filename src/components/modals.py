import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.forms import transaction_form

logger = logging.getLogger(__name__)


def render_transaction_modal(is_open: bool = False) -> dbc.Modal:
    """
    Renderiza um modal com formulários de receita e despesa em abas.

    Exibe um modal Bootstrap com duas abas internas que alternam
    entre formulários de entrada de Receita e Despesa. Inclui seleção
    de conta com filtros por tipo de transação.

    Args:
        is_open: Se True, modal abre por padrão. Padrão: False.

    Returns:
        dbc.Modal contendo tabs com formulários de transação.

    Example:
        >>> modal = render_transaction_modal(is_open=False)
        >>> isinstance(modal, dbc.Modal)
        True
    """
    try:
        logger.info(f"🎯 Renderizando modal de transações (is_open={is_open})")

        modal = dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("💳 Nova Transação"),
                    close_button=True,
                ),
                dbc.ModalBody(
                    [
                        dbc.Alert(
                            "Erro ao salvar transação.",
                            id="alerta-modal",
                            is_open=False,
                            color="danger",
                            dismissable=True,
                            className="mb-3",
                        ),
                        dcc.Tabs(
                            id="tabs-modal-transacao",
                            value="tab-despesa",
                            children=[
                                dcc.Tab(
                                    label="💸 Despesa",
                                    value="tab-despesa",
                                    children=[
                                        html.Div(
                                            [
                                                _render_conta_selector("despesa"),
                                                transaction_form("despesa"),
                                            ],
                                            className="p-3",
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="💰 Receita",
                                    value="tab-receita",
                                    children=[
                                        html.Div(
                                            [
                                                _render_conta_selector("receita"),
                                                transaction_form("receita"),
                                            ],
                                            className="p-3",
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                    className="pt-3",
                ),
            ],
            id="modal-transacao",
            is_open=is_open,
            size="lg",
            centered=True,
        )
        logger.info("✓ Modal renderizado com sucesso")
        return modal

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar modal de transação: {e}", exc_info=True)
        return dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Erro"),
                    close_button=True,
                ),
                dbc.ModalBody(
                    dbc.Alert(
                        "Erro ao carregar formulário. Tente novamente.",
                        color="danger",
                    )
                ),
            ],
            id="modal-transacao",
            is_open=False,
            size="lg",
            centered=True,
        )


def _render_conta_selector(tipo: str) -> dbc.Row:
    """
    Renderiza seletor de conta para modal de transação.

    Args:
        tipo: Tipo de transação ('receita' ou 'despesa').

    Returns:
        dbc.Row com dropdown de seleção de conta.
    """
    return dbc.Row(
        dbc.Col(
            [
                dbc.Label(
                    "Conta",
                    html_for=f"select-{tipo}-conta",
                    className="fw-bold",
                ),
                dcc.Dropdown(
                    id=f"select-{tipo}-conta",
                    placeholder="Selecione uma conta",
                    clearable=False,
                ),
            ],
            md=12,
        ),
        className="mb-3",
    )
