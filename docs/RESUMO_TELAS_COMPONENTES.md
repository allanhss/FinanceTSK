# 📋 RESUMO COMPLETO - FinanceTSK Telas, Botões e Widgets

**Data:** 22 de Janeiro de 2026  
**Status:** MVP em desenvolvimento  
**Framework:** Dash (Python) + Bootstrap 5  
**Tema:** FLATLY  

---

## 🎯 ESTRUTURA GERAL

```
┌─────────────────────────────────────────────────┐
│  🏠 NAVBAR (Topo Fixo)                          │
│  💰 FinanceTSK | Dashboard | Receitas |...      │
├─────────────────────────────────────────────────┤
│                                                 │
│  🎛️ CONTROLES GLOBAIS (Sempre Visíveis)        │
│  ├─ Dropdown: Meses Passados (0-12)            │
│  ├─ Dropdown: Meses Futuros (0-12)             │
│                                                 │
│  📊 FLUXO DE CAIXA (Tabela)                     │
│  ├─ Colunas: Mês | Saldo Anterior | ...        │
│                                                 │
│  🎨 BOTÕES DE AÇÃO (Sempre Visíveis)           │
│  ├─ + Receita (Verde, lg)                      │
│  ├─ + Despesa (Vermelho, lg)                   │
│                                                 │
│  📑 ABAS PRINCIPAIS (7 Abas)                    │
│  ├─ 📊 Dashboard                               │
│  ├─ 💰 Receitas                                │
│  ├─ 💸 Despesas                                │
│  ├─ 📈 Análise                                 │
│  ├─ 🎯 Orçamento                               │
│  ├─ 🏷️  Tags                                   │
│  ├─ 📁 Categorias                              │
│                                                 │
│  📱 CONTEÚDO DAS ABAS (Dinâmico)               │
│  ├─ Renderizado pelo callback render_tab...   │
│                                                 │
├─────────────────────────────────────────────────┤
│  📋 MODALS + STORES (Ocultos)                   │
│  └─ Modal de Transação | Modals de Detalhes   │
└─────────────────────────────────────────────────┘
```

---

## 📊 NAVBAR (Topo)

**Componente:** `dbc.NavbarSimple`  
**Propriedades:**
- **Brand:** "💰 FinanceTSK" (clicável, vai para "/")
- **Cor:** "primary" (Azul)
- **Dark Mode:** Ativado
- **Links Internos:**
  - Dashboard (href="/")
  - Receitas (href="/receitas")
  - Despesas (href="/despesas")
  - Categorias (href="/categorias")

---

## 🎛️ CONTROLES GLOBAIS (Abaixo Navbar)

### 1️⃣ Dropdown: Meses Passados
- **ID:** `select-past`
- **Tipo:** `dcc.Dropdown`
- **Opções:**
  - Nenhum (0)
  - 1 mês (1)
  - 3 meses (3) **← Padrão**
  - 6 meses (6)
  - 12 meses (12)
- **Função:** Controla horizonte de análise retroativo
- **Atualiza:** `update_cash_flow`, `render_tab_content`

### 2️⃣ Dropdown: Meses Futuros
- **ID:** `select-future`
- **Tipo:** `dcc.Dropdown`
- **Opções:** Idem anterior
- **Padrão:** 6 meses
- **Função:** Controla horizonte de previsão

---

## 📊 FLUXO DE CAIXA (Tabela)

**Componente:** `render_cash_flow_table()`  
**Localização:** Entre controles e botões  
**Atualização:** Automática ao mudar dropdowns ou salvar transação  
**Scroll:** Horizontal habilitado (overflowX: auto)

**Colunas:**
- Data (Mês)
- Saldo Anterior
- Receitas
- Despesas
- Saldo
- (Dados por mês)

---

## 🎨 BOTÕES DE AÇÃO

### ✅ Botão: + Receita
- **ID:** `btn-nova-receita`
- **Tipo:** `dbc.Button`
- **Cor:** success (Verde)
- **Tamanho:** lg
- **Largura:** 100%
- **Ação:** Abre Modal de Transação (aba Receita)
- **Callback:** `toggle_modal_open()`

