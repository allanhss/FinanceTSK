import logging
from typing import List, Dict, Union, Tuple

import dash
import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State, dcc
from dash.exceptions import PreventUpdate
from datetime import date

from src.database.connection import get_db
from src.database.models import Categoria
from src.components.forms import transaction_form
from src.components.tables import render_transactions_table
from src.database.operations import (
    create_transaction,
    get_transactions,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Inicializar aplicação Dash com tema Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

app.title = "FinanceTSK"


def get_category_options() -> List[Dict[str, Union[str, int]]]:
    """
    Fetches all categories from database for dropdown.

    Connects to the database and retrieves all available categories,
    formatting them for use in a dcc.Dropdown component.

    Returns:
        List of dicts with 'label' (category name) and 'value' (id).
        Returns empty list if error occurs.

    Raises:
        Logs errors but doesn't raise exceptions to prevent app crash.
    """
    try:
        with get_db() as session:
            categorias = session.query(Categoria).all()
            opcoes = [
                {"label": categoria.nome, "value": categoria.id}
                for categoria in categorias
            ]
            logger.info(
                f"✓ {len(opcoes)} categorias carregadas com sucesso"
            )
            return opcoes
    except Exception as e:
        logger.error(f"✗ Erro ao carregar categorias: {e}")
        return []


# Layout da aplicação
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("FinanceTSK", className="text-center mt-5 mb-5"),
                width=12,
            )
        ),
        dcc.Tabs(
            id="tabs-tipo-transacao",
            value="tab-despesas",
            children=[
                # ABA DESPESAS
                dcc.Tab(
                    label="Despesas",
                    value="tab-despesas",
                    children=[
                        dbc.Container(
                            [
                                dbc.Row(
                                    dbc.Col(
                                        transaction_form(tipo="despesa"),
                                        width=12,
                                        md=8,
                                        className="mx-auto",
                                    )
                                ),
                                dbc.Alert(
                                    id="alerta-sucesso-despesa",
                                    is_open=False,
                                    duration=4000,
                                    color="success",
                                    className="mt-4",
                                ),
                                dbc.Alert(
                                    id="alerta-erro-despesa",
                                    is_open=False,
                                    duration=4000,
                                    color="danger",
                                    className="mt-4",
                                ),
                                html.H4(
                                    "Últimas Despesas",
                                    className="mt-4",
                                ),
                                html.Div(
                                    id="tabela-transacoes-despesa",
                                    className="mt-3",
                                ),
                            ],
                            fluid=True,
                            className="mt-3",
                        )
                    ],
                ),
                # ABA RECEITAS
                dcc.Tab(
                    label="Receitas",
                    value="tab-receitas",
                    children=[
                        dbc.Container(
                            [
                                dbc.Row(
                                    dbc.Col(
                                        transaction_form(tipo="receita"),
                                        width=12,
                                        md=8,
                                        className="mx-auto",
                                    )
                                ),
                                dbc.Alert(
                                    id="alerta-sucesso-receita",
                                    is_open=False,
                                    duration=4000,
                                    color="success",
                                    className="mt-4",
                                ),
                                dbc.Alert(
                                    id="alerta-erro-receita",
                                    is_open=False,
                                    duration=4000,
                                    color="danger",
                                    className="mt-4",
                                ),
                                html.H4(
                                    "Últimas Receitas",
                                    className="mt-4",
                                ),
                                html.Div(
                                    id="tabela-transacoes-receita",
                                    className="mt-3",
                                ),
                            ],
                            fluid=True,
                            className="mt-3",
                        )
                    ],
                ),
            ],
        ),
        # Store para sinalizar quando salvar
        dcc.Store(id="store-despesa-salva"),
        dcc.Store(id="store-receita-salva"),
    ],
    fluid=True,
    className="mt-4",
)


@callback(
    [
        Output("alerta-sucesso-despesa", "children"),
        Output("alerta-sucesso-despesa", "is_open"),
        Output("alerta-erro-despesa", "children"),
        Output("alerta-erro-despesa", "is_open"),
        Output("input-despesa-descricao", "value"),
        Output("input-despesa-valor", "value"),
        Output("store-despesa-salva", "data"),
    ],
    Input("btn-salvar-despesa", "n_clicks"),
    [
        State("input-despesa-descricao", "value"),
        State("input-despesa-valor", "value"),
        State("dcc-despesa-data", "date"),
        State("dcc-despesa-categoria", "value"),
        State("input-despesa-tags", "value"),
    ],
    prevent_initial_call=True,
)
def salvar_despesa(
    n_clicks: int,
    descricao: str,
    valor: Union[float, None],
    data_str: str,
    categoria_id: int,
    tags: str,
) -> Tuple[str, bool, str, bool, str, Union[float, None], Dict]:
    """
    Salva nova despesa e exibe alertas apropriados.

    Args:
        n_clicks: Número de cliques no botão salvar.
        descricao: Descrição da despesa.
        valor: Valor da despesa.
        data_str: Data em formato ISO.
        categoria_id: ID da categoria selecionada.
        tags: Tags/etiquetas associadas.

    Returns:
        Tupla contendo alertas, campos limpos e sinalização
        para atualizar tabela.
    """
    if n_clicks is None:
        raise PreventUpdate

    logger.info("Tentando salvar nova despesa...")

    try:
        valor_convertido = float(valor) if valor else 0.0
        data_objeto = date.fromisoformat(data_str)

        sucesso, mensagem = create_transaction(
            tipo="despesa",
            descricao=descricao,
            valor=valor_convertido,
            data=data_objeto,
            categoria_id=categoria_id,
            tags=tags,
        )

        if sucesso:
            logger.info(
                f"✓ Despesa salva: {descricao} - R$ {valor_convertido}"
            )
            return (
                mensagem,
                True,
                "",
                False,
                "",
                None,
                {"saved": True},
            )
        else:
            logger.warning(f"✗ Erro ao salvar despesa: {mensagem}")
            return (
                "",
                False,
                mensagem,
                True,
                descricao,
                valor,
                {"saved": False},
            )

    except ValueError as e:
        mensagem_erro = f"Erro ao converter dados: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            "",
            False,
            mensagem_erro,
            True,
            descricao,
            valor,
            {"saved": False},
        )
    except Exception as e:
        mensagem_erro = f"Erro inesperado: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            "",
            False,
            mensagem_erro,
            True,
            descricao,
            valor,
            {"saved": False},
        )


