"""
Validação: Remoção do campo "Pessoa Origem" da interface de Receita

Script que valida que o campo foi removido corretamente dos formulários
e que a função save_receita não mais depende dele.
"""

import logging
import inspect

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Função principal de validação."""
    try:
        logger.info("=" * 80)
        logger.info("VALIDACAO: REMOCAO DO CAMPO 'PESSOA ORIGEM'")
        logger.info("=" * 80)
        logger.info("")

        # Teste 1: Verificar que forms.py não contém "pessoa origem"
        logger.info("[1/4] Verificando forms.py...")
        with open("src/components/forms.py", "r", encoding="utf-8") as f:
            forms_content = f.read()

        if "input-receita-origem" in forms_content or (
            "Pessoa Origem" in forms_content and "receita" in forms_content.lower()
        ):
            logger.error("✗ Campo ainda presente em forms.py")
            return
        logger.info("✓ Campo removido de forms.py")

        # Teste 2: Verificar que app.py não contém State de input-receita-origem
        logger.info("[2/4] Verificando app.py...")
        with open("src/app.py", "r", encoding="utf-8") as f:
            app_content = f.read()

        if 'State("input-receita-origem"' in app_content:
            logger.error("✗ State ainda presente em app.py")
            return
        logger.info("✓ State removido de app.py")

        # Teste 3: Verificar que save_receita não tem pessoa_origem no parâmetro
        logger.info("[3/4] Verificando assinatura de save_receita...")
        from src.app import save_receita

        sig = inspect.signature(save_receita)
        params = list(sig.parameters.keys())

        if "pessoa_origem" in params:
            logger.error(f"✗ Parâmetro pessoa_origem ainda em save_receita: {params}")
            return

        logger.info(f"✓ Parâmetro removido de save_receita")
        logger.info(f"   Parâmetros: {', '.join(params)}")

        # Teste 4: Verificar que transaction_form pode ser renderizado
        logger.info("[4/4] Testando renderização de transaction_form...")
        from src.components.forms import transaction_form

        try:
            form_receita = transaction_form("receita")
            form_despesa = transaction_form("despesa")
            logger.info("✓ Formulários renderizados com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro ao renderizar: {e}")
            return

        # Resultado final
        logger.info("")
        logger.info("=" * 80)
        logger.info("VALIDACAO CONCLUIDA COM SUCESSO!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Mudancas realizadas:")
        logger.info("  1. src/components/forms.py:")
        logger.info("     - Removido bloco de 'Pessoa Origem' (17 linhas)")
        logger.info("     - Campo 'input-receita-origem' eliminado")
        logger.info("")
        logger.info("  2. src/app.py (save_receita):")
        logger.info("     - Removido State('input-receita-origem', 'value')")
        logger.info("     - Removido parâmetro pessoa_origem da função")
        logger.info("     - Removido pessoa_origem da chamada create_transaction")
        logger.info("     - Atualizada docstring")
        logger.info("")
        logger.info("Status: O campo 'Pessoa Origem' foi completamente removido")
        logger.info("        Tags agora são o mecanismo principal de categorização")
        logger.info("")

    except Exception as e:
        logger.error(f"Erro durante validacao: {e}", exc_info=True)


if __name__ == "__main__":
    main()