### ❌ Botão: + Despesa
- **ID:** `btn-nova-despesa`
- **Tipo:** `dbc.Button`
- **Cor:** danger (Vermelho)
- **Tamanho:** lg
- **Largura:** 100%
- **Ação:** Abre Modal de Transação (aba Despesa)
- **Callback:** `toggle_modal_open()`

**Layout:** 2 colunas (md=6), responsivo

---

## 📑 ABAS PRINCIPAIS (7 Abas)

**Componente:** `dcc.Tabs`  
**ID:** `tabs-principal`  
**Padrão:** `tab-dashboard`  
**Propriedade:** Conteúdo renderizado dinamicamente via callback

### 📊 TAB 1: Dashboard

**ID:** `tab-dashboard`  
**Status:** Placeholder (Em breve)

**Conteúdo Esperado:**
- Cards de resumo (Receitas, Despesas, Saldo)
- Gráfico de evolução mensal (linha)
- Gráfico de despesas por categoria (pizza)
- Últimas 10 transações

**Callback:** `render_tab_content(tab_value="tab-dashboard")`  
**Retorno:** `dbc.Card` com placeholder

---

### 💰 TAB 2: Receitas

**ID:** `tab-receitas`  
**Status:** ✅ Funcional

**Conteúdo:**
- Tabela de receitas (todas)
- Colunas: Data, Descrição, Categoria, Origem, Valor, Tags, Recorrência, Ações

**Callback:** `render_tab_content(tab_value="tab-receitas")`  
**Dados:** `render_transactions_table(receitas)`  
**Filtro:** `tipo == "receita"`

---

### 💸 TAB 3: Despesas

**ID:** `tab-despesas`  
**Status:** ✅ Funcional

**Conteúdo:**
- Tabela de despesas (todas)
- Colunas: Data, Descrição, Categoria, Forma Pagamento, Parcelas, Valor, Tags, Recorrência, Ações

**Callback:** `render_tab_content(tab_value="tab-despesas")`  
**Dados:** `render_transactions_table(despesas)`  
**Filtro:** `tipo == "despesa"`

---

### 📈 TAB 4: Análise

**ID:** `tab-analise`  
**Status:** ✅ Funcional

**Conteúdo:**
- Matriz Analítica (Categorias vs Meses)
- Formato: Tabela interativa
- Células: Valores de transações por categoria/mês
- Cores: Código semáforo por criticidade

**Callback:** `render_tab_content(tab_value="tab-analise")`  
**Dados:** `get_category_matrix_data(months_past, months_future)`  
**Renderização:** `render_category_matrix()`  
**Card:** Header com título, body com tabela

---

### 🎯 TAB 5: Orçamento

**ID:** `tab-budget`  
**Status:** ✅ Funcional (Novo!)

**Conteúdo:**
- Matriz de Orçamento (Categorias vs Meses)
- Formato: Tabela com barras de progresso (CSS Gradient)
- Filtra: Apenas despesas com `meta > 0`
- Células: Valor gasto / Meta (percentual%)
- Cores: Verde (<80%), Amarelo (80-100%), Vermelho (>100%)

**Callback:** `render_tab_content(tab_value="tab-budget")`  
**Dados:** `get_category_matrix_data(months_past, months_future)`  
**Renderização:** `render_budget_matrix()`  
**Card:** Header com título, body com tabela

**Estilos CSS:**
```css
background: linear-gradient(90deg, {cor_barra} {percentual}%, transparent {percentual}%)
whiteSpace: nowrap
position: relative
borderRight: 2px solid #0d6efd (se mês atual)
```

---

### 🏷️ TAB 6: Tags

**ID:** `tab-tags`  
**Status:** ✅ Funcional

**Conteúdo:**
- Matriz de Tags (Tags/Entidades vs Meses)
- Formato: Tabela interativa
- Células: Saldo líquido (Receitas - Despesas) por tag/mês
- Cores: Código semáforo

**Callback:** `render_tab_content(tab_value="tab-tags")`  
**Dados:** `get_tag_matrix_data(months_past, months_future)`  
**Renderização:** `render_tag_matrix()`  
**Card:** Header com título, body com tabela

---

### 📁 TAB 7: Categorias

