import logging
from datetime import date
from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, callback, Input, Output, State
from dateutil.relativedelta import relativedelta

from src.components.dashboard import render_summary_cards
from src.components.modals import render_transaction_modal
from src.components.tables import render_transactions_table
from src.database.operations import get_transactions, create_transaction

logger = logging.getLogger(__name__)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)

app.title = "FinanceTSK - Gestor Financeiro"


app.layout = dbc.Container(
    [
        dbc.NavbarSimple(
            children=[
                dbc.Nav(
                    [
                        dbc.NavLink("Dashboard", href="/", active="exact"),
                        dbc.NavLink("Receitas", href="/receitas", active="exact"),
                        dbc.NavLink("Despesas", href="/despesas", active="exact"),
                        dbc.NavLink("Categorias", href="/categorias", active="exact"),
                    ],
                    className="ms-auto",
                    navbar=True,
                )
            ],
            brand="💰 FinanceTSK",
            brand_href="/",
            color="primary",
            dark=True,
            className="mb-4",
        ),
        dcc.Location(id="url", refresh=False),
        html.Div(
            id="dashboard-container",
            children=render_summary_cards(),
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "+ Nova Transação",
                        id="btn-nova-transacao",
                        color="primary",
                        size="lg",
                        className="mb-3",
                        style={"width": "100%"},
                    ),
                    width=12,
                )
            ]
        ),
        dcc.Tabs(
            id="tabs-principal",
            value="tab-dashboard",
            children=[
                dcc.Tab(
                    label="📊 Dashboard",
                    value="tab-dashboard",
                ),
                dcc.Tab(
                    label="💰 Receitas",
                    value="tab-receitas",
                ),
                dcc.Tab(
                    label="💸 Despesas",
                    value="tab-despesas",
                ),
                dcc.Tab(
                    label="📁 Categorias",
                    value="tab-categorias",
                ),
            ],
        ),
        html.Div(id="conteudo-abas", className="mt-4"),
        render_transaction_modal(is_open=False),
        dcc.Store(
            id="store-data-atual",
            data={"ano": date.today().year, "mes": date.today().month},
        ),
        dcc.Store(
            id="store-transacao-salva",
            data=0,
        ),
        html.Div(id="dummy-output", style={"display": "none"}),
        html.Hr(className="mt-5"),
        html.Footer(
            "FinanceTSK v1.0 | Gestor Financeiro Pessoal",
            className="text-center text-muted mt-4 mb-3",
        ),
    ],
    fluid=True,
    className="pt-4",
)


@app.callback(
    Output("conteudo-abas", "children"),
    Input("tabs-principal", "value"),
    Input("store-transacao-salva", "data"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def render_tab_content(
    tab_value: str,
    store_data: float,
):
    """
    Renderiza o conteúdo dinâmico das abas.

    Exibe gráficos no Dashboard, tabelas de transações nas abas
    de Receitas e Despesas. Atualiza quando uma transação é salva
    (via store-transacao-salva).

    Args:
        tab_value: Valor da aba selecionada.
        store_data: Timestamp da última transação salva (sinal).

    Returns:
        Componente do Dash com o conteúdo da aba selecionada.
    """
    try:
        logger.info(f"📌 Renderizando aba: {tab_value} (signal={store_data})")

        if tab_value == "tab-dashboard":
            logger.info("✓ Dashboard selecionado")
            return dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.H3(
                                "📈 Gráficos em breve",
                                className="text-center text-muted",
                            )
                        )
                    ),
                    width=12,
                )
            )

        elif tab_value == "tab-receitas":
            logger.info("💰 Carregando receitas...")
            try:
                transacoes = get_transactions()
                receitas = [t for t in transacoes if t.get("tipo") == "receita"]
                logger.info(f"✓ {len(receitas)} receitas carregadas")
                return render_transactions_table(receitas)
            except Exception as e:
                logger.error(f"✗ Erro ao carregar receitas: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar receitas: {str(e)}",
                    color="danger",
                )

        elif tab_value == "tab-despesas":
            logger.info("💸 Carregando despesas...")
            try:
                transacoes = get_transactions()
                despesas = [t for t in transacoes if t.get("tipo") == "despesa"]
                logger.info(f"✓ {len(despesas)} despesas carregadas")
                return render_transactions_table(despesas)
            except Exception as e:
                logger.error(f"✗ Erro ao carregar despesas: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar despesas: {str(e)}",
                    color="danger",
                )

        elif tab_value == "tab-categorias":
            logger.info("📁 Categorias selecionadas")
            return dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            html.H3(
                                "📁 Categorias em breve",
                                className="text-center text-muted",
                            )
                        )
                    ),
                    width=12,
                )
            )

        else:
            logger.warning(f"⚠️ Aba desconhecida: {tab_value}")
            return html.Div()

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar conteúdo das abas: {e}", exc_info=True)
        return dbc.Alert(
            f"Erro ao carregar conteúdo: {str(e)}",
            color="danger",
        )


