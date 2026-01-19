import logging

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.components.forms import transaction_form

logger = logging.getLogger(__name__)


def render_transaction_modal(is_open: bool = False) -> dbc.Modal:
    """
    Renderiza um modal com formulários de receita e despesa em abas.

    Exibe um modal Bootstrap com duas abas internas que alternam
    entre formulários de entrada de Receita e Despesa.

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
                                            transaction_form("despesa"),
                                            className="p-3",
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="💰 Receita",
                                    value="tab-receita",
                                    children=[
                                        html.Div(
                                            transaction_form("receita"),
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
