import sys
import os
from pathlib import Path

# --- FIX DE IMPORTAÇÃO ---
# Adiciona a raiz do projeto ao path para conseguir importar 'src'
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
# -------------------------

import logging
from typing import List, Tuple
from sqlalchemy import inspect

from src.database.connection import SessionLocal, init_database, engine
from src.database.models import Categoria

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Dados iniciais de categorias
CATEGORIAS_PADRAO: List[Tuple[str, str, str]] = [
    ("Alimentação", "🍔", "#22C55E"),
    ("Transporte", "🚗", "#3B82F6"),
    ("Moradia", "🏠", "#F59E0B"),
    ("Lazer", "🎮", "#8B5CF6"),
    ("Saúde", "⚕️", "#EF4444"),
    ("Educação", "📚", "#06B6D4"),
    ("Outros", "❓", "#6B7280"),
    ("Investimentos", "📈", "#10B981"),
]


def categoria_existe(sessao, nome: str) -> bool:
    """Verifica se uma categoria com o nome já existe no banco."""
    # Nota: Usando estilo legacy query() que é mais simples, mas funcional
    resultado = sessao.query(Categoria).filter(Categoria.nome == nome).first()
    return resultado is not None


def criar_categoria(sessao, nome: str, icone: str, cor: str) -> bool:
    """Cria uma nova categoria no banco de dados com tratamento de erro."""
    try:
        nova_categoria = Categoria(nome=nome, icone=icone, cor=cor)
        sessao.add(nova_categoria)
        sessao.commit()
        logger.info(f"✓ Categoria '{nome}' criada com sucesso")
        return True
    except Exception as e:
        sessao.rollback()
        logger.error(f"✗ Erro ao criar categoria '{nome}': {e}")
        return False


def seed_database() -> None:
    """
    Popula o banco de dados com categorias padrão.
    """
    sessao = SessionLocal()

    try:
        logger.info("🌱 Iniciando população do banco de dados...")
        logger.info(f"Processando {len(CATEGORIAS_PADRAO)} categorias padrão")

        categorias_criadas = 0
        categorias_existentes = 0

        for nome, icone, cor in CATEGORIAS_PADRAO:
            if categoria_existe(sessao, nome):
                logger.info(f"⊘ Categoria '{nome}' já existe, pulando")
                categorias_existentes += 1
            else:
                if criar_categoria(sessao, nome, icone, cor):
                    categorias_criadas += 1

        logger.info("=" * 60)
        logger.info(f"✓ População concluída!")
        logger.info(f"  → Categorias criadas: {categorias_criadas}")
        logger.info(f"  → Categorias existentes: {categorias_existentes}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Erro fatal ao popular banco: {e}")
    finally:
        sessao.close()
        logger.info("Sessão encerrada")


def reset_database() -> None:
    """
    Reseta o banco de dados removendo a versão antiga e criando um novo
    com o schema atualizado. Útil após mudanças estruturais nos modelos.
    """
    logger.info("🗑️  Removendo banco de dados antigo...")

    db_path = Path.home() / "OneDrive" / "FinanceTSK" / "finance.db"
    if db_path.exists():
        db_path.unlink()
        logger.info(f"✓ Banco removido: {db_path}")
    else:
        logger.info(f"⊘ Banco não encontrado em {db_path}")

    logger.info("\n🔨 Recriando banco de dados com novo schema...")
    init_database()
    logger.info("✓ Banco criado com sucesso")

    logger.info("\n📋 Verificando colunas da tabela transacoes...")
    try:
        inspector = inspect(engine)
        colunas = inspector.get_columns("transacoes")
        for col in colunas:
            logger.info(f"  - {col['name']}: {col['type']}")
    except Exception as e:
        logger.warning(f"Não foi possível inspecionar tabela: {e}")

    logger.info("\n✅ Banco de dados recriado com sucesso!")


if __name__ == "__main__":
    reset_database()
    seed_database()
