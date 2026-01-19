"""
Testes para o sistema de Categorias com separação por tipo (receita/despesa).

Valida:
- Criação de categorias com tipo
- Filtro por tipo
- Inicialização de categorias padrão
- Deleção de categorias
- Constraint de unicidade (nome, tipo)
"""

import pytest
from datetime import date
from pathlib import Path
import sys

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import init_database, get_db
from src.database.models import Categoria, Transacao
from src.database.operations import (
    create_category,
    get_categories,
    delete_category,
    initialize_default_categories,
    get_category_options,
    create_transaction,
)


@pytest.fixture(scope="function")
def clean_database():
    """Limpa banco de dados antes e depois de cada teste."""
    # Cleanup antes
    with get_db() as session:
        session.query(Transacao).delete()
        session.query(Categoria).delete()
        session.commit()

    yield

    # Cleanup depois
    with get_db() as session:
        session.query(Transacao).delete()
        session.query(Categoria).delete()
        session.commit()


@pytest.mark.usefixtures("clean_database")
class TestCategoriaModel:
    """Testes para o modelo Categoria."""

    def test_categoria_tipo_receita(self):
        """Testa criação de categoria de receita."""
        success, msg = create_category(
            nome="Teste Receita",
            tipo="receita",
            cor="#22C55E",
            icone="💰",
        )
        assert success
        assert "sucesso" in msg.lower()

        categorias = get_categories(tipo="receita")
        assert any(c["nome"] == "Teste Receita" for c in categorias)

    def test_categoria_tipo_despesa(self):
        """Testa criação de categoria de despesa."""
        success, msg = create_category(
            nome="Teste Despesa",
            tipo="despesa",
            cor="#EF4444",
            icone="💸",
        )
        assert success
        assert "sucesso" in msg.lower()

        categorias = get_categories(tipo="despesa")
        assert any(c["nome"] == "Teste Despesa" for c in categorias)

    def test_categoria_tipo_invalido(self):
        """Testa validação de tipo inválido."""
        success, msg = create_category(
            nome="Inválido",
            tipo="invalido",
            cor="#000000",
        )
        assert not success
        assert "receita" in msg.lower() or "despesa" in msg.lower()

    def test_categoria_nome_vazio(self):
        """Testa validação de nome vazio."""
        success, msg = create_category(
            nome="",
            tipo="receita",
        )
        assert not success

    def test_categoria_cor_invalida(self):
        """Testa validação de cor hexadecimal."""
        success, msg = create_category(
            nome="Teste",
            tipo="receita",
            cor="INVALID",
        )
        assert not success
        assert "hex" in msg.lower()

    def test_categoria_duplicata_mesmo_tipo(self):
        """Testa constraint de unicidade (nome, tipo)."""
        # Criar primeira categoria
        success1, msg1 = create_category(
            nome="Alimentação",
            tipo="despesa",
            cor="#22C55E",
        )
        assert success1

        # Tentar criar com mesmo nome e tipo
        success2, msg2 = create_category(
            nome="Alimentação",
            tipo="despesa",
            cor="#EF4444",
        )
        assert not success2
        assert "duplicada" in msg2.lower() or "já existe" in msg2.lower()

    def test_categoria_mesmo_nome_tipos_diferentes(self):
        """Testa que mesmo nome é permitido em tipos diferentes."""
        # Criar categoria receita
        success1, msg1 = create_category(
            nome="Outros",
            tipo="receita",
            cor="#6B7280",
        )
        assert success1

        # Criar categoria despesa com mesmo nome (deve funcionar)
        success2, msg2 = create_category(
            nome="Outros",
            tipo="despesa",
            cor="#6B7280",
        )
        assert success2


