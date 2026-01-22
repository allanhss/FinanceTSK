# Integração do Campo `teto_mensal` (Budget Ceiling)

**Data**: 22 de janeiro de 2026  
**Status**: ✅ Implementação Completa (Camada de Banco de Dados)  
**Próxima Fase**: Frontend Integration

---

## Resumo das Mudanças

### 1. **Camada de Banco de Dados (Database Layer)**

#### [src/database/models.py](src/database/models.py)
- **Adicionado**: Coluna `teto_mensal` na classe `Categoria`
  - Tipo: `Float`
  - Padrão: `0.0` (sem limite)
  - Nullable: `False`
  - Índice: Implícito (apenas querie rápida)

- **Atualizado**: Método `__init__()` 
  - Novo parâmetro: `teto_mensal: float = 0.0`
  - Validação: Garante valor não-negativo com `max(0.0, float(teto_mensal))`

- **Atualizado**: Método `to_dict()`
  - Novo campo: `"teto_mensal": self.teto_mensal`
  - Garante que API e callbacks recebem o valor

#### [src/database/operations.py](src/database/operations.py)
- **Atualizado**: Função `create_category()`
  - Novo parâmetro: `teto_mensal: float = 0.0`
  - Documentação completa com exemplo

- **Atualizado**: Função `initialize_default_categories()`
  - Todas as 12 categorias padrão agora incluem `teto_mensal`
  - Valores realistas por categoria:
    - **Receitas**: Salário (5000), Vendas (2000), Investimentos (1000), Mesada (500), Outros (0)
    - **Despesas**: Moradia (2000), Alimentação (1000), Educação (800), Lazer (500), Transporte (500), Saúde (300), Outros (0)

---

### 2. **Migração do Banco de Dados**

#### [tests/migration_add_teto_mensal.py](tests/migration_add_teto_mensal.py)
**Novo arquivo** - Script de migração automático que:
- Detecta bancos existentes em `data/finance.db` ou `data/financetsk.db`
- Adiciona coluna `teto_mensal` de forma segura com `ALTER TABLE`
- Define valores padrão realistas para categorias existentes
- É **idempotente** (seguro executar múltiplas vezes)
- Tratamento completo de erros com logging

**Uso**:
```bash
python -m tests.migration_add_teto_mensal
```

#### [tests/update_budget_values.py](tests/update_budget_values.py)
**Novo arquivo** - Script utilitário que:
- Atualiza valores de `teto_mensal` em banco já migrado
- Usa busca parcial de nomes para suportar variações de idioma
- Útil se valores precisarem ser recalibrados

**Uso**:
```bash
python -m tests.update_budget_values
```

---

## Fluxo de Dados

```
┌─────────────────────────┐
│ Categoria (ORM Model)   │
│  └─ teto_mensal: float  │
└────────────┬────────────┘
             │
             ├─→ to_dict() 
             │    └─→ API Response {"teto_mensal": 1000.0}
             │
             └─→ get_categories()
                  └─→ Lista com teto_mensal para cada categoria
```

---

## Validação

### ✅ Verificações Realizadas

1. **Sintaxe Python**
   - ✅ models.py: Sem erros de sintaxe
   - ✅ operations.py: Sem erros de sintaxe

2. **Importação**
   - ✅ App importa com sucesso
   - ✅ Modelo instancia corretamente

3. **Persistência**
   - ✅ Migração executada com sucesso
   - ✅ 12 categorias afetadas
   - ✅ Valores atualizados corretamente

4. **Operações CRUD**
   - ✅ `create_category()` aceita `teto_mensal`
   - ✅ `get_categories()` retorna campo
   - ✅ `to_dict()` inclui novo campo

5. **Valores Padrão**
   - ✅ Todos os 5 receita têm orçamento atribuído
   - ✅ Todos os 7 despesas têm orçamento atribuído
   - ✅ Total: 12 categorias com valores realistas

---

## Próximos Passos (Roadmap)

### **Fase 2: Frontend Integration** (⏳ Próximo)
- [ ] Campo input `teto_mensal` em forms de categoria
- [ ] Validação de float não-negativo no frontend
- [ ] Display do orçamento em list de categorias

### **Fase 3: Dashboard & Visualização**
- [ ] Card "Status de Orçamento" no dashboard
- [ ] Barra de progresso: Gasto / Orçamento por categoria
- [ ] Color coding:
  - 🟢 Verde: 0-80% do orçamento
  - 🟡 Amarelo: 80-100%
  - 🔴 Vermelho: >100% (Excedido)

### **Fase 4: Alertas & Compliance**
- [ ] Alerta quando gasto > 80% de orçamento
- [ ] Opção para bloquear transações se >100%
- [ ] Relatório mensal de conformidade

### **Fase 5: Analytics & Reporting**
- [ ] Gráfico de tendência: Orçamento vs. Real
- [ ] Projeção mensal de gastos
- [ ] Recomendações de ajuste de orçamento

---

## Notas Técnicas

### Coluna no Banco
```sql
ALTER TABLE categorias ADD COLUMN teto_mensal FLOAT NOT NULL DEFAULT 0.0;
```

### Model Definition
```python
teto_mensal: float = Column(Float, nullable=False, default=0.0)
```

### Valores Padrão Implementados
- **0.0** = Sem limite (Outros, Investimentos opcionais)
- **Valores positivos** = Limite explícito em R$

### Migração Segura
- Non-destructive (não deleta dados)
- Pode ser executada em bancos com dados existentes
- Idempotente (seguro rodar múltiplas vezes)
- Logging completo de operações

---

## Testes

### Teste Manual
```python
from src.database.operations import get_categories

# Verificar que teto_mensal está presente
cats = get_categories(tipo='receita')
for cat in cats:
    print(f"{cat['nome']}: {cat['teto_mensal']}")
```

**Esperado**:
```
Salário: 5000.0
Mesada: 500.0
Vendas: 2000.0
Investimentos: 1000.0
Outros: 0.0
```

---

## Configuração

### Variáveis de Ambiente
Nenhuma necessária. Campo usa defaults no banco.

### Arquivo de Configuração
Valores padrão em `src/database/operations.py`:
- Linha 253-278: `CATEGORIAS_RECEITA`
- Linha 280-297: `CATEGORIAS_DESPESA`

---

## Troubleshooting

### Erro: "no such column: categorias.teto_mensal"
**Solução**: Execute migração:
```bash
python -m tests.migration_add_teto_mensal
```

### Valores teto_mensal estão 0.0
**Solução**: Execute update script:
```bash
python -m tests.update_budget_values
```

### Banco não encontrado
**Verificar**: `data/finance.db` deve estar presente
**Se vazio**: Rodará com valores padrão quando app iniciar

---

## Referências

- [Conversation History](../.github/copilot-instructions.md)
- Phase 8: Budget Foundation (22 Jan 2026)
- Tag System Implementation (Phases 1-7)
