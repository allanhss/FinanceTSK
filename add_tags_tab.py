#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script para adicionar a aba de Tags ao app.py"""

with open("src/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the section
old_section = """                dcc.Tab(
                    label="📈 Análise",
                    value="tab-analise",
                ),
                dcc.Tab(
                    label="📁 Categorias",
                    value="tab-categorias","""

new_section = """                dcc.Tab(
                    label="📈 Análise",
                    value="tab-analise",
                ),
                dcc.Tab(
                    label="🏷️ Tags",
                    value="tab-tags",
                ),
                dcc.Tab(
                    label="📁 Categorias",
                    value="tab-categorias","""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open("src/app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Aba 'Tags' adicionada com sucesso!")

    # Verify
    with open("src/app.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if "tab-tags" in line:
                print(f"✅ Verificação: linha {i} contém 'tab-tags'")
else:
    print("❌ Seção não encontrada")
