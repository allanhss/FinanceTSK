"""
Módulo de conexão SQLAlchemy com banco de dados SQLite.

Gerencia a criação e configuração do engine, sessions e modelos
declarativos para o aplicativo FinanceTSK.
"""

import logging
import os
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logger
logger = logging.getLogger(__name__)


# ===== DETECÇÃO ROBUSTA DE AMBIENTE DE TESTE =====
def is_test_env() -> bool:
    """
    Detecta automaticamente se estamos em um ambiente de teste.

    Verifica múltiplas condições para garantir proteção do banco de produção:
    1. Variável de ambiente TESTING_MODE explicitamente setada
    2. Execução via pytest (pytest em sys.modules)
    3. Script em execução está na pasta /tests ou \tests

    Returns:
        bool: True se em ambiente de teste, False caso contrário.
    """
    # Condição 1: Verificar variável de ambiente explícita
    if os.environ.get("TESTING_MODE") == "1":
        return True

    # Condição 2: Verificar se rodando via pytest
    if "pytest" in sys.modules:
        return True

    # Condição 3: Verificar se script em execução está em pasta /tests ou \tests
    try:
        script_path = os.path.abspath(sys.argv[0])
        # Normalizar path separators para verificação
        normalized_path = script_path.replace("\\", "/")
        if "/tests/" in normalized_path:
            return True
    except (IndexError, Exception):
        # Falhar de forma segura
        pass

    return False


# Determinar se estamos em ambiente de teste
TESTING_MODE = is_test_env()

# Log da detecção
if TESTING_MODE:
    try:
        print(
            "[TESTE] MODO TESTE DETECTADO (Script em /tests ou ENV setado). Usando: test_finance.db"
        )
    except (UnicodeEncodeError, Exception):
        print("[TEST] TEST MODE DETECTED. Using: test_finance.db")
    logger.warning(
        "MODO TESTE DETECTADO - Usando banco de teste para proteção de dados"
    )

# ===== DEFINIÇÃO ROBUSTA DO CAMINHO DO BANCO DE DADOS =====
# Obter caminho da raiz do projeto (diretório acima de src/)
PROJETO_RAIZ = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
logger.info(f"📁 Raiz do projeto: {PROJETO_RAIZ}")

# Diretório de dados
DIRETORIO_DADOS = os.path.join(PROJETO_RAIZ, "data")

# Criar diretório se não existir (apenas em modo normal)
if not TESTING_MODE:
    try:
        os.makedirs(DIRETORIO_DADOS, exist_ok=True)
        logger.info(f"📁 Diretório de dados criado/verificado: {DIRETORIO_DADOS}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar diretório de dados: {e}")
        raise

# Caminho completo do banco de dados
if TESTING_MODE:
    # Use banco de teste em modo de testes
    CAMINHO_BANCO = os.path.join(PROJETO_RAIZ, "test_finance.db")
    logger.warning("TESTE: Banco de teste isolado em uso")
    logger.warning(f"   Caminho: {CAMINHO_BANCO}")
else:
    CAMINHO_BANCO = os.path.join(DIRETORIO_DADOS, "finance.db")
    logger.info(f"PRODUCAO: Banco de dados será salvo em: {CAMINHO_BANCO}")

# Alternativa: Ler DATA_PATH do .env se existir
DATA_PATH_ENV = os.getenv("DATA_PATH", None)
if DATA_PATH_ENV and not TESTING_MODE:
    logger.debug(f"DATA_PATH encontrado no .env: {DATA_PATH_ENV}")

# URL do banco de dados SQLite (com caminho absoluto)
DATABASE_URL = f"sqlite:///{CAMINHO_BANCO}"
logger.debug(f"DATABASE_URL: {DATABASE_URL}")

# Criar engine SQLAlchemy
try:
    engine: Engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )
    logger.info("✅ Engine SQLAlchemy criado com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao criar engine: {e}")
    raise

# Configurar sessionmaker
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base declarativa para os modelos
Base = declarative_base()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Obtém uma sessão do banco de dados usando context manager.

    Fornece uma sessão que automaticamente realiza commit/rollback
    e gerencia a limpeza de recursos.

    Yields:
        Session: Sessão SQLAlchemy do banco de dados

    Example:
        >>> with get_db() as session:
        ...     transacao = session.query(Transacao).first()
        ...     print(transacao.descricao)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na sessão do banco de dados: {e}")
        raise
    finally:
        session.close()


def init_database() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas.

    Cria todas as tabelas definidas nos modelos SQLAlchemy caso
    não existam. Deve ser chamada uma vez na inicialização da
    aplicação.

    Após criar as tabelas, executa a inicialização de categorias
    padrão se o banco estiver vazio.

    Raises:
        Exception: Se a criação do banco falhar

    Example:
        >>> init_database()
        >>> logger.info("Banco de dados inicializado com sucesso")
    """
    try:
        # Importar modelos para registrá-los no Base
        from src.database import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info(f"Banco de dados inicializado com sucesso em {DATABASE_URL}")

        # Auto-inicializar categorias padrão se banco estiver vazio
        from src.database.operations import (
            initialize_default_categories,
            ensure_fallback_categories,
            ensure_default_accounts,
        )

        success, msg = initialize_default_categories()
        if success:
            logger.info(msg)

        # Garantir que categorias de fallback existem para importação
        success, msg = ensure_fallback_categories()
        if success:
            logger.info(msg)

        # Garantir que contas padrão existem para compatibilidade
        success, msg = ensure_default_accounts()
        if success:
            logger.info(msg)

    except Exception as e:
        logger.error(f"Falha ao inicializar banco de dados: {e}")
        raise


def get_engine() -> Engine:
    """
    Retorna a instância do engine SQLAlchemy.

    Returns:
        Engine: Engine do banco de dados SQLAlchemy

    Example:
        >>> engine = get_engine()
        >>> with engine.connect() as connection:
        ...     resultado = connection.execute(text("SELECT 1"))
    """
    return engine


if __name__ == "__main__":
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        # Inicializar banco de dados
        print("Inicializando banco de dados...")
        init_database()

        # Testar conexão com context manager
        print("Testando conexão com session...")
        with get_db() as session:
            # Verificar se a sessão foi criada com sucesso
            print(f"✓ Session criada: {session}")
            print(f"✓ Engine ativo: {get_engine()}")

        print("✓ Conexão OK!")
        print(f"✓ Banco de dados em: {DATABASE_URL}")

    except Exception as e:
        print(f"✗ Erro ao testar conexão: {e}")
        logger.error(f"Erro no teste de conexão: {e}")
        exit(1)
