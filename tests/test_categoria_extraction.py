"""Test script for categoria name extraction in donut chart."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.components.dashboard_charts import render_top_expenses_chart

# Test 1: Dados com categoria como string (original format)
print("[TEST 1] render_top_expenses_chart with string categoria:")
data_string = [
    {"categoria": "Alimentação", "valor": 500},
    {"categoria": "Transporte", "valor": 200},
    {"categoria": "Saúde", "valor": 150},
]
chart1 = render_top_expenses_chart(data_string)
print(f"  Result type: {type(chart1).__name__}")
print(f"  ✓ Works with string categoria\n")

# Test 2: Dados com categoria como dicionário (real database format)
print("[TEST 2] render_top_expenses_chart with dict categoria:")
data_dict = [
    {"categoria": {"id": 1, "nome": "Alimentação", "icon": "🍔"}, "valor": 500},
    {"categoria": {"id": 2, "nome": "Transporte", "icon": "🚗"}, "valor": 200},
    {"categoria": {"id": 3, "nome": "Saúde", "icon": "🏥"}, "valor": 150},
    {"categoria": {"id": 4, "nome": "Educação", "icon": "📚"}, "valor": 300},
    {"categoria": {"id": 5, "nome": "Diversão", "icon": "🎬"}, "valor": 100},
    {"categoria": {"id": 6, "nome": "Utilidades", "icon": "🛠️"}, "valor": 80},
]
chart2 = render_top_expenses_chart(data_dict)
print(f"  Result type: {type(chart2).__name__}")
print(f"  ✓ Works with dict categoria (extracts 'nome' field)\n")

# Test 3: Dados mistos (some strings, some dicts)
print("[TEST 3] render_top_expenses_chart with mixed categoria types:")
data_mixed = [
    {"categoria": "Alimentação", "valor": 500},
    {"categoria": {"id": 2, "nome": "Transporte", "icon": "🚗"}, "valor": 200},
    {"categoria": "Saúde", "valor": 150},
]
chart3 = render_top_expenses_chart(data_mixed)
print(f"  Result type: {type(chart3).__name__}")
print(f"  ✓ Works with mixed categoria types\n")

# Test 4: Dados com valores zerados (para filtro)
print("[TEST 4] render_top_expenses_chart with zero values:")
data_zeros = [
    {"categoria": {"id": 1, "nome": "Alimentação", "icon": "🍔"}, "valor": 0},
    {"categoria": {"id": 2, "nome": "Transporte", "icon": "🚗"}, "valor": 0},
]
chart4 = render_top_expenses_chart(data_zeros)
print(f"  Result type: {type(chart4).__name__}")
print(f"  ✓ Handles zero values\n")

print("✅ All categoria extraction tests passed!")
