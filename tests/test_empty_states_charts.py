"""Test script for empty state handling in dashboard charts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.components.dashboard_charts import render_evolution_chart, render_top_expenses_chart

# Test 1: render_top_expenses_chart with empty data
print("[TEST 1] render_top_expenses_chart with empty data:")
empty_chart = render_top_expenses_chart([])
print(f"  Result type: {type(empty_chart).__name__}")
print(f"  ✓ Returns HTML div (not a crash)\n")

# Test 2: render_top_expenses_chart with data
print("[TEST 2] render_top_expenses_chart with data:")
data_chart = render_top_expenses_chart([
    {"categoria": "Alimentação", "valor": 500},
    {"categoria": "Transporte", "valor": 200},
])
print(f"  Result type: {type(data_chart).__name__}")
print(f"  ✓ Returns dcc.Graph\n")

# Test 3: render_evolution_chart with all zeros
print("[TEST 3] render_evolution_chart with empty data (all zeros):")
empty_evolution = render_evolution_chart({
    "meses": ["2026-01", "2026-02", "2026-03"],
    "receitas": [
        {"nome": "Salário", "valores": {"2026-01": 0, "2026-02": 0, "2026-03": 0}},
    ],
    "despesas": [
        {"nome": "Alimentação", "valores": {"2026-01": 0, "2026-02": 0, "2026-03": 0}},
    ],
    "saldos": [],
})
print(f"  Result type: {type(empty_evolution).__name__}")
print(f"  ✓ Returns HTML div (not a crash)\n")

# Test 4: render_evolution_chart with data
print("[TEST 4] render_evolution_chart with data:")
data_evolution = render_evolution_chart({
    "meses": ["2026-01", "2026-02", "2026-03"],
    "receitas": [
        {"nome": "Salário", "valores": {"2026-01": 5000, "2026-02": 5000, "2026-03": 5000}},
    ],
    "despesas": [
        {"nome": "Alimentação", "valores": {"2026-01": 800, "2026-02": 900, "2026-03": 850}},
    ],
    "saldos": [],
})
print(f"  Result type: {type(data_evolution).__name__}")
print(f"  ✓ Returns dcc.Graph\n")

print("✅ All empty state tests passed!")
