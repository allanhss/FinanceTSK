"""Quick test script for dashboard charts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.components.dashboard_charts import (
    render_evolution_chart,
    render_top_expenses_chart,
)

# Test 1: render_evolution_chart
sample_matrix = {
    "meses": ["2026-01", "2026-02", "2026-03"],
    "receitas": [5000, 5200, 5100],
    "despesas": [3000, 3200, 2900],
    "saldos": [2000, 2000, 2200],
}

chart1 = render_evolution_chart(sample_matrix)
print("[OK] render_evolution_chart works with sample data")

# Test 2: render_top_expenses_chart
sample_expenses = [
    {"categoria": "Alimentação", "valor": 500},
    {"categoria": "Transporte", "valor": 200},
    {"categoria": "Saúde", "valor": 150},
    {"categoria": "Educação", "valor": 300},
    {"categoria": "Diversão", "valor": 100},
    {"categoria": "Utilidades", "valor": 80},
]

chart2 = render_top_expenses_chart(sample_expenses)
print("[OK] render_top_expenses_chart works with sample data")

print("\n✅ All dashboard charts functions validated successfully!")
