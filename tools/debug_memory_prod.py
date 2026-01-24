"""
Script de Debug: Inspeciona o Historico de Classificacao - PRODUCAO

Conecta ESPECIFICAMENTE ao banco de producao (finance.db).
Procura por chaves contendo "ipiranga" para debug.
"""

import os
import sys

# Garantir que NÃO usa TESTING_MODE (força produção)
if "TESTING_MODE" in os.environ:
    del os.environ["TESTING_MODE"]

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.connection import engine, TESTING_MODE, CAMINHO_BANCO
from src.database.operations import get_classification_history


def format_tags(tags_str):
    """Format tags for display with indicator."""
    if not tags_str or tags_str.strip() == "":
        return "[SEM-TAGS] (vazio)"
    else:
        return f"[TAGS] {tags_str}"


def main():
    """Display classification history from PRODUCTION database."""
    print("=" * 100)
    print("[DEBUG] INSPECIONADOR DE HISTORICO - BANCO DE PRODUCAO")
    print("=" * 100)

    # Verificar ambiente
    print(f"\n[AMBIENTE]")
    print(f"   - TESTING_MODE: {TESTING_MODE}")
    print(f"   - Banco em uso: {CAMINHO_BANCO}")
    print(f"   - Engine URL: {engine.url}")

    # Validar que está em produção
    if TESTING_MODE:
        print(f"\n[ERRO] TESTING_MODE está ativado!")
        print(f"   Este script deve usar o banco de PRODUCAO")
        sys.exit(1)

    if "test_finance.db" in str(engine.url):
        print(f"\n[ERRO] Conectado ao banco de TESTE, não produção!")
        sys.exit(1)

    if "finance.db" not in str(engine.url):
        print(f"\n[AVISO] Banco desconhecido: {engine.url}")

    print(f"   [OK] Conectado ao banco de PRODUCAO")

    # Load history
    print(f"\n[PROCESSANDO] Carregando historico...")
    try:
        historico = get_classification_history()
    except Exception as e:
        print(f"[ERRO] Falha ao carregar historico: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    if not historico:
        print(f"\n[RESULTADO] Historico vazio!")
        print(f"   Nenhuma transacao classificada foi encontrada no banco de producao.")
        sys.exit(0)

    print(f"\n[RESULTADO] {len(historico)} entradas no historico")
    print("\n" + "-" * 100)
    print(f"{'Descricao (Chave)':<40} | {'Categoria':<20} | {'Tags':<35}")
    print("-" * 100)

    # Display ALL entries
    for descricao_normalizada, dados in historico.items():
        categoria = dados.get("categoria", "[NAO-DEFINIDO]")
        tags = dados.get("tags")
        tags_display = format_tags(tags)

        # Truncate long descriptions
        desc_display = descricao_normalizada[:40]
        if len(descricao_normalizada) > 40:
            desc_display = descricao_normalizada[:37] + "..."

        print(f"{desc_display:<40} | {categoria:<20} | {tags_display:<35}")

    print("-" * 100)

    # Search for "ipiranga"
    print("\n[BUSCA] Procurando por 'ipiranga'...")
    ipiranga_entries = {k: v for k, v in historico.items() if "ipiranga" in k.lower()}

    if ipiranga_entries:
        print(f"   Encontradas {len(ipiranga_entries)} entrada(s) contendo 'ipiranga':")
        for desc, dados in ipiranga_entries.items():
            tags = dados.get("tags")
            categoria = dados.get("categoria")
            print(f"\n   - Descricao: '{desc}'")
            print(f"     Categoria: {categoria}")
            print(f"     Tags: {format_tags(tags)}")
    else:
        print(f"   Nenhuma entrada contendo 'ipiranga' encontrada")

    # Summary statistics
    print("\n[ESTATISTICAS]")
    total_entries = len(historico)
    entries_with_tags = sum(
        1 for d in historico.values() if d.get("tags") and d.get("tags").strip()
    )
    entries_without_tags = total_entries - entries_with_tags

    print(f"   - Total de entradas: {total_entries}")
    print(f"   - Com tags: {entries_with_tags}")
    print(f"   - Sem tags: {entries_without_tags}")

    if total_entries > 0:
        pct = entries_with_tags / total_entries * 100
        print(f"   - Percentual com tags: {pct:.1f}%")

    # Problem indicators
    print("\n[DIAGNOSTICO]")
    if entries_without_tags == total_entries:
        print(f"   [PROBLEMA] Nenhuma entrada tem tags!")
        print(f"   Causa provavel:")
        print(f"      - Tags nao estao sendo salvas no banco de producao")
        print(f"      - Campo 'tags' pode estar NULL ou vazio na tabela Transacao")
    elif entries_without_tags > 0:
        print(f"   [AVISO] {entries_without_tags} entrada(s) sem tags")
        print(f"   Possivel causa:")
        print(f"      - Transacoes antigas nao tem tags (antes da implementacao)")
        print(f"      - Tags foram adicionadas apenas recentemente")
    else:
        print(f"   [OK] Todas as {total_entries} entradas tem tags!")
        print(f"   Sistema de persistencia de tags funcionando corretamente.")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
