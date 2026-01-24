"""
Script de Debug: Inspeciona o Historico de Classificacao

Exibe o conteudo bruto da "memoria" do sistema (get_classification_history).
Util para verificar se as tags estao sendo salvas e recuperadas corretamente.

AVISO: Este script lê do banco de dados. Use com cuidado em producao.
"""

import os
import sys

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
    """Display classification history in a readable table."""
    print("=" * 100)
    print("[DEBUG] INSPECIONADOR DE HISTORICO DE CLASSIFICACAO")
    print("=" * 100)
    
    # Show environment info
    print(f"\n[INFO] Ambiente:")
    print(f"   - TESTING_MODE: {TESTING_MODE}")
    print(f"   - Banco em uso: {CAMINHO_BANCO}")
    print(f"   - Engine URL: {engine.url}")
    
    if TESTING_MODE:
        print(f"   [AVISO] Lendo do banco de TESTE")
    else:
        print(f"   [AVISO] Lendo do banco de PRODUCAO - Cuidado!")
    
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
        print(f"   Nenhuma transacao classificada foi encontrada no banco.")
        sys.exit(0)
    
    print(f"\n[RESULTADO] {len(historico)} entradas no historico")
    print("\n" + "-" * 100)
    print(f"{'Descricao (Chave)':<40} | {'Categoria':<20} | {'Tags':<35}")
    print("-" * 100)
    
    # Display entries
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
    
    # Summary statistics
    print("\n[ESTATISTICAS]")
    total_entries = len(historico)
    entries_with_tags = sum(1 for d in historico.values() if d.get("tags") and d.get("tags").strip())
    entries_without_tags = total_entries - entries_with_tags
    
    print(f"   - Total de entradas: {total_entries}")
    print(f"   - Com tags: {entries_with_tags}")
    print(f"   - Sem tags: {entries_without_tags}")
    print(f"   - Percentual com tags: {(entries_with_tags / total_entries * 100):.1f}%")
    
    # Problem indicators
    print("\n[DIAGNOSTICO]")
    if entries_without_tags == total_entries:
        print(f"   [PROBLEMA] Nenhuma entrada tem tags!")
        print(f"   Possivel causa:")
        print(f"      - Tags nao estao sendo salvas no banco")
        print(f"      - Necessario verificar se campo 'tags' da Transacao esta sendo preenchido")
    elif entries_without_tags > 0:
        print(f"   [AVISO] {entries_without_tags} entrada(s) sem tags")
        print(f"   Possivel causa:")
        print(f"      - Transacoes antigas nao tem tags")
        print(f"      - Tags foram adicionadas apenas recentemente")
    else:
        print(f"   [OK] Todas as {total_entries} entradas tem tags!")
        print(f"   Sistema funcionando corretamente.")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