@pytest.mark.usefixtures("clean_database")
class TestCategoriaOperations:
    """Testes para operações de categoria."""

    def test_get_categories_sem_filtro(self):
        """Testa recuperação de todas as categorias."""
        create_category("Cat A", "receita")
        create_category("Cat B", "despesa")

        categorias = get_categories()
        assert len(categorias) >= 2

    def test_get_categories_filtro_receita(self):
        """Testa filtro por receita."""
        create_category("Receita 1", "receita")
        create_category("Despesa 1", "despesa")

        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        assert len(receitas) >= 1
        assert len(despesas) >= 1
        assert all(c["tipo"] == "receita" for c in receitas)
        assert all(c["tipo"] == "despesa" for c in despesas)

    def test_delete_category(self):
        """Testa deleção de categoria."""
        # Criar categoria
        success, msg = create_category("Para Deletar", "receita")
        assert success

        # Obter ID
        with get_db() as session:
            cat = (
                session.query(Categoria)
                .filter(Categoria.nome == "Para Deletar")
                .first()
            )
            assert cat is not None
            cat_id = cat.id

        # Deletar
        success, msg = delete_category(cat_id)
        assert success

        # Verificar que foi deletada
        with get_db() as session:
            cat = session.query(Categoria).filter(Categoria.id == cat_id).first()
            assert cat is None

    def test_delete_category_inexistente(self):
        """Testa deleção de categoria que não existe."""
        success, msg = delete_category(99999)
        assert not success
        assert "não encontrada" in msg.lower()

    def test_get_category_options_com_filtro(self):
        """Testa get_category_options com filtro."""
        create_category("Opt A", "receita", icone="💰")
        create_category("Opt B", "despesa", icone="💸")

        opcoes_receita = get_category_options(tipo="receita")
        opcoes_despesa = get_category_options(tipo="despesa")

        assert len(opcoes_receita) >= 1
        assert len(opcoes_despesa) >= 1
        assert all("label" in o and "value" in o for o in opcoes_receita)


@pytest.mark.usefixtures("clean_database")
class TestInitializeDefaults:
    """Testes para inicialização de categorias padrão."""

    def test_initialize_default_categories(self):
        """Testa inicialização de categorias padrão."""
        # Primeira inicialização
        success, msg = initialize_default_categories()
        assert success

        # Verificar quantidades
        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        assert len(receitas) == 5
        assert len(despesas) == 7

    def test_initialize_default_categories_idempotente(self):
        """Testa que inicialização é idempotente."""
        # Primeira inicialização
        success1, msg1 = initialize_default_categories()
        assert success1

        # Segunda inicialização
        success2, msg2 = initialize_default_categories()
        assert success2
        assert "já foram inicializadas" in msg2.lower()

        # Verificar que não duplicou
        todas = get_categories()
        assert len(todas) == 12

    def test_default_categories_nomes(self):
        """Testa que categorias padrão têm nomes corretos."""
        initialize_default_categories()

        receitas = get_categories(tipo="receita")
        despesas = get_categories(tipo="despesa")

        nomes_receita = sorted([c["nome"] for c in receitas])
        nomes_despesa = sorted([c["nome"] for c in despesas])

        assert "Salário" in nomes_receita
        assert "Investimentos" in nomes_receita
        assert "Alimentação" in nomes_despesa
        assert "Moradia" in nomes_despesa

    def test_default_categories_com_emojis(self):
        """Testa que categorias padrão têm emojis."""
        initialize_default_categories()

        todas = get_categories()
        assert all(c["icone"] for c in todas)


@pytest.mark.usefixtures("clean_database")
class TestCategoriaIntegration:
    """Testes de integração com transações."""

    def test_criar_transacao_com_categoria(self):
        """Testa criação de transação com categoria tipada."""
        # Criar categoria de despesa
        success, msg = create_category("Alimentação", "despesa")
        assert success

        # Obter ID da categoria
        categorias = get_categories(tipo="despesa")
        cat_id = next(c["id"] for c in categorias if c["nome"] == "Alimentação")

        # Criar transação
        success, msg = create_transaction(
            tipo="despesa",
            descricao="Compra no mercado",
            valor=150.50,
            data=date(2026, 1, 19),
            categoria_id=cat_id,
        )
        assert success

    def test_categoria_to_dict(self):
        """Testa serialização de categoria para dict."""
        create_category("Test", "receita", icone="🎉")

        categorias = get_categories()
        cat = next(c for c in categorias if c["nome"] == "Test")

        assert "id" in cat
        assert "nome" in cat
        assert "tipo" in cat
        assert "cor" in cat
        assert "icone" in cat
        assert cat["tipo"] == "receita"
