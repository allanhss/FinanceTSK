import logging
import re
import time
import traceback
import json
from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
import dash
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL, ctx, no_update
from dash.exceptions import PreventUpdate

from src.database.connection import init_database
from src.utils.init_data import ensure_default_accounts, ensure_default_categories
from src.database.operations import (
    get_transactions,
    create_transaction,
    get_cash_flow_data,
    get_category_matrix_data,
    get_tag_matrix_data,
    get_categories,
    create_category,
    delete_category,
    update_category,
    get_used_icons,
    get_all_tags,
    get_unique_tags_list,
    get_classification_history,
    get_accounts,
    create_account,
    delete_account,
    get_account_balance,
)
from src.components.dashboard import render_summary_cards
from src.components.dashboard_cards import render_dashboard_cards
from src.components.modals import render_transaction_modal
from src.components.tables import render_transactions_table
from src.components.cash_flow import render_cash_flow_table
from src.components.category_manager import render_category_manager, EMOJI_OPTIONS
from src.components.category_matrix import render_category_matrix
from src.components.tag_matrix import render_tag_matrix
from src.components.account_manager import render_account_manager, render_accounts_grid
from src.components.account_extract import render_account_extract
from src.components.budget_progress import (
    render_budget_progress,
    render_budget_dashboard,
    render_budget_matrix,
)
from src.components.dashboard_charts import (
    render_evolution_chart,
    render_top_expenses_chart,
)
from src.components.importer import (
    render_importer_page,
    render_preview_table,
    render_import_success,
    render_import_error,
    render_tag_editor_modal,
)
from src.utils.importers import parse_upload_content

logger = logging.getLogger(__name__)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)

app.title = "FinanceTSK - Gestor Financeiro"


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Container(
            [
                dbc.Row(
                    [
                        # ===== SIDEBAR (Coluna 1) =====
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        # Cabeçalho da Sidebar
                                        html.H4(
                                            "💰 FinanceTSK",
                                            className="fw-bold text-primary",
                                        ),
                                        html.Hr(),
                                        # Ações Rápidas
                                        dbc.Button(
                                            "+ Receita",
                                            id="btn-nova-receita",
                                            color="success",
                                            size="md",
                                            className="w-100 mb-2",
                                        ),
                                        dbc.Button(
                                            "+ Despesa",
                                            id="btn-nova-despesa",
                                            color="danger",
                                            size="md",
                                            className="w-100 mb-4",
                                        ),
                                        # Seção: Lançamentos
                                        html.P(
                                            "Lançamentos",
                                            className="fw-bold text-muted small",
                                        ),
                                        dbc.Nav(
                                            [
                                                dbc.NavLink(
                                                    "📊 Dashboard",
                                                    href="/",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "💰 Receitas",
                                                    href="/receitas",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "💸 Despesas",
                                                    href="/despesas",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "📥 Importar",
                                                    href="/importar",
                                                    active="exact",
                                                ),
                                            ],
                                            vertical=True,
                                            pills=True,
                                            className="mb-4",
                                        ),
                                        # Seção: Inteligência
                                        html.P(
                                            "Inteligência",
                                            className="fw-bold text-muted small",
                                        ),
                                        dbc.Nav(
                                            [
                                                dbc.NavLink(
                                                    "🎯 Orçamento",
                                                    href="/orcamento",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "📈 Análise",
                                                    href="/analise",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "🏷️ Tags",
                                                    href="/tags",
                                                    active="exact",
                                                ),
                                            ],
                                            vertical=True,
                                            pills=True,
                                            className="mb-4",
                                        ),
                                        # Seção: Configuração
                                        html.P(
                                            "Configuração",
                                            className="fw-bold text-muted small",
                                        ),
                                        dbc.Nav(
                                            [
                                                dbc.NavLink(
                                                    "� Contas",
                                                    href="/contas",
                                                    active="exact",
                                                ),
                                                dbc.NavLink(
                                                    "�📁 Categorias",
                                                    href="/categorias",
                                                    active="exact",
                                                ),
                                            ],
                                            vertical=True,
                                            pills=True,
                                            className="mb-4",
                                        ),
                                        # Divisor
                                        html.Hr(),
                                        # Filtros Globais (Footer da Sidebar)
                                        html.P(
                                            "Horizonte Temporal",
                                            className="fw-bold text-muted small",
                                        ),
                                        dbc.Label(
                                            "Meses Passados:",
                                            html_for="select-past",
                                            className="small mb-2",
                                        ),
                                        dcc.Dropdown(
                                            id="select-past",
                                            options=[
                                                {"label": "Nenhum", "value": 0},
                                                {"label": "1 mês", "value": 1},
                                                {"label": "3 meses", "value": 3},
                                                {"label": "6 meses", "value": 6},
                                                {"label": "12 meses", "value": 12},
                                            ],
                                            value=3,
                                            className="mb-3",
                                        ),
                                        dbc.Label(
                                            "Meses Futuros:",
                                            html_for="select-future",
                                            className="small mb-2",
                                        ),
                                        dcc.Dropdown(
                                            id="select-future",
                                            options=[
                                                {"label": "Nenhum", "value": 0},
                                                {"label": "1 mês", "value": 1},
                                                {"label": "3 meses", "value": 3},
                                                {"label": "6 meses", "value": 6},
                                                {"label": "12 meses", "value": 12},
                                            ],
                                            value=6,
                                        ),
                                    ],
                                    className="p-3",
                                    style={
                                        "backgroundColor": "#f8f9fa",
                                        "borderRadius": "0.25rem",
                                        "height": "100vh",
                                        "overflowY": "auto",
                                        "position": "sticky",
                                        "top": 0,
                                    },
                                )
                            ],
                            width=2,
                            className="border-end",
                        ),
                        # ===== ÁREA DE CONTEÚDO (Coluna 2) =====
                        dbc.Col(
                            [
                                html.Div(
                                    id="page-content",
                                    className="p-4",
                                )
                            ],
                            width=10,
                        ),
                    ],
                    className="g-0",
                    style={"minHeight": "100vh"},
                )
            ],
            fluid=True,
            className="p-0",
        ),
        # ===== MODALS E STORES =====
        render_transaction_modal(is_open=False),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    html.H5(id="modal-categoria-titulo", className="fw-bold")
                ),
                dbc.ModalBody(html.Div(id="conteudo-modal-detalhes")),
            ],
            id="modal-detalhes-categoria",
            size="xl",
            centered=True,
            style={"maxWidth": "95vw"},
        ),
        dcc.Store(
            id="store-data-atual",
            data={"ano": date.today().year, "mes": date.today().month},
        ),
        dcc.Store(
            id="store-transacao-salva",
            data=0,
        ),
        dcc.Store(
            id="store-categorias-atualizadas",
            data=0,
        ),
        html.Div(id="dummy-output", style={"display": "none"}),
    ],
    style={"margin": 0, "padding": 0},
)


# ===== FUNÇÕES DE RENDERIZAÇÃO DE PÁGINAS =====


def render_dashboard_page(months_past: int, months_future: int) -> dbc.Container:
    """
    Renderiza a página do Dashboard com resumo financeiro, gráficos e fluxo de caixa.

    Exibe:
    - Cards de resumo (Total Receitas, Despesas, Saldo)
    - Gráficos: Evolução financeira (barras + linha) e Top 5 despesas (rosca)
    - Tabela de Fluxo de Caixa detalhada

    Args:
        months_past: Número de meses passados para análise.
        months_future: Número de meses futuros para análise.

    Returns:
        Componente do Dash com o dashboard renderizado.
    """
    logger.info(
        f"📊 Renderizando Dashboard: {months_past} meses passados, "
        f"{months_future} meses futuros"
    )

    try:
        # Buscar dados de fluxo de caixa
        fluxo_data = get_cash_flow_data(
            months_past=months_past, months_future=months_future
        )

        # Buscar dados para matriz (gráfico de evolução)
        matriz_data = get_category_matrix_data(
            months_past=months_past, months_future=months_future
        )

        # Buscar transações para gráfico de despesas do mês
        transacoes = get_transactions()

        # Buscar despesas do mês atual para gráfico de rosca
        mes_atual = datetime.now()
        primeiro_dia_mes = date(mes_atual.year, mes_atual.month, 1)
        if mes_atual.month == 12:
            ultimo_dia_mes = date(mes_atual.year + 1, 1, 1) - relativedelta(days=1)
        else:
            ultimo_dia_mes = date(
                mes_atual.year, mes_atual.month + 1, 1
            ) - relativedelta(days=1)

        transacoes_mes_atual = get_transactions(
            start_date=primeiro_dia_mes, end_date=ultimo_dia_mes
        )
        despesas_mes_atual = [
            t for t in transacoes_mes_atual if t.get("tipo") == "despesa"
        ]

        logger.info("✓ Dashboard Multi-Contas renderizado com sucesso")

        # Renderizar novos cards do Dashboard Multi-Contas
        dashboard_cards = render_dashboard_cards()

        return dbc.Container(
            [
                # Cards de Resumo Multi-Contas (Disponível, Faturas, Investimentos, Patrimônio, Detalhe por Conta)
                dashboard_cards,
                html.Hr(className="my-4"),
                # Gráficos (Evolução + Top Despesas)
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        render_evolution_chart(matriz_data),
                                        className="p-3",
                                    )
                                ],
                                className="shadow-sm",
                            ),
                            md=8,
                            className="mb-3",
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        render_top_expenses_chart(despesas_mes_atual),
                                        className="p-3",
                                    )
                                ],
                                className="shadow-sm",
                            ),
                            md=4,
                            className="mb-3",
                        ),
                    ],
                    className="mb-4",
                ),
                # Fluxo de Caixa
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Fluxo de Caixa", className="mb-0")),
                        dbc.CardBody(
                            [
                                render_cash_flow_table(fluxo_data),
                            ]
                        ),
                    ],
                    className="shadow-sm",
                ),
            ],
            fluid=True,
        )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar dashboard: {e}", exc_info=True)
        return dbc.Alert(
            f"Erro ao carregar dashboard: {str(e)}",
            color="danger",
            className="mt-4",
        )


