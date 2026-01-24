# Editor de Tags - Implementação de Callbacks

## Resumo

Implementação completa da lógica interativa do Editor de Tags Modal no FinanceTSK. O sistema permite:

1. **Abrir Modal** ao clicar na coluna de tags
2. **Selecionar Múltiplas Tags** via dropdown com autocomplete
3. **Salvar Alterações** de volta na tabela DataTable
4. **Cancelar** sem guardar mudanças

---

## Arquitetura de Callbacks

### 1. Callback de Abertura: `open_tag_editor_modal`

**Responsabilidade:** Abrir o modal quando uma célula da coluna "tags" é clicada.

**Inputs:**
- `preview-table.active_cell` → Célula ativa (ex: `{"row": 1, "column": 5}`)
- `preview-table.data` → Dados completos da tabela (State)

**Outputs:**
- `modal-tag-editor.is_open` → `True/False` para abrir/fechar modal
- `dropdown-tag-editor.options` → Lista de tags disponíveis `[{"label": "Moto", "value": "Moto"}, ...]`
- `dropdown-tag-editor.value` → Tags pré-selecionadas `["Moto", "Viagem"]`
- `store-editing-row-index.data` → Índice da linha sendo editada `0`

**Lógica:**
```python
def open_tag_editor_modal(active_cell: Dict, table_data: List[Dict]) -> tuple:
    # 1. Verificar se coluna clicada é tags (col_idx == 5)
    if col_idx != 5:
        raise PreventUpdate
    
    # 2. Extrair tags atuais da linha
    tags_str = table_data[row_idx].get("tags", "")  # Ex: "Moto, Viagem"
    
    # 3. Converter string em lista
    tags_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    # Result: ["Moto", "Viagem"]
    
    # 4. Carregar opções do banco
    existing_tags = get_unique_tags_list()
    dropdown_options = [{"label": tag, "value": tag} for tag in existing_tags]
    
    # 5. Retornar para popular modal
    return (True, dropdown_options, tags_list, row_idx)
```

**Casos Especiais:**
- Se clique for em coluna diferente de tags: `raise PreventUpdate` (modal não abre)
- Se célula não existir: `raise PreventUpdate` (proteção de índice)
- Se tags_str vazio: `tags_list = []` (modal abre com dropdown vazio)

---

### 2. Callback de Salvamento: `save_tags_to_table`

**Responsabilidade:** Salvar tags selecionadas de volta na tabela quando botão "Salvar" é clicado.

**Inputs:**
- `btn-save-tags.n_clicks` → Número de cliques no botão

**States:**
- `dropdown-tag-editor.value` → Tags selecionadas pelo usuário `["Moto", "Viagem", "Lazer"]`
- `store-editing-row-index.data` → Índice da linha `1`
- `preview-table.data` → Dados atuais da tabela (State)

**Outputs:**
- `preview-table.data` → Tabela atualizada com novas tags
- `modal-tag-editor.is_open` → `False` (fecha modal)

**Lógica:**
```python
def save_tags_to_table(n_clicks: int, selected_tags: List[str], row_index: int, table_data: List[Dict]) -> tuple:
    if not n_clicks or row_index is None:
        raise PreventUpdate
    
    # 1. Fazer cópia para não mutar original
    updated_data = [row.copy() for row in table_data]
    
    # 2. Converter lista em string CSV
    tags_str = ", ".join(selected_tags) if selected_tags else ""
    # Result: "Moto, Viagem, Lazer"
    
    # 3. Atualizar linha correspondente
    updated_data[row_index]["tags"] = tags_str
    
    # 4. Retornar tabela atualizada e fechar modal
    return (updated_data, False)
```

**Casos Especiais:**
- Se `selected_tags = []`: `tags_str = ""` (limpa tags da linha)
- Se `row_index` inválido: `raise PreventUpdate` (proteção de índice)
- Dados originais NÃO são mutados (safe copy)

---

### 3. Callback de Cancelamento: `cancel_tag_editor_modal`

**Responsabilidade:** Fechar modal sem salvar alterações.

**Inputs:**
- `btn-cancel-tags.n_clicks` → Número de cliques no botão

**Outputs:**
- `modal-tag-editor.is_open` → `False` (fecha modal)
- `dropdown-tag-editor.value` → `[]` (reseta dropdown)

