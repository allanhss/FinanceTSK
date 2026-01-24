"""Nubank CSV importer interface component."""

import logging
from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dash_table import DataTable

logger = logging.getLogger(__name__)


def render_importer_page(
    account_options: List[Dict[str, Any]] = None, existing_tags: List[str] = None
) -> dbc.Container:
    """Render Nubank CSV importer interface with preview.

    Creates a full-page interface for uploading CSV files, previewing
    transactions before import, and confirming the operation.

    Args:
        account_options: List of account options for dropdown. Defaults to empty list.
        existing_tags: List of existing tag strings for modal dropdown. Defaults to empty list.

    Components:
        - Account selection dropdown
        - Upload area with drag-and-drop support
        - Temporary store for transaction data
        - Preview table (editable and deletable rows)
        - Tag editor modal with multi-select dropdown
        - Confirm button and feedback messages

    Returns:
        dbc.Container with complete importer interface.

    Example:
        >>> page = render_importer_page(
        ...     account_options=[{"label": "Nubank", "value": 1}],
        ...     existing_tags=["Moto", "Viagem"]
        ... )
    """
    if account_options is None:
        account_options = []

    if existing_tags is None:
        existing_tags = []

    return dbc.Container(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                "📥 Importador Nubank",
                                className="mb-1",
                            ),
                            html.P(
                                "Selecione um arquivo CSV de extrato "
                                "para revisar e importar transações",
                                className="text-muted small",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Account Selection
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "1. Selecione a Conta de Destino:",
                                className="fw-bold",
                            ),
                            dcc.Dropdown(
                                id="dropdown-import-conta",
                                options=account_options,
                                placeholder="Ex: 💳 Nubank Crédito...",
                                className="mb-3",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Upload Area
            dbc.Row(
                [
                    dbc.Col(
                        [
                            _render_upload_area(),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Preview Area (initially hidden)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                id="preview-container",
                                children=[],
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Action Buttons
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button(
                                "💾 Confirmar Importação",
                                id="btn-save-import",
                                color="success",
                                size="lg",
                                disabled=True,
                                className="me-2",
                            ),
                            dbc.Button(
                                "🔄 Limpar",
                                id="btn-clear-import",
                                color="secondary",
                                size="lg",
                                outline=True,
                                disabled=True,
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Feedback Messages
            html.Div(
                id="import-feedback",
                children=[],
            ),
            # Hidden Stores
            dcc.Store(
                id="store-import-data",
                data=None,
            ),
            dcc.Store(
                id="store-import-status",
                data={
                    "imported": False,
                    "count": 0,
                    "message": "",
                },
            ),
            # Store for tracking editing row index
            dcc.Store(
                id="store-editing-row-index",
                data=None,
            ),
            # Modal for tag editing
            render_tag_editor_modal(existing_tags=existing_tags),
        ],
        fluid=True,
        className="py-4",
    )


def _render_upload_area() -> dbc.Card:
    """Render the upload area with drag-and-drop support.

    Returns:
        dbc.Card with upload component and styling.
    """
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Label(
                        "2. Arraste ou Selecione o Arquivo (CSV/OFX):",
                        className="fw-bold mt-3",
                    ),
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            [
                                html.H5(
                                    "📂 Arraste o arquivo CSV aqui",
                                    className="mb-2",
                                ),
                                html.P(
                                    "ou clique para selecionar",
                                    className="text-muted",
                                ),
                                html.P(
                                    "Aceita extratos do Nubank "
                                    "(Cartão e Conta Corrente)",
                                    className="small text-info",
                                ),
                            ],
                            className="text-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "200px",
                            "lineHeight": "60px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "10px",
                            "textAlign": "center",
                            "padding": "40px",
                            "cursor": "pointer",
                            "backgroundColor": "#f8f9fa",
                            "transition": "all 0.3s",
                        },
                    ),
                    html.Div(
                        id="upload-status",
                        children=[],
                        className="mt-3",
                    ),
                ],
                className="p-4",
            ),
        ],
        className="border-0 shadow-sm",
    )