# ===== CALLBACK: Renderizar conteúdo da página baseado em URL =====


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("store-transacao-salva", "data"),
    Input("store-categorias-atualizadas", "data"),
    Input("select-past", "value"),
    Input("select-future", "value"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def render_page_content(
    pathname: str,
    store_transacao: float,
    store_categorias: float,
    months_past: int,
    months_future: int,
) -> dbc.Container:
    """
    Renderiza o conteúdo dinâmico baseado na URL (pathname).

    Implementa roteamento de cliente que alterna entre 7 páginas:
    - `/` (Dashboard): Resumo financeiro + Fluxo de Caixa
    - `/receitas`: Tabela de receitas
    - `/despesas`: Tabela de despesas
    - `/analise`: Matriz de categorias vs meses
    - `/orcamento`: Matriz de orçamento (realizado vs meta)
    - `/tags`: Matriz de tags/entidades
    - `/categorias`: Gerenciador de categorias

    Atualiza quando:
    - URL muda (pathname)
    - Transações são salvas (via store-transacao-salva)
    - Categorias são modificadas (via store-categorias-atualizadas)
    - Filtros de data mudança (select-past ou select-future)

    Args:
        pathname: Caminho da URL (ex: "/", "/receitas", "/despesas").
        store_transacao: Timestamp da última transação salva (sinal).
        store_categorias: Timestamp da última atualização de categorias (sinal).
        months_past: Número de meses passados para análise.
        months_future: Número de meses futuros para análise.

    Returns:
        Componente do Dash com o conteúdo da página selecionada.
    """
    # Normalizar pathname (remover trailing slash)
    if pathname and pathname != "/":
        pathname = pathname.rstrip("/")

    try:
        logger.info(
            f"📌 Renderizando página: {pathname} (transacao_signal={store_transacao}, cat_signal={store_categorias})"
        )

        if pathname == "/" or pathname == "":
            return render_dashboard_page(months_past, months_future)

        elif pathname == "/receitas":
            logger.info("[RECEITAS] Carregando receitas...")
            try:
                transacoes = get_transactions()
                receitas = [t for t in transacoes if t.get("tipo") == "receita"]
                logger.info(f"✓ {len(receitas)} receitas carregadas")

                return dbc.Container(
                    [
                        html.H2("Receitas", className="mb-4 fw-bold text-success"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5(f"Total: {len(receitas)} transações")
                                ),
                                dbc.CardBody(render_transactions_table(receitas)),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar receitas: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar receitas: {str(e)}",
                    color="danger",
                    className="mt-4",
                )

        elif pathname == "/despesas":
            logger.info("[DESPESAS] Carregando despesas...")
            try:
                # Recuperar apenas despesas reais (excluir "Transferência Interna")
                transacoes = get_transactions(exclude_transfers=True)
                despesas = [t for t in transacoes if t.get("tipo") == "despesa"]
                logger.info(f"✓ {len(despesas)} despesas carregadas")

                return dbc.Container(
                    [
                        html.H2("Despesas", className="mb-4 fw-bold text-danger"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5(f"Total: {len(despesas)} transações")
                                ),
                                dbc.CardBody(render_transactions_table(despesas)),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar despesas: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar despesas: {str(e)}",
                    color="danger",
                    className="mt-4",
                )

        elif pathname == "/analise":
            logger.info("[ANALISE] Carregando matriz analítica...")
            try:
                matriz_data = get_category_matrix_data(
                    months_past=months_past, months_future=months_future
                )
                logger.info("✓ Matriz analítica carregada com sucesso")
                return dbc.Container(
                    [
                        html.H2("Análise Financeira", className="mb-4 fw-bold"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5("Categorias vs Meses - Valores por Período")
                                ),
                                dbc.CardBody(render_category_matrix(matriz_data)),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar matriz analítica: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar matriz analítica: {str(e)}",
                    color="danger",
                    className="mt-4",
                )

        elif pathname == "/orcamento":
            logger.info("[ORCAMENTO] Carregando matriz de orçamento...")
            try:
                matriz_data = get_category_matrix_data(
                    months_past=months_past, months_future=months_future
                )
                logger.info("✓ Matriz de orçamento carregada com sucesso")
                return dbc.Container(
                    [
                        html.H2("Orçamento", className="mb-4 fw-bold text-primary"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5("Realizado vs Meta - Evolução do Orçamento")
                                ),
                                dbc.CardBody(render_budget_matrix(matriz_data)),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(
                    f"✗ Erro ao carregar matriz de orçamento: {e}", exc_info=True
                )
                return dbc.Alert(
                    f"Erro ao carregar matriz de orçamento: {str(e)}",
                    color="danger",
                    className="mt-4",
                )

        elif pathname == "/tags":
            logger.info("[TAGS] Carregando matriz de tags...")
            try:
                matriz_tags_data = get_tag_matrix_data(
                    months_past=months_past, months_future=months_future
                )
                logger.info("✓ Matriz de tags carregada com sucesso")
                return dbc.Container(
                    [
                        html.H2("Tags", className="mb-4 fw-bold"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H5("Saldo por Entidade - Análise Dinâmica")
                                ),
                                dbc.CardBody(render_tag_matrix(matriz_tags_data)),
                            ],
                            className="shadow-sm",
                        ),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar matriz de tags: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar matriz de tags: {str(e)}",
                    color="danger",
                    className="mt-4",
                )

        elif pathname == "/categorias":
            logger.info("[CATEGORIAS] Carregando categorias...")
            try:
                # Carregar categorias separadas por tipo
                receitas = get_categories(tipo="receita")
                despesas = get_categories(tipo="despesa")
                logger.info(
                    f"✓ {len(receitas)} receitas e "
                    f"{len(despesas)} despesas carregadas"
                )

                # Usar componente render_category_manager
                return dbc.Container(
                    [
                        html.H2("Categorias", className="mb-4 fw-bold"),
                        render_category_manager(receitas, despesas),
                    ],
                    fluid=True,
                )

            except Exception as e:
                logger.error(f"✗ Erro ao carregar categorias: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar categorias: {str(e)}",
                    color="danger",
                )

        elif pathname == "/contas":
            logger.info("[CONTAS] Carregando gerenciador de contas...")
            try:
                contas = get_accounts()
                # Converter Conta objects para dicts com emoji
                contas_dict = []
                for c in contas:
                    conta_dict = c.to_dict()
                    # Adicionar emoji baseado no tipo
                    emoji_map = {
                        "conta": "🏦",
                        "cartao": "💳",
                        "investimento": "📈",
                    }
                    conta_dict["emoji"] = emoji_map.get(c.tipo, "💰")
                    contas_dict.append(conta_dict)

                logger.info(f"✓ {len(contas_dict)} contas carregadas")
                return dbc.Container(
                    [
                        html.H2("Contas", className="mb-4 fw-bold"),
                        render_account_manager(contas_dict),
                    ],
                    fluid=True,
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar contas: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar contas: {str(e)}",
                    color="danger",
                )

        elif pathname == "/importar":
            logger.info("[IMPORTADOR] Carregando interface de importação...")
            contas = get_accounts()
            account_options = [
                {
                    "label": f"{conta.emoji if hasattr(conta, 'emoji') else ''} {conta.nome if hasattr(conta, 'nome') else conta.get('nome', '')}",
                    "value": conta.id if hasattr(conta, 'id') else conta.get('id'),
                }
                for conta in contas
            ]
            
            # Get existing tags for tag editor
            try:
                existing_tags = get_unique_tags_list()
            except Exception as e:
                logger.warning(f"[IMPORTADOR] Erro ao buscar tags: {e}")
                existing_tags = []
            
            return render_importer_page(account_options=account_options, existing_tags=existing_tags)

        # ===== ROTA DINÂMICA: Extrato de Conta /contas/<conta_id> =====
        elif re.match(r"^/contas/\d+$", pathname):
            # Extrair conta_id da URL
            match = re.match(r"^/contas/(\d+)$", pathname)
            if match:
                conta_id = int(match.group(1))
                logger.info(f"[EXTRATO] Carregando extrato da conta {conta_id}...")
                try:
                    return render_account_extract(conta_id)
                except Exception as e:
                    logger.error(
                        f"[EXTRATO] Erro ao carregar extrato: {e}", exc_info=True
                    )
                    return dbc.Alert(
                        f"Erro ao carregar extrato: {str(e)}",
                        color="danger",
                    )

        else:
            logger.warning(f"[404] Página desconhecida: {pathname}")
            return dbc.Container(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H2(
                                            "404 - Página Não Encontrada",
                                            className="text-danger mb-4",
                                        ),
                                        html.P(
                                            f"O caminho '{pathname}' não foi encontrado.",
                                            className="text-muted mb-3",
                                        ),
                                        html.P(
                                            "Navegue usando o menu lateral para acessar as páginas disponíveis.",
                                            className="text-muted",
                                        ),
                                        html.Hr(),
                                        dbc.Button(
                                            "Voltar para Dashboard",
                                            href="/",
                                            color="primary",
                                            className="mt-3",
                                        ),
                                    ],
                                    className="text-center",
                                ),
                            ],
                            md=8,
                            className="mx-auto",
                        ),
                        className="mt-5",
                    )
                ],
                fluid=True,
            )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar conteúdo das abas: {e}", exc_info=True)
        return dbc.Alert(
            f"Erro ao carregar conteúdo: {str(e)}",
            color="danger",
        )


