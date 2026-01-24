"""
Componente de Gerenciamento de Contas.

Fornece interface para cadastrar, visualizar e gerenciar contas bancárias,
cartões de crédito e investimentos. Organiza as contas em cards separados
por tipo para melhor visualização.
"""

from typing import List, Dict, Any, Union
import dash_bootstrap_components as dbc
from dash import html, dcc

from src.database.models import Conta


def render_account_manager(contas: List[Any]) -> dbc.Container:
    """
    Renderiza interface completa de gerenciamento de contas.

    Exibe formulário para cadastro de novas contas e grid de cards com
    contas existentes, separadas por tipo (conta, cartão, investimento).

    Args:
        contas: Lista de dicionários com dados das contas.
                Formato: [{'id': int, 'nome': str, 'tipo': str,
                'saldo_inicial': float}, ...]

    Returns:
        Componente dbc.Container com layout completo.

    Example:
        >>> contas_data = [
        ...     {'id': 1, 'nome': 'Conta Corrente', 'tipo': 'conta',
        ...      'saldo_inicial': 1000.0}
        ... ]
        >>> layout = render_account_manager(contas_data)
        >>> assert layout is not None
    """
    # Gerar grid de contas
    grid_contas = render_accounts_grid(contas)

    return dbc.Container(
        [
            # Alerta (posicionado no topo para visibilidade)
            html.Div(
                id="account-feedback-alert",
                children=[],
                className="mb-3",
            ),
            # Título principal
            html.Div(
                [
                    html.H2(
                        "💰 Gerenciamento de Contas",
                        className="mb-4 text-primary fw-bold",
                    )
                ],
                className="mt-4 mb-5",
            ),
            # Linha: Formulário + Instruções
            dbc.Row(
                [
                    dbc.Col(
                        _render_form_nova_conta(),
                        md=12,
                        lg=5,
                        className="mb-4 mb-lg-0",
                    ),
                    dbc.Col(
                        _render_instrucoes(),
                        md=12,
                        lg=7,
                    ),
                ],
                className="mb-5",
            ),
            # Divisor visual
            html.Hr(className="my-5"),
            # Título "Suas Contas"
            html.H3(
                "📊 Suas Contas",
                className="mb-4 text-secondary fw-bold",
            ),
            # Container para lista de contas (alvo para atualizações)
            html.Div(
                id="accounts-list-container",
                children=grid_contas,
            ),
            # Store para dados temporários
            dcc.Store(id="account-store-data"),
        ],
        fluid=True,
        className="py-4",
    )


def render_accounts_grid(contas: List[Any]) -> html.Div:
    """
    Renderiza grid de cards das contas, separadas por tipo.

    Esta função é isolada para permitir atualização dinâmica via callbacks,
    quando novas contas são criadas ou excluídas.

    Args:
        contas: Lista de dicionários com dados das contas.

    Returns:
        Componente html.Div contendo as seções de contas por tipo.

    Example:
        >>> contas = [{'id': 1, 'nome': 'Nubank', 'tipo': 'conta'}]
        >>> grid = render_accounts_grid(contas)
        >>> isinstance(grid, html.Div)
        True
    """
    # Separar contas por tipo
    contas_por_tipo = _organize_contas_by_tipo(contas)

    return html.Div(
        [
            _render_secao_contas(
                "Contas Corrente/Pagamentos",
                "🏦",
                contas_por_tipo.get("conta", []),
                "conta",
            ),
            _render_secao_contas(
                "Cartões de Crédito",
                "💳",
                contas_por_tipo.get("cartao", []),
                "cartao",
            ),
            _render_secao_contas(
                "Investimentos",
                "📈",
                contas_por_tipo.get("investimento", []),
                "investimento",
            ),
        ],
        id="contas-container",
    )


