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
from src.database.models import Categoria, Conta

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


def categoria_existe(sessao, nome: str, tipo: str = None) -> bool:
    """Verifica se uma categoria com o nome já existe no banco.

    Args:
        sessao: Sessão SQLAlchemy
        nome: Nome da categoria
        tipo: Tipo opcional (receita/despesa). Se None, verifica qualquer tipo

    Returns:
        True se a categoria existe, False caso contrário
    """
    query = sessao.query(Categoria).filter(Categoria.nome == nome)
    if tipo:
        query = query.filter(Categoria.tipo == tipo)
    return query.first() is not None


def criar_categoria(
    sessao,
    nome: str,
    icone: str,
    cor: str,
    tipo: str = "despesa",
    teto_mensal: float = 0.0,
) -> bool:
    """Cria uma nova categoria no banco de dados com tratamento de erro.

    Args:
        sessao: Sessão SQLAlchemy
        nome: Nome da categoria
        icone: Emoji ou ícone
        cor: Cor em hexadecimal (#RRGGBB)
        tipo: Tipo de categoria (receita/despesa). Padrão: despesa
        teto_mensal: Teto mensal. Padrão: 0.0

    Returns:
        True se criado com sucesso, False caso contrário
    """
    try:
        nova_categoria = Categoria(
            nome=nome,
            icone=icone,
            cor=cor,
            tipo=tipo,
            teto_mensal=teto_mensal,
        )
        sessao.add(nova_categoria)
        sessao.commit()
        logger.info(f"✓ Categoria '{nome}' ({tipo}) criada com sucesso")
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


def ensure_default_accounts() -> None:
    """
    Garante que as contas padrão existam no banco de dados.

    Cria contas iniciais para:
    - Conta corrente padrão
    - Investimentos
    """
    sessao = SessionLocal()

    try:
        logger.info("[SETUP] Verificando contas padrão...")

        # Contas padrão
        contas_padrao = [
            {"nome": "Conta Padrão", "tipo": "conta", "saldo_inicial": 0.0},
            {"nome": "Investimentos", "tipo": "investimento", "saldo_inicial": 0.0},
        ]

        criadas = 0
        existentes = 0

        for conta_info in contas_padrao:
            nome = conta_info["nome"]
            conta_existe = sessao.query(Conta).filter_by(nome=nome).first() is not None

            if conta_existe:
                logger.info(f"[SETUP] Conta '{nome}' já existe")
                existentes += 1
            else:
                try:
                    nova_conta = Conta(
                        nome=nome,
                        tipo=conta_info["tipo"],
                        saldo_inicial=conta_info["saldo_inicial"],
                    )
                    sessao.add(nova_conta)
                    sessao.commit()
                    criadas += 1
                    logger.info(
                        f"[SETUP] Conta padrão '{nome}' ({conta_info['tipo']}) criada"
                    )
                except Exception as e:
                    sessao.rollback()
                    logger.error(f"[SETUP] Erro ao criar conta '{nome}': {e}")

        logger.info(
            f"[SETUP] Contas padrão prontas "
            f"(criadas: {criadas}, existentes: {existentes})"
        )

    except Exception as e:
        logger.error(f"[SETUP] Erro ao garantir contas padrão: {e}", exc_info=True)
    finally:
        sessao.close()


def ensure_default_categories() -> None:
    """
    Garante que as categorias padrão de fallback existam no banco de dados.

    Essa função é chamada durante a inicialização da aplicação para garantir
    que as categorias de classificação padrão ("A Classificar") existam,
    evitando erros de chave estrangeira ao salvar transações importadas.

    Cria três categorias:
    - "A Classificar" (tipo: despesa) - Para despesas sem categoria
    - "A Classificar" (tipo: receita) - Para receitas sem categoria
    - "Transferência Interna" (tipo: despesa) - Para movimentações entre contas

    Se as categorias já existirem, apenas registra no log e não faz nada.

    Raises:
        Nenhuma exceção é levantada; erros são apenas registrados em log.
    """
    sessao = SessionLocal()

    try:
        logger.info("[SETUP] Verificando categorias de fallback...")

        # Categorias de fallback a serem criadas
        categorias_fallback = [
            {
                "nome": "A Classificar",
                "tipo": "despesa",
                "icone": "📂",
                "cor": "#6c757d",
                "teto_mensal": 0.0,
            },
            {
                "nome": "A Classificar",
                "tipo": "receita",
                "icone": "📂",
                "cor": "#6c757d",
                "teto_mensal": 0.0,
            },
            {
                "nome": "Transferência Interna",
                "tipo": "despesa",
                "icone": "🔄",
                "cor": "#6f42c1",
                "teto_mensal": 0.0,
            },
        ]

        criadas = 0
        existentes = 0

        for cat_info in categorias_fallback:
            nome = cat_info["nome"]
            tipo = cat_info["tipo"]

            if categoria_existe(sessao, nome, tipo):
                logger.info(
                    f"[SETUP] Categoria fallback '{nome}' " f"({tipo}) já existe"
                )
                existentes += 1
            else:
                if criar_categoria(
                    sessao=sessao,
                    nome=nome,
                    icone=cat_info["icone"],
                    cor=cat_info["cor"],
                    tipo=tipo,
                    teto_mensal=cat_info["teto_mensal"],
                ):
                    criadas += 1
                    logger.info(
                        f"[SETUP] Categoria fallback '{nome}' "
                        f"({tipo}) criada com sucesso"
                    )

        logger.info(
            f"[SETUP] Categorias de fallback prontas "
            f"(criadas: {criadas}, existentes: {existentes})"
        )

    except Exception as e:
        logger.error(
            f"[SETUP] Erro ao garantir categorias de fallback: {e}",
            exc_info=True,
        )
    finally:
        sessao.close()


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