def render_preview_table(
    data: List[Dict[str, Any]],
    category_options: List[Dict[str, str]] = None,
    existing_tags: List[str] = None,
) -> dbc.Card:
    """Render editable preview table for transactions.

    Args:
        data: List of transaction dictionaries with keys:
            - data (str): ISO format date
            - descricao (str): Transaction description
            - valor (float): Transaction value
            - tipo (str): "receita" or "despesa"
            - categoria (str): Category name
            - tags (str): Comma-separated tags
        category_options: List of category options for dropdown.
            Format: [{'label': 'Alimentação', 'value': 'Alimentação'}, ...]
        existing_tags: List of existing tag strings for dropdown autocomplete.
            Format: ['Moto', 'Viagem', 'Lazer', ...]

    Returns:
        dbc.Card with DataTable for editing.
    """
    if not data:
        return html.Div()

    if category_options is None:
        category_options = []

    if existing_tags is None:
        existing_tags = []

    # Prepare data for table display
    dados_tabela = [
        {
            "data": tx.get("data", ""),
            "descricao": tx.get("descricao", ""),
            "valor": f"R$ {tx.get('valor', 0):.2f}".replace(
                ".",
                ",",
            ),
            "tipo": "💰 Receita" if tx.get("tipo") == "receita" else "💸 Despesa",
            "categoria": tx.get("categoria", "A Classificar"),
            "tags": tx.get("tags", ""),
            "skipped": tx.get("skipped", False),
            "disable_edit": tx.get("disable_edit", False),
        }
        for tx in data
    ]

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        f"📋 Pré-visualização ({len(data)} " "transações)",
                        className="mb-0",
                    ),
                ],
                className="bg-light",
            ),
            dbc.CardBody(
                [
                    DataTable(
                        id="table-import-preview",
                        columns=[
                            {
                                "name": "Data",
                                "id": "data",
                                "editable": False,
                            },
                            {
                                "name": "Descrição",
                                "id": "descricao",
                                "editable": True,
                            },
                            {
                                "name": "Valor",
                                "id": "valor",
                                "editable": False,
                            },
                            {
                                "name": "Tipo",
                                "id": "tipo",
                                "editable": False,
                            },
                            {
                                "name": "Categoria",
                                "id": "categoria",
                                "editable": True,
                                "presentation": "dropdown",
                            },
                            {
                                "name": "Tags (clique para editar)",
                                "id": "tags",
                                "editable": False,
                            },
                        ],
                        data=dados_tabela,
                        row_deletable=True,
                        editable=True,
                        dropdown={
                            "categoria": {
                                "options": category_options,
                                "clearable": False,
                            }
                        },
                        style_cell={
                            "textAlign": "left",
                            "padding": "10px",
                            "fontSize": "14px",
                            "minHeight": "40px",
                            "height": "auto",
                        },
                        style_cell_conditional=[
                            {
                                "if": {"column_id": "categoria"},
                                "minWidth": "180px",
                                "minHeight": "45px",
                            },
                            {
                                "if": {"column_id": "tags"},
                                "minWidth": "120px",
                            },
                        ],
                        style_header={
                            "backgroundColor": "rgb(230, 230, 230)",
                            "fontWeight": "bold",
                            "padding": "12px",
                        },
                        style_data_conditional=[
                            {
                                "if": {"row_index": "odd"},
                                "backgroundColor": "rgb(248, 249, 250)",
                            },
                            {
                                "if": {"filter_query": "{disable_edit} = true"},
                                "color": "#adb5bd",
                                "backgroundColor": "#f8f9fa",
                                "fontStyle": "italic",
                            },
                        ],
                        css=[
                            {
                                "selector": ".Select-menu-outer",
                                "rule": "display: block !important; z-index: 1000 !important;",
                            },
                            {
                                "selector": ".Select-menu",
                                "rule": "max-height: 300px; overflow-y: auto;",
                            },
                            {
                                "selector": "td.cell--selected, td.focused",
                                "rule": "background-color: #f8f9fa !important;",
                            },
                            {
                                "selector": ".dash-table-cell.dash-cell.editing",
                                "rule": "display: flex !important;",
                            },
                        ],
                    ),
                ],
                className="p-0",
            ),
        ],
        className="border-0 shadow-sm mt-3",
    )


