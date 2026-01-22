"""
Script para atualizar valores de teto_mensal com base no nome da categoria.

Este script usa a correspondência de nomes com e sem acentos.
"""

import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

# Mapeamento de nomes de categorias para teto_mensal
BUDGET_MAPPINGS = {
    # Receitas
    ("receita", "Sal"): 5000.0,  # Salário
    ("receita", "Mesada"): 500.0,
    ("receita", "Vendas"): 2000.0,
    ("receita", "Investimentos"): 1000.0,
    ("receita", "Outros"): 0.0,
    # Despesas
    ("despesa", "Alimenta"): 1000.0,  # Alimentação
    ("despesa", "Moradia"): 2000.0,
    ("despesa", "Transporte"): 500.0,
    ("despesa", "Lazer"): 500.0,
    ("despesa", "Sa"): 300.0,  # Saúde
    ("despesa", "Educa"): 800.0,  # Educação
    ("despesa", "Outros"): 0.0,
}

if __name__ == "__main__":
    if not DB_PATH.exists():
        logger.error(f"Banco nao encontrado em: {DB_PATH}")
        exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    logger.info("Atualizando valores de teto_mensal...")

    for (tipo, nome_match), valor in BUDGET_MAPPINGS.items():
        cursor.execute(
            """
            UPDATE categorias 
            SET teto_mensal = ? 
            WHERE tipo = ? AND nome LIKE ?
            """,
            (valor, tipo, f"{nome_match}%"),
        )
        rows_affected = cursor.rowcount
        logger.info(
            f"Atualizado {rows_affected} categoria(s) de tipo '{tipo}' com nome como '{nome_match}' para {valor}"
        )

    conn.commit()
    conn.close()

    logger.info("Atualizado com sucesso!")
