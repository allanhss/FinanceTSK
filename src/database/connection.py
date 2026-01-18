"""
Módulo de conexão SQLAlchemy com banco de dados SQLite.

Gerencia a criação e configuração do engine, sessions e modelos
declarativos para o aplicativo FinanceTSK.
"""

import logging
import os
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

# Obter caminho dos dados do arquivo .env
DATA_PATH = os.getenv("DATA_PATH", str(Path.home() / "OneDrive" / "FinanceTSK"))

# Garantir que o diretório de dados existe
diretorio_dados = Path(DATA_PATH)
diretorio_dados.mkdir(parents=True, exist_ok=True)

# URL do banco de dados SQLite
DATABASE_URL = f"sqlite:///{diretorio_dados / 'finance.db'}"

# Criar engine SQLAlchemy
engine: Engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, echo=False, future=True
)

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

    Raises:
        Exception: Se a criação do banco falhar

    Example:
        >>> init_database()
        >>> logger.info("Banco de dados inicializado com sucesso")
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Banco de dados inicializado com sucesso em {DATABASE_URL}")
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
