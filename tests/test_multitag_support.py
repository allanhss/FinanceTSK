"""
Test suite para validar suporte de múltiplas tags.

Valida:
1. create_transaction aceita lista de tags e normaliza para CSV
2. get_all_tags desagrupa tags CSV
3. get_tag_matrix_data "explode" transações multi-tag
"""

import pytest
from datetime import date
from src.database.models import Transacao, Categoria, Conta
from src.database.operations import (
    create_transaction,
    get_all_tags,
    get_tag_matrix_data,
    create_category,
)
from src.database.connection import get_db


@pytest.fixture(autouse=True)
def setup_teardown():
    """Preparar e limpar banco para cada teste."""
    # Setup: Criar categoria padrão e obter conta padrão
    with get_db() as session:
        session.query(Transacao).delete()
        session.query(Categoria).delete()
        session.commit()

    success, _ = create_category("Teste", "receita", "#22C55E", "💰")
    assert success

    yield

    # Teardown: Limpar dados
    with get_db() as session:
        session.query(Transacao).delete()
        session.query(Categoria).delete()
        session.commit()


def _get_default_account_id():
    """Get default account ID for tests."""
    with get_db() as session:
        conta = session.query(Conta).filter_by(nome="Conta Padrão").first()
        return conta.id if conta else 1


def test_create_transaction_single_tag_string():
    """Testar create_transaction com tag simples (string)."""
    conta_id = _get_default_account_id()
    success, msg = create_transaction(
        tipo="receita",
        descricao="Teste Single Tag",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag="Mãe",  # String simples
    )

    assert success, f"Falha: {msg}"

    with get_db() as session:
        transacao = session.query(Transacao).first()
        assert transacao is not None
        assert transacao.tag == "Mãe"  # Deve estar armazenada como-é


def test_create_transaction_multiple_tags_list():
    """Testar create_transaction com múltiplas tags (lista)."""
    conta_id = _get_default_account_id()
    success, msg = create_transaction(
        tipo="receita",
        descricao="Teste Multi Tag",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Mãe", "Saúde", "Trabalho"],  # Lista
    )

    assert success, f"Falha: {msg}"

    with get_db() as session:
        transacao = session.query(Transacao).first()
        assert transacao is not None
        # Deve estar salvo como CSV
        assert transacao.tag == "Mãe,Saúde,Trabalho"


def test_create_transaction_tag_none():
    """Testar create_transaction com tag=None."""
    conta_id = _get_default_account_id()
    success, msg = create_transaction(
        tipo="receita",
        descricao="Teste No Tag",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag=None,
    )

    assert success, f"Falha: {msg}"

    with get_db() as session:
        transacao = session.query(Transacao).first()
        assert transacao is not None
        assert transacao.tag is None


def test_get_all_tags_single_tags():
    """Testar get_all_tags com tags simples."""
    # Criar 3 transações com tags diferentes
    conta_id = _get_default_account_id()
    for tag_name in ["Mãe", "Trabalho", "Saúde"]:
        create_transaction(
            tipo="receita",
            descricao=f"Teste {tag_name}",
            valor=100.0,
            data=date(2026, 1, 20),
            categoria_id=1,
            conta_id=conta_id,
            tag=tag_name,
        )

    tags = get_all_tags()
    assert len(tags) == 3
    assert "Mãe" in tags
    assert "Trabalho" in tags
    assert "Saúde" in tags
    # Deve estar ordenada
    assert tags == sorted(tags)


def test_get_all_tags_csv_tags():
    """Testar get_all_tags desagrupando tags CSV."""
    # Criar transações com tags CSV
    conta_id = _get_default_account_id()
    create_transaction(
        tipo="receita",
        descricao="Teste 1",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Mãe", "Saúde"],
    )
    create_transaction(
        tipo="receita",
        descricao="Teste 2",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Trabalho", "Saúde"],
    )

    tags = get_all_tags()
    # Deve retornar 3 tags únicas (Mãe, Saúde, Trabalho)
    assert len(tags) == 3
    assert set(tags) == {"Mãe", "Saúde", "Trabalho"}


def test_get_all_tags_mixed():
    """Testar get_all_tags com mix de tags simples e CSV."""
    conta_id = _get_default_account_id()
    create_transaction(
        tipo="receita",
        descricao="Teste 1",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag="Mãe",  # Simples
    )
    create_transaction(
        tipo="receita",
        descricao="Teste 2",
        valor=100.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Trabalho", "Saúde"],  # CSV
    )

    tags = get_all_tags()
    # Deve ter 3 tags (Mãe, Trabalho, Saúde)
    assert len(tags) == 3
    assert set(tags) == {"Mãe", "Trabalho", "Saúde"}


def test_get_tag_matrix_data_single_tags():
    """Testar get_tag_matrix_data com tags simples."""
    # Criar transações
    conta_id = _get_default_account_id()
    create_transaction(
        tipo="receita",
        descricao="Renda",
        valor=1000.0,
        data=date(2026, 1, 15),
        categoria_id=1,
        conta_id=conta_id,
        tag="Trabalho",
    )
    create_transaction(
        tipo="despesa",
        descricao="Compra",
        valor=200.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag="Trabalho",
    )

    matriz = get_tag_matrix_data(months_past=0, months_future=0)

    assert len(matriz["tags"]) == 1
    assert matriz["tags"][0]["nome"] == "Trabalho"
    # Saldo deve ser 1000 - 200 = 800
    assert matriz["tags"][0]["valores"]["2026-01"] == 800.0


def test_get_tag_matrix_data_explode_multitags():
    """Testar get_tag_matrix_data explodindo transações multi-tag."""
    # Criar transação com 2 tags
    conta_id = _get_default_account_id()
    create_transaction(
        tipo="receita",
        descricao="Renda",
        valor=1000.0,
        data=date(2026, 1, 15),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Mãe", "Trabalho"],  # 2 tags
    )

    matriz = get_tag_matrix_data(months_past=0, months_future=0)

    # Deve ter 2 tags
    assert len(matriz["tags"]) == 2
    tag_names = {tag["nome"] for tag in matriz["tags"]}
    assert tag_names == {"Mãe", "Trabalho"}

    # Cada tag deve ter o valor completo (1000)
    for tag in matriz["tags"]:
        assert tag["valores"]["2026-01"] == 1000.0


def test_get_tag_matrix_data_partial_allocation():
    """Testar get_tag_matrix_data com múltiplas transações multi-tag."""
    # Transação 1: Receita 1000 para "Mãe" e "Trabalho"
    conta_id = _get_default_account_id()
    create_transaction(
        tipo="receita",
        descricao="Renda",
        valor=1000.0,
        data=date(2026, 1, 15),
        categoria_id=1,
        conta_id=conta_id,
        tag=["Mãe", "Trabalho"],
    )
    # Transação 2: Despesa 200 apenas para "Mãe"
    create_transaction(
        tipo="despesa",
        descricao="Compra",
        valor=200.0,
        data=date(2026, 1, 20),
        categoria_id=1,
        conta_id=conta_id,
        tag="Mãe",
    )

    matriz = get_tag_matrix_data(months_past=0, months_future=0)

    # Deve ter 2 tags
    assert len(matriz["tags"]) == 2

    # Validar saldos
    tags_dict = {tag["nome"]: tag["valores"]["2026-01"] for tag in matriz["tags"]}
    assert tags_dict["Mãe"] == 1000.0 - 200.0  # 800
    assert tags_dict["Trabalho"] == 1000.0  # 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
