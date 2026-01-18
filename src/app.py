import logging
from typing import List, Dict, Union, Tuple

import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output
from dash import State
from dash.exceptions import PreventUpdate
from datetime import date
from dash import callback_context

from src.database.connection import get_db
from src.database.models import Categoria
from src.components.forms import transaction_form
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
            logger.info(f"✓ {len(opcoes)} categorias carregadas com sucesso")
            return opcoes
    except Exception as e:
        logger.error(f"✗ Erro ao carregar categorias: {e}")
        return []


def render_transactions_table() -> dbc.Table:
    """
    Renders a table with recent transactions.

    Fetches all transactions from database and formats them
    into a styled Bootstrap table with monetary formatting.

    Returns:
        dbc.Table component with transaction data or empty message.
    """
    try:
        transacoes = get_transactions()

        if not transacoes:
            return html.P(
                "Nenhuma transação registrada.",
                className="text-muted mt-3",
            )

        # Converter lista de dicts para DataFrame
        df = pd.DataFrame(transacoes)

        # Remover colunas que contêm objetos/dicts (categoria, tags, etc)
        colunas_escalares = [
            "data",
            "descricao",
            "valor",
            "tipo",
        ]
        df = df[[col for col in colunas_escalares if col in df.columns]]

        # Formatar valor como moeda brasileira
        df["valor"] = df["valor"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        # Renomear colunas para português
        df = df.rename(
            columns={
                "data": "Data",
                "descricao": "Descrição",
                "valor": "Valor",
                "tipo": "Tipo",
            }
        )

        return dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-3",
        )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar tabela: {e}")
        return html.P(
            "Erro ao carregar transações.",
            className="text-danger mt-3",
        )


# Layout da aplicação
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1("FinanceTSK", className="text-center mt-5 mb-5"),
                width=12,
            )
        ),
        dbc.Row(
            dbc.Col(
                transaction_form(tipo="despesa"),
                width=12,
                md=8,
                className="mx-auto",
            )
        ),
        dbc.Alert(
            id="alerta-sucesso",
            is_open=False,
            duration=4000,
            color="success",
            className="mt-4",
        ),
        dbc.Alert(
            id="alerta-erro",
            is_open=False,
            duration=4000,
            color="danger",
            className="mt-4",
        ),
        html.H4("Últimas Movimentações", className="mt-4"),
        html.Div(id="tabela-transacoes"),
    ],
    fluid=True,
    className="mt-4",
)


@callback(
    [
        [Output("alerta-sucesso", "children"), Output("alerta-sucesso", "is_open")],
        [Output("alerta-erro", "children"), Output("alerta-erro", "is_open")],
        Output("input-despesa-descricao", "value"),
        Output("input-despesa-valor", "value"),
        Output("tabela-transacoes", "children"),
    ],
    Input("btn-salvar-despesa", "n_clicks"),
    Input("tabela-transacoes", "id"),
    [
        State("input-despesa-descricao", "value"),
        State("input-despesa-valor", "value"),
        State("dcc-despesa-data", "date"),
        State("dcc-despesa-categoria", "value"),
        State("input-despesa-tags", "value"),
    ],
    prevent_initial_call=False,
)
def atualizar_transacoes(
    n_clicks: Union[int, None],
    tabela_id: str,
    descricao: str,
    valor: Union[float, None],
    data_str: str,
    categoria_id: int,
    tags: str,
) -> Tuple[
    Tuple[str, bool],
    Tuple[str, bool],
    str,
    Union[float, None],
    dbc.Table,
]:
    """
    Atualiza tabela ao carregar página ou salvar despesa.

    Distingue entre carregamento inicial e salvamento usando
    callback_context para executar lógica apropriada.

    Returns:
        Tupla com alertas, campos limpos e tabela atualizada.
    """
    ctx = callback_context
    
    # Carregamento inicial da página
    if not ctx.triggered or ctx.triggered[0]["prop_id"] == "tabela-transacoes.id":
        logger.info("Carregando tabela inicial...")
        return (
            ("", False),
            ("", False),
            "",
            None,
            render_transactions_table(),
        )

    # Salvamento de despesa
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

        tabela_atualizada = render_transactions_table()

        if sucesso:
            logger.info(f"✓ Despesa salva: {descricao} - R$ {valor_convertido}")
            return (
                (mensagem, True),
                ("", False),
                "",
                None,
                tabela_atualizada,
            )
        else:
            logger.warning(f"✗ Erro ao salvar despesa: {mensagem}")
            return (
                ("", False),
                (mensagem, True),
                descricao,
                valor,
                tabela_atualizada,
            )

    except ValueError as e:
        mensagem_erro = f"Erro ao converter dados: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            ("", False),
            (mensagem_erro, True),
            descricao,
            valor,
            render_transactions_table(),
        )
    except Exception as e:
        mensagem_erro = f"Erro inesperado: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            ("", False),
            (mensagem_erro, True),
            descricao,
            valor,
            render_transactions_table(),
        )


if __name__ == "__main__":
    app.run_server(debug=True)