# ===== CALLBACKS PARA DRILL-DOWN (CATEGORIAS E TAGS) =====
@app.callback(
    Output("modal-detalhes-categoria", "is_open"),
    Output("modal-categoria-titulo", "children"),
    Output("conteudo-modal-detalhes", "children"),
    Input({"type": "btn-cat-detail", "index": ALL}, "n_clicks"),
    Input({"type": "btn-tag-detail", "index": ALL}, "n_clicks"),
    State("select-past", "value"),
    State("select-future", "value"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def open_category_detail_modal(
    n_clicks_cat_list: List[int],
    n_clicks_tag_list: List[int],
    months_past: int,
    months_future: int,
) -> tuple:
    """
    Abre modal com detalhes de categoria OU tag com transações filtradas.

    Este callback é polimórfico: aceita tanto cliques de categorias quanto de tags.
    Identifica qual botão disparou e renderiza o conteúdo correspondente.

    Quando o usuário clica em uma categoria/tag na Matriz Analítica,
    este callback:
    1. Identifica qual categoria/tag foi clicada
    2. Busca as transações desse filtro no período
    3. Renderiza uma tabela com as transações
    4. Abre o modal

    Args:
        n_clicks_cat_list: Lista de contagens de cliques dos botões de categoria.
        n_clicks_tag_list: Lista de contagens de cliques dos botões de tag.
        months_past: Número de meses passados para filtro.
        months_future: Número de meses futuros para filtro.

    Returns:
        Tuple (is_open, titulo, conteudo) para o modal.
    """
    try:
        # ===== PROTEÇÃO CONTRA DISPAROS FALSOS =====
        if not ctx.triggered:
            print("⚠️ Nenhum trigger detectado (ctx.triggered vazio)")
            raise PreventUpdate

        if not any(n_clicks_cat_list) and not any(n_clicks_tag_list):
            print("⚠️ Nenhum clique detectado (todos os n_clicks são None/0)")
            raise PreventUpdate

        # ===== IDENTIFICAR TIPO DE TRIGGER (CATEGORIA OU TAG) =====
        trigger_id = ctx.triggered[0]["prop_id"]
        trigger_obj = eval(trigger_id.split(".")[0])
        trigger_type = trigger_obj.get("type")
        trigger_index = trigger_obj.get("index")

        is_categoria = trigger_type == "btn-cat-detail"
        is_tag = trigger_type == "btn-tag-detail"

        if is_categoria:
            categoria_id = trigger_index
            print(f"🕵️‍♂️ Drill-down acionado para Categoria ID: {categoria_id}")
            filtro_nome = "categoria"
        elif is_tag:
            tag_name = trigger_index
            print(f"🕵️‍♂️ Drill-down acionado para Tag: {tag_name}")
            filtro_nome = "tag"
        else:
            print(f"❌ Tipo de trigger desconhecido: {trigger_type}")
            raise PreventUpdate

        print(
            f"   Período solicitado: {months_past} meses passados, {months_future} meses futuros"
        )

        # ===== CALCULAR DATAS (SINCRONIZADO COM get_cash_flow_data) =====
        hoje = date.today()
        # Primeiro dia do mês X meses atrás
        start_date = (hoje - relativedelta(months=months_past)).replace(day=1)
        # Último dia do mês X meses adiante
        end_date = (
            (hoje + relativedelta(months=months_future)).replace(day=1)
            + relativedelta(months=1)
            - relativedelta(days=1)
        )

        print(f"📅 Período Modal: {start_date} até {end_date}")

        # ===== BUSCAR TODAS AS TRANSAÇÕES DO PERÍODO =====
        print(f"📊 Buscando no DB de {start_date} até {end_date}")
        todas_transacoes = get_transactions(
            start_date=start_date,
            end_date=end_date,
        )
        print(f"📦 Total bruto encontrado no período: {len(todas_transacoes)}")

        # Mostrar exemplo da primeira transação se houver
        if todas_transacoes:
            print(f"🔍 Exemplo de transação: {todas_transacoes[0]}")

        # ===== FILTRAR POR CATEGORIA OU TAG EM PYTHON =====
        transacoes_encontradas: List[Dict[str, Any]] = []

        if is_categoria:
            # Filtrar por categoria
            cat_id_int: int
            try:
                cat_id_int = int(categoria_id)
            except (ValueError, TypeError):
                print(f"❌ Erro ao converter categoria_id para int: {categoria_id}")
                raise PreventUpdate

            for t in todas_transacoes:
                # Extrair ID da categoria da estrutura aninhada
                cat_data = t.get("categoria") or {}  # Garante que é dict
                t_cat_id = cat_data.get("id")

                # Fallback: Se não achar no aninhado, tenta na raiz (compatibilidade)
                if t_cat_id is None:
                    t_cat_id = t.get("categoria_id")

                # Comparar IDs com segurança de tipo
                try:
                    if t_cat_id is not None and int(t_cat_id) == cat_id_int:
                        transacoes_encontradas.append(t)
                except (ValueError, TypeError):
                    pass

        elif is_tag:
            # Filtrar por tag com busca parcial (contém)
            # Suporta tags simples ("Mãe") e multi-tag ("Mãe,Saúde")
            for t in todas_transacoes:
                tag_str = t.get("tag") or ""
                # Split por vírgula para suportar CSV
                tags_transacao = [
                    tag.strip() for tag in tag_str.split(",") if tag.strip()
                ]
                # Verifica se a tag procurada está na lista
                if tag_name in tags_transacao:
                    transacoes_encontradas.append(t)

        print(
            f"🎯 Filtrado para {filtro_nome} '{categoria_id if is_categoria else tag_name}': "
            f"{len(transacoes_encontradas)} encontrados."
        )

        # ===== BUSCAR NOME/LABEL DO FILTRO =====
        if is_categoria:
            # Buscar categoria no banco
            categorias = get_categories()
            categoria = next(
                (c for c in categorias if c.get("id") == categoria_id), None
            )

            if not categoria:
                print(f"❌ Categoria ID {categoria_id} não encontrada no banco")
                raise PreventUpdate

            categoria_nome = categoria.get("nome", "Desconhecida")
            categoria_icon = categoria.get("icone", "📊")

            print(f"✅ Categoria encontrada: {categoria_icon} {categoria_nome}")
            titulo_label = f"{categoria_icon} {categoria_nome}"

        elif is_tag:
            print(f"✅ Tag encontrada: {tag_name}")
            titulo_label = f"🏷️ {tag_name}"

        # ===== RENDERIZAR CONTEÚDO DO MODAL =====
        if not transacoes_encontradas:
            print(f"ℹ️  Nenhuma transação para {titulo_label} no período")
            tabela_conteudo = dbc.Alert(
                f"Nenhuma transação encontrada para {titulo_label} "
                f"no período de {start_date.strftime('%d/%m/%Y')} "
                f"até {end_date.strftime('%d/%m/%Y')}.",
                color="info",
            )
        else:
            # ===== GERAR LISTA DE MESES PARA PIVOT TABLE =====
            meses_headers: List[str] = []
            data_atual = start_date.replace(day=1)
            while data_atual <= end_date:
                mes_str = data_atual.strftime("%Y-%m")
                meses_headers.append(mes_str)
                data_atual = data_atual + relativedelta(months=1)

            # ===== CONSTRUIR EXTRATO (Descrição x Mês com Saldos) =====
            # dados_matrix[row_key][mês] = valor (com sinal: receita positiva, despesa negativa)
            dados_matrix: Dict[str, Dict[str, float]] = defaultdict(
                lambda: defaultdict(float)
            )
            totais_por_mes: Dict[str, float] = defaultdict(float)

            for transacao in transacoes_encontradas:
                # Extrair data em formato YYYY-MM
                raw_date = transacao.get("data")
                mes_key = None

                if isinstance(raw_date, str):
                    try:
                        # String ISO: YYYY-MM-DD
                        mes_key = raw_date[:7]  # Pega YYYY-MM
                    except Exception:
                        pass
                elif hasattr(raw_date, "strftime"):
                    # Objeto datetime.date ou datetime.datetime
                    mes_key = raw_date.strftime("%Y-%m")

                if mes_key is None:
                    continue  # Pula se não conseguir extrair mês

                # Limpar descrição removendo sufixos de recorrência e parcelamento
                descricao = transacao.get("descricao", "")
                # Remove: "(Recorrência #1)", "(1/10)", "1/10" e espaços sobrando
                desc_limpa = re.sub(
                    r"\s*(\(Recorrência #\d+\)|\(\d+/\d+\)|\d+/\d+)", "", descricao
                ).strip()

                # Extrair valor e tipo
                valor = transacao.get("valor", 0.0)
                tipo = transacao.get("tipo", "")

                # Aplicar sinal: despesa negativa, receita positiva
                valor_com_sinal = valor if tipo == "receita" else -valor

                # Criar chave de linha: descrição com tipo (para separar receita/despesa)
                row_key = f"{desc_limpa} ({tipo})"

                # Agregar na matriz e totais
                dados_matrix[row_key][mes_key] += valor_com_sinal
                totais_por_mes[mes_key] += valor_com_sinal

            # ===== CONSTRUIR CABEÇALHO DA TABELA =====
            header_cells = [html.Th("Descrição", className="text-nowrap fw-bold")]
            for mes in meses_headers:
                mes_formatado = f"{mes[5:7]}/{mes[-2:]}"  # MM/YY
                header_cells.append(
                    html.Th(
                        mes_formatado,
                        className="text-center text-nowrap fw-bold",
                        style={"minWidth": "70px"},
                    )
                )

            cabecalho = html.Thead(html.Tr(header_cells, className="table-light"))

            # ===== CONSTRUIR CORPO DA TABELA (Extrato) =====
            linhas = []
            for row_key in sorted(dados_matrix.keys()):
                valores_por_mes = dados_matrix[row_key]

                # Determinar cor baseada no valor (positivo=verde, negativo=vermelho)
                def get_cor_valor(val: float) -> str:
                    if val > 0:
                        return "text-success"
                    elif val < 0:
                        return "text-danger"
                    else:
                        return "text-muted"

                # Célula de descrição
                desc_cell = html.Td(
                    row_key,
                    className="fw-bold",
                    style={"minWidth": "150px"},
                )

                # Células de valores por mês
                valor_cells = []
                for mes in meses_headers:
                    valor = valores_por_mes.get(mes, 0.0)

                    if valor == 0.0:
                        # Sem valor neste mês
                        valor_cells.append(
                            html.Td(
                                "-",
                                className="text-center text-muted",
                                style={"minWidth": "70px"},
                            )
                        )
                    else:
                        # Com valor: formatar em R$ (com sinal)
                        sinal = "-" if valor < 0 else ""
                        valor_abs = abs(valor)
                        valor_fmt = (
                            f"{sinal}R$ {valor_abs:,.2f}".replace(",", "X")
                            .replace(".", ",")
                            .replace("X", ".")
                        )
                        cor_texto = get_cor_valor(valor)
                        valor_cells.append(
                            html.Td(
                                valor_fmt,
                                className=f"text-end text-nowrap fw-bold {cor_texto}",
                                style={"minWidth": "70px"},
                            )
                        )

                linhas.append(
                    html.Tr(
                        [desc_cell] + valor_cells,
                        className="table-light",
                    )
                )

            # ===== ADICIONAR LINHA DE SALDO =====
            saldo_cells = [
                html.Td(
                    "=== SALDO ===",
                    className="fw-bold text-nowrap",
                    style={"minWidth": "150px"},
                )
            ]

            for mes in meses_headers:
                saldo_mes = totais_por_mes.get(mes, 0.0)

                if saldo_mes == 0.0:
                    saldo_fmt = "-"
                    cor_saldo = "text-muted"
                else:
                    sinal = "-" if saldo_mes < 0 else ""
                    saldo_abs = abs(saldo_mes)
                    saldo_fmt = (
                        f"{sinal}R$ {saldo_abs:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                    cor_saldo = "text-success" if saldo_mes > 0 else "text-danger"

                saldo_cells.append(
                    html.Td(
                        saldo_fmt,
                        className=f"text-end text-nowrap fw-bold {cor_saldo}",
                        style={"minWidth": "70px"},
                    )
                )

            # Linha de saldo com destaque
            linhas.append(
                html.Tr(
                    saldo_cells,
                    className="table-active fw-bold border-top border-3",
                )
            )

            corpo = html.Tbody(linhas)
            tabela_conteudo = dbc.Table(
                [cabecalho, corpo],
                bordered=True,
                hover=True,
                responsive=True,
                size="sm",
                className="mb-0 table-striped",
                style={"overflowX": "auto", "minWidth": "1000px"},
            )

        # Título do modal
        titulo = html.Span(titulo_label)

        print(
            f"✅ Modal renderizado com sucesso ({len(transacoes_encontradas)} transações)"
        )

        return True, titulo, tabela_conteudo

    except PreventUpdate:
        raise
    except Exception as e:
        erro_traceback = traceback.format_exc()
        print(f"❌ ERRO ao abrir detalhes:")
        print(erro_traceback)
        logger.error(f"Erro ao abrir detalhes: {e}", exc_info=True)
        return (
            True,
            "❌ Erro",
            dbc.Alert(
                f"Erro ao carregar detalhes: {str(e)}\n\nVerifique o console para mais informações.",
                color="danger",
            ),
        )


# ===== CALLBACKS PARA EMOJI PICKER (RECEITA) =====
@app.callback(
    Output("popover-icon-receita", "is_open"),
    Output("btn-icon-receita", "children"),
    Output("radio-icon-receita", "options"),
    Input("btn-icon-receita", "n_clicks"),
    Input("radio-icon-receita", "value"),
    State("popover-icon-receita", "is_open"),
    State("btn-icon-receita", "children"),
    prevent_initial_call=True,
)
def toggle_emoji_picker_receita(
    n_clicks_btn: Optional[int],
    radio_value: Optional[str],
    is_open: bool,
    btn_icon_current: str,
) -> tuple:
    """
    Gerencia abertura/fechamento e filtro dinamico do Popover de icones (Receita).

    Logica Hibrida:
    - Clique no botao: Deixa o navegador (legacy) gerenciar abertura/fechamento.
      Retorna no_update para is_open. Python gerencia apenas o filtro de opcoes.
    - Selecao de icone: Força o fechamento (False) e atualiza o botao.

    Args:
        n_clicks_btn: Cliques no botao seletor.
        radio_value: Valor selecionado no RadioItems.
        is_open: Estado atual do popover.
        btn_icon_current: Icone atual exibido no botao.

    Returns:
        Tupla: (is_open, btn_children, radio_options)
    """
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    logger.debug(f"Emoji Picker Receita acionado: {triggered_id}")

    # Cenario 1: Clique no botao
    # Deixa o navegador (legacy) gerenciar abertura/fechamento
    # Python apenas filtra as opcoes de icones
    if triggered_id == "btn-icon-receita":
        # Recuperar icones ja usados e filtrar disponiveis
        icones_usados = get_used_icons("receita")
        opcoes_disponiveis = [
            {"label": e, "value": e} for e in EMOJI_OPTIONS if e not in icones_usados
        ]
        logger.info(
            f"Popover Receita alternado. "
            f"Icones disponiveis: {len(opcoes_disponiveis)}/{len(EMOJI_OPTIONS)}"
        )
        # Retorna no_update para is_open: deixa o navegador controlar
        return (no_update, no_update, opcoes_disponiveis)

    # Cenario 2: Selecao no RadioItems
    # Força o fechamento e atualiza o botao com o novo icone
    elif triggered_id == "radio-icon-receita" and radio_value:
        logger.info(f"Icone selecionado (Receita): {radio_value}")
        # Fecha o popover (False), atualiza o botao, nao atualiza options
        return (False, radio_value, no_update)

    # Cenario 3: Sem trigger valido
    raise PreventUpdate


# ===== CALLBACKS PARA EMOJI PICKER (DESPESA) =====
@app.callback(
    Output("popover-icon-despesa", "is_open"),
    Output("btn-icon-despesa", "children"),
    Output("radio-icon-despesa", "options"),
    Input("btn-icon-despesa", "n_clicks"),
    Input("radio-icon-despesa", "value"),
    State("popover-icon-despesa", "is_open"),
    State("btn-icon-despesa", "children"),
    prevent_initial_call=True,
)
def toggle_emoji_picker_despesa(
    n_clicks_btn: Optional[int],
    radio_value: Optional[str],
    is_open: bool,
    btn_icon_current: str,
) -> tuple:
    """
    Gerencia abertura/fechamento e filtro dinamico do Popover de icones (Despesa).

    Logica Hibrida:
    - Clique no botao: Deixa o navegador (legacy) gerenciar abertura/fechamento.
      Retorna no_update para is_open. Python gerencia apenas o filtro de opcoes.
    - Selecao de icone: Força o fechamento (False) e atualiza o botao.

    Args:
        n_clicks_btn: Cliques no botao seletor.
        radio_value: Valor selecionado no RadioItems.
        is_open: Estado atual do popover.
        btn_icon_current: Icone atual exibido no botao.

    Returns:
        Tupla: (is_open, btn_children, radio_options)
    """
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    logger.debug(f"Emoji Picker Despesa acionado: {triggered_id}")

    # Cenario 1: Clique no botao
    # Deixa o navegador (legacy) gerenciar abertura/fechamento
    # Python apenas filtra as opcoes de icones
    if triggered_id == "btn-icon-despesa":
        # Recuperar icones ja usados e filtrar disponiveis
        icones_usados = get_used_icons("despesa")
        opcoes_disponiveis = [
            {"label": e, "value": e} for e in EMOJI_OPTIONS if e not in icones_usados
        ]
        logger.info(
            f"Popover Despesa alternado. "
            f"Icones disponiveis: {len(opcoes_disponiveis)}/{len(EMOJI_OPTIONS)}"
        )
        # Retorna no_update para is_open: deixa o navegador controlar
        return (no_update, no_update, opcoes_disponiveis)

    # Cenario 2: Selecao no RadioItems
    # Força o fechamento e atualiza o botao com o novo icone
    elif triggered_id == "radio-icon-despesa" and radio_value:
        logger.info(f"Icone selecionado (Despesa): {radio_value}")
        # Fecha o popover (False), atualiza o botao, nao atualiza options
        return (False, radio_value, no_update)

    # Cenario 3: Sem trigger valido
    raise PreventUpdate


@app.callback(
    Output("store-categorias-atualizadas", "data"),
    Output("input-cat-receita", "value"),
    Output("input-cat-despesa", "value"),
    Output("input-cat-meta-receita", "value"),
    Output("input-cat-meta-despesa", "value"),
    Output("radio-icon-receita", "value"),
    Output("radio-icon-despesa", "value"),
    Input("btn-add-cat-receita", "n_clicks"),
    Input("btn-add-cat-despesa", "n_clicks"),
    Input({"type": "btn-delete-category", "index": ALL}, "n_clicks"),
    State("input-cat-receita", "value"),
    State("input-cat-despesa", "value"),
    State("input-cat-meta-receita", "value"),
    State("input-cat-meta-despesa", "value"),
    State("radio-icon-receita", "value"),
    State("radio-icon-despesa", "value"),
    prevent_initial_call=True,
)
def manage_categories(
    n_clicks_add_receita: Optional[int],
    n_clicks_add_despesa: Optional[int],
    n_clicks_delete: List,
    input_receita: str,
    input_despesa: str,
    meta_receita: Optional[float],
    meta_despesa: Optional[float],
    icon_receita: Optional[str],
    icon_despesa: Optional[str],
):
    """
    Gerencia adição e remoção de categorias (apenas banco de dados).

    Não renderiza conteúdo, apenas atualiza o banco e sinaliza via Store.
    O callback render_tab_content escuta o Store e recarrega a aba.

    Identifica qual botão foi clicado usando ctx.triggered_id:
    - Se foi btn-add-cat-receita: adiciona categoria de receita com ícone e meta
    - Se foi btn-add-cat-despesa: adiciona categoria de despesa com ícone e meta
    - Se foi btn-delete-category: remove categoria pelo ID

    Args:
        n_clicks_add_receita: Cliques no botão adicionar receita.
        n_clicks_add_despesa: Cliques no botão adicionar despesa.
        n_clicks_delete: Lista de cliques em botões de exclusão.
        input_receita: Valor do input de receita.
        input_despesa: Valor do input de despesa.
        meta_receita: Meta/orçamento mensal para receita (R$).
        meta_despesa: Meta/orçamento mensal para despesa (R$).
        icon_receita: Ícone selecionado para receita.
        icon_despesa: Ícone selecionado para despesa.

    Returns:
        (timestamp para Store, input_receita limpo, input_despesa limpo,
         meta_receita limpa, meta_despesa limpa, icon_receita limpo,
         icon_despesa limpo)
    """
    # Verificar se realmente há um trigger válido
    if not ctx.triggered or not ctx.triggered_id:
        logger.debug("⏭️  Nenhum trigger - PreventUpdate")
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    triggered_prop = ctx.triggered[0].get("prop_id") if ctx.triggered else None

    # Se foi disparado por um Input que não é um clique, ignorar
    if (
        triggered_prop
        and "n_clicks" not in triggered_prop
        and "index" not in triggered_prop
    ):
        logger.debug(f"⏭️  Não é clique: {triggered_prop} - PreventUpdate")
        raise PreventUpdate

    # Verificações de ID
    if isinstance(triggered_id, dict):
        if triggered_id.get("type") != "btn-delete-category":
            logger.debug(f"⏭️  ID desconhecido: {triggered_id}")
            raise PreventUpdate
    elif triggered_id not in ["btn-add-cat-receita", "btn-add-cat-despesa"]:
        logger.debug(f"⏭️  ID desconhecido: {triggered_id}")
        raise PreventUpdate

    try:
        # Ação: Adicionar categoria de receita
        if triggered_id == "btn-add-cat-receita":
            if not input_receita or not input_receita.strip():
                logger.warning("⚠️ Tentativa de adicionar categoria vazia")
                raise PreventUpdate

            if not icon_receita:
                logger.warning("⚠️ Nenhum ícone selecionado para receita")
                raise PreventUpdate

            # Validar e converter meta
            meta_valor = 0.0
            if meta_receita is not None:
                try:
                    meta_valor = float(meta_receita)
                    if meta_valor < 0:
                        meta_valor = 0.0
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Meta inválida: {meta_receita}, usando 0.0")
                    meta_valor = 0.0

            logger.info(
                f"➕ Adicionando categoria de receita: {input_receita} "
                f"(ícone: {icon_receita}, meta: R$ {meta_valor:.2f})"
            )
            success, msg = create_category(
                input_receita,
                tipo="receita",
                icone=icon_receita,
                teto_mensal=meta_valor,
            )

            if not success:
                logger.warning(f"⚠️ Erro ao adicionar receita: {msg}")
                raise PreventUpdate

            logger.info(f"✅ Categoria de receita criada: {msg}")

        # Ação: Adicionar categoria de despesa
        elif triggered_id == "btn-add-cat-despesa":
            if not input_despesa or not input_despesa.strip():
                logger.warning("⚠️ Tentativa de adicionar categoria vazia")
                raise PreventUpdate

            if not icon_despesa:
                logger.warning("⚠️ Nenhum ícone selecionado para despesa")
                raise PreventUpdate

            # Validar e converter meta
            meta_valor = 0.0
            if meta_despesa is not None:
                try:
                    meta_valor = float(meta_despesa)
                    if meta_valor < 0:
                        meta_valor = 0.0
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ Meta inválida: {meta_despesa}, usando 0.0")
                    meta_valor = 0.0

            logger.info(
                f"➕ Adicionando categoria de despesa: {input_despesa} "
                f"(ícone: {icon_despesa}, meta: R$ {meta_valor:.2f})"
            )
            success, msg = create_category(
                input_despesa,
                tipo="despesa",
                icone=icon_despesa,
                teto_mensal=meta_valor,
            )

            if not success:
                logger.warning(f"⚠️ Erro ao adicionar despesa: {msg}")
                raise PreventUpdate

            logger.info(f"✅ Categoria de despesa criada: {msg}")

        # Ação: Remover categoria
        elif (
            isinstance(triggered_id, dict)
            and triggered_id.get("type") == "btn-delete-category"
        ):
            category_id = triggered_id.get("index")
            logger.info(f"🗑️  Removendo categoria ID: {category_id}")
            success, msg = delete_category(category_id)
            logger.info(f"✓ Resultado: {msg}")

        # Retornar: (timestamp para Store, inputs/dropdowns limpos)
        return (
            time.time(),  # Sinaliza que houve mudança
            "",  # Limpar input-cat-receita
            "",  # Limpar input-cat-despesa
            None,  # Limpar input-cat-meta-receita
            None,  # Limpar input-cat-meta-despesa
            None,  # Limpar radio-icon-receita
            None,  # Limpar radio-icon-despesa
        )

    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"✗ Erro ao gerenciar categorias: {e}", exc_info=True)
        raise PreventUpdate
        # Retornar: (alerta_erro, input_receita, input_despesa, icon_receita, icon_despesa)
        return (
            dbc.Alert(
                f"Erro ao gerenciar categorias: {str(e)}",
                color="danger",
            ),
            "",  # Limpar input
            "",  # Limpar input
            None,  # Limpar icon
            None,  # Limpar icon
        )


@app.callback(
    Output("dcc-receita-categoria", "options"),
    Output("dcc-despesa-categoria", "options"),
    Input("modal-transacao", "is_open"),
    Input("store-transacao-salva", "data"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def update_category_dropdowns(modal_is_open: bool, store_data: float):
    """
    Atualiza as opções dos dropdowns de categorias no modal.

    Carrega categorias do banco toda vez que o modal abre ou
    uma transação é salva (sinalizando possível nova categoria).

    Args:
        modal_is_open: Se o modal está aberto.
        store_data: Timestamp da última transação salva (sinal).

    Returns:
        Tuple (opcoes_receita, opcoes_despesa).
    """
    logger.debug(
        f"🔄 Atualizando dropdowns de categorias (modal_open={modal_is_open}, signal={store_data})"
    )

    try:
        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        # Construir label com ícone + nome (sem espaços extras se não houver ícone)
        opcoes_receita = [
            {
                "label": f"{cat.get('icone', '')} {cat.get('nome')}".strip(),
                "value": cat.get("id"),
            }
            for cat in receitas
        ]
        opcoes_despesa = [
            {
                "label": f"{cat.get('icone', '')} {cat.get('nome')}".strip(),
                "value": cat.get("id"),
            }
            for cat in despesas
        ]

        logger.debug(
            f"✓ Dropdowns atualizados: {len(opcoes_receita)} receitas, {len(opcoes_despesa)} despesas"
        )
        return opcoes_receita, opcoes_despesa

    except Exception as e:
        logger.error(f"✗ Erro ao atualizar dropdowns: {e}", exc_info=True)
        return [], []


@app.callback(
    Output("dropdown-receita-tag", "options"),
    Output("dropdown-despesa-tag", "options"),
    Input("modal-transacao", "is_open"),
    Input("store-transacao-salva", "data"),
    Input("dropdown-receita-tag", "search_value"),
    Input("dropdown-despesa-tag", "search_value"),
    Input("dropdown-receita-tag", "value"),
    Input("dropdown-despesa-tag", "value"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def update_tag_dropdowns(
    modal_is_open: bool,
    store_data: float,
    search_value_receita: Optional[str],
    search_value_despesa: Optional[str],
    current_value_receita: Optional[list],
    current_value_despesa: Optional[list],
):
    """
    Atualiza as opções dos dropdowns de tags no modal (com suporte a multi=True).

    Carrega tags únicas do banco (desagrupando tags CSV) e permite criação
    dinâmica de novas tags. Persiste valores selecionados (mesmo que ainda não
    estejam no banco) para evitar que tags recém-criadas desapareçam.

    Suporta seleção múltipla: current_value_* agora é uma lista (ou None).

    Args:
        modal_is_open: Se o modal está aberto.
        store_data: Timestamp da última transação salva (sinal).
        search_value_receita: Texto digitado no dropdown de receita (creatable).
        search_value_despesa: Texto digitado no dropdown de despesa (creatable).
        current_value_receita: Lista de tags selecionadas em receita (ou None).
        current_value_despesa: Lista de tags selecionadas em despesa (ou None).

    Returns:
        Tuple (opcoes_receita, opcoes_despesa).
    """
    logger.debug(
        f"🔄 Atualizando dropdowns de tags (modal_open={modal_is_open}, signal={store_data})"
    )

    try:
        # Buscar tags já existentes no banco
        tags_db = get_all_tags()

        # Criar lista base de opções
        base_options = [{"label": tag, "value": tag} for tag in tags_db]

        # Função auxiliar para adicionar valores dinamicamente
        def build_options(
            base_opts: List[Dict],
            current_value: Optional[list],
            search_value: Optional[str],
            tags_banco: List[str],
        ) -> List[Dict]:
            """
            Constrói lista de opções, adicionando valores dinamicamente criados.

            Suporta seleção múltipla: current_value é uma lista de tags selecionadas.

            Args:
                base_opts: Lista base de opções do banco.
                current_value: Lista de tags atualmente selecionadas (ou None).
                search_value: Texto digitado pelo usuário.
                tags_banco: Tags existentes no banco (desagrupadas).

            Returns:
                Lista de opções com valores dinâmicos inclusos.
            """
            options = base_opts.copy()
            values_to_check: set[str] = set()

            # Adicionar valores atuais selecionados se existirem
            # (multi=True retorna uma lista)
            if current_value and isinstance(current_value, list):
                for valor in current_value:
                    if valor and valor.strip() and valor not in tags_banco:
                        values_to_check.add(valor.strip())

            # Adicionar valor digitado se existir
            if search_value and search_value.strip() and search_value not in tags_banco:
                values_to_check.add(search_value.strip())

            # Adicionar valores únicos às opções
            for value in values_to_check:
                if not any(opt["value"] == value for opt in options):
                    options.append({"label": value, "value": value})
                    logger.debug(f"✏️ Tag adicionada dinamicamente: {value}")

            return options

        # Opções para Receita
        options_receita = build_options(
            base_options, current_value_receita, search_value_receita, tags_db
        )

        # Opções para Despesa
        options_despesa = build_options(
            base_options, current_value_despesa, search_value_despesa, tags_db
        )

        logger.debug(
            f"✓ Dropdowns de tags atualizados: {len(base_options)} base + dinâmicas"
        )
        return options_receita, options_despesa

    except Exception as e:
        logger.error(f"✗ Erro ao atualizar dropdowns de tags: {e}", exc_info=True)
        return [], []


@app.callback(
    Output("alerta-modal", "is_open"),
    Output("alerta-modal", "children"),
    Output("modal-transacao", "is_open", allow_duplicate=True),
    Output("store-transacao-salva", "data"),
    Output("input-receita-descricao", "value"),
    Output("input-receita-valor", "value"),
    Output("dropdown-receita-tag", "value"),
    Output("dcc-receita-categoria", "value"),
    Input("btn-salvar-receita", "n_clicks"),
    State("input-receita-valor", "value"),
    State("input-receita-descricao", "value"),
    State("dcc-receita-data", "date"),
    State("dcc-receita-categoria", "value"),
    State("dropdown-receita-tag", "value"),
    State("check-receita-recorrente", "value"),
    State("select-receita-frequencia", "value"),
    State("select-receita-conta", "value"),
    State("modal-transacao", "is_open"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def save_receita(
    n_clicks: int,
    valor: float,
    descricao: str,
    data: str,
    categoria_id: int,
    tag: Optional[list],
    is_recorrente: List,
    frequencia_recorrencia: str,
    conta_id: int,
    modal_is_open: bool,
):
    """
    Salva uma nova receita no banco de dados.

    Suporta recorrência e associação a tags múltiplas. Atualiza store-transacao-salva
    ao salvar com sucesso, sinalizando a atualização dos componentes dependentes
    (Fluxo de Caixa, Abas).

    Args:
        n_clicks: Número de cliques no botão.
        valor: Valor da receita.
        descricao: Descrição da receita.
        data: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        tag: Tags opcionais para entidade/agrupamento (ex: ['Mãe', 'Saúde']).
             Pode ser uma lista (multi=True) ou None. Será salvo como CSV se houver múltiplas.
        is_recorrente: Lista com valor 1 se recorrente, vazia se não.
        frequencia_recorrencia: Frequência (mensal, quinzenal, semanal).
        conta_id: ID da conta selecionada.
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, timestamp).
    """

    logger.info(f"💾 Salvando receita: {descricao} - R${valor} (conta_id={conta_id})")

    if not all([valor, descricao, data, categoria_id, conta_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios, incluindo a conta!"
        logger.warning(f"⚠️ {msg_erro}")
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return (
            True,
            msg_erro,
            True,
            0,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    try:
        from datetime import datetime

        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        eh_recorrente = len(is_recorrente) > 0 if is_recorrente else False

        success, message = create_transaction(
            tipo="receita",
            descricao=descricao,
            valor=float(valor),
            data=data_obj,
            categoria_id=int(categoria_id),
            conta_id=int(conta_id),
            tag=tag,
            is_recorrente=eh_recorrente,
            frequencia_recorrencia=frequencia_recorrencia if eh_recorrente else None,
        )

        if success:
            logger.info(f"✓ Receita salva com sucesso: {descricao}")
            timestamp = time.time()
            logger.info(f"📡 Sinalizando atualização (timestamp={timestamp})")
            return False, "", False, timestamp, "", None, [], None
        else:
            msg_erro = f"❌ Erro: {message}"
            logger.error(f"✗ {msg_erro}")
            return (
                True,
                msg_erro,
                True,
                0,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return (
            True,
            msg_erro,
            True,
            0,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )


@app.callback(
    Output("alerta-modal", "is_open", allow_duplicate=True),
    Output("alerta-modal", "children", allow_duplicate=True),
    Output("modal-transacao", "is_open", allow_duplicate=True),
    Output("store-transacao-salva", "data", allow_duplicate=True),
    Output("input-despesa-descricao", "value"),
    Output("input-despesa-valor", "value"),
    Output("dropdown-despesa-tag", "value"),
    Output("dcc-despesa-categoria", "value"),
    Input("btn-salvar-despesa", "n_clicks"),
    State("input-despesa-valor", "value"),
    State("input-despesa-descricao", "value"),
    State("dcc-despesa-data", "date"),
    State("dcc-despesa-categoria", "value"),
    State("input-despesa-parcelas", "value"),
    State("dropdown-despesa-tag", "value"),
    State("check-despesa-recorrente", "value"),
    State("select-despesa-frequencia", "value"),
    State("select-despesa-conta", "value"),
    State("modal-transacao", "is_open"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def save_despesa(
    n_clicks: int,
    valor: float,
    descricao: str,
    data: str,
    categoria_id: int,
    numero_parcelas: int,
    tag: Optional[list],
    is_recorrente: List,
    frequencia_recorrencia: str,
    conta_id: int,
    modal_is_open: bool,
):
    """
    Salva uma nova despesa no banco de dados.

    Suporta parcelamento, recorrência e associação a tags múltiplas.
    Atualiza store-transacao-salva ao salvar com sucesso, sinalizando
    a atualização dos componentes dependentes (Fluxo de Caixa, Abas).

    Args:
        n_clicks: Número de cliques no botão.
        valor: Valor da despesa.
        descricao: Descrição da despesa.
        data: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        numero_parcelas: Número de parcelas (default 1).
        tag: Tags opcionais para entidade/agrupamento (ex: ['Mãe', 'Saúde']).
             Pode ser uma lista (multi=True) ou None. Será salvo como CSV se houver múltiplas.
        is_recorrente: Lista com valor 1 se recorrente, vazia se não.
        frequencia_recorrencia: Frequência (mensal, quinzenal, semanal).
        conta_id: ID da conta selecionada.
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, timestamp).
    """

    logger.info(f"💾 Salvando despesa: {descricao} - R${valor} (conta_id={conta_id})")

    if not all([valor, descricao, data, categoria_id, conta_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios, incluindo a conta!"
        logger.warning(f"⚠️ {msg_erro}")
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return (
            True,
            msg_erro,
            True,
            0,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    try:
        from datetime import datetime

        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        eh_recorrente = len(is_recorrente) > 0 if is_recorrente else False
        num_parcelas = (
            int(numero_parcelas) if numero_parcelas and numero_parcelas > 0 else 1
        )

        # Deduzir forma de pagamento baseado no tipo de conta
        contas = get_accounts()
        conta_selecionada = None
        for c in contas:
            c_id = c.id if hasattr(c, 'id') else c.get('id')
            if c_id == conta_id:
                conta_selecionada = c
                break
        
        if not conta_selecionada:
            msg_erro = "❌ Conta selecionada não encontrada."
            logger.error(f"✗ {msg_erro}")
            return (
                True,
                msg_erro,
                True,
                0,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )
        
        tipo_conta = conta_selecionada.tipo if hasattr(conta_selecionada, 'tipo') else conta_selecionada.get('tipo')
        
        # Deduzir forma de pagamento
        if tipo_conta == 'cartao':
            forma_pagamento = 'credito'
            # Para crédito, usar parcelas selecionadas
            num_parcelas = int(numero_parcelas) if numero_parcelas and numero_parcelas > 0 else 1
            logger.info(f"[DESPESA] Forma de pagamento deducida: Crédito ({num_parcelas}x)")
        else:
            forma_pagamento = 'debito'
            # Para débito/à vista, forçar 1 parcela
            num_parcelas = 1
            logger.info(f"[DESPESA] Forma de pagamento deducida: Débito (1x)")

        success, message = create_transaction(
            tipo="despesa",
            descricao=descricao,
            valor=float(valor),
            data=data_obj,
            categoria_id=int(categoria_id),
            conta_id=int(conta_id),
            forma_pagamento=forma_pagamento,
            numero_parcelas=num_parcelas,
            tag=tag,
            is_recorrente=eh_recorrente,
            frequencia_recorrencia=frequencia_recorrencia if eh_recorrente else None,
        )

        if success:
            logger.info(f"✓ Despesa salva com sucesso: {descricao}")
            timestamp = time.time()
            logger.info(f"📡 Sinalizando atualização (timestamp={timestamp})")
            return False, "", False, timestamp, "", None, [], None
        else:
            msg_erro = f"❌ Erro: {message}"
            logger.error(f"✗ {msg_erro}")
            return (
                True,
                msg_erro,
                True,
                0,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return (
            True,
            msg_erro,
            True,
            0,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )


@app.callback(
    Output("dashboard-container", "children"),
    Input("store-transacao-salva", "data"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def update_dashboard_cards(store_data: float):
    """
    Atualiza cards do dashboard ao salvar transações.

    Recalcula totais de receitas, despesas e saldo consultando
    o banco de dados atualizado. Acionado pelo store-transacao-salva
    para garantir serialização.

    Args:
        store_data: Timestamp da última transação salva.

    Returns:
        dbc.Row com os cards de resumo atualizados.
    """
    logger.info(f"🔄 Atualizando cards do dashboard (signal={store_data})...")
    cards = render_summary_cards()
    logger.info("✓ Cards atualizados com sucesso")
    return cards


@app.callback(
    Output("modal-transacao", "is_open"),
    Output("tabs-modal-transacao", "value"),
    Input("btn-nova-receita", "n_clicks"),
    Input("btn-nova-despesa", "n_clicks"),
    State("modal-transacao", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal_open(
    n_clicks_receita: int, n_clicks_despesa: int, is_open: bool
) -> tuple:
    """
    Abre o modal ao clicar em "+ Receita" ou "+ Despesa".

    Identifica qual botão disparou o callback usando dash.ctx
    e abre o modal na aba correta.

    Args:
        n_clicks_receita: Cliques no botão "+ Receita".
        n_clicks_despesa: Cliques no botão "+ Despesa".
        is_open: Estado atual do modal.

    Returns:
        Tuple (novo_estado_modal, aba_ativa).
    """
    from dash import ctx

    if not ctx.triggered:
        return False, "tab-despesa"

    botao_disparado = ctx.triggered[0]["prop_id"].split(".")[0]
    logger.info(f"🔘 Abrindo modal via botão: {botao_disparado}")

    if botao_disparado == "btn-nova-receita":
        return True, "tab-receita"
    elif botao_disparado == "btn-nova-despesa":
        return True, "tab-despesa"
    else:
        return not is_open, "tab-despesa"


@app.callback(
    Output("select-despesa-frequencia", "disabled"),
    Input("check-despesa-recorrente", "value"),
    prevent_initial_call=True,
)
def toggle_despesa_frequencia(is_recorrente: List) -> bool:
    """
    Controla ativação do campo de frequência para despesas.

    Ativa o dropdown de frequência apenas quando a recorrência está marcada.

    Args:
        is_recorrente: Lista vazia ou com valor 1 (Checklist switch).

    Returns:
        True para desabilitar, False para habilitar.
    """
    habilitado = len(is_recorrente) > 0 if is_recorrente else False
    if habilitado:
        logger.debug("📅 Habilitando frequência de recorrência (Despesa)")
    else:
        logger.debug("🔒 Desabilitando frequência de recorrência (Despesa)")
    return not habilitado


@app.callback(
    Output("select-receita-frequencia", "disabled"),
    Input("check-receita-recorrente", "value"),
    prevent_initial_call=True,
)
def toggle_receita_frequencia(is_recorrente: List) -> bool:
    """
    Controla ativação do campo de frequência para receitas.

    Ativa o dropdown de frequência apenas quando a recorrência está marcada.

    Args:
        is_recorrente: Lista vazia ou com valor 1 (Checklist switch).

    Returns:
        True para desabilitar, False para habilitar.
    """
    habilitado = len(is_recorrente) > 0 if is_recorrente else False
    if habilitado:
        logger.debug("📅 Habilitando frequência de recorrência (Receita)")
    else:
        logger.debug("🔒 Desabilitando frequência de recorrência (Receita)")
    return not habilitado


# ===== CALLBACKS PARA EDIÇÃO DE CATEGORIAS =====


@app.callback(
    Output("modal-edit-category", "is_open"),
    Output("input-edit-cat-nome", "value"),
    Output("input-edit-cat-meta", "value"),
    Output("btn-icon-edit", "children"),
    Output("radio-icon-edit", "value"),
    Output("store-edit-cat-id", "data"),
    Input({"type": "btn-edit-cat", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_edit_modal(n_clicks_list: List[int]) -> tuple:
    """
    Abre o modal de edição com dados da categoria carregados.

    Args:
        n_clicks_list: Lista de cliques dos botões de editar.

    Returns:
        Tupla: (modal_is_open, nome, meta, icone_btn, icone_value, category_id)
    """
    if not ctx.triggered or not ctx.triggered_id:
        logger.debug("⏭️  Nenhum trigger válido para edição")
        raise PreventUpdate

    triggered_id = ctx.triggered_id

    # Validar se é um padrão-matched button
    if not isinstance(triggered_id, dict) or triggered_id.get("type") != "btn-edit-cat":
        logger.debug(f"⏭️  ID não é btn-edit-cat: {triggered_id}")
        raise PreventUpdate

    category_id = triggered_id.get("index")
    if not category_id:
        logger.warning("⚠️ Nenhum ID de categoria fornecido")
        raise PreventUpdate

    try:
        # Buscar a categoria no banco
        todas_categorias = get_categories()
        categoria = next(
            (c for c in todas_categorias if c.get("id") == category_id), None
        )

        if not categoria:
            logger.warning(f"⚠️ Categoria com ID {category_id} não encontrada")
            raise PreventUpdate

        logger.info(
            f"📝 Abrindo modal de edição: {categoria.get('nome')} (ID: {category_id})"
        )

        return (
            True,  # Abrir modal
            categoria.get("nome", ""),  # Nome
            categoria.get("teto_mensal", 0.0),  # Meta
            categoria.get("icone", "💰"),  # Ícone no botão
            categoria.get("icone", "💰"),  # Ícone selecionado
            category_id,  # ID armazenado no store
        )

    except Exception as e:
        logger.error(f"✗ Erro ao abrir modal de edição: {e}", exc_info=True)
        raise PreventUpdate


@app.callback(
    Output("popover-icon-edit", "is_open"),
    Output("btn-icon-edit", "children", allow_duplicate=True),
    Output("radio-icon-edit", "options"),
    Input("btn-icon-edit", "n_clicks"),
    Input("radio-icon-edit", "value"),
    State("popover-icon-edit", "is_open"),
    State("btn-icon-edit", "children"),
    State("store-edit-cat-id", "data"),
    prevent_initial_call=True,
)
def toggle_edit_icon_picker(
    n_clicks_btn: Optional[int],
    radio_value: Optional[str],
    is_open: bool,
    btn_icon_current: str,
    category_id: Optional[int],
) -> tuple:
    """
    Gerencia abertura/fechamento e filtro dinâmico do Popover de ícones (Edição).

    Mantém o ícone atual da categoria na lista de opções (exceção à regra de unicidade).

    Args:
        n_clicks_btn: Cliques no botão seletor.
        radio_value: Valor selecionado no RadioItems.
        is_open: Estado atual do popover.
        btn_icon_current: Ícone atual exibido no botão.
        category_id: ID da categoria sendo editada (para exclusão).

    Returns:
        Tupla: (is_open, btn_children, radio_options)
    """
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered_id
    logger.debug(f"Emoji Picker Edição acionado: {triggered_id}")

    # Cenário 1: Clique no botão
    # Deixa o navegador gerenciar abertura/fechamento
    # Python filtra as opções de ícones
    if triggered_id == "btn-icon-edit":
        # Recuperar ícones já usados em TODAS as categorias
        todas_categorias = get_categories()
        icones_usados = {c.get("icone") for c in todas_categorias if c.get("icone")}

        # Remover ícone da categoria atual da lista de "não permitidos"
        # (permitindo que mantenha seu próprio ícone)
        if category_id:
            categoria_atual = next(
                (c for c in todas_categorias if c.get("id") == category_id), None
            )
            if categoria_atual and categoria_atual.get("icone"):
                icones_usados.discard(categoria_atual.get("icone"))

        # Ícones disponíveis: todos, menos os já usados
        opcoes_disponiveis = [
            {"label": e, "value": e} for e in EMOJI_OPTIONS if e not in icones_usados
        ]
        logger.info(
            f"Popover Edição alternado. "
            f"Ícones disponíveis: {len(opcoes_disponiveis)}/{len(EMOJI_OPTIONS)}"
        )
        return (no_update, no_update, opcoes_disponiveis)

    # Cenário 2: Seleção no RadioItems
    # Força o fechamento e atualiza o botão
    elif triggered_id == "radio-icon-edit" and radio_value:
        logger.info(f"Ícone selecionado (Edição): {radio_value}")
        return (False, radio_value, no_update)

    raise PreventUpdate


@app.callback(
    Output("modal-edit-category", "is_open", allow_duplicate=True),
    Output("store-edit-cat-id", "data", allow_duplicate=True),
    Output("store-transacao-salva", "data", allow_duplicate=True),
    Input("btn-save-edit-cat", "n_clicks"),
    State("input-edit-cat-nome", "value"),
    State("radio-icon-edit", "value"),
    State("input-edit-cat-meta", "value"),
    State("store-edit-cat-id", "data"),
    prevent_initial_call=True,
)
def save_edit_category(
    n_clicks: Optional[int],
    novo_nome: Optional[str],
    novo_icone: Optional[str],
    novo_teto: Optional[float],
    category_id: Optional[int],
) -> tuple:
    """
    Salva as alterações da categoria no banco de dados.

    Args:
        n_clicks: Cliques no botão salvar.
        novo_nome: Novo nome da categoria.
        novo_icone: Novo ícone da categoria.
        novo_teto: Novo teto/meta mensal.
        category_id: ID da categoria sendo editada.

    Returns:
        Tupla: (modal_is_open, store_id, store_timestamp)
    """
    if not ctx.triggered or not category_id:
        logger.debug("⏭️  Trigger inválido para salvar edição")
        raise PreventUpdate

    if not n_clicks:
        raise PreventUpdate

    try:
        # Validações básicas
        if not novo_nome or not novo_nome.strip():
            logger.warning("⚠️ Nome não pode ser vazio")
            raise PreventUpdate

        if not novo_icone:
            logger.warning("⚠️ Ícone não pode ser vazio")
            raise PreventUpdate

        # Normalizar meta
        meta_valor = 0.0
        if novo_teto is not None:
            try:
                meta_valor = float(novo_teto)
                if meta_valor < 0:
                    meta_valor = 0.0
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Meta inválida: {novo_teto}, usando 0.0")
                meta_valor = 0.0

        logger.info(
            f"💾 Salvando edição de categoria ID {category_id}: "
            f"nome={novo_nome}, ícone={novo_icone}, meta=R$ {meta_valor:.2f}"
        )

        # Chamar update_category
        success, msg = update_category(
            category_id,
            novo_nome=novo_nome.strip(),
            novo_icone=novo_icone,
            novo_teto=meta_valor,
        )

        if not success:
            logger.warning(f"⚠️ Erro ao atualizar categoria: {msg}")
            raise PreventUpdate

        logger.info(f"✅ Categoria atualizada com sucesso: {msg}")

        # Retornar: fechar modal, limpar store, sinalizar atualização
        return (
            False,  # Fechar modal
            None,  # Limpar ID do store
            time.time(),  # Sinalizar mudança (atualiza categorias)
        )

    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(f"✗ Erro ao salvar edição: {e}", exc_info=True)
        raise PreventUpdate


# ===== CALLBACKS DE IMPORTAÇÃO CSV =====


@app.callback(
    Output("preview-container", "children"),
    Output("store-import-data", "data"),
    Output("btn-save-import", "disabled"),
    Output("btn-clear-import", "disabled"),
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def update_import_preview(
    contents: str,
    filename: str,
) -> tuple:
    """Process CSV upload and show preview table.

    Args:
        contents: Base64-encoded file content from dcc.Upload
        filename: Original filename

    Returns:
        Tuple of (preview_table, store_data, btn_disabled, clear_disabled, status_msg)
    """
    if not contents:
        raise PreventUpdate

    try:
        logger.info(f"[IMPORT] Processando upload: {filename}")

        # Extract base64 from Dash format
        content_type, encoded = contents.split(",")

        # Load classification history from database for smart suggestions
        classification_history = get_classification_history()
        logger.info(
            f"[IMPORT] Histórico de classificação carregado: "
            f"{len(classification_history)} entradas"
        )

        # Parse CSV with importer (with historical categorization)
        transactions = parse_upload_content(
            encoded,
            filename,
            classification_history=classification_history,
        )

        if not transactions:
            logger.warning(f"[IMPORT] Arquivo {filename} retornou 0 transações")
            return (
                [],
                None,
                True,
                True,
                html.Div(
                    "Nenhuma transação válida encontrada no arquivo.",
                    className="alert alert-warning",
                ),
            )

        logger.info(
            f"[IMPORT] {len(transactions)} transações parseadas " f"de {filename}"
        )

        # Fetch categories from database for dropdown
        category_options = []
        try:
            # Get categories for both types
            cats_receita = get_categories(tipo="receita")
            cats_despesa = get_categories(tipo="despesa")

            # Combine all categories
            todas_cats = cats_receita + cats_despesa

            # Format for dropdown
            category_options = [
                {
                    "label": cat.get("nome", cat.get("name")),
                    "value": cat.get("nome", cat.get("name")),
                }
                for cat in todas_cats
            ]

            # Ensure "A Classificar" is in the list
            classificar_values = [
                opt["value"]
                for opt in category_options
                if opt["value"] == "A Classificar"
            ]
            if not classificar_values:
                category_options.insert(
                    0, {"label": "A Classificar", "value": "A Classificar"}
                )

            logger.info(
                f"[IMPORT] {len(category_options)} categorias carregadas para dropdown"
            )
        except Exception as e:
            logger.warning(f"[IMPORT] Erro ao buscar categorias: {e}")
            # Fallback: at least have "A Classificar"
            category_options = [{"label": "A Classificar", "value": "A Classificar"}]

        # Get existing tags for dropdown
        try:
            existing_tags = get_unique_tags_list()
            logger.info(
                f"[IMPORT] {len(existing_tags)} tags únicas carregadas para dropdown"
            )
        except Exception as e:
            logger.warning(f"[IMPORT] Erro ao buscar tags: {e}")
            existing_tags = []

        # Render preview table with category and tag options
        preview = render_preview_table(transactions, category_options, existing_tags)

        # Status message
        status_msg = html.Div(
            f"✅ {len(transactions)} transações carregadas de {filename}",
            className="alert alert-success mt-3",
        )

        return (
            preview,
            transactions,
            False,  # Enable save button
            False,  # Enable clear button
            status_msg,
        )

    except ValueError as e:
        logger.error(f"[IMPORT] Erro ao fazer parse de {filename}: {e}")
        return (
            [],
            None,
            True,
            True,
            html.Div(
                f"❌ Erro ao processar arquivo: {str(e)}",
                className="alert alert-danger",
            ),
        )

    except Exception as e:
        logger.error(f"[IMPORT] Erro inesperado em {filename}: {e}", exc_info=True)
        return (
            [],
            None,
            True,
            True,
            html.Div(
                f"❌ Erro inesperado: {str(e)}",
                className="alert alert-danger",
            ),
        )


def _transaction_exists(
    session,
    descricao: str,
    valor: float,
    data_futura: date,
    conta_id: int,
) -> bool:
    """
    Verifica se uma transação futura já existe no banco para evitar duplicatas.

    Busca uma transação com a mesma descrição, valor, data e conta.
    Usado para evitar recriar parcelas futuras em importações repetidas.

    Args:
        session: Sessão SQLAlchemy ativa.
        descricao: Descrição da transação.
        valor: Valor da transação.
        data_futura: Data futura a verificar.
        conta_id: ID da conta.

    Returns:
        True se transação existe, False caso contrário.
    """
    from src.database.models import Transacao
    
    transacao_existe = (
        session.query(Transacao)
        .filter(
            Transacao.descricao == descricao,
            Transacao.valor == valor,
            Transacao.data == data_futura,
            Transacao.conta_id == conta_id,
        )
        .first()
    )
    return transacao_existe is not None


@app.callback(
    Output("import-feedback", "children"),
    Output("store-import-data", "data", allow_duplicate=True),
    Output("preview-container", "children", allow_duplicate=True),
    Output("upload-status", "children", allow_duplicate=True),
    Input("btn-save-import", "n_clicks"),
    State("table-import-preview", "data"),
    State("dropdown-import-conta", "value"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def save_imported_transactions(
    n_clicks: int,
    table_data: List[Dict[str, Any]],
    conta_id_selecionada: Optional[int],
) -> tuple:
    """Save imported transactions to database.

    Processes the edited table data and inserts each transaction
    into the database. If a transaction has installments (parcelas),
    creates future transactions for remaining installments.

    Args:
        n_clicks: Button click count (used to trigger)
        table_data: Edited data from DataTable
        conta_id_selecionada: Selected account ID from dropdown

    Returns:
        Tuple of (feedback_alert, cleared_store, cleared_preview, cleared_status)
    """
    if not table_data:
        logger.warning("[IMPORT] Tentativa de salvar com tabela vazia")
        raise PreventUpdate

    # Validação crítica: verificar se conta foi selecionada
    if conta_id_selecionada is None:
        logger.warning("[IMPORT] Tentativa de salvar sem selecionar conta")
        feedback = dbc.Alert(
            "⚠️ Por favor, selecione a conta de destino antes de confirmar.",
            color="warning",
            className="mt-3",
        )
        return (
            feedback,
            no_update,
            no_update,
            no_update,
        )

    try:
        logger.info(
            f"[IMPORT] Salvando {len(table_data)} transações na conta ID={conta_id_selecionada}..."
        )

        count = 0
        count_parcelas_futuras = 0
        skipped_count = 0
        errors = []

        for idx, row in enumerate(table_data, start=1):
            try:
                # Log detalhado dos dados recebidos (DEBUG DE TAGS)
                logger.info(
                    f"[SAVE] Processando linha {idx}: "
                    f"Desc='{row.get('descricao')}' | "
                    f"Cat='{row.get('categoria')}' | "
                    f"Tags='{row.get('tags')}'"
                )
                
                # Skip rows marked as filtered/disabled
                if row.get("skipped") or row.get("disable_edit"):
                    logger.info(
                        f"[IMPORT] ⊘ Linha {idx} ignorada (marcada como desabilitada)"
                    )
                    continue

                # Parse values from table
                data_str = row.get("data", "").strip()
                descricao = row.get("descricao", "Sem descrição").strip()
                valor_str = row.get("valor", "0").strip()
                tipo_str = row.get("tipo", "").strip()
                categoria_nome = row.get("categoria", "A Classificar").strip()
                tags_str = row.get("tags", "").strip()

                # Parse valor (remove R$ and comma)
                valor = float(valor_str.replace("R$", "").replace(",", ".").strip())

                # Parse tipo (extract from emoji text)
                if "Receita" in tipo_str or "receita" in tipo_str:
                    tipo = "receita"
                elif "Despesa" in tipo_str or "despesa" in tipo_str:
                    tipo = "despesa"
                else:
                    tipo = "despesa"  # Default

                # Parse tags: convert comma-separated string to list
                tags_list = []
                tags_str = row.get('tags')
                if tags_str and isinstance(tags_str, str):
                    tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]

                # Parse date
                data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()

                # Get categoria ID by name
                categoria_id = None
                try:
                    from src.database.connection import get_db
                    from src.database.models import Categoria

                    with get_db() as session:
                        categoria = (
                            session.query(Categoria)
                            .filter_by(nome=categoria_nome)
                            .first()
                        )
                        if categoria:
                            categoria_id = categoria.id
                        else:
                            logger.warning(
                                f"[IMPORT] Categoria '{categoria_nome}' não encontrada. "
                                f"Usando 'A Classificar'."
                            )
                            # Try to find "A Classificar" as fallback
                            categoria_fallback = (
                                session.query(Categoria)
                                .filter_by(nome="A Classificar", tipo=tipo)
                                .first()
                            )
                            if categoria_fallback:
                                categoria_id = categoria_fallback.id
                except Exception as e:
                    logger.error(f"[IMPORT] Erro ao buscar categoria: {e}")
                    categoria_id = None

                if not categoria_id:
                    errors.append(
                        f"Linha {idx}: Categoria '{categoria_nome}' não encontrada."
                    )
                    logger.warning(
                        f"[IMPORT] Erro na linha {idx}: Categoria não encontrada"
                    )
                    continue

                # Use selected conta_id from dropdown
                conta_id = conta_id_selecionada

                # ===== VERIFICAR DUPLICIDADE =====
                # Checar se a transação já existe no banco
                with get_db() as session:
                    if _transaction_exists(session, descricao, valor, data_obj, conta_id):
                        skipped_count += 1
                        logger.info(
                            f"[IMPORT] 🔄 Duplicata ignorada (linha {idx}): "
                            f"{descricao} R$ {valor:.2f} em {data_obj}"
                        )
                        continue

                success, message = create_transaction(
                    data=data_obj,
                    descricao=descricao,
                    valor=valor,
                    tipo=tipo,
                    categoria_id=categoria_id,
                    conta_id=conta_id,
                    tags=tags_str,
                )

                if not success:
                    errors.append(f"Linha {idx}: {message}")
                    logger.warning(f"[IMPORT] Erro na linha {idx}: {message}")
                else:
                    count += 1
                    logger.info(
                        f"[IMPORT] ✓ Transação {idx} salva: "
                        f"{tipo} {descricao} R$ {valor} | "
                        f"Categoria: {categoria_nome} | Tags: {', '.join(tags_list) if tags_list else 'nenhuma'}"
                    )

                    # ===== CRIAR PARCELAS FUTURAS SE HOUVER =====
                    parcela_atual = row.get("parcela_atual")
                    total_parcelas = row.get("total_parcelas")

                    if parcela_atual and total_parcelas:
                        try:
                            parcela_atual = int(parcela_atual)
                            total_parcelas = int(total_parcelas)

                            # Verificar explicitamente se há parcelas futuras a criar
                            if parcela_atual and total_parcelas and parcela_atual < total_parcelas:
                                logger.info(
                                    f"[PARCELAS] 🔄 Processando parcelas para '{descricao}': {parcela_atual}/{total_parcelas}"
                                )

                                # Usar a mesma sessão do banco para evitar conflitos
                                with get_db() as session:
                                    # Loop para criar parcelas futuras
                                    for i in range(parcela_atual + 1, total_parcelas + 1):
                                        # Calcular data futura: adicionar (i - parcela_atual) meses
                                        meses_offset = i - parcela_atual
                                        data_futura = data_obj + relativedelta(
                                            months=meses_offset
                                        )

                                        logger.debug(
                                            f"[PARCELAS] Calculando parcela {i}/{total_parcelas}: "
                                            f"data_obj={data_obj} + {meses_offset} meses = {data_futura}"
                                        )

                                        # Atualizar descrição: adicionar "(Proj. X/Y)" para indicar que foi gerada
                                        # Padrão: encontrar o último "XX/YY" e substituir, depois adicionar (Proj.)
                                        desc_futura = re.sub(
                                            r"(\d{1,2})(/|-)(\d{1,2})(?!.*\d{1,2}/\d{1,2})",
                                            lambda m: f"{i}{m.group(2)}{total_parcelas}",
                                            descricao,
                                        )
                                        # Adicionar marcação de projeção se não tiver
                                        if "(Proj." not in desc_futura:
                                            desc_futura = f"{desc_futura} (Proj. {i}/{total_parcelas})"

                                        # Verificar se parcela já existe
                                        if _transaction_exists(
                                            session, desc_futura, valor, data_futura, conta_id
                                        ):
                                            logger.debug(
                                                f"[PARCELAS] ✓ Parcela {i}/{total_parcelas} já existe "
                                                f"(data: {data_futura}), pulando..."
                                            )
                                            continue

                                        # Criar transação futura
                                        success_parcela, msg_parcela = create_transaction(
                                            data=data_futura,
                                            descricao=desc_futura,
                                            valor=valor,
                                            tipo=tipo,
                                            categoria_id=categoria_id,
                                            conta_id=conta_id,
                                            tags=tags_str,
                                        )

                                        if success_parcela:
                                            count_parcelas_futuras += 1
                                            logger.info(
                                                f"[PARCELAS] ✓ Parcela {i}/{total_parcelas} criada: "
                                                f"{desc_futura} em {data_futura}"
                                            )
                                        else:
                                            logger.warning(
                                                f"[PARCELAS] ✗ Erro ao criar parcela {i}/{total_parcelas}: {msg_parcela}"
                                            )
                            else:
                                logger.debug(
                                    f"[PARCELAS] Nenhuma parcela futura a criar (parcela_atual={parcela_atual}, total={total_parcelas})"
                                )

                        except (ValueError, TypeError) as e:
                            logger.warning(
                                f"[PARCELAS] Erro ao processar parcelas para linha {idx}: {e}"
                            )

            except Exception as e:
                errors.append(f"Linha {idx}: {str(e)}")
                logger.error(f"[IMPORT] Erro ao processar linha {idx}: {e}")
                continue

        # Return feedback
        if count > 0:
            msg_duplicatas = (
                f" {skipped_count} duplicatas ignoradas."
                if skipped_count > 0
                else ""
            )
            msg_parcelas = (
                f"\n🔄 Parcelas futuras criadas: {count_parcelas_futuras}"
                if count_parcelas_futuras > 0
                else ""
            )
            feedback = render_import_success(
                f"{count} transações importadas.{msg_duplicatas}{msg_parcelas}"
            )
            logger.info(
                f"[IMPORT] ✅ {count} transações importadas com sucesso"
                f" ({count_parcelas_futuras} parcelas futuras criadas)"
            )

        elif skipped_count > 0:
            # Special case: All duplicates (not an error!)
            feedback = dbc.Alert(
                [
                    html.H4("ℹ️ Nenhuma nova transação", className="alert-heading"),
                    html.P(
                        f"Todas as {skipped_count} transações deste arquivo já existem "
                        "no banco de dados e foram ignoradas."
                    )
                ],
                color="info",
                dismissable=True
            )
            logger.info(
                f"[IMPORT] ℹ️ Arquivo continha apenas duplicatas ({skipped_count} ignoradas)"
            )

        else:
            # Real error case (empty file or nothing saved due to error)
            error_msg = "; ".join(errors) if errors else "Nenhuma transação importada"
            feedback = render_import_error(f"✗ Importação falhou: {error_msg}")
            logger.error(f"[IMPORT] ✗ Importação falhou: {error_msg}")

        # Clear data after save
        return (
            feedback,
            None,  # Clear store
            [],  # Clear preview
            html.Div(),  # Clear status
        )

    except Exception as e:
        logger.error(f"[IMPORT] Erro crítico ao salvar: {e}", exc_info=True)
        feedback = render_import_error(f"Erro crítico: {str(e)}")
        return feedback, None, [], html.Div()


@app.callback(
    Output("store-import-data", "data", allow_duplicate=True),
    Output("preview-container", "children", allow_duplicate=True),
    Output("upload-status", "children", allow_duplicate=True),
    Output("btn-save-import", "disabled", allow_duplicate=True),
    Output("btn-clear-import", "disabled", allow_duplicate=True),
    Input("btn-clear-import", "n_clicks"),
    prevent_initial_call=True,
    allow_duplicate=True,
)
def clear_import_data(n_clicks: int) -> tuple:
    """Clear all import data and reset UI.

    Args:
        n_clicks: Button click count

    Returns:
        Tuple of reset values
    """
    logger.info("[IMPORT] Limpando dados de importação...")
    return (
        None,  # Clear store
        [],  # Clear preview
        html.Div(),  # Clear status
        True,  # Disable save
        True,  # Disable clear
    )


# ===== ACCOUNT MANAGEMENT CALLBACKS =====


@app.callback(
    Output("select-receita-conta", "options"),
    Output("select-receita-conta", "value"),
    Input("modal-transacao", "is_open"),
    State("tabs-modal-transacao", "value"),
    prevent_initial_call=True,
)
def update_receita_conta_options(is_open, tab_value):
    """
    Atualiza opções de conta para receitas (conta e investimento).

    Quando o modal abre na aba de receita, popula o dropdown com
    apenas contas do tipo "conta" ou "investimento".
    """
    logger.debug(f"[RECEITA] Modal aberto: {is_open}, Tab: {tab_value}")
    if not is_open or tab_value != "tab-receita":
        logger.debug(f"[RECEITA] Ignorando callback (aberto={is_open}, tab_receita={tab_value == 'tab-receita'})")
        return [], None

    try:
        contas = get_accounts()
        logger.info(f"[RECEITA] Total de contas no banco: {len(contas)}")
        
        receita_contas = [
            c for c in contas 
            if (hasattr(c, 'tipo') and c.tipo in ["conta", "investimento"]) or
               (isinstance(c, dict) and c.get("tipo") in ["conta", "investimento"])
        ]
        logger.info(f"[RECEITA] Contas filtradas para receita: {len(receita_contas)}")

        emoji_map = {
            "conta": "🏦",
            "cartao": "💳",
            "investimento": "📈",
        }

        options = [
            {
                "label": f'{emoji_map.get(c.tipo if hasattr(c, "tipo") else c.get("tipo"), "💰")} {c.nome if hasattr(c, "nome") else c.get("nome")}',
                "value": c.id if hasattr(c, "id") else c.get("id"),
            }
            for c in receita_contas
        ]

        logger.info(f"✓ {len(options)} contas carregadas para receita: {[opt['label'] for opt in options]}")
        return options, None

    except Exception as e:
        logger.error(f"✗ Erro ao carregar contas de receita: {e}", exc_info=True)
        return [], None


@app.callback(
    Output("select-despesa-conta", "options"),
    Output("select-despesa-conta", "value"),
    Input("modal-transacao", "is_open"),
    State("tabs-modal-transacao", "value"),
    prevent_initial_call=True,
)
def update_despesa_conta_options(is_open, tab_value):
    """
    Atualiza opções de conta para despesas (conta e cartão).

    Quando o modal abre na aba de despesa, popula o dropdown com
    apenas contas do tipo "conta" ou "cartao".
    """
    logger.debug(f"[DESPESA] Modal aberto: {is_open}, Tab: {tab_value}")
    if not is_open or tab_value != "tab-despesa":
        logger.debug(f"[DESPESA] Ignorando callback (aberto={is_open}, tab_despesa={tab_value == 'tab-despesa'})")
        return [], None

    try:
        contas = get_accounts()
        logger.info(f"[DESPESA] Total de contas no banco: {len(contas)}")
        
        despesa_contas = [
            c for c in contas 
            if (hasattr(c, 'tipo') and c.tipo in ["conta", "cartao"]) or
               (isinstance(c, dict) and c.get("tipo") in ["conta", "cartao"])
        ]
        logger.info(f"[DESPESA] Contas filtradas para despesa: {len(despesa_contas)}")

        emoji_map = {
            "conta": "🏦",
            "cartao": "💳",
            "investimento": "📈",
        }

        options = [
            {
                "label": f'{emoji_map.get(c.tipo if hasattr(c, "tipo") else c.get("tipo"), "💰")} {c.nome if hasattr(c, "nome") else c.get("nome")}',
                "value": c.id if hasattr(c, "id") else c.get("id"),
            }
            for c in despesa_contas
        ]

        logger.info(f"✓ {len(options)} contas carregadas para despesa: {[opt['label'] for opt in options]}")
        return options, None

    except Exception as e:
        logger.error(f"✗ Erro ao carregar contas de despesa: {e}", exc_info=True)
        return [], None


@app.callback(
    Output("container-parcelas", "style"),
    Input("select-despesa-conta", "value"),
    prevent_initial_call=True,
)
def toggle_parcelas_visibility(conta_id: Optional[int]) -> Dict:
    """
    Mostra/esconde o campo de parcelas baseado na conta selecionada.

    Se a conta for do tipo 'cartao' (crédito), mostra o campo de parcelas.
    Caso contrário, mantém oculto.

    Args:
        conta_id: ID da conta selecionada no dropdown.

    Returns:
        Dict com propriedade 'display' para CSS.
    """
    if not conta_id:
        logger.debug("[PARCELAS] Nenhuma conta selecionada")
        return {'display': 'none'}

    try:
        contas = get_accounts()
        conta_selecionada = None
        
        for c in contas:
            c_id = c.id if hasattr(c, 'id') else c.get('id')
            if c_id == conta_id:
                conta_selecionada = c
                break
        
        if not conta_selecionada:
            logger.warning(f"[PARCELAS] Conta não encontrada: ID {conta_id}")
            return {'display': 'none'}
        
        tipo_conta = conta_selecionada.tipo if hasattr(conta_selecionada, 'tipo') else conta_selecionada.get('tipo')
        logger.info(f"[PARCELAS] Conta selecionada: tipo={tipo_conta}")
        
        if tipo_conta == 'cartao':
            logger.info(f"[PARCELAS] Mostrando campo de parcelas (Cartão de Crédito)")
            return {'display': 'block'}
        else:
            logger.info(f"[PARCELAS] Ocultando campo de parcelas (Conta Corrente)")
            return {'display': 'none'}
            
    except Exception as e:
        logger.error(f"[PARCELAS] Erro ao verificar tipo de conta: {e}", exc_info=True)
        return {'display': 'none'}


@app.callback(
    Output("account-feedback-alert", "children"),
    Output("account-feedback-alert", "is_open"),
    Output("accounts-list-container", "children"),
    Output("input-nome-conta", "value"),
    Output("input-saldo-inicial", "value"),
    Input("btn-salvar-conta", "n_clicks"),
    State("input-nome-conta", "value"),
    State("dropdown-tipo-conta", "value"),
    State("input-saldo-inicial", "value"),
    prevent_initial_call=True,
)
def save_new_account(n_clicks, nome, tipo, saldo):
    """
    Cria nova conta a partir dos inputs do formulário.

    Valida entrada, chama create_account(), atualiza a lista de contas
    e limpa o formulário após sucesso.

    Saldo inicial é opcional e assume 0.0 se não preenchido.
    """
    if not n_clicks:
        raise PreventUpdate

    # Validar campos obrigatórios (nome e tipo)
    if not nome or not tipo:
        return (
            dbc.Alert(
                "Preencha os campos obrigatórios: Nome e Tipo.",
                color="warning",
            ),
            True,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    # Saldo inicial é opcional: default 0.0 se vazio ou None
    if saldo is None or saldo == "":
        saldo_float = 0.0
    else:
        try:
            saldo_float = float(str(saldo).replace(",", "."))
        except ValueError:
            return (
                dbc.Alert(
                    "Saldo Inicial deve ser um número válido (ou deixe vazio para 0).",
                    color="warning",
                ),
                True,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

    try:
        success, message = create_account(nome, tipo, saldo_float)

        if success:
            logger.info(f"✓ Conta '{nome}' criada com sucesso (Saldo: R$ {saldo_float:.2f})")
            # Buscar lista atualizada e gerar novo grid
            contas = get_accounts()
            novo_grid = render_accounts_grid(contas)
            
            return (
                dbc.Alert(
                    f"✓ Conta '{nome}' criada com sucesso!",
                    color="success",
                ),
                True,
                novo_grid,
                "",  # Limpar nome
                "",  # Limpar saldo
            )
        else:
            logger.warning(f"✗ Erro ao criar conta: {message}")
            return (
                dbc.Alert(f"Erro: {message}", color="danger"),
                True,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

    except Exception as e:
        logger.error(f"✗ Erro ao salvar conta: {e}")
        return (
            dbc.Alert(f"Erro ao salvar conta: {str(e)}", color="danger"),
            True,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )


@app.callback(
    Output("account-feedback-alert", "children", allow_duplicate=True),
    Output("account-feedback-alert", "is_open", allow_duplicate=True),
    Output("accounts-list-container", "children", allow_duplicate=True),
    Input({"type": "btn-excluir-conta", "index": ALL}, "n_clicks"),
    State({"type": "btn-excluir-conta", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def delete_account_callback(n_clicks, btn_ids):
    """
    Deleta uma conta ao clicar no botão de exclusão.

    Usa pattern matching para identificar qual conta foi clicada,
    chama delete_account() para removê-la e atualiza a lista.
    """
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate

    # Encontrar qual botão foi clicado
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_data = json.loads(trigger_id)
    conta_id = trigger_data.get("index")

    if not conta_id:
        raise PreventUpdate

    try:
        success, message = delete_account(conta_id)

        if success:
            logger.info(f"✓ Conta {conta_id} deletada com sucesso")
            # Buscar lista atualizada e gerar novo grid
            contas = get_accounts()
            novo_grid = render_accounts_grid(contas)
            
            return (
                dbc.Alert(
                    "✓ Conta deletada com sucesso!",
                    color="success",
                ),
                True,
                novo_grid,
            )
        else:
            logger.warning(f"✗ Erro ao deletar conta: {message}")
            return (
                dbc.Alert(f"Erro: {message}", color="danger"),
                True,
                dash.no_update,
            )

    except Exception as e:
        logger.error(f"✗ Erro ao deletar conta: {e}")
        return (
            dbc.Alert(f"Erro ao deletar conta: {str(e)}", color="danger"),
            True,
            dash.no_update,
        )


# ===== TAG EDITOR MODAL CALLBACKS =====


@app.callback(
    Output("modal-tag-editor", "is_open"),
    Output("dropdown-tag-editor", "options", allow_duplicate=True),
    Output("dropdown-tag-editor", "value"),
    Output("store-editing-row-index", "data"),
    Input("table-import-preview", "active_cell"),
    State("table-import-preview", "data"),
    prevent_initial_call=True,
)
def open_tag_editor_modal(
    active_cell: Dict[str, Any],
    table_data: List[Dict[str, Any]],
) -> tuple:
    """
    Abre o editor de tags quando uma célula da coluna 'tags' é clicada.

    Extrai as tags atuais, converte para lista, carrega opções do banco
    e abre o modal para edição.

    Args:
        active_cell: Célula ativa do DataTable (ex: {"row": 2, "column_id": "tags"})
        table_data: Dados completos da tabela

    Returns:
        Tuple: (modal_is_open, dropdown_options, dropdown_value, row_index)
    """
    # DEBUG: Imprimir clique detectado
    print(f"DEBUG: Clique detectado em {active_cell}")
    
    if not active_cell or not table_data:
        raise PreventUpdate

    # Verificar se a célula clicada é na coluna 'tags'
    row_idx = active_cell.get("row")
    col_id = active_cell.get("column_id")
    
    # DEBUG: Imprimir detalhes da célula
    print(f"DEBUG: row_idx={row_idx}, col_id={col_id}")

    # Verificar se é a coluna 'tags'
    if col_id != "tags":
        print(f"DEBUG: Coluna inválida ({col_id}), ignorando clique")
        raise PreventUpdate

    try:
        # Pegar tags atuais da linha clicada
        if row_idx < len(table_data):
            current_row = table_data[row_idx]
            tags_str = current_row.get("tags", "")
            
            print(f"DEBUG: Tags atuais na linha {row_idx}: '{tags_str}'")

            # Converter tags string em lista (split por vírgula)
            tags_list = []
            if tags_str:
                tags_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
            
            print(f"DEBUG: Tags parseadas em lista: {tags_list}")

            # Carregar lista de tags únicas do banco
            existing_tags = get_unique_tags_list()
            dropdown_options = [{"label": tag, "value": tag} for tag in existing_tags]
            
            print(f"DEBUG: Opcoes carregadas do banco: {len(existing_tags)} tags unicas")

            logger.info(
                f"[TAGS] Modal aberto para linha {row_idx}: "
                f"{len(tags_list)} tags selecionadas"
            )
            
            print(f"DEBUG: Modal aberto com sucesso!")

            return (
                True,  # Abrir modal
                dropdown_options,  # Options do dropdown
                tags_list,  # Value pré-selecionado
                row_idx,  # Guardar índice da linha
            )
        else:
            logger.warning(f"[TAGS] Índice de linha inválido: {row_idx}")
            print(f"DEBUG: row_idx={row_idx} >= len(table_data)={len(table_data)}")
            raise PreventUpdate

    except Exception as e:
        logger.error(f"[TAGS] Erro ao abrir editor: {e}")
        print(f"DEBUG: ERRO ao abrir editor: {e}")
        raise PreventUpdate


@app.callback(
    Output("table-import-preview", "data"),
    Output("modal-tag-editor", "is_open", allow_duplicate=True),
    Input("btn-save-tags", "n_clicks"),
    State("dropdown-tag-editor", "value"),
    State("store-editing-row-index", "data"),
    State("table-import-preview", "data"),
    prevent_initial_call=True,
)
def save_tags_to_table(
    n_clicks: int,
    selected_tags: List[str],
    row_index: int,
    table_data: List[Dict[str, Any]],
) -> tuple:
    """
    Salva as tags selecionadas de volta à tabela e fecha o modal.

    Converte a lista de tags em string, atualiza a linha correspondente
    na tabela e fecha o modal de edição.

    Args:
        n_clicks: Número de cliques no botão Salvar
        selected_tags: Lista de tags selecionadas no dropdown
        row_index: Índice da linha sendo editada
        table_data: Dados completos da tabela

    Returns:
        Tuple: (updated_table_data, modal_is_open)
    """
    if not n_clicks or row_index is None or not table_data:
        raise PreventUpdate

    try:
        # Fazer cópia para não mutar original
        updated_data = [row.copy() for row in table_data]

        # Converter lista de tags em string (ex: "Tag1, Tag2, Tag3")
        tags_str = ", ".join(selected_tags) if selected_tags else ""

        # Atualizar a linha correspondente
        if row_index < len(updated_data):
            updated_data[row_index]["tags"] = tags_str

            logger.info(
                f"[TAGS] Salvadas {len(selected_tags)} tags na linha {row_index}: "
                f"{tags_str}"
            )

            return (
                updated_data,  # Retornar tabela atualizada
                False,  # Fechar modal
            )
        else:
            logger.warning(f"[TAGS] Índice de linha inválido: {row_index}")
            raise PreventUpdate

    except Exception as e:
        logger.error(f"[TAGS] Erro ao salvar tags: {e}")
        raise PreventUpdate


@app.callback(
    Output("modal-tag-editor", "is_open", allow_duplicate=True),
    Output("dropdown-tag-editor", "value", allow_duplicate=True),
    Input("btn-cancel-tags", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_tag_editor_modal(n_clicks: int) -> tuple:
    """
    Fecha o editor de tags sem salvar alterações.

    Args:
        n_clicks: Número de cliques no botão Cancelar

    Returns:
        Tuple: (modal_is_open, dropdown_value_reset)
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("[TAGS] Modal cancelado")
    return (
        False,  # Fechar modal
        [],  # Resetar dropdown
    )


@app.callback(
    Output("dropdown-tag-editor", "options", allow_duplicate=True),
    Input("dropdown-tag-editor", "search_value"),
    State("dropdown-tag-editor", "options"),
    prevent_initial_call=True,
)
def add_new_tag_option(
    search_value: str,
    existing_options: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Permite criar novas tags digitando no dropdown.
    
    Quando o usuário digita um valor que não existe na lista de opções,
    adiciona dinamicamente como uma nova opção válida (feature "Type to Create").

    Args:
        search_value: Texto digitado pelo usuário no dropdown
        existing_options: Lista atual de opções {'label': tag, 'value': tag}

    Returns:
        List[Dict[str, str]]: Lista atualizada de opções com nova tag se aplicável
    """
    # Se nenhum valor foi digitado, não fazer nada
    if not search_value or not isinstance(search_value, str):
        raise PreventUpdate

    # Normalizar o valor para comparação (lowercase, strip whitespace)
    # Se após strip ficar vazio, rejeitar
    normalized_search = search_value.strip().lower()
    
    if not normalized_search:  # Se vazio após strip, rejeitar
        raise PreventUpdate
    
    print(f"DEBUG: search_value digitado: '{search_value}'")
    print(f"DEBUG: Verificando se já existe na lista...")

    # Verificar se a tag já existe (case-insensitive)
    tag_exists = any(
        opt.get("value", "").lower() == normalized_search
        for opt in existing_options
    )

    if tag_exists:
        print(f"DEBUG: Tag '{search_value}' já existe, ignorando")
        raise PreventUpdate

    # Tag não existe, criar nova opção
    new_option = {
        "label": search_value,
        "value": search_value,
    }
    
    print(f"DEBUG: Criando nova tag: {new_option}")

    # Adicionar à lista existente
    updated_options = existing_options + [new_option]

    logger.info(f"[TAGS] Nova tag criada via dropdown: '{search_value}'")
    print(f"DEBUG: Lista de opcoes atualizada: {len(updated_options)} tags")

    return updated_options


if __name__ == "__main__":
    # ===== INICIALIZAÇÃO AUTOMÁTICA DO BANCO DE DADOS =====
    print("\n" + "=" * 70)
    print("[INICIANDO FINANCETSK]")
    print("=" * 70)

    logger.info("[SETUP] Inicializando banco de dados...")
    try:
        logger.info("[SETUP] Verificando estrutura de diretórios...")
        init_database()
        logger.info("[SETUP] Banco de dados pronto!")
        
        # Initialize default accounts and categories
        ensure_default_accounts()
        ensure_default_categories()
        
        print("✅ Banco de dados inicializado com sucesso")

    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO ao inicializar banco: {e}", exc_info=True)
        print(f"\n❌ ERRO CRÍTICO ao inicializar banco:")
        print(f"   {e}\n")
        import traceback

        traceback.print_exc()
        print("\n" + "=" * 70)
        raise

    # ===== INICIAR SERVIDOR =====
    print("=" * 70)
    logger.info("[SETUP] Iniciando servidor FinanceTSK em http://localhost:8050")
    print("[SERVER] Servidor rodando em: http://localhost:8050")
    print("=" * 70 + "\n")

    try:
        app.run_server(debug=True, host="localhost", port=8050)
    except Exception as e:
        logger.error(f"[ERROR] Erro ao iniciar servidor: {e}", exc_info=True)
        print(f"\n[ERROR] Erro ao iniciar servidor: {e}\n")
        raise