**Lógica:**
```python
def cancel_tag_editor_modal(n_clicks: int) -> tuple:
    if not n_clicks:
        raise PreventUpdate
    
    return (False, [])  # Fechar modal e limpar dropdown
```

---

## Fluxo Completo de Uso

### Passo a Passo

```
1. USUÁRIO CLICA NA CÉLULA DE TAGS
   └─> active_cell = {"row": 1, "column": 5}
   └─> open_tag_editor_modal() é disparado
   └─> Modal abre com tags atuais

2. MODAL ABRE
   └─> Mostra:
       - Dropdown com opções: ["Casa", "Compras", "Moto", "Viagem", "Lazer"]
       - Valores pré-selecionados: ["Moto", "Viagem"]
       - Botões: "Cancelar" e "Salvar Tags"

3. USUÁRIO SELECIONA NOVAS TAGS
   └─> Pode adicionar: ["Moto", "Viagem", "Lazer"]
   └─> Pode remover: ["Viagem"]
   └─> Pode limpar: []

4. USUÁRIO CLICA "SALVAR TAGS"
   └─> selected_tags = ["Moto", "Viagem", "Lazer"]
   └─> save_tags_to_table() é disparado
   └─> Tabela atualizada: row[1]["tags"] = "Moto, Viagem, Lazer"
   └─> Modal fecha

5. NOVO ESTADO
   └─> Tabela mostra novas tags
   └─> Usuário pode clicar em outra célula ou fazer novo clique
```

---

## Dados Compartilhados (Store)

### `store-editing-row-index`

**Finalidade:** Armazenar qual linha está sendo editada.

**Ciclo de Vida:**
```
┌─────────────────────────────────────────┐
│ 1. Abrir Modal                          │
│    └─> data = 1 (índice da linha)      │
├─────────────────────────────────────────┤
│ 2. Editar Tags (modal aberto)           │
│    └─> data continua = 1               │
├─────────────────────────────────────────┤
│ 3. Salvar ou Cancelar                   │
│    └─> data permanece = 1              │
│    └─> (Será resetado no próximo clique)│
└─────────────────────────────────────────┘
```

---

## Estrutura do DataTable

### Colunas (índice 0-based)

| Índice | Nome | ID | Editável | Tipo |
|--------|------|-------|----------|------|
| 0 | Data | data | Não | Text |
| 1 | Descrição | descricao | Sim | Text |
| 2 | Valor | valor | Não | Text |
| 3 | Tipo | tipo | Não | Text |
| 4 | Categoria | categoria | Sim | Dropdown |
| **5** | **Tags** | **tags** | **Não** | **Modal** |

**Importante:** Coluna 5 (tags) é read-only (`editable=False`) porque a edição é feita via modal, não inline.

---

## Componentes do Modal

### Estrutura HTML/Dash

```
Modal: "modal-tag-editor"
├── Header: "Editar Tags"
├── Body:
│   ├── dcc.Dropdown (multi=True):
│   │   ├── id: "dropdown-tag-editor"
│   │   ├── options: Carregadas dinamicamente
│   │   ├── value: Tags atuais (pré-selecionadas)
│   │   └── Multi-select: Ctrl/Cmd + clique
│   │
│   └── div: "Preview de tags selecionadas"
│
└── Footer:
    ├── Botão: "Cancelar" (btn-cancel-tags)
    │   └─> Callback: cancel_tag_editor_modal()
    │
    └── Botão: "Salvar Tags" (btn-save-tags)
        └─> Callback: save_tags_to_table()
```

### Store

```
Store: "store-editing-row-index"
├── data: Índice inteiro (ex: 2)
└── Usado por: save_tags_to_table()
```

---

## Validação e Testes

### Testes Implementados

```
[TESTE 1] Abrindo modal na célula de tags ✓
  - Modal abre (is_open=True)
  - Opções carregadas (5 tags)
  - Valores pré-selecionados corretamente
  - Índice armazenado

[TESTE 2] Evitando abertura em coluna errada ✓
  - PreventUpdate quando col_idx != 5
  - Modal não abre em colunas diferentes

[TESTE 3] Salvando tags na tabela ✓
  - Tags convertidas em string CSV
  - Linha correta atualizada
  - Modal fecha
  - Dados originais não mutados

[TESTE 4] Salvando com lista vazia ✓
  - Limpa tags quando nenhuma selecionada
  - String vazia gerada corretamente

[TESTE 5] Cancelando editor ✓
  - Modal fecha sem salvar
  - Dropdown resetado

[TESTE 6] Fluxo completo de edição ✓
  - Abrir → Selecionar → Salvar
  - End-to-end workflow completo
```