**ID:** `tab-categorias`  
**Status:** ✅ Funcional

**Conteúdo:**
- Gerenciador de Categorias (Receitas + Despesas)
- 2 abas internas: Receitas | Despesas
- Por categoria:
  - Ícone + Nome + Meta (Orçamento)
  - Botão Editar (✏️) → Modal de edição
  - Botão Deletar (🗑️) → Confirmação
  - Seletor de Emoji/Ícone
  - Input de Meta Mensal

**Callback:** `render_tab_content(tab_value="tab-categorias")`  
**Dados:** 
  - `get_categories(tipo="receita")`
  - `get_categories(tipo="despesa")`
**Renderização:** `render_category_manager(receitas, despesas)`

**Componente Interno:** `render_category_manager()` com:
- Tabs internas
- Grid de cards por categoria
- Modal de edição (Icon picker + Meta input)
- Callbacks para salvar/deletar

---

## 🔘 MODALS (Ocultos Inicialmente)

### 1️⃣ Modal: Transação (Nova Receita/Despesa)

**ID:** `modal-transacao`  
**Tipo:** `dbc.Modal`  
**Tamanho:** lg  
**Centralizado:** Sim

**Conteúdo:**
- Título dinâmico: "Nova Receita" ou "Nova Despesa"
- 2 Abas internas:
  - **Tab Receita:**
    - Input: Valor
    - Input: Descrição
    - Input: Data (dcc.DatePickerSingle)
    - Dropdown: Categoria (receita)
    - Input: Pessoa/Origem
    - Multi-Select: Tags
    - Checkbox: Recorrente
    - Dropdown: Frequência (se recorrente)
    - Botão: Salvar (Verde)
    - Botão: Cancelar
  
  - **Tab Despesa:**
    - Input: Valor
    - Input: Descrição
    - Input: Data (dcc.DatePickerSingle)
    - Dropdown: Categoria (despesa)
    - Dropdown: Forma de Pagamento (Dinheiro, Débito, Crédito, PIX)
    - Input: Número de Parcelas (se crédito)
    - Multi-Select: Tags
    - Checkbox: Recorrente
    - Dropdown: Frequência (se recorrente)
    - Botão: Salvar (Vermelho)
    - Botão: Cancelar

**Callbacks:**
- `toggle_modal_open()` - Abre/fecha ao clicar em botões
- `save_receita()` - Salva receita, limpa form, fecha modal
- `save_despesa()` - Salva despesa, limpa form, fecha modal

**Validações:**
- Campos obrigatórios
- Valores positivos
- Datas válidas
- Parcelas > 0

---

### 2️⃣ Modal: Detalhes de Categoria

**ID:** `modal-detalhes-categoria`  
**Tipo:** `dbc.Modal`  
**Tamanho:** xl  
**MaxWidth:** 95vw  
**Centralizado:** Sim

**Conteúdo:**
- Header: Título dinâmico (nome da categoria)
- Body: Conteúdo renderizado pelo callback

**Callback:**
- `show_category_details()` - Busca dados da categoria e renderiza

---

### 3️⃣ Modal: Edição de Categoria (Dentro de tab-categorias)

**ID:** `modal-edit-category`  
**Localização:** Dentro do componente `render_category_manager`

**Conteúdo:**
- Header: "Editar Categoria"
- Body:
  - Input: Nome
  - Icon Picker (Emoji Selector com modal interno)
  - Input: Meta Mensal (orçamento)
  - Botão: Salvar
  - Botão: Cancelar

**Callbacks:**
- `open_edit_modal()` - Carrega dados atuais
- `toggle_edit_icon_picker()` - Abre icon picker
- `save_edit_category()` - Salva mudanças

---

## 🗄️ STORES (dcc.Store - Sincronização)

### Store 1: `store-data-atual`
- **Padrão:** `{"ano": 2026, "mes": 1}`
- **Função:** Mantém contexto de data atual
- **Uso:** Callbacks de atualização

### Store 2: `store-transacao-salva`
- **Tipo:** Timestamp (float)
- **Valor Padrão:** 0
- **Função:** Sinal de que transação foi salva
- **Atualiza:** Cash flow, tabs de Receitas/Despesas, Dashboard
- **Padrão:** `allow_duplicate=True` (múltiplos callbacks escrevem)