@callback(
    [
        Output("alerta-sucesso-receita", "children"),
        Output("alerta-sucesso-receita", "is_open"),
        Output("alerta-erro-receita", "children"),
        Output("alerta-erro-receita", "is_open"),
        Output("input-receita-descricao", "value"),
        Output("input-receita-valor", "value"),
        Output("store-receita-salva", "data"),
    ],
    Input("btn-salvar-receita", "n_clicks"),
    [
        State("input-receita-descricao", "value"),
        State("input-receita-valor", "value"),
        State("dcc-receita-data", "date"),
        State("dcc-receita-categoria", "value"),
        State("input-receita-tags", "value"),
        State("input-receita-pessoa-origem", "value"),
    ],
    prevent_initial_call=True,
)
def salvar_receita(
    n_clicks: int,
    descricao: str,
    valor: Union[float, None],
    data_str: str,
    categoria_id: int,
    tags: str,
    pessoa_origem: str,
) -> Tuple[str, bool, str, bool, str, Union[float, None], Dict]:
    """
    Salva nova receita e exibe alertas apropriados.

    Args:
        n_clicks: Número de cliques no botão salvar.
        descricao: Descrição da receita.
        valor: Valor da receita.
        data_str: Data em formato ISO.
        categoria_id: ID da categoria selecionada.
        tags: Tags/etiquetas associadas.
        pessoa_origem: Pessoa ou fonte de origem da receita.

    Returns:
        Tupla contendo alertas, campos limpos e sinalização
        para atualizar tabela.
    """
    if n_clicks is None:
        raise PreventUpdate

    logger.info("Tentando salvar nova receita...")

    try:
        valor_convertido = float(valor) if valor else 0.0
        data_objeto = date.fromisoformat(data_str)

        sucesso, mensagem = create_transaction(
            tipo="receita",
            descricao=descricao,
            valor=valor_convertido,
            data=data_objeto,
            categoria_id=categoria_id,
            tags=tags,
            pessoa_origem=pessoa_origem,
        )

        if sucesso:
            logger.info(
                f"✓ Receita salva: {descricao} - R$ {valor_convertido}"
            )
            return (
                mensagem,
                True,
                "",
                False,
                "",
                None,
                {"saved": True},
            )
        else:
            logger.warning(f"✗ Erro ao salvar receita: {mensagem}")
            return (
                "",
                False,
                mensagem,
                True,
                descricao,
                valor,
                {"saved": False},
            )

    except ValueError as e:
        mensagem_erro = f"Erro ao converter dados: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            "",
            False,
            mensagem_erro,
            True,
            descricao,
            valor,
            {"saved": False},
        )
    except Exception as e:
        mensagem_erro = f"Erro inesperado: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            "",
            False,
            mensagem_erro,
            True,
            descricao,
            valor,
            {"saved": False},
        )


@callback(
    Output("tabela-transacoes-despesa", "children"),
    Input("store-despesa-salva", "data"),
)
def atualizar_tabela_despesa(_dados_salvos: Dict) -> Union[dbc.Table, dbc.Alert]:
    """
    Atualiza tabela de despesas após salvar.

    Args:
        _dados_salvos: Sinalização de salvamento no store.

    Returns:
        Tabela renderizada com transações atualizadas.
    """
    logger.info("Atualizando tabela de despesas...")
    todas_transacoes = get_transactions()
    despesas = [
        t for t in todas_transacoes if t.get("tipo") == "despesa"
    ]
    return render_transactions_table(despesas)


@callback(
    Output("tabela-transacoes-receita", "children"),
    Input("store-receita-salva", "data"),
)
def atualizar_tabela_receita(_dados_salvos: Dict) -> Union[dbc.Table, dbc.Alert]:
    """
    Atualiza tabela de receitas após salvar.

    Args:
        _dados_salvos: Sinalização de salvamento no store.

    Returns:
        Tabela renderizada com transações atualizadas.
    """
    logger.info("Atualizando tabela de receitas...")
    todas_transacoes = get_transactions()
    receitas = [
        t for t in todas_transacoes if t.get("tipo") == "receita"
    ]
    return render_transactions_table(receitas)


if __name__ == "__main__":
    app.run_server(debug=True)