def render_import_success(
    count: int | str,
) -> dbc.Alert:
    """Render success alert for completed import.

    Args:
        count: Number of transactions imported (int) or custom message (str).
               If int: shows default message with count.
               If str: uses as-is (allows custom messages like "10\n🔄 Parcelas futuras: 5").

    Returns:
        dbc.Alert with success message.
    """
    # Determinar se é número ou mensagem customizada
    if isinstance(count, int):
        message_text = f"Foram importadas {count} transações para o banco de dados."
    else:
        # String customizada: pode conter quebras de linha e emojis
        message_text = str(count)

    return dbc.Alert(
        [
            html.H5(
                "✅ Importação Concluída com Sucesso!",
                className="alert-heading mb-3",
            ),
            html.P(
                message_text,
                className="mb-0",
                style={"whiteSpace": "pre-wrap"},  # Preservar quebras de linha
            ),
        ],
        color="success",
        dismissable=True,
        className="mt-3",
    )


def render_import_error(message: str) -> dbc.Alert:
    """Render error alert for failed import.

    Args:
        message: Error message to display.

    Returns:
        dbc.Alert with error message.
    """
    return dbc.Alert(
        [
            html.H5(
                "❌ Erro na Importação",
                className="alert-heading mb-3",
            ),
            html.P(message, className="mb-0"),
        ],
        color="danger",
        dismissable=True,
        className="mt-3",
    )


def render_import_info(message: str) -> dbc.Alert:
    """Render info alert for import status messages.

    Args:
        message: Info message to display.

    Returns:
        dbc.Alert with info message.
    """
    return dbc.Alert(
        message,
        color="info",
        dismissable=True,
        className="mt-3",
    )


def render_tag_editor_modal(existing_tags: List[str] = None) -> dbc.Modal:
    """Render modal for editing tags with multi-select dropdown.

    Args:
        existing_tags: List of existing tag strings for dropdown options.

    Returns:
        dbc.Modal with tag editor components.
    """
    if existing_tags is None:
        existing_tags = []

    # Convert tag strings to dropdown options
    tag_options = [{"label": tag, "value": tag} for tag in existing_tags]

    return dbc.Modal(
        [
            dbc.ModalHeader(
                "Editar Tags",
                close_button=True,
                className="bg-light",
            ),
            dbc.ModalBody(
                [
                    html.Label(
                        "Selecione as tags (use Ctrl/Cmd para múltiplas seleções):",
                        htmlFor="dropdown-tag-editor",
                        className="fw-bold mb-2",
                    ),
                    dcc.Dropdown(
                        id="dropdown-tag-editor",
                        options=tag_options,
                        value=[],
                        multi=True,
                        searchable=True,
                        clearable=True,
                        placeholder="Selecione tags ou comece a digitar...",
                        optionHeight=50,
                        className="mb-3",
                    ),
                    html.Div(
                        id="div-tag-editor-preview",
                        className="alert alert-light",
                        children="Nenhuma tag selecionada",
                    ),
                ],
                style={"padding": "20px"},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancelar",
                        id="btn-cancel-tags",
                        color="secondary",
                        outline=True,
                    ),
                    dbc.Button(
                        "Salvar Tags",
                        id="btn-save-tags",
                        color="primary",
                    ),
                ],
                className="gap-2",
            ),
        ],
        id="modal-tag-editor",
        is_open=False,
        size="md",
        backdrop="static",
        keyboard=False,
    )
