"""
PyTest Configuration - Isolamento de Banco de Dados para Testes

Este arquivo configura o pytest para garantir que todos os testes
usem um banco de dados isolado e não afetem os dados de produção.
"""

import os
import pytest
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configura o ambiente de teste antes de qualquer teste ser executado.

    Este fixture:
    1. Ativa o modo de teste (TESTING_MODE=1)
    2. Garante que connection.py usará banco de teste
    3. Limpa o banco de teste no início da sessão

    Scope: session (executado uma única vez por sessão de testes)
    Autouse: True (executa automaticamente sem ser chamado)
    """
    logger.info("🧪 Configurando ambiente de teste...")

    # Definir modo de teste ANTES de importar qualquer código que use connection.py
    os.environ["TESTING_MODE"] = "1"
    logger.warning("⚠️  TESTING_MODE=1 configurado")

    # Agora que TESTING_MODE está definido, importar os módulos de banco
    # para garantir que usem a configuração correta
    from src.database.connection import (
        Base,
        engine,
        CAMINHO_BANCO,
        TESTING_MODE,
    )

    logger.info(f"🗄️  Banco de teste: {CAMINHO_BANCO}")
    logger.info(f"🧪 TESTING_MODE ativo: {TESTING_MODE}")

    # Criar todas as tabelas no banco de teste
    logger.info("📋 Criando tabelas do banco de teste...")
    Base.metadata.create_all(engine)
    logger.info("✅ Tabelas criadas com sucesso")

    yield  # Executar todos os testes aqui

    # Limpeza após todos os testes (teardown da sessão)
    logger.info("🧹 Limpando ambiente de teste...")

    # Remover arquivo de banco de teste se desejar limpeza completa
    # (comentado por padrão para permitir investigação pós-teste)
    test_db_path = Path(CAMINHO_BANCO)
    if test_db_path.exists():
        logger.debug(f"Banco de teste mantido em: {CAMINHO_BANCO}")
        # Para limpeza automática, descomente:
        # test_db_path.unlink()
        # logger.info(f"✅ Banco de teste removido: {CAMINHO_BANCO}")

    # Remover TESTING_MODE após os testes
    if "TESTING_MODE" in os.environ:
        del os.environ["TESTING_MODE"]
        logger.info("✅ TESTING_MODE removido")


@pytest.fixture(autouse=True)
def reset_database_state():
    """
    Reseta o estado do banco de dados antes de cada teste individual.

    Este fixture:
    1. Garante que cada teste comece com um banco "limpo"
    2. Previne contaminação entre testes
    3. Executa após setup_test_environment

    Scope: function (executado antes de cada teste)
    Autouse: True (executa automaticamente)
    """
    # Setup: não fazer nada (tabelas já criadas)
    yield

    # Teardown: limpar dados após cada teste
    # (opcional, comentado por padrão para permitir investigação)
    # from src.database.connection import get_db
    # with get_db() as session:
    #     # Limpar todas as tabelas
    #     for table in reversed(Base.metadata.sorted_tables):
    #         session.execute(table.delete())
    #     session.commit()


@pytest.fixture
def test_database():
    """
    Fixture que fornece acesso ao engine de teste.

    Use em testes que precisam de acesso direto ao engine:
    - Criar tabelas customizadas
    - Limpar dados específicos
    - Verificar estado do banco

    Example:
        def test_something(test_database):
            engine = test_database
            # usar engine...
    """
    from src.database.connection import engine

    return engine


@pytest.fixture
def test_session():
    """
    Fixture que fornece uma sessão de teste isolada.

    Use em testes que precisam de uma sessão SQLAlchemy:
    - Executar queries diretas
    - Gerenciar transações
    - Verificar dados após operações

    Example:
        def test_something(test_session):
            # Use test_session para queries...
            result = test_session.query(Model).first()
    """
    from src.database.connection import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# Configurar logging para testes
@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """
    Configura logging mais verboso para testes.
    """
    import logging

    # Aumentar nível de logging para DEBUG em testes
    logging.getLogger("src.database").setLevel(logging.DEBUG)
    logging.getLogger("src").setLevel(logging.DEBUG)

    # Adicionar handler para console
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    for logger_name in ["src.database", "src"]:
        logger_obj = logging.getLogger(logger_name)
        logger_obj.addHandler(handler)
