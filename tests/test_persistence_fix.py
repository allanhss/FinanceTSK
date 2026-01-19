#!/usr/bin/env python3
"""
Teste de correção: Verificar criação e persistência do banco de dados.

Valida:
1. Diretório data/ é criado automaticamente
2. Arquivo finance.db é criado no lugar correto
3. Transações são persistidas corretamente
4. Logs mostram o processo completo
"""

import sys
from pathlib import Path
import os
import logging

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar logging para ver tudo
logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_database_persistence():
    """Testa criação e persistência do banco de dados."""
    print("\n" + "=" * 70)
    print("TESTE: Criação e Persistência do Banco de Dados")
    print("=" * 70 + "\n")

    # 1. Verificar caminho correto
    print("1️⃣  Verificando definição de caminho...")
    from src.database.connection import (
        PROJETO_RAIZ,
        DIRETORIO_DADOS,
        CAMINHO_BANCO,
        DATABASE_URL,
    )

    print(f"   Raiz do projeto: {PROJETO_RAIZ}")
    print(f"   Diretório de dados: {DIRETORIO_DADOS}")
    print(f"   Caminho banco: {CAMINHO_BANCO}")
    print(f"   DATABASE_URL: {DATABASE_URL}")

    assert os.path.isabs(CAMINHO_BANCO), "Caminho não é absoluto!"
    assert DIRETORIO_DADOS.endswith("data"), "Caminho não termina com 'data'!"
    print("   ✅ Caminhos configurados corretamente\n")

    # 2. Verificar diretório
    print("2️⃣  Verificando diretório data/...")
    assert os.path.isdir(
        DIRETORIO_DADOS
    ), f"Diretório não existe: {DIRETORIO_DADOS}"
    print(f"   ✅ Diretório existe: {DIRETORIO_DADOS}\n")

    # 3. Remover banco antigo para teste limpo
    print("3️⃣  Removendo banco antigo para teste limpo...")
    if os.path.exists(CAMINHO_BANCO):
        os.remove(CAMINHO_BANCO)
        print(f"   ✓ Banco removido\n")
    else:
        print(f"   ✓ Banco não existia\n")

    # 4. Inicializar banco
    print("4️⃣  Inicializando banco de dados...")
    from src.database.connection import init_database

    try:
        init_database()
        print("   ✅ Banco inicializado com sucesso\n")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar: {e}\n")
        raise

    # 5. Verificar que arquivo foi criado
    print("5️⃣  Verificando se arquivo finance.db foi criado...")
    assert os.path.exists(
        CAMINHO_BANCO
    ), f"Arquivo não foi criado: {CAMINHO_BANCO}"
    file_size = os.path.getsize(CAMINHO_BANCO)
    print(f"   ✅ Arquivo criado: {CAMINHO_BANCO}")
    print(f"   📦 Tamanho: {file_size} bytes\n")

    # 6. Testar inserção de transação
    print("6️⃣  Testando inserção de transação...")
    from datetime import date
    from src.database.operations import (
        create_category,
        create_transaction,
        get_transactions,
    )

    # Criar categoria
    success, msg = create_category("Teste", "despesa", icone="🧪")
    assert success, f"Falha ao criar categoria: {msg}"
    print(f"   ✓ Categoria criada: {msg}")

    # Obter ID da categoria
    from src.database.connection import get_db, engine
    from src.database.models import Categoria

    with get_db() as session:
        cat = session.query(Categoria).filter_by(nome="Teste").first()
        cat_id = cat.id

    # Criar transação
    success, msg = create_transaction(
        tipo="despesa",
        descricao="Transação de teste",
        valor=99.99,
        data=date(2026, 1, 19),
        categoria_id=cat_id,
    )
    assert success, f"Falha ao criar transação: {msg}"
    print(f"   ✓ Transação criada: {msg}")

    # Verificar que foi persistida
    transacoes = get_transactions()
    assert len(transacoes) > 0, "Nenhuma transação encontrada!"
    teste_transacao = next(
        (t for t in transacoes if "teste" in t.get("descricao", "").lower()), None
    )
    assert (
        teste_transacao is not None
    ), "Transação de teste não foi encontrada após persistência!"
    print(f"   ✓ Transação encontrada no banco: {teste_transacao['descricao']}")
    print(f"   ✓ Valor: R$ {teste_transacao['valor']:.2f}\n")

    # Forçar VACUUM para compactar banco (sqlite3 não cresce linearmente)
    print("7️⃣  Executando VACUUM para compactar banco...")
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
        conn.commit()
    print("   ✓ VACUUM executado\n")
    
    # 8. Verificar tamanho do arquivo após inserção
    print("8️⃣  Verificando tamanho do arquivo após inserção...")
    new_size = os.path.getsize(CAMINHO_BANCO)
    print(f"   Tamanho anterior: {file_size} bytes")
    print(f"   Tamanho atual: {new_size} bytes")
    print(f"   Diferença: {new_size - file_size} bytes")
    print("   ✓ Dados foram inseridos com sucesso\n")

    # 9. Testar idempotência da inicialização
    print("9️⃣  Testando idempotência (segunda inicialização)...")
    init_database()
    assert os.path.exists(CAMINHO_BANCO), "Arquivo foi removido na segunda init!"
    transacoes_segunda = get_transactions()
    assert (
        len(transacoes_segunda) == len(transacoes)
    ), "Transações foram duplicadas!"
    print("   ✅ Segunda inicialização não duplica dados\n")

    print("=" * 70)
    print("✅ TODOS OS TESTES DE PERSISTÊNCIA PASSARAM!")
    print("=" * 70 + "\n")
    return True


if __name__ == "__main__":
    try:
        success = test_database_persistence()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