**Resultado:** 6/6 testes passando ✓

---

## Integração com Sistema Existente

### Imports Necessários (Já Presentes em `src/app.py`)

```python
from dash import Input, Output, State  # Decoradores
from dash import ctx                   # Contexto do callback
from dash.exceptions import PreventUpdate

from src.database.operations import get_unique_tags_list  # Carregar tags
```

### Funções Existentes Utilizadas

- `get_unique_tags_list()` → Retorna tags únicas do banco
- `logger.info()` / `logger.warning()` / `logger.error()` → Logging

---

## Fluxo de Dados

```
┌──────────────────────────────────────────────────────────┐
│ USUÁRIO CLICA NA CÉLULA DE TAGS                          │
└─────────────────┬──────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ active_cell    │ {"row": 1, "column": 5}
         │ table_data     │ [..., {"tags": "Moto"}, ...]
         └────────┬───────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ open_tag_editor_modal()      │
    │ ├─ Verificar coluna == 5    │
    │ ├─ Extrair tags da linha     │
    │ ├─ Split por vírgula         │
    │ └─ Carregar opções do banco  │
    └────────┬────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ OUTPUTS:                     │
    │ ├─ modal-tag-editor.is_open  │ True
    │ ├─ dropdown-tag-editor.options
    │ ├─ dropdown-tag-editor.value │ ["Moto", ...]
    │ └─ store-editing-row-index   │ 1
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ MODAL ABRE               │
    │ Usuário seleciona tags   │
    └────────┬─────────────────┘
             │
    ┌────────▼─────────┐
    │ USUÁRIO CLICA    │
    │ "SALVAR TAGS"    │
    └────────┬─────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ save_tags_to_table()       │
    │ ├─ Copiar table_data       │
    │ ├─ Join tags com ", "      │
    │ ├─ Atualizar linha[1]      │
    │ └─ Retornar novo data      │
    └────────┬───────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ OUTPUTS:             │
    │ ├─ preview-table.data │ [..., {"tags": "Moto, ..."}, ...]
    │ └─ modal-tag-editor.is_open │ False
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ MODAL FECHA      │
    │ TABELA ATUALIZADA│
    └──────────────────┘
```

---

## Logging

### Mensagens Registradas

```python
# Abertura do modal
logger.info(f"[TAGS] Modal aberto para linha {row_idx}: {len(tags_list)} tags selecionadas")

# Erro na abertura
logger.error(f"[TAGS] Erro ao abrir editor: {e}")

# Salvamento
logger.info(f"[TAGS] Salvas {len(selected_tags)} tags na linha {row_index}: {tags_str}")

# Erro no salvamento
logger.error(f"[TAGS] Erro ao salvar tags: {e}")

# Cancelamento
logger.info("[TAGS] Modal cancelado")
```

---

## Melhorias Futuras

### Possíveis Extensões

1. **Tag Autocomplete com Histórico**
   - Sugerir tags baseado em histórico de transações
   - Usar `get_classification_history()` para IA

2. **Criação de Novas Tags**
   - Permitir usuário criar tags não existentes
   - Salvar no banco automaticamente

3. **Tag Validation**
   - Comprimento máximo
   - Caracteres permitidos
   - Duplicatas

4. **Confirmação Antes de Limpar**
   - Modal de confirmação se limpar todas as tags
   - Undo/Redo stack

5. **Bulk Edit**
   - Editar tags de múltiplas linhas ao mesmo tempo
   - Multi-select de linhas

---

## Referências

- **Componentes:** [src/components/importer.py](src/components/importer.py) (render_tag_editor_modal)
- **Callbacks:** [src/app.py](src/app.py) (linhas ~3180)
- **Testes:** [tests/validation_tag_editor_callbacks.py](tests/validation_tag_editor_callbacks.py)
- **Database:** [src/database/operations.py](src/database/operations.py) (get_unique_tags_list)

---

**Status:** ✓ Pronto para Produção  
**Data:** Janeiro 24, 2026  
**Versão:** 1.0 - Callbacks Complete
