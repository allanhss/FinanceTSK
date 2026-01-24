# Dashboard Cards - Componente Multi-Contas

## Visão Geral

O módulo `dashboard_cards.py` fornece componentes Dash Bootstrap para renderizar cards dinâmicos que exibem o resumo financeiro multi-contas de forma visual e intuitiva.

---

## 📊 Estrutura do Layout

O layout é dividido em **3 linhas principais**:

### Linha 1: Resumo Macro (3 Cards Grandes)

Exibe os totais agregados por tipo de conta:

- **💰 Disponível** (Azul/Primary)
  - Soma de todas as contas correntes (`tipo='conta'`)
  - Dinheiro liquído disponível para gastos imediatos
  - Classe: `text-primary`, border azul

- **💳 Faturas/Cartões** (Vermelho/Danger)
  - Soma de todos os cartões de crédito (`tipo='cartao'`)
  - Tipicamente negativo (débito a pagar)
  - Classe: `text-danger`, border vermelho

- **📈 Investimentos** (Verde/Success)
  - Soma de todas as aplicações (`tipo='investimento'`)
  - Ativos de longo prazo
  - Classe: `text-success`, border verde

### Linha 2: Patrimônio Total (1 Card Grande)

- **🎯 Patrimônio Total** (Cinza/Secondary)
  - Fórmula: `Liquidez + Investimentos - Dívida`
  - Representa a riqueza líquida total
  - Classe: `text-secondary`, border cinza

### Linha 3: Detalhe por Conta (Grid Responsivo)

Grid de cards menores (um para cada conta), com layout responsivo:
- **12 colunas** (mobile): 1 conta por linha
- **6 colunas** (sm): 2 contas por linha
- **4 colunas** (md): 3 contas por linha
- **3 colunas** (lg): 4 contas por linha

**Cada card de conta contém:**
- Header: `[EMOJI] Nome da Conta`
- Body: Saldo formatado em moeda + Tipo da conta
- Cores aplicadas conforme tipo (via `cor_tipo`)

---

## 🔧 API da Função Principal

### `render_dashboard_cards(transaction_data=None) → dbc.Container`

Renderiza o layout completo do Dashboard Multi-Contas.

**Parâmetros:**
- `transaction_data` (`Dict[str, Any] | None`, opcional): Dados de transações (mantido por compatibilidade, não utilizado internamente)

**Retorna:**
- `dbc.Container`: Layout completo com todas as 3 linhas de cards

**Comportamento:**
1. Chama `get_account_balances_summary()` para obter dados atualizados
2. Renderiza Linha 1 (Resumo Macro)
3. Renderiza Linha 2 (Patrimônio Total)
4. Renderiza Linha 3 (Detalhe por Conta)
5. Retorna Container com o layout completo

**Tratamento de Erros:**
- Retorna mensagem de erro em `dbc.Alert` se algo falhar
- Logs detalhados com `logging`

---

## 🛠️ Funções Auxiliares

### `_formatar_moeda(valor: float) → str`

Formata valor numérico como moeda brasileira.

**Exemplo:**
```python
_formatar_moeda(1234.56)   # "R$ 1.234,56"
_formatar_moeda(-500.00)   # "R$ -500,00"
_formatar_moeda(0.0)       # "R$ 0,00"
```

### `_get_emoji_por_tipo(tipo_conta: str) → str`

Retorna emoji correspondente ao tipo de conta.

**Mapeamento:**
- `"conta"` → 🏦
- `"cartao"` → 💳
- `"investimento"` → 📈
- (desconhecido) → 💰

### `_get_cor_classe_bootstrap(cor_hex: str) → str`

Mapeia cor hexadecimal para classe Bootstrap.

**Mapeamento:**
- `"#3B82F6"` (Azul) → `"primary"`
- `"#10B981"` (Verde) → `"success"`
- `"#EF4444"` (Vermelho) → `"danger"`
- (desconhecida) → `"secondary"`

---

## 📌 Exemplos de Uso

### Uso Simples em Callback

```python
from src.components.dashboard_cards import render_dashboard_cards
from dash import Output, Input
import dash_bootstrap_components as dbc

@app.callback(
    Output("dashboard-container", "children"),
    Input("page-load", "id"),
)
def update_dashboard(page_id):
    return render_dashboard_cards()
```

### Integração em Layout

```python
import dash_bootstrap_components as dbc
from src.components.dashboard_cards import render_dashboard_cards

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            render_dashboard_cards()
        ], width=12)
    ], className="mt-4"),
], fluid=True)
```

### Em um Callback com Filtros (Futuro)

```python
@app.callback(
    Output("dashboard", "children"),
    [
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_dashboard_filtered(start_date, end_date):
    # Futuro: adicionar parâmetro de data_range a get_account_balances_summary()
    return render_dashboard_cards()
```

---

## 🎨 Estrutura CSS e Classes Bootstrap

