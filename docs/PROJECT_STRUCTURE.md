# FinanceTSK - Estrutura de Pastas Organizada

## 📁 Estrutura Final

```
FinanceTSK/
├── src/                          # Código-fonte da aplicação
│   ├── __init__.py
│   ├── app.py                   # Aplicação principal Dash
│   ├── components/              # Componentes reutilizáveis da UI
│   │   ├── dashboard_charts.py
│   │   ├── category_manager.py
│   │   ├── forms.py
│   │   ├── tables.py
│   │   ├── modals.py
│   │   ├── cash_flow.py
│   │   ├── budget_progress.py
│   │   └── charts.py
│   ├── database/                # Camada de dados
│   │   ├── models.py
│   │   ├── operations.py
│   │   └── connection.py
│   ├── pages/                   # Páginas da aplicação
│   │   ├── dashboard.py
│   │   ├── receitas.py
│   │   ├── despesas.py
│   │   ├── relatorios.py
│   │   └── analise.py
│   └── utils/                   # Utilitários
│       ├── extrato_parser.py
│       ├── nf_scraper.py
│       └── init_data.py
│
├── tests/                        # Testes da aplicação
│   ├── __init__.py              # ✅ CRIADO AGORA
│   ├── test_*.py                # Testes unitários
│   ├── validation_*.py          # Scripts de validação
│   └── migration_*.py           # Scripts de migração
│
├── docs/                         # Documentação técnica
│   ├── README.md
│   ├── BUDGET_IMPLEMENTATION.md
│   ├── DYNAMIC_FILTER_IMPLEMENTATION.md
│   ├── GESTAO_CATEGORIAS.md
│   ├── ICON_INTEGRATION.md
│   ├── REFACTORING_SIDEBAR_LAYOUT.md
│   ├── RESUMO_TELAS_COMPONENTES.md
│   └── todo.md
│
├── data/                         # Dados da aplicação
│   ├── config.json
│   ├── finance.db
│   └── backups/
│
├── .github/                      # Configurações GitHub
├── .venv/                        # Virtual environment
├── README.md                     # Documentação principal (RAIZ)
├── requirements.txt              # Dependências
├── .env                          # Variáveis de ambiente
└── .gitignore                    # Git ignore


⚠️ Arquivos ainda na raiz (scripts antigos):
- add_tags_tab.py                 # Considerar movimentar para tests/migration_*
- fix_tabs.py                     # Considerar movimentar para tests/migration_*
```

---

## ✅ Mudanças Realizadas

1. **✓ Pasta `docs/` organizada**
   - Todos os `.md` de feature (exceto README.md) já estão em `docs/`
   - Exemplos: BUDGET_IMPLEMENTATION.md, GESTAO_CATEGORIAS.md, etc.

2. **✓ Pasta `tests/` organizada**
   - Todos os `test_*.py` já estão em `tests/`
   - Todos os `validation_*.py` já estão em `tests/`
   - Scripts de migração (migration_*.py, update_*.py) também estão em `tests/`

3. **✓ Arquivo `tests/__init__.py` criado**
   - Permite que Python reconheça `tests/` como pacote
   - Facilita imports relativos como `from tests.test_*.py import ...`

4. **✓ Imports validados**
   - Testes em `tests/` conseguem importar `from src...` sem problemas
   - PYTHONPATH automático funciona quando executado pela raiz

---

## 🚀 Como Usar

### Executar testes:
```bash
# A partir da raiz do projeto
python -m pytest tests/
python tests/test_active_date_filters.py
```

### Estrutura de imports nos testes:
```python
# tests/test_exemplo.py
from src.app import app
from src.database.operations import get_transactions
from src.components.dashboard_charts import render_evolution_chart
```

### Criar novo arquivo:
- **Novo componente**: `src/components/novo_componente.py`
- **Novo teste**: `tests/test_novo_modulo.py`
- **Nova documentação**: `docs/NOVO_FEATURE.md`

---

## 📋 Checklist de Conformidade

- ✅ Todos os `.md` em `docs/` (exceto README.md)
- ✅ Todos os `test_*.py` em `tests/`
- ✅ Todos os `validation_*.py` em `tests/`
- ✅ `tests/__init__.py` criado
- ✅ Imports de testes funcionando corretamente
- ✅ Código-fonte em `src/`
- ✅ Dados em `data/`

---

**Data**: Janeiro 22, 2026
**Status**: ✅ Organização completa