def _render_form_nova_conta() -> dbc.Card:
    """
    Renderiza formulário para cadastro de nova conta.

    Returns:
        Componente dbc.Card com formulário.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    "🆕 Nova Conta / Cartão",
                    className="mb-0 fw-bold",
                ),
                className="bg-light",
            ),
            dbc.CardBody(
                [
                    # Input: Nome
                    dbc.Row(
                        [
                            dbc.Label(
                                "Nome da Conta",
                                html_for="input-nome-conta",
                                className="fw-bold",
                            ),
                            dbc.Input(
                                id="input-nome-conta",
                                type="text",
                                placeholder="Ex: Conta Banco X",
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Dropdown: Tipo
                    dbc.Row(
                        [
                            dbc.Label(
                                "Tipo",
                                html_for="dropdown-tipo-conta",
                                className="fw-bold",
                            ),
                            dcc.Dropdown(
                                id="dropdown-tipo-conta",
                                options=[
                                    {
                                        "label": "Conta Corrente/Pagamentos",
                                        "value": "conta",
                                    },
                                    {
                                        "label": "Cartão de Crédito",
                                        "value": "cartao",
                                    },
                                    {
                                        "label": "Investimentos",
                                        "value": "investimento",
                                    },
                                ],
                                value="conta",
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Input: Saldo Inicial
                    dbc.Row(
                        [
                            dbc.Label(
                                "Saldo Inicial / Limite",
                                html_for="input-saldo-inicial",
                                className="fw-bold",
                            ),
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("R$"),
                                    dbc.Input(
                                        id="input-saldo-inicial",
                                        type="number",
                                        placeholder="0,00",
                                        min=0,
                                        step=0.01,
                                        className="mb-3",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Botão: Salvar
                    dbc.Button(
                        "💾 Salvar Conta",
                        id="btn-salvar-conta",
                        color="success",
                        size="lg",
                        className="w-100 fw-bold",
                    ),
                ]
            ),
        ],
        className="shadow-sm border-0 mb-4",
    )


def _render_instrucoes() -> dbc.Alert:
    """
    Renderiza card com instruções de uso.

    Returns:
        Componente dbc.Alert com instruções.
    """
    return dbc.Alert(
        [
            html.H5("ℹ️ Como usar", className="alert-heading fw-bold"),
            html.Hr(),
            html.Ul(
                [
                    html.Li("Preencha o formulário com os dados da sua conta"),
                    html.Li(
                        "Selecione o tipo correto (Conta, Cartão ou " "Investimento)"
                    ),
                    html.Li("Insira o saldo inicial ou limite de crédito"),
                    html.Li("Clique em 'Salvar Conta' para registrar"),
                    html.Li(
                        [
                            "Suas contas aparecerão abaixo, " "separadas por tipo",
                        ]
                    ),
                    html.Li("Use o botão '🗑️ Excluir' para remover uma conta"),
                ]
            ),
        ],
        color="info",
        className="shadow-sm border-0",
    )


def _render_secao_contas(
    titulo: str,
    icone: str,
    contas_lista: List[Any],
    tipo: str,
) -> html.Div:
    """
    Renderiza seção com cards de contas de um tipo específico.

    Args:
        titulo: Título da seção.
        icone: Emoji para título.
        contas_lista: Lista de contas deste tipo.
        tipo: Tipo de conta ('conta', 'cartao', 'investimento').

    Returns:
        Componente html.Div com seção de contas.
    """
    if not contas_lista:
        return html.Div(
            [
                html.H5(
                    f"{icone} {titulo}",
                    className="text-muted mb-3",
                ),
                dbc.Alert(
                    "Nenhuma conta cadastrada nesta categoria.",
                    color="light",
                    className="text-center mb-4",
                ),
            ]
        )

    return html.Div(
        [
            html.H5(
                f"{icone} {titulo}",
                className="text-secondary mb-3 fw-bold",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        _render_card_conta(conta),
                        xs=12,
                        sm=6,
                        lg=4,
                        className="mb-4",
                    )
                    for conta in contas_lista
                ]
            ),
        ],
        className="mb-5",
    )


def _render_card_conta(
    conta: Any,
) -> dbc.Card:
    """
    Renderiza card individual para uma conta.

    Args:
        conta: Objeto Conta ou dicionário com dados da conta.
               Deve conter 'id', 'nome', 'tipo', 'saldo_inicial'.

    Returns:
        Componente dbc.Card com informações da conta.
    """
    conta_id = conta.id if hasattr(conta, "id") else conta["id"]
    nome = conta.nome if hasattr(conta, "nome") else conta["nome"]
    tipo = conta.tipo if hasattr(conta, "tipo") else conta["tipo"]
    saldo = (
        conta.saldo_inicial
        if hasattr(conta, "saldo_inicial")
        else conta["saldo_inicial"]
    )

    # Emoji por tipo
    emoji_tipo = {
        "conta": "🏦",
        "cartao": "💳",
        "investimento": "📈",
    }.get(tipo, "💰")

    # Cor de borda por tipo
    cor_borda = {
        "conta": "success",
        "cartao": "warning",
        "investimento": "info",
    }.get(tipo, "secondary")

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    # Cabeçalho com nome e tipo
                    html.Div(
                        [
                            html.H6(
                                f"{emoji_tipo} {nome}",
                                className="card-title fw-bold mb-2",
                                style={
                                    "overflow": "hidden",
                                    "text-overflow": "ellipsis",
                                    "white-space": "nowrap",
                                },
                            ),
                        ]
                    ),
                    # Saldo
                    html.Div(
                        [
                            html.Small(
                                "Saldo Inicial",
                                className="text-muted",
                            ),
                            html.H5(
                                f"R$ {saldo:,.2f}".replace(",", "#")
                                .replace(".", ",")
                                .replace("#", "."),
                                className="text-primary fw-bold mb-3",
                            ),
                        ]
                    ),
                    # Botões
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Link(
                                    dbc.Button(
                                        "📋 Extrato",
                                        color="info",
                                        size="sm",
                                        className="w-100",
                                        outline=True,
                                    ),
                                    href=f"/contas/{conta_id}",
                                    style={"textDecoration": "none"},
                                ),
                                xs=12,
                                className="mb-2",
                            ),
                            dbc.Col(
                                dbc.Button(
                                    "🗑️ Excluir",
                                    id={"type": "btn-excluir-conta", "index": conta_id},
                                    color="danger",
                                    size="sm",
                                    className="w-100",
                                    outline=True,
                                ),
                                xs=12,
                            ),
                        ]
                    ),
                ]
            ),
        ],
        className=f"shadow-sm border border-{cor_borda}",
    )


def _organize_contas_by_tipo(
    contas: List[Any],
) -> Dict[str, List[Any]]:
    """
    Organiza contas em dicionário separado por tipo.

    Args:
        contas: Lista de contas.

    Returns:
        Dicionário: {'conta': [...], 'cartao': [...],
        'investimento': [...]}
    """
    resultado = {"conta": [], "cartao": [], "investimento": []}

    for conta in contas:
        # Extrair tipo suportando tanto objetos quanto dicionários
        if hasattr(conta, "tipo"):
            tipo = conta.tipo
        else:
            tipo = conta.get("tipo", "conta")

        if tipo in resultado:
            resultado[tipo].append(conta)

    # Ordenar por nome dentro de cada tipo
    for tipo in resultado:
        resultado[tipo].sort(
            key=lambda c: c.nome if hasattr(c, "nome") else c.get("nome", "")
        )

    return resultado