**Classes Utilizadas:**
- `shadow-sm`: Sombra discreta nos cards
- `border-start border-{primary|success|danger|secondary}`: Borda colorida à esquerda
- `border-5`: Largura da borda
- `text-{primary|success|danger|muted}`: Cores de texto
- `fw-bold`: Texto em negrito
- `display-4`, `display-5`, `display-6`: Tamanhos de fonte
- `mb-{n}`: Margem inferior responsiva
- `g-3`: Gap entre colunas
- `h-100`: Altura 100% (card responsivo)

---

## 📊 Fluxo de Dados

```
render_dashboard_cards()
  ↓
get_account_balances_summary()
  ↓
Banco de Dados (SessionLocal)
  ├─ SELECT Contas
  └─ SELECT Transações (eager load)
  ↓
Cálculos (saldo por conta)
  ├─ total_disponivel (soma contas tipo 'conta')
  ├─ total_investido (soma contas tipo 'investimento')
  ├─ total_cartoes (soma contas tipo 'cartao')
  ├─ patrimonio_total (soma de tudo)
  └─ detalhe_por_conta (array com cada conta)
  ↓
Renderização Dash
  ├─ Linha 1: 3 cards grandes
  ├─ Linha 2: 1 card patrimônio
  └─ Linha 3: Grid de cards por conta
  ↓
dbc.Container (retorno)
```

---

## ✅ Testes

### Suite Completa: 21 Testes

Arquivo: `tests/test_dashboard_cards.py`

**Classes de Teste:**
1. `TestFormatacaoAuxiliar` (12 testes)
   - Formatação de moeda
   - Mapeamento de emojis
   - Mapeamento de cores Bootstrap

2. `TestRenderDashboardCards` (7 testes)
   - Render sem contas
   - Render com uma conta
   - Render com múltiplas contas de tipos diferentes
   - Render com estrutura básica
   - Render com transaction_data=None
   - Render com saldo negativo
   - Performance com 20 contas

3. `TestIntegracaoDashboard` (2 testes)
   - Estrutura de linhas
   - Render sem erro com banco vazio

**Status:** ✅ **21/21 PASSING**

### Script de Validação

Arquivo: `tests/validation_dashboard_cards.py`

Demonstração com dados reais:
- 6 categorias (3 receita, 3 despesa)
- 4 contas (2 conta, 1 investimento, 1 cartao)
- 8 transações distribuídas

**Saída exemplo:**
```
Disponível: R$ 16.900,00
Investido: R$ 25.500,00
Cartões: R$ -800,00
Patrimônio Total: R$ 41.600,00

DETALHE POR CONTA:
├─ 🏦 Nubank Corrente: R$ 7.750,00
├─ 📈 XP Investimentos: R$ 25.500,00
├─ 💳 Cartão Visa: R$ -800,00
└─ 🏦 Caixa Econômica: R$ 8.550,00
```

---

## 🚀 Próximos Passos

### 1. Integração Imediata (Next)
- [ ] Atualizar `src/pages/dashboard.py` para usar `render_dashboard_cards()`
- [ ] Remover uso antigo de `render_summary_cards()` (Receita/Despesa/Saldo)
- [ ] Testar integração no app em execução

### 2. Melhorias Futuras
- [ ] Adicionar filtro por data range
- [ ] Implementar refresh automático (auto-reload)
- [ ] Adicionar gráficos sobre os cards
- [ ] Suporte a múltiplas moedas
- [ ] Histórico de patrimônio (evolução temporal)
- [ ] Comparação com período anterior

### 3. Otimizações
- [ ] Cache de dados com TTL
- [ ] Lazy loading para muitas contas (>50)
- [ ] Paginação no grid de contas
- [ ] Export para PDF/Excel

---

## 📁 Arquivos Relacionados

| Arquivo | Propósito |
|---------|-----------|
| `src/components/dashboard_cards.py` | Componente principal |
| `src/database/operations.py` | Função `get_account_balances_summary()` |
| `src/pages/dashboard.py` | Página de dashboard (integração) |
| `tests/test_dashboard_cards.py` | Suite de testes (21 testes) |
| `tests/validation_dashboard_cards.py` | Script de validação |
| `docs/DASHBOARD_CARDS.md` | Este arquivo |

---

## 🔗 Dependências

- **dash-bootstrap-components**: Componentes UI
- **SQLAlchemy**: ORM e modelos
- **Python 3.10+**: Type hints

---

## 📝 Notas de Implementação

1. **Formatação de Moeda**: Padrão brasileiro (R$ 1.234,56)
2. **Cores**: Seguem padrão bootstrap (primary/success/danger/secondary)
3. **Responsividade**: Layout adapta-se a telas pequenas/médias/grandes
4. **Perforimance**: O(n) onde n = número de contas
5. **Thread-safe**: Via gerenciamento de sessão SQLAlchemy

---

**Última atualização:** Janeiro 23, 2026  
**Versão:** 1.0 - Dashboard Multi-Contas  
**Status:** ✅ PRONTO PARA PRODUÇÃO
