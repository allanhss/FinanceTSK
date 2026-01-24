"""
Script para resetar o banco de dados.

AVISO: Este script DELETA todos os dados do banco de dados e reinicializa
o schema. Use apenas para desenvolvimento e testes.

Uso:
    python tests/reset_db.py

O script executará:
    1. Drop de todas as tabelas existentes
    2. Recriação do schema
    3. Inicialização com dados padrão (categorias, contas)
"""

import logging
import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database.connection import Base, engine, get_db
from src.database.models import Categoria, Conta
from src.utils.init_data import init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def reset_database() -> None:
    """
    Reseta o banco de dados.

    Deleta todas as tabelas existentes e recria o schema com dados padrão.
    Isso é útil para:
    - Limpar dados de teste
    - Restaurar schema para estado padrão
    - Preparar banco para nova carga de dados

    Raises:
        Exception: Se houver erro ao dropar ou criar tabelas
    """
    logger.warning("=" * 70)
    logger.warning("AVISO: TODOS OS DADOS SERÃO DELETADOS")
    logger.warning("=" * 70)

    try:
        # Drop all tables
        logger.info("Deletando todas as tabelas...")
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ Tabelas deletadas")

        # Recreate schema
        logger.info("Recriando schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Schema recriado")

        # Initialize default data
        logger.info("Inicializando dados padrão...")
        init_database()

        # Initialize accounts
        from src.utils.init_data import ensure_default_accounts

        ensure_default_accounts()

        logger.info("✓ Dados padrão inicializados")

        # Verify database state
        with get_db() as session:
            categoria_count = session.query(Categoria).count()
            conta_count = session.query(Conta).count()

        logger.info("=" * 70)
        logger.info("✓ RESET CONCLUÍDO COM SUCESSO")
        logger.info("=" * 70)
        logger.info(f"  • Categorias inicializadas: {categoria_count}")
        logger.info(f"  • Contas padrão: {conta_count}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Erro ao resetar banco de dados: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    reset_database()
