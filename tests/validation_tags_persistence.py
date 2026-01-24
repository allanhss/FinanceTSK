"""
Validacao de Persistencia de Tags no Historico

Problema: Tags nao sao recuperadas em reimportacoes, mas categorias sao.

Este teste valida o ciclo completo:
1. Tags sao salvas no banco de dados
2. get_classification_history() recupera as tags
3. parse_upload_content() aplica as tags em nova importacao
"""

import os

os.environ["TESTING_MODE"] = "1"  # Forcar modo teste ANTES de imports do src

import sys
import csv
import io
import base64
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import engine, SessionLocal, TESTING_MODE
from src.database.models import Base, Conta, Categoria, Transacao
from src.database.operations import (
    get_classification_history,
    create_account,
)
from src.utils.importers import parse_upload_content


def setup_database():
    """Setup test database."""
    print("[SETUP] Criando tabelas no banco de teste...")
    Base.metadata.create_all(engine)
    print("[OK] Tabelas criadas com sucesso")


def create_test_account():
    """Create test account for validation."""
    print("\n[SETUP] Criando conta de teste...")
    with SessionLocal() as session:
        # Check if account already exists
        existing = session.query(Conta).filter_by(nome="Teste").first()
        if existing:
            print(f"[OK] Conta 'Teste' ja existe (ID: {existing.id})")
            return existing.id

        # Create new account
        nova_conta = Conta(
            nome="Teste",
            tipo="conta",
            saldo_inicial=1000.00,
        )
        session.add(nova_conta)
        session.commit()
        print(f"[OK] Conta 'Teste' criada com sucesso (ID: {nova_conta.id})")
        return nova_conta.id


def ensure_categories():
    """Ensure basic categories exist."""
    print("[SETUP] Verificando categorias...")
    with SessionLocal() as session:
        transporte = session.query(Categoria).filter_by(nome="Transporte").first()
        if not transporte:
            transporte = Categoria(nome="Transporte", tipo="despesa")
            session.add(transporte)
            session.commit()
            print("[OK] Categoria 'Transporte' criada")
        else:
            print("[OK] Categoria 'Transporte' ja existe")

        return transporte.id


def insert_manual_transaction(conta_id, categoria_id):
    """Insert a manual transaction with tags for learning."""
    print("\n[PASSO1] Inserindo transacao manual com tags...")

    with SessionLocal() as session:
        transacao = Transacao(
            tipo="despesa",
            descricao="Posto Ipiranga",
            valor=100.00,
            data=date(2026, 1, 20),
            conta_id=conta_id,
            categoria_id=categoria_id,
            tags="Moto,Viagem",
        )
        session.add(transacao)
        session.commit()
        print(f"[OK] Transacao inserida:")
        print(f"   - Descricao: {transacao.descricao}")
        print(f"   - Categoria: Transporte")
        print(f"   - Tags: {transacao.tags}")
        print(f"   - Valor: {transacao.valor}")


def validate_history_retrieval():
    """Validate that get_classification_history() retrieves tags."""
    print("\n[PASSO2] Verificando recuperacao do historico...")

    historico = get_classification_history()
    print(f"[INFO] Historico carregado: {len(historico)} entradas")

    # Check if "posto ipiranga" exists (normalized key)
    if "posto ipiranga" in historico:
        entry = historico["posto ipiranga"]
        print(f"[OK] Chave 'posto ipiranga' encontrada no historico")
        print(f"   - Categoria: {entry.get('categoria')}")
        print(f"   - Tags: {entry.get('tags')}")

        # Validate tags
        if entry.get("tags") == "Moto,Viagem":
            print(f"[SUCESSO] Tags recuperadas corretamente: {entry.get('tags')}")
            return True
        else:
            print(f"[ERRO] Tags nao correspondem!")
            print(f"   Esperado: 'Moto,Viagem'")
            print(f"   Obtido: '{entry.get('tags')}'")
            return False
    else:
        print(f"[ERRO] Chave 'posto ipiranga' NAO encontrada no historico")
        print(f"[INFO] Chaves disponiveis: {list(historico.keys())}")
        return False


