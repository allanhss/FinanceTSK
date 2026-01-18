import logging
from typing import List, Dict

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


def render_transactions_table(transacoes: List[Dict]) -> dbc.Table | dbc.Alert:
    """
    Renderiza tabela formatada com transações.

    Converte lista de transações em DataFrame e formata para
    exibição como tabela Bootstrap responsiva. Trata moeda
    brasileira e datas no formato DD/MM/YYYY.

    Args:
        transacoes: Lista de dicionários com dados de transações
            vindos de database/operations.py

    Returns:
        dbc.Table formatada com dados ou dbc.Alert se lista vazia.

    Example:
        >>> transacoes = [
        ...     {
        ...         "data": "2026-01-15",
        ...         "descricao": "Supermercado",
        ...         "valor": 125.50,
        ...         "tipo": "despesa",
        ...         "categoria": {"nome": "Alimentação"},
        ...         "tags": "compras"
        ...     }
        ... ]
        >>> tabela = render_transactions_table(transacoes)
    """
    try:
        # Verificar se lista está vazia
        if not transacoes:
            logger.info("Nenhuma transação encontrada para exibição")
            return dbc.Alert(
                "Nenhuma transação encontrada.",
                color="info",
                className="mt-3",
            )

        # Converter para DataFrame
        df = pd.DataFrame(transacoes)

        # Colunas desejadas na ordem de exibição
        colunas_desejadas = [
            "data",
            "categoria",
            "descricao",
            "valor",
            "tipo",
            "tags",
        ]

        # Manter apenas colunas que existem no DataFrame
        colunas_existentes = [
            col for col in colunas_desejadas if col in df.columns
        ]
        df = df[colunas_existentes]

        # Formatar data para DD/MM/YYYY
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"]).dt.strftime(
                "%d/%m/%Y"
            )

        # Formatar valor como moeda brasileira R$ 1.234,56
        if "valor" in df.columns:
            df["valor"] = df["valor"].apply(
                lambda x: f"R$ {x:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        # Extrair nome da categoria (se vem como objeto/dicionário)
        if "categoria" in df.columns:
            df["categoria"] = df["categoria"].apply(
                lambda x: x["nome"] if isinstance(x, dict) else x
            )

        # Renomear colunas para português
        df = df.rename(
            columns={
                "data": "Data",
                "categoria": "Categoria",
                "descricao": "Descrição",
                "valor": "Valor",
                "tipo": "Tipo",
                "tags": "Tags",
            }
        )

        # Criar tabela Bootstrap
        tabela = dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mt-3",
        )

        logger.info(f"✓ Tabela renderizada com {len(df)} transações")
        return tabela

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar tabela de transações: {e}")
        return dbc.Alert(
            "Erro ao carregar transações. Tente novamente.",
            color="danger",
            className="mt-3",
        )