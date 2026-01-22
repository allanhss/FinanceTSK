import logging
import re
import time
import traceback
from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL, ctx, no_update
from dash.exceptions import PreventUpdate

from src.database.connection import init_database
from src.database.operations import (
    get_transactions,
    create_transaction,
    get_cash_flow_data,
    get_category_matrix_data,
    get_tag_matrix_data,
    get_categories,
    create_category,
    delete_category,
    get_used_icons,
    get_all_tags,
)
from src.components.dashboard import render_summary_cards
from src.components.modals import render_transaction_modal
from src.components.tables import render_transactions_table
from src.components.cash_flow import render_cash_flow_table
from src.components.category_manager import render_category_manager, EMOJI_OPTIONS
from src.components.category_matrix import render_category_matrix
from src.components.tag_matrix import render_tag_matrix
from src.components.category_matrix import render_category_matrix

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
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Meses Passados:", html_for="select-past"),
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
                        ),
                    ],
                    md=6,
                    className="mb-3",
                ),
                dbc.Col(
                    [
                        dbc.Label("Meses Futuros:", html_for="select-future"),
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
                    md=6,
                    className="mb-3",
                ),
            ],
            className="mb-4",
        ),
        html.Div(
            id="cash-flow-container",
            children=render_cash_flow_table([]),
            style={"overflowX": "auto"},
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "+ Receita",
                        id="btn-nova-receita",
                        color="success",
                        size="lg",
                        className="mb-3 w-100",
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Button(
                        "+ Despesa",
                        id="btn-nova-despesa",
                        color="danger",
                        size="lg",
                        className="mb-3 w-100",
                    ),
                    md=6,
                ),
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
                    label="� Análise",
                    value="tab-analise",
                ),
                dcc.Tab(
                    label="🏷️ Tags",
                    value="tab-tags",
                ),
                dcc.Tab(
                    label="�📁 Categorias",
                    value="tab-categorias",
                ),
            ],
        ),
        html.Div(id="conteudo-abas", className="mt-4"),
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
    Output("cash-flow-container", "children"),
    Input("select-past", "value"),
    Input("select-future", "value"),
    Input("store-transacao-salva", "data"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def update_cash_flow(
    months_past: int, months_future: int, store_data: float
) -> dbc.Card:
    """
    Atualiza a tabela de Fluxo de Caixa baseado nos controles de horizonte temporal.

    Recarrega os dados sempre que o usuário muda os seletores de meses passados/futuros
    ou quando uma transação é salva com sucesso (via store-transacao-salva).

    O padrão Store/Signal elimina a condição de corrida onde o callback de leitura
    disparava antes do término da gravação no banco.

    Args:
        months_past: Número de meses para trás (padrão 3).
        months_future: Número de meses para frente (padrão 6).
        store_data: Timestamp da última transação salva (sinal de sincronização).

    Returns:
        dbc.Card com a tabela de fluxo de caixa atualizada.
    """
    logger.info(
        f"🔄 Atualizando Fluxo de Caixa: {months_past} meses passados, "
        f"{months_future} meses futuros (signal={store_data})"
    )

    try:
        fluxo_data = get_cash_flow_data(
            months_past=months_past, months_future=months_future
        )
        tabela = render_cash_flow_table(fluxo_data)
        logger.info("✓ Fluxo de caixa renderizado com sucesso")
        return tabela

    except Exception as e:
        logger.error(f"✗ Erro ao atualizar fluxo de caixa: {e}", exc_info=True)
        return dbc.Card(
            [
                dbc.CardHeader(html.H5("💰 Fluxo de Caixa")),
                dbc.CardBody(
                    dbc.Alert(
                        f"Erro ao carregar fluxo de caixa: {str(e)}",
                        color="danger",
                        className="mb-0",
                    )
                ),
            ],
            className="shadow-sm",
        )


@app.callback(
    Output("conteudo-abas", "children"),
    Input("tabs-principal", "value"),
    Input("store-transacao-salva", "data"),
    Input("store-categorias-atualizadas", "data"),
    State("select-past", "value"),
    State("select-future", "value"),
    prevent_initial_call=False,
    allow_duplicate=True,
)
def render_tab_content(
    tab_value: str,
    store_transacao: float,
    store_categorias: float,
    months_past: int,
    months_future: int,
):
    """
    Renderiza o conteúdo dinâmico das abas.

    Exibe gráficos no Dashboard, tabelas de transações nas abas
    de Receitas e Despesas. Atualiza quando uma transação é salva
    (via store-transacao-salva) ou categorias são modificadas
    (via store-categorias-atualizadas).

    Args:
        tab_value: Valor da aba selecionada.
        store_transacao: Timestamp da última transação salva (sinal).
        store_categorias: Timestamp da última atualização de categorias (sinal).
        months_past: Número de meses passados para análise.
        months_future: Número de meses futuros para análise.

    Returns:
        Componente do Dash com o conteúdo da aba selecionada.
    """
    try:
        logger.info(
            f"📌 Renderizando aba: {tab_value} (transacao_signal={store_transacao}, cat_signal={store_categorias})"
        )

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

        elif tab_value == "tab-analise":
            logger.info("📈 Carregando matriz analítica...")
            try:
                matriz_data = get_category_matrix_data(
                    months_past=months_past, months_future=months_future
                )
                logger.info("✓ Matriz analítica carregada com sucesso")
                return dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H3("📈 Matriz Analítica - Categorias vs Meses")
                        ),
                        dbc.CardBody(render_category_matrix(matriz_data)),
                    ],
                    className="shadow-sm",
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar matriz analítica: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar matriz analítica: {str(e)}",
                    color="danger",
                )

        elif tab_value == "tab-tags":
            logger.info("🏷️ Carregando matriz de tags...")
            try:
                matriz_tags_data = get_tag_matrix_data(
                    months_past=months_past, months_future=months_future
                )
                logger.info("✓ Matriz de tags carregada com sucesso")
                return dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H3("🏷️ Matriz de Tags - Saldo por Entidade")
                        ),
                        dbc.CardBody(render_tag_matrix(matriz_tags_data)),
                    ],
                    className="shadow-sm",
                )
            except Exception as e:
                logger.error(f"✗ Erro ao carregar matriz de tags: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar matriz de tags: {str(e)}",
                    color="danger",
                )

        elif tab_value == "tab-categorias":
            logger.info("📁 Carregando categorias...")
            try:
                # Carregar categorias separadas por tipo
                receitas = get_categories(tipo="receita")
                despesas = get_categories(tipo="despesa")
                logger.info(
                    f"✓ {len(receitas)} receitas e "
                    f"{len(despesas)} despesas carregadas"
                )

                # Usar componente render_category_manager
                return render_category_manager(receitas, despesas)

            except Exception as e:
                logger.error(f"✗ Erro ao carregar categorias: {e}", exc_info=True)
                return dbc.Alert(
                    f"Erro ao carregar categorias: {str(e)}",
                    color="danger",
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
                desc_limpa = re.sub(r"\s*(\(Recorrência #\d+\)|\(\d+/\d+\)|\d+/\d+)", "", descricao).strip()

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
    Output("radio-icon-receita", "value"),
    Output("radio-icon-despesa", "value"),
    Input("btn-add-cat-receita", "n_clicks"),
    Input("btn-add-cat-despesa", "n_clicks"),
    Input({"type": "btn-delete-category", "index": ALL}, "n_clicks"),
    State("input-cat-receita", "value"),
    State("input-cat-despesa", "value"),
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
    icon_receita: Optional[str],
    icon_despesa: Optional[str],
):
    """
    Gerencia adição e remoção de categorias (apenas banco de dados).

    Não renderiza conteúdo, apenas atualiza o banco e sinaliza via Store.
    O callback render_tab_content escuta o Store e recarrega a aba.

    Identifica qual botão foi clicado usando ctx.triggered_id:
    - Se foi btn-add-cat-receita: adiciona categoria de receita com ícone
    - Se foi btn-add-cat-despesa: adiciona categoria de despesa com ícone
    - Se foi btn-delete-category: remove categoria pelo ID

    Args:
        n_clicks_add_receita: Cliques no botão adicionar receita.
        n_clicks_add_despesa: Cliques no botão adicionar despesa.
        n_clicks_delete: Lista de cliques em botões de exclusão.
        input_receita: Valor do input de receita.
        input_despesa: Valor do input de despesa.
        icon_receita: Ícone selecionado para receita.
        icon_despesa: Ícone selecionado para despesa.

    Returns:
        (timestamp para Store, input_receita limpo, input_despesa limpo,
         icon_receita limpo, icon_despesa limpo)
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

            logger.info(
                f"➕ Adicionando categoria de receita: {input_receita} "
                f"(ícone: {icon_receita})"
            )
            success, msg = create_category(
                input_receita, tipo="receita", icone=icon_receita
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

            logger.info(
                f"➕ Adicionando categoria de despesa: {input_despesa} "
                f"(ícone: {icon_despesa})"
            )
            success, msg = create_category(
                input_despesa, tipo="despesa", icone=icon_despesa
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
            None,  # Limpar dropdown-icon-receita
            None,  # Limpar dropdown-icon-despesa
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
    Output("select-receita-categoria", "value"),
    Input("btn-salvar-receita", "n_clicks"),
    State("input-receita-valor", "value"),
    State("input-receita-descricao", "value"),
    State("dcc-receita-data", "date"),
    State("dcc-receita-categoria", "value"),
    State("input-receita-origem", "value"),
    State("dropdown-receita-tag", "value"),
    State("check-receita-recorrente", "value"),
    State("select-receita-frequencia", "value"),
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
    pessoa_origem: str,
    tag: Optional[list],
    is_recorrente: List,
    frequencia_recorrencia: str,
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
        pessoa_origem: Pessoa/entidade de origem.
        tag: Tags opcionais para entidade/agrupamento (ex: ['Mãe', 'Saúde']).
             Pode ser uma lista (multi=True) ou None. Será salvo como CSV se houver múltiplas.
        is_recorrente: Lista com valor 1 se recorrente, vazia se não.
        frequencia_recorrencia: Frequência (mensal, quinzenal, semanal).
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, timestamp).
    """

    logger.info(f"💾 Salvando receita: {descricao} - R${valor} (tag={tag})")

    if not all([valor, descricao, data, categoria_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update

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
            pessoa_origem=pessoa_origem,
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
            return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("alerta-modal", "is_open", allow_duplicate=True),
    Output("alerta-modal", "children", allow_duplicate=True),
    Output("modal-transacao", "is_open", allow_duplicate=True),
    Output("store-transacao-salva", "data", allow_duplicate=True),
    Output("input-despesa-descricao", "value"),
    Output("input-despesa-valor", "value"),
    Output("dropdown-despesa-tag", "value"),
    Output("select-despesa-categoria", "value"),
    Input("btn-salvar-despesa", "n_clicks"),
    State("input-despesa-valor", "value"),
    State("input-despesa-descricao", "value"),
    State("dcc-despesa-data", "date"),
    State("dcc-despesa-categoria", "value"),
    State("select-despesa-pagamento", "value"),
    State("input-despesa-parcelas", "value"),
    State("dropdown-despesa-tag", "value"),
    State("check-despesa-recorrente", "value"),
    State("select-despesa-frequencia", "value"),
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
    forma_pagamento: str,
    numero_parcelas: int,
    tag: Optional[list],
    is_recorrente: List,
    frequencia_recorrencia: str,
    modal_is_open: bool,
):
    """
    Salva uma nova despesa no banco de dados.

    Suporta parcelamento, forma de pagamento, recorrência e associação a tags
    múltiplas. Atualiza store-transacao-salva ao salvar com sucesso, sinalizando
    a atualização dos componentes dependentes (Fluxo de Caixa, Abas).

    Args:
        n_clicks: Número de cliques no botão.
        valor: Valor da despesa.
        descricao: Descrição da despesa.
        data: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        forma_pagamento: Forma de pagamento (dinheiro, pix, credito, etc).
        numero_parcelas: Número de parcelas (default 1).
        tag: Tags opcionais para entidade/agrupamento (ex: ['Mãe', 'Saúde']).
             Pode ser uma lista (multi=True) ou None. Será salvo como CSV se houver múltiplas.
        is_recorrente: Lista com valor 1 se recorrente, vazia se não.
        frequencia_recorrencia: Frequência (mensal, quinzenal, semanal).
        modal_is_open: Estado atual do modal.

    Returns:
        Tuple (alerta_aberto, mensagem_alerta, modal_aberto, timestamp).
    """

    logger.info(f"💾 Salvando despesa: {descricao} - R${valor} (tag={tag})")

    if not all([valor, descricao, data, categoria_id]):
        msg_erro = "❌ Preencha todos os campos obrigatórios!"
        logger.warning(f"⚠️ {msg_erro}")
        return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    try:
        from datetime import datetime

        data_obj = datetime.strptime(data, "%Y-%m-%d").date()
        eh_recorrente = len(is_recorrente) > 0 if is_recorrente else False
        num_parcelas = (
            int(numero_parcelas) if numero_parcelas and numero_parcelas > 0 else 1
        )

        success, message = create_transaction(
            tipo="despesa",
            descricao=descricao,
            valor=float(valor),
            data=data_obj,
            categoria_id=int(categoria_id),
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
            return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    except Exception as e:
        msg_erro = f"❌ Erro ao salvar: {str(e)}"
        logger.error(f"✗ {msg_erro}", exc_info=True)
        return True, msg_erro, True, 0, dash.no_update, dash.no_update, dash.no_update, dash.no_update


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
    Output("input-despesa-parcelas", "style"),
    Input("select-despesa-pagamento", "value"),
    prevent_initial_call=True,
)
def toggle_parcelas_visibility(forma_pagamento: str) -> Dict:
    """
    Controla visibilidade do campo de parcelas baseado na forma de pagamento.

    Mostra o campo de parcelas apenas quando a forma de pagamento é 'crédito'.

    Args:
        forma_pagamento: Forma de pagamento selecionada.

    Returns:
        Dict com propriedade 'display' para CSS.
    """
    if forma_pagamento and forma_pagamento.lower() == "credito":
        logger.debug("💳 Mostrando campo de parcelas (Crédito selecionado)")
        return {"display": "block"}
    logger.debug("🚫 Ocultando campo de parcelas")
    return {"display": "none"}


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


if __name__ == "__main__":
    # ===== INICIALIZAÇÃO AUTOMÁTICA DO BANCO DE DADOS =====
    print("\n" + "=" * 70)
    print("🚀 INICIANDO FINANCETSK")
    print("=" * 70)

    logger.info("🔧 Inicializando banco de dados...")
    try:
        logger.info("📁 Verificando estrutura de diretórios...")
        init_database()
        logger.info("✅ Banco de dados pronto!")
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
    logger.info("🚀 Iniciando servidor FinanceTSK em http://localhost:8050")
    print("🚀 Servidor rodando em: http://localhost:8050")
    print("=" * 70 + "\n")

    try:
        app.run_server(debug=True, host="localhost", port=8050)
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}", exc_info=True)
        print(f"\n❌ Erro ao iniciar servidor: {e}\n")
        raise
