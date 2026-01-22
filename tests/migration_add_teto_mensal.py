"""
Script de migração para adicionar coluna teto_mensal à tabela categorias.

Executa: python -m tests.migration_add_teto_mensal

Este script é seguro para executar múltiplas vezes e tratará:
- Banco de dados vazio (criará novo com schema correto)
- Banco de dados existente sem coluna teto_mensal (adicionará coluna)
- Banco de dados já atualizado (não fará nada)
"""

import logging
import sqlite3
from pathlib import Path
from typing import Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Caminhos possíveis do banco de dados
POSSIBLE_DB_PATHS = [
    Path(__file__).parent.parent / "data" / "finance.db",
    Path(__file__).parent.parent / "data" / "financetsk.db",
]


def find_database() -> Path | None:
    """Encontra o banco de dados existente."""
    for db_path in POSSIBLE_DB_PATHS:
        if db_path.exists():
            logger.info(f"Banco encontrado em: {db_path}")
            return db_path
    logger.info("Nenhum banco existente encontrado")
    return None


def check_column_exists(db_path: Path) -> bool:
    """Verifica se a coluna teto_mensal já existe."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Verificar se a tabela existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categorias'"
        )
        if not cursor.fetchone():
            logger.info("Tabela categorias nao existe ainda")
            conn.close()
            return True

        # Verificar se a coluna existe
        cursor.execute("PRAGMA table_info(categorias)")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        return "teto_mensal" in column_names

    except sqlite3.Error as e:
        logger.warning(f"Erro ao verificar coluna: {e}")
        return False


def migrate_add_teto_mensal() -> Tuple[bool, str]:
    """
    Adiciona a coluna teto_mensal à tabela categorias.

    Returns:
        Tupla com (sucesso: bool, mensagem: str)
    """
    db_path = find_database()

    if not db_path:
        logger.info(
            "Banco de dados nao existe ainda. "
            "Sera criado com o schema correto na proxima inicializacao."
        )
        return True, "Banco sera criado com schema correto na inicializacao."

    if check_column_exists(db_path):
        logger.info("Coluna teto_mensal ja existe. Migracao nao necessaria.")
        return True, "Coluna teto_mensal ja existe. Nenhuma acao necessaria."

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        logger.info("Iniciando migracao: adicionando coluna teto_mensal...")

        # Adicionar coluna
        cursor.execute(
            """
            ALTER TABLE categorias
            ADD COLUMN teto_mensal FLOAT NOT NULL DEFAULT 0.0
            """
        )

        conn.commit()
        logger.info("Coluna teto_mensal adicionada com sucesso.")

        # Recuperar quantas categorias foram afetadas
        cursor.execute("SELECT COUNT(*) as total FROM categorias")
        total = cursor.fetchone()["total"]

        # Definir valores padrao para categorias existentes
        # Receitas: Salario, Mesada, Vendas, Investimentos, Outros
        salarios = ["Salario", "Salary"]  # PT e EN
        mesadas = ["Mesada"]
        vendas_list = ["Vendas", "Sales"]
        investimentos = ["Investimentos", "Investments"]

        # Despesas
        alimentacoes = ["Alimentacao", "Food"]
        moradias = ["Moradia", "Housing", "Rent"]
        transportes = ["Transporte", "Transport", "Uber"]
        lazeres = ["Lazer", "Entertainment"]
        saudes = ["Saude", "Health", "Medical"]
        educacoes = ["Educacao", "Education"]

        # Atualizar categorias receita com valores padrao
        for nome in salarios:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 5000.0 WHERE nome = ?",
                (nome,),
            )
        for nome in mesadas:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 500.0 WHERE nome = ?",
                (nome,),
            )
        for nome in vendas_list:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 2000.0 WHERE nome = ?",
                (nome,),
            )
        for nome in investimentos:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 1000.0 WHERE nome = ?",
                (nome,),
            )

        # Atualizar categorias despesa com valores padrao
        for nome in alimentacoes:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 1000.0 WHERE nome = ?",
                (nome,),
            )
        for nome in moradias:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 2000.0 WHERE nome = ?",
                (nome,),
            )
        for nome in transportes:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 500.0 WHERE nome = ?",
                (nome,),
            )
        for nome in lazeres:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 500.0 WHERE nome = ?",
                (nome,),
            )
        for nome in saudes:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 300.0 WHERE nome = ?",
                (nome,),
            )
        for nome in educacoes:
            cursor.execute(
                "UPDATE categorias SET teto_mensal = 800.0 WHERE nome = ?",
                (nome,),
            )

        conn.commit()
        conn.close()

        logger.info(f"Migracao concluida com sucesso. {total} categorias afetadas.")
        return True, f"Migracao concluida. {total} categorias atualizado."

    except sqlite3.Error as e:
        logger.error(f"Erro ao migrar banco de dados: {e}")
        return False, f"Erro ao migrar: {e}"

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return False, f"Erro inesperado: {e}"


if __name__ == "__main__":
    logger.info("=== Script de Migracao: Adicionar teto_mensal ===")
    db = find_database()
    if db:
        logger.info(f"Caminho do banco de dados: {db}")
    else:
        logger.info("Nenhum banco de dados encontrado")

    sucesso, mensagem = migrate_add_teto_mensal()

    if sucesso:
        logger.info(f"SUCESSO: {mensagem}")
    else:
        logger.error(f"FALHA: {mensagem}")
        exit(1)