### Store 3: `store-categorias-atualizadas`
- **Tipo:** Timestamp (float)
- **Valor Padrão:** 0
- **Função:** Sinal de que categorias foram modificadas
- **Atualiza:** Tabs de Receitas/Despesas (recarrega dropdowns)

---

## 🎨 COMPONENTES REUTILIZÁVEIS (src/components/)

### 1. `dashboard.py`
- **Função:** `render_summary_cards(month, year, total_receitas, total_despesas, saldo)`
- **Retorno:** 3 Cards com KPIs
- **Uso:** Dashboard (não em uso atualmente)

### 2. `modals.py`
- **Função:** `render_transaction_modal(is_open)`
- **Retorno:** Modal estruturado com abas (Receita/Despesa)
- **Componentes Internos:** Formulários reutilizáveis

### 3. `forms.py`
- **Função:** `transaction_form(tipo: str)`
- **Retorno:** Card com formulário (Receita ou Despesa)
- **Campos:** Dinâmicos por tipo

### 4. `tables.py`
- **Função:** `render_transactions_table(transacoes: List[Dict])`
- **Retorno:** `dbc.Table` formatada
- **Colunas:** Data, Descrição, Categoria, Valor, etc.

### 5. `cash_flow.py`
- **Função:** `render_cash_flow_table(data: List[Dict])`
- **Retorno:** Tabela de fluxo de caixa
- **Colunas:** Mês, Saldo Anterior, Receitas, Despesas, Saldo

### 6. `category_manager.py`
- **Função:** `render_category_manager(receitas, despesas)`
- **Retorno:** Tabs internas com gerenciamento de categorias
- **Recursos:** Cards por categoria, modais de edição

### 7. `category_matrix.py`
- **Função:** `render_category_matrix(data)`
- **Retorno:** Tabela de categorias vs meses
- **Formato:** Interativo com cores por criticidade

### 8. `tag_matrix.py`
- **Função:** `render_tag_matrix(data)`
- **Retorno:** Tabela de tags vs meses
- **Formato:** Interativo com saldos por entidade

### 9. `budget_progress.py` (NOVO!)
- **Funções:**
  - `render_budget_progress(data, month_index=None)` - Card single/específico
  - `render_budget_dashboard(data)` - Grid de cards (alternativo)
  - `render_budget_matrix(data)` - **Tabela com gradients (USADO)**
- **Retorno:** Card com tabela responsiva
- **Estilo:** CSS Gradients dinâmicos (barras de progresso)

---

## 🔄 CALLBACKS PRINCIPAIS (Ordem de Execução)

### 1. `update_cash_flow()`
- **Trigger:** `select-past.value`, `select-future.value`, `store-transacao-salva.data`
- **Output:** `cash-flow-container.children`
- **Função:** Atualiza tabela de fluxo de caixa
- **Reatualiza:** A cada mudança de horizonte ou nova transação

### 2. `render_tab_content()`
- **Trigger:** `tabs-principal.value`, `store-transacao-salva.data`, `store-categorias-atualizadas.data`
- **Output:** `conteudo-abas.children`
- **Função:** Renderiza conteúdo dinâmico da aba selecionada
- **Lógica:** 7 cases (um por aba)
- **Atualiza:** Sempre que muda aba, salva transação ou categoria

### 3. `toggle_modal_open()`
- **Trigger:** `btn-nova-receita.n_clicks`, `btn-nova-despesa.n_clicks`
- **Output:** `modal-transacao.is_open`, `tabs-modal-transacao.value`
- **Função:** Abre modal e seleciona aba (Receita ou Despesa)

### 4. `save_receita()`
- **Trigger:** `btn-salvar-receita.n_clicks`
- **Outputs:**
  - `alerta-modal.is_open` (erro)
  - `alerta-modal.children` (mensagem)
  - `modal-transacao.is_open` (fecha)
  - `store-transacao-salva.data` (atualiza store)
  - Limpeza de inputs
- **Função:** Valida, salva receita, limpa, fecha
- **Validação:** 3 camadas (UI, callback, DB)

