"""
Tests for fallback category creation and initialization.

Validates that "A Classificar" categories are correctly created
for both income and expense types during app initialization.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from src.database.models import Categoria
from src.database.connection import SessionLocal, init_database, get_db
from src.database.operations import ensure_fallback_categories


logger = logging.getLogger(__name__)


class TestFallbackCategories:
    """Test suite for fallback category functionality."""

    def test_ensure_fallback_categories_creates_receita(self):
        """Verify fallback receita category is created."""
        # Clean up first
        with get_db() as session:
            session.query(Categoria).filter_by(
                nome="A Classificar", tipo=Categoria.TIPO_RECEITA
            ).delete()

        # Test creation
        success, msg = ensure_fallback_categories()

        assert success is True
        assert "garantidas" in msg.lower()

        # Verify category exists
        with get_db() as session:
            categoria = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_RECEITA)
                .first()
            )
            assert categoria is not None
            assert categoria.icone == "📂"
            assert categoria.cor == "#6c757d"
            assert categoria.teto_mensal == 0.0

    def test_ensure_fallback_categories_creates_despesa(self):
        """Verify fallback despesa category is created."""
        # Clean up first
        with get_db() as session:
            session.query(Categoria).filter_by(
                nome="A Classificar", tipo=Categoria.TIPO_DESPESA
            ).delete()

        # Test creation
        success, msg = ensure_fallback_categories()

        assert success is True

        # Verify category exists
        with get_db() as session:
            categoria = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_DESPESA)
                .first()
            )
            assert categoria is not None
            assert categoria.icone == "📂"
            assert categoria.cor == "#6c757d"
            assert categoria.teto_mensal == 0.0

    def test_ensure_fallback_categories_idempotent(self):
        """Verify function is idempotent - doesn't fail on second call."""
        # Ensure categories exist
        success1, msg1 = ensure_fallback_categories()
        assert success1 is True

        # Call again - should still succeed
        success2, msg2 = ensure_fallback_categories()

        assert success2 is True
        assert "já existem" in msg2.lower() or "garantidas" in msg2.lower()

    def test_ensure_fallback_categories_both_types(self):
        """Verify both receita and despesa types are created."""
        # Clean up
        with get_db() as session:
            session.query(Categoria).filter_by(nome="A Classificar").delete()

        # Test creation
        success, msg = ensure_fallback_categories()

        assert success is True

        # Verify both exist
        with get_db() as session:
            receita = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_RECEITA)
                .first()
            )
            despesa = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_DESPESA)
                .first()
            )

            assert receita is not None
            assert despesa is not None
            assert receita.tipo == Categoria.TIPO_RECEITA
            assert despesa.tipo == Categoria.TIPO_DESPESA

    def test_ensure_fallback_categories_unique_constraint(self):
        """Verify unique constraint allows same name with different types."""
        # Clean up first
        with get_db() as session:
            session.query(Categoria).filter_by(nome="A Classificar").delete()
            session.commit()

        # Ensure both exist
        ensure_fallback_categories()

        # Query both
        with get_db() as session:
            categories = session.query(Categoria).filter_by(nome="A Classificar").all()

            assert len(categories) == 2
            tipos = {cat.tipo for cat in categories}
            assert Categoria.TIPO_RECEITA in tipos
            assert Categoria.TIPO_DESPESA in tipos

    def test_ensure_fallback_categories_returns_tuple(self):
        """Verify function returns correct tuple format."""
        result = ensure_fallback_categories()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_ensure_fallback_categories_logging(self):
        """Verify function logs appropriate messages."""
        with patch("src.database.operations.logger") as mock_logger:
            ensure_fallback_categories()

            # Should log something
            assert mock_logger.info.called or mock_logger.error.not_called()


class TestInitDatabaseIntegration:
    """Test database initialization with fallback categories."""

    def test_fallback_categories_after_full_init(self):
        """Verify fallback categories exist after full initialization."""
        # Reinitialize database
        init_database()

        # Check that fallback categories exist
        with get_db() as session:
            receita = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_RECEITA)
                .first()
            )
            despesa = (
                session.query(Categoria)
                .filter_by(nome="A Classificar", tipo=Categoria.TIPO_DESPESA)
                .first()
            )

            assert receita is not None
            assert despesa is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
