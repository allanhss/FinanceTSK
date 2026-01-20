#!/usr/bin/env python3
"""Add Tags tab to src/app.py"""
import sys

file_path = r"c:\Users\allan\OneDrive\Documentos\Python\FinanceTSK\src\app.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the lines with tab-analise and tab-categorias
analise_line = None
categorias_line = None

for i, line in enumerate(lines):
    if 'value="tab-analise"' in line:
        analise_line = i
    if 'value="tab-categorias"' in line:
        categorias_line = i

print(f"tab-analise found at line: {analise_line + 1 if analise_line else 'NOT FOUND'}")
print(
    f"tab-categorias found at line: {categorias_line + 1 if categorias_line else 'NOT FOUND'}"
)

if analise_line and categorias_line:
    # We need to insert after the closing ), after tab-analise
    # Find the line with just "             )," after tab-analise
    insert_line = None
    for i in range(analise_line, categorias_line):
        if lines[i].strip() == "),":
            insert_line = i + 1
            break

    if insert_line:
        print(f"Will insert at line: {insert_line + 1}")

        # Create the new tab
        new_tab = """                dcc.Tab(
                    label="🏷️ Tags",
                    value="tab-tags",
                ),
"""

        # Insert
        lines.insert(insert_line, new_tab)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print("✅ Success! Tags tab added.")

        # Verify
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "tab-tags" in content:
                print("✅ Verification: 'tab-tags' found in file")
    else:
        print("Could not find insertion point")
else:
    print("Could not find tab-analise or tab-categorias")