### 5. `save_despesa()`
- **Trigger:** `btn-salvar-despesa.n_clicks`
- **Outputs:** Idem `save_receita()`
- **Função:** Valida, salva despesa com parcelas
- **Lógica:** Se crédito com parcelas, cria múltiplas transações

### 6. `update_dashboard_cards()`
- **Trigger:** `store-transacao-salva.data`
- **Output:** `dashboard-container.children`
- **Função:** Atualiza cards de resumo (não em uso)

### 7. (Categoria Manager) - Callbacks Internos
- **open_edit_modal()** - Carrega dados da categoria
- **toggle_edit_icon_picker()** - Abre/fecha seletor de emoji
- **save_edit_category()** - Salva edições
- **delete_category()** - Deleta com confirmação

---

## 📊 TABELAS (Tipos e Estruturas)

### Tabela 1: Fluxo de Caixa
- **Uso:** Always visible (top)
- **Colunas:** Mês, Saldo Ant., Receitas, Despesas, Saldo
- **Dados:** Agregado por mês
- **Atualização:** Automática (horizonte + nova transação)

### Tabela 2: Receitas / Despesas
- **Uso:** Abas tab-receitas / tab-despesas
- **Colunas:** Data, Descrição, Categoria, Valor, Tags, Recorrência, Ações
- **Dados:** Todas as transações filtradas por tipo
- **Atualização:** Ao salvar nova, ao deletar

### Tabela 3: Matriz Analítica
- **Uso:** Aba tab-analise
- **Colunas:** Categoria + Um mês por coluna
- **Células:** Valores gastos/recebidos por categoria/mês
- **Cores:** Código semáforo (criticidade)
- **Dados:** `get_category_matrix_data()`

### Tabela 4: Matriz de Orçamento (NOVO!)
- **Uso:** Aba tab-budget
- **Colunas:** Categoria + Um mês por coluna
- **Células:** Gasto / Meta (%) com barra visual (gradiente)
- **Cores:** Verde (<80%), Amarelo, Vermelho (>100%)
- **Filtro:** Apenas despesas com meta > 0
- **Dados:** `get_category_matrix_data()`

### Tabela 5: Matriz de Tags
- **Uso:** Aba tab-tags
- **Colunas:** Tag/Entidade + Um mês por coluna
- **Células:** Saldo líquido (Receita - Despesa)
- **Cores:** Código semáforo
- **Dados:** `get_tag_matrix_data()`

---

## 🎨 GRID & LAYOUT

### Responsividade
- **Mobile:** 1 coluna (width=12)
- **Tablet:** 2 colunas (md=6)
- **Desktop:** 3-4 colunas (lg=4, xl=3)

### Componentes Containers
- **Container Principal:** `dbc.Container` (fluid=True)
- **Rows/Cols:** `dbc.Row` / `dbc.Col`
- **Cards:** `dbc.Card` com `dbc.CardHeader`, `dbc.CardBody`

### Espaçamento
- `className="mb-3"` - Margem inferior
- `className="mt-4"` - Margem superior
- `className="g-3"` - Gutter (espaço entre colunas)
- `className="p-3"` - Padding interno

---

## 🎯 FLUXO DE CRIAÇÃO (Nova Transação)

```
1. User clica "+ Receita" ou "+ Despesa"
   ↓
2. toggle_modal_open() abre modal com aba correta
   ↓
3. User preenche formulário (Val, Desc, Data, Cat, etc)
   ↓
4. User clica "Salvar"
   ↓
5. save_receita() ou save_despesa() validam:
   ├─ Camada UI (inputs required)
   ├─ Camada Callback (valores válidos)
   └─ Camada DB (unique, constraints)
   ↓
6. Se OK:
   ├─ Salva em DB (create_transaction)
   ├─ Limpa formulário (inputs.value = "")
   ├─ Fecha modal
   ├─ Atualiza store-transacao-salva (timestamp)
   └─ Triggers:
       ├─ update_cash_flow() → Atualiza fluxo
       ├─ render_tab_content() → Atualiza Receitas/Despesas
       ├─ update_dashboard_cards() → Atualiza KPIs
       └─ store-categorias-atualizadas → Re-carrega dropdowns
   ↓
7. Se ERRO:
   └─ Mostra alerta (modal fica aberta)
```

