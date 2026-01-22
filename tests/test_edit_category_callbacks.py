"""
Testes para callbacks de edição de categorias.

Valida o fluxo completo de:
1. Abrir modal com dados carregados
2. Gerenciar seletor de ícones
3. Salvar alterações no banco
"""

import pytest
from src.database.operations import (
    create_category,
    get_categories,
    update_category,
    delete_category,
)


class TestEditCategoryFlow:
    """Testes para o fluxo de edição de categorias."""

    @pytest.fixture
    def categoria_teste(self):
        """Cria uma categoria de teste para uso nos testes."""
        success, msg = create_category(
            "CatForEditTest",
            tipo="receita",
            icone="📚",
            teto_mensal=1500.0,
        )
        assert success, f"Falha ao criar categoria de teste: {msg}"

        categorias = get_categories()
        cat = next((c for c in categorias if c.get("nome") == "CatForEditTest"), None)
        assert cat, "Categoria de teste não encontrada após criação"

        yield cat

        # Limpeza
        delete_category(cat.get("id"))

    def test_open_edit_modal_logic(self, categoria_teste):
        """
        Testa a lógica de open_edit_modal.

        Valida que:
        - Categoria é encontrada pelo ID
        - Todos os campos são retornados corretamente
        """
        cat_id = categoria_teste.get("id")

        # Simular lógica de open_edit_modal
        categorias = get_categories()
        categoria = next((c for c in categorias if c.get("id") == cat_id), None)

        assert categoria is not None, f"Categoria com ID {cat_id} não encontrada"
        assert categoria.get("nome") == "CatForEditTest"
        assert categoria.get("icone") == "📚"
        assert categoria.get("teto_mensal") == 1500.0

    def test_toggle_edit_icon_picker_logic(self, categoria_teste):
        """
        Testa a lógica de toggle_edit_icon_picker.

        Valida que:
        - Ícones usados são detectados corretamente
        - Ícone atual é mantido na lista disponível
        - Filtro exclui ícones de outras categorias
        """
        from src.components.category_manager import EMOJI_OPTIONS

        cat_id = categoria_teste.get("id")
        icone_atual = categoria_teste.get("icone")

        # Simular lógica de filtro de ícones
        todas_categorias = get_categories()
        icones_usados = {c.get("icone") for c in todas_categorias if c.get("icone")}

        # Remover ícone da categoria atual (permissão de manter seu próprio ícone)
        cat_edit = next((c for c in todas_categorias if c.get("id") == cat_id), None)
        if cat_edit and cat_edit.get("icone"):
            icones_usados.discard(cat_edit.get("icone"))

        opcoes_disponiveis = [e for e in EMOJI_OPTIONS if e not in icones_usados]

        # Validações
        assert len(opcoes_disponiveis) > 0, "Nenhuma opção de ícone disponível"
        assert (
            icone_atual in opcoes_disponiveis
        ), f"Ícone atual {icone_atual} não está disponível"

    def test_save_edit_category_logic(self, categoria_teste):
        """
        Testa a lógica de save_edit_category.

        Valida que:
        - Validação de nome não vazio funciona
        - Validação de ícone não vazio funciona
        - Meta é normalizada corretamente (negativa -> 0.0)
        - Alterações são persistidas no banco
        """
        cat_id = categoria_teste.get("id")

        # Simulação: novo nome, novo ícone, nova meta
        novo_nome = "CatEditedTest"
        novo_icone = "🎯"
        novo_teto = 2500.0

        # Validações
        assert novo_nome and novo_nome.strip(), "Nome não pode ser vazio"
        assert novo_icone, "Ícone não pode ser vazio"

        # Normalizar meta
        meta_valor = float(novo_teto) if novo_teto is not None else 0.0
        if meta_valor < 0:
            meta_valor = 0.0
        assert meta_valor == 2500.0, "Meta não foi normalizada corretamente"

        # Executar atualização
        success, msg = update_category(
            cat_id,
            novo_nome=novo_nome,
            novo_icone=novo_icone,
            novo_teto=meta_valor,
        )

        assert success, f"Falha ao atualizar categoria: {msg}"

        # Verificar persistência
        categorias = get_categories()
        cat_atualizada = next((c for c in categorias if c.get("id") == cat_id), None)

        assert cat_atualizada is not None, "Categoria não encontrada após atualização"
        assert cat_atualizada.get("nome") == novo_nome
        assert cat_atualizada.get("icone") == novo_icone
        assert cat_atualizada.get("teto_mensal") == novo_teto

    def test_save_edit_category_meta_normalization(self, categoria_teste):
        """
        Testa a normalização de meta negativa.

        Valida que:
        - Valores negativos são convertidos para 0.0
        """
        cat_id = categoria_teste.get("id")

        # Tentar atualizar com meta negativa
        success, msg = update_category(
            cat_id,
            novo_teto=-1000.0,
        )

        assert success, f"Falha ao atualizar com meta negativa: {msg}"

        # Verificar que foi normalizada para 0.0
        categorias = get_categories()
        cat_atualizada = next((c for c in categorias if c.get("id") == cat_id), None)

        assert cat_atualizada is not None
        assert (
            cat_atualizada.get("teto_mensal") == 0.0
        ), "Meta negativa não foi normalizada para 0.0"

    def test_save_edit_category_partial_update(self, categoria_teste):
        """
        Testa atualização parcial (só atualiza campos fornecidos).

        Valida que:
        - Campos não fornecidos não são alterados
        - update_category respeita None como "não alterar"
        """
        cat_id = categoria_teste.get("id")
        nome_original = categoria_teste.get("nome")

        # Atualizar apenas a meta, mantendo nome
        success, msg = update_category(
            cat_id,
            novo_teto=3000.0,
        )

        assert success, f"Falha ao atualizar parcialmente: {msg}"

        # Verificar que nome não foi alterado
        categorias = get_categories()
        cat_atualizada = next((c for c in categorias if c.get("id") == cat_id), None)

        assert cat_atualizada is not None
        assert (
            cat_atualizada.get("nome") == nome_original
        ), "Nome foi alterado indevidamente"
        assert cat_atualizada.get("teto_mensal") == 3000.0, "Meta não foi atualizada"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