@app.callback(
    Output("alerta-modal", "is_open"),
    Output("alerta-modal", "children"),
    Output("modal-transacao", "is_open", allow_duplicate=True),
    Output("store-transacao-salva", "data"),
    Input("btn-salvar-receita", "n_clicks"),
    State("input-receita-valor", "value"),
    State("input-receita-descricao", "value"),
    State("dcc-receita-data", "date"),
    State("dcc-receita-categoria", "value"),
    State("input-receita-tags", "value"),
    State("input-receita-pessoa-origem", "value"),
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
    tags: str,
    pessoa_origem: str,
    modal_is_open: bool,
):
    """
    Salva uma nova receita no banco de dados.

    Args:
        n_clicks: Número de cliques no botão.
        valor: Valor da receita.
        descricao: Descrição da receita.
        data: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        tags: Tags separadas por vírgula.
        pessoa_origem: Pessoa/entidade de origem.
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, store_data).
    """
    import time

    logger.info(f"💾 Salvando receita: {descricao} - R${valor}")

    if not all([valor, descricao, data, categoria_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return True, msg_erro, True, 0

    try:
        from datetime import datetime

        data_obj = datetime.strptime(data, "%Y-%m-%d").date()

        success, message = create_transaction(
            tipo="receita",
            descricao=descricao,
            valor=float(valor),
            data=data_obj,
            categoria_id=int(categoria_id),
            tags=tags,
            pessoa_origem=pessoa_origem,
        )

        if success:
            logger.info(f"✓ Receita salva com sucesso: {descricao}")
            timestamp = time.time()
            logger.info(f"📡 Sinalizando atualização (timestamp={timestamp})")
            return False, "", False, timestamp
        else:
            msg_erro = f"❌ Erro: {message}"
            logger.error(f"✗ {msg_erro}")
            return True, msg_erro, True, 0

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return True, msg_erro, True, 0


@app.callback(
    Output("alerta-modal", "is_open", allow_duplicate=True),
    Output("alerta-modal", "children", allow_duplicate=True),
    Output("modal-transacao", "is_open", allow_duplicate=True),
    Output("store-transacao-salva", "data", allow_duplicate=True),
    Input("btn-salvar-despesa", "n_clicks"),
    State("input-despesa-valor", "value"),
    State("input-despesa-descricao", "value"),
    State("dcc-despesa-data", "date"),
    State("dcc-despesa-categoria", "value"),
    State("input-despesa-tags", "value"),
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
    tags: str,
    modal_is_open: bool,
):
    """
    Salva uma nova despesa no banco de dados.

    Args:
        n_clicks: Número de cliques no botão.
        valor: Valor da despesa.
        descricao: Descrição da despesa.
        data: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        tags: Tags separadas por vírgula.
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, store_data).
    """
    import time

    logger.info(f"💾 Salvando despesa: {descricao} - R${valor}")

    if not all([valor, descricao, data, categoria_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return True, msg_erro, True, 0

    try:
        from datetime import datetime

        data_obj = datetime.strptime(data, "%Y-%m-%d").date()

        success, message = create_transaction(
            tipo="despesa",
            descricao=descricao,
            valor=float(valor),
            data=data_obj,
            categoria_id=int(categoria_id),
            tags=tags,
        )

        if success:
            logger.info(f"✓ Despesa salva com sucesso: {descricao}")
            timestamp = time.time()
            logger.info(f"📡 Sinalizando atualização (timestamp={timestamp})")
            return False, "", False, timestamp
        else:
            msg_erro = f"❌ Erro: {message}"
            logger.error(f"✗ {msg_erro}")
            return True, msg_erro, True, 0

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return True, msg_erro, True, 0


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
    Input("btn-nova-transacao", "n_clicks"),
    State("modal-transacao", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal_open(n_clicks_nova: int, is_open: bool) -> bool:
    """
    Abre o modal ao clicar em "+ Nova Transação".

    Args:
        n_clicks_nova: Cliques no botão "+ Nova Transação".
        is_open: Estado atual do modal.

    Returns:
        Novo estado booleano do modal.
    """
    logger.info(f"🔘 Abrindo modal...")
    return not is_open


if __name__ == "__main__":
    app.run_server(debug=True, host="localhost", port=8050)