---

## 🔍 FLUXO DE EDIÇÃO (Categoria)

```
1. User clica ✏️ (editar) em uma categoria
   ↓
2. open_edit_modal() carrega dados atuais (nome, meta, ícone)
   ↓
3. Modal de edição abre com dados pré-preenchidos
   ↓
4. User pode:
   ├─ Editar nome
   ├─ Clicar em ícone para abrir seletor (emoji picker)
   ├─ Editar meta (orçamento mensal)
   └─ Clicar "Salvar"
   ↓
5. save_edit_category() valida e:
   ├─ Chama update_category(cat_id, novo_nome, novo_icone, novo_teto)
   ├─ Limpa modal
   ├─ Fecha modal
   ├─ Atualiza store-categorias-atualizadas
   └─ Triggers re-render da aba categorias
   ↓
6. Se ERRO:
   └─ Mostra alerta, modal fica aberta
```

---

## 📦 DADOS FLOWS (Inputs/Outputs por Callback)

### Callback: `render_tab_content`
**Inputs:**
- `tabs-principal.value` (qual aba)
- `store-transacao-salva.data` (sinal)
- `store-categorias-atualizadas.data` (sinal)

**States:**
- `select-past.value` (meses passados)
- `select-future.value` (meses futuros)

**Outputs:**
- `conteudo-abas.children` (renderiza aba)

---

## 🚀 PERFORMANCE & OTIMIZAÇÕES

### Stores + Signals
- `store-transacao-salva` evita race condition
- Timestamp como sinal (não precisa guardar dado real)
- Atualiza apenas quando necessário

### Prevent Initial Call
- `prevent_initial_call=True/False` em callbacks
- Evita renderizações desnecessárias

### Allow Duplicate
- `allow_duplicate=True` para outputs compartilhados
- Múltiplos callbacks podem escrever no mesmo store

### Cache de Dados
- Dropdowns carregam opções sob demanda
- Matriz recalculada apenas ao trocar horizonte

---

## 📝 RESUMO EXECUTIVO PARA REFATORAÇÃO

### ✅ Pontos Fortes
1. **Separação clara MVC** (database/models, operations, components, app)
2. **Type hints** em todas as funções
3. **Logging detalhado** para debug
4. **Validação em 3 camadas** (UI, callback, DB)
5. **Componentes reutilizáveis** bem estruturados
6. **Abas dinâmicas** com callbacks inteligentes
7. **Stores para sincronização** evita race conditions

### 🔴 Pontos a Refatorar
1. **Dashboard placeholder** (gráficos ainda não implementados)
2. **Callbacks muito grandes** (`render_tab_content` tem 200+ linhas)
3. **Lógica de validação repetida** (salvar receita/despesa similar)
4. **IDs espalhados** em múltiplos arquivos (difícil rastrear)
5. **Tests limitados** (adicionar mais testes unitários)
6. **Documentação inline** (alguns callbacks faltam docstrings)
7. **Modal de detalhes** não totalmente implementado

### 💡 Sugestões de Refatoração
1. **Extrair validações** para módulo compartilhado (`validators.py`)
2. **Criar factory de callbacks** para evitar duplicação
3. **Centralizar IDs de componentes** em `constants.py`
4. **Quebrar `render_tab_content`** em sub-funções por aba
5. **Implementar Page Factory** para renderizar abas modularmente
6. **Adicionar tests** para todos os callbacks críticos
7. **Criar tipo `CallbackContext`** typed para type hints
8. **Documentar arquitetura** em `ARCHITECTURE.md`

---

## 📚 Arquivos Principais

| Arquivo | Linhas | Propósito |
|---------|--------|----------|
| `src/app.py` | ~2000 | App principal, layout, callbacks |
| `src/database/models.py` | ~200 | Modelos SQLAlchemy |
| `src/database/operations.py` | ~1000 | CRUD + agregações |
| `src/components/*.py` | ~100-300 | Componentes reutilizáveis |
| `tests/test_*.py` | ~50-200 | Testes unitários |

---

**Gerado em:** 22/01/2026 - FinanceTSK MVP v1.0