def validate_tags_application():
    """Validate that parse_upload_content applies tags from history."""
    print("\n[PASSO3] Verificando aplicacao de tags em nova importacao...")

    # Get current history
    historico = get_classification_history()

    # Simulate CSV upload with same description
    csv_content = """data,descricao,valor
23/01/2026,Posto Ipiranga,-80.00
24/01/2026,Restaurante Novo,-45.00
"""

    print(f"[INFO] CSV simulado:")
    print(csv_content)

    # Encode to base64 (as the app would do)
    csv_encoded = base64.b64encode(csv_content.encode()).decode()

    # Parse the content
    resultado = parse_upload_content(
        csv_encoded,
        filename="test_import.csv",
        classification_history=historico,
    )

    if not resultado or len(resultado) == 0:
        print(f"[ERRO] parse_upload_content retornou vazio")
        return False

    # Find the "Posto Ipiranga" row
    posto_row = None
    for row in resultado:
        if "Ipiranga" in row.get("descricao", ""):
            posto_row = row
            break

    if not posto_row:
        print(f"[ERRO] Transacao 'Posto Ipiranga' nao encontrada no resultado")
        return False

    print(f"[OK] Transacao encontrada no resultado do parser:")
    print(f"   - Descricao: {posto_row.get('descricao')}")
    print(f"   - Categoria: {posto_row.get('categoria')}")
    print(f"   - Tags: {posto_row.get('tags')}")

    # Validate tags were applied
    if posto_row.get("tags") == "Moto,Viagem":
        print(f"[SUCESSO] Tags aplicadas corretamente na nova importacao!")
        return True
    else:
        print(f"[ERRO] Tags nao foram aplicadas corretamente")
        print(f"   Esperado: 'Moto,Viagem'")
        print(f"   Obtido: '{posto_row.get('tags')}'")
        return False


def main():
    """Run complete validation flow."""
    print("=" * 80)
    print("[TESTE] VALIDACAO DE PERSISTENCIA DE TAGS")
    print("=" * 80)

    # Validation 0: Check environment
    print(f"\n[INFO] Ambiente de teste ativado: {TESTING_MODE}")
    if not TESTING_MODE:
        print(f"[ERRO] TESTING_MODE nao esta ativado!")
        print(f"[INFO] Engine URL: {engine.url}")
        sys.exit(1)

    # Check database
    db_url = str(engine.url)
    if "test_finance.db" not in db_url:
        print(f"[ERRO] Nao esta usando test_finance.db")
        print(f"[INFO] Engine URL: {db_url}")
        sys.exit(1)

    print(f"[OK] Banco de teste isolado em uso")

    try:
        # Setup
        setup_database()
        categoria_id = ensure_categories()
        conta_id = create_test_account()

        # Insert manual transaction with tags
        insert_manual_transaction(conta_id, categoria_id)

        # Validate history retrieval
        if not validate_history_retrieval():
            print(f"\n[ERRO] Passo 2 falhou: Historico nao recuperou tags")
            sys.exit(1)

        # Validate tags application in new import
        if not validate_tags_application():
            print(f"\n[ERRO] Passo 3 falhou: Tags nao aplicadas em nova importacao")
            sys.exit(1)

        # Success
        print("\n" + "=" * 80)
        print("[SUCESSO] TODOS OS TESTES DE PERSISTENCIA DE TAGS PASSARAM!")
        print("=" * 80)
        print("\n[RESUMO]")
        print("   1. Tags foram salvas no banco de dados")
        print("   2. get_classification_history() recuperou as tags")
        print("   3. parse_upload_content() aplicou as tags em nova importacao")
        print("\nCiclo completo de persistencia de tags validado com sucesso!")

    except Exception as e:
        print(f"\n[ERRO] Excecao durante validacao: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
