import logging
from typing import List, Dict, Union, Tuple

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
from dash import State
from dash.exceptions import PreventUpdate
from datetime import date

from src.database.connection import get_db
from src.database.models import Categoria
from src.components.forms import transaction_form
from src.database.operations import create_transaction

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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


# Layout da aplicação
app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1("FinanceTSK", className="text-center mt-5 mb-5"), width=12)
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
) -> Tuple[
    Tuple[str, bool],
    Tuple[str, bool],
    str,
    Union[float, None],
]:
    """
    Salva uma nova despesa no banco de dados.

    Converte os dados do formulário para os tipos apropriados,
    valida os campos e persiste a transação no banco de dados.

    Args:
        n_clicks: Número de cliques no botão.
        descricao: Descrição da despesa.
        valor: Valor da despesa.
        data_str: Data em formato YYYY-MM-DD.
        categoria_id: ID da categoria.
        tags: Tags separadas por vírgula.

    Returns:
        Tupla com mensagens de alerta (sucesso e erro) e campos limpos.
    """
    if n_clicks is None:
        raise PreventUpdate

    logger.info("Tentando salvar nova despesa...")

    try:
        # Converter valor para float
        valor_convertido = float(valor) if valor else 0.0

        # Converter data de string para objeto date
        data_objeto = date.fromisoformat(data_str)

        # Chamar função para criar transação
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
                f"✓ Despesa salva com sucesso: {descricao} - R$ {valor_convertido}"
            )
            return (
                (mensagem, True),  # alerta-sucesso
                ("", False),  # alerta-erro
                "",  # limpar descricao
                None,  # limpar valor
            )
        else:
            logger.warning(f"✗ Erro ao salvar despesa: {mensagem}")
            return (
                ("", False),  # alerta-sucesso
                (mensagem, True),  # alerta-erro
                descricao,  # manter descricao
                valor,  # manter valor
            )

    except ValueError as e:
        mensagem_erro = f"Erro ao converter dados: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            ("", False),  # alerta-sucesso
            (mensagem_erro, True),  # alerta-erro
            descricao,  # manter descricao
            valor,  # manter valor
        )
    except Exception as e:
        mensagem_erro = f"Erro inesperado: {str(e)}"
        logger.error(f"✗ {mensagem_erro}")
        return (
            ("", False),  # alerta-sucesso
            (mensagem_erro, True),  # alerta-erro
            descricao,  # manter descricao
            valor,  # manter valor
        )


if __name__ == "__main__":
    app.run_server(debug=True)
