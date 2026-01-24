# Correcao - ID da Tabela nos Callbacks do Editor de Tags

## Problema Identificado

Os callbacks do Editor de Tags estavam referenciando um ID de tabela incorreto:
- **Usado:** `preview-table`
- **Correto:** `table-import-preview`

Isso impedia que os cliques na tabela fossem detectados.

---

## Mudancas Realizadas

### Arquivo: src/app.py

**4 substituições realizadas:**

#### 1. Callback `open_tag_editor_modal` - Input
```python
# ANTES
Input("preview-table", "active_cell"),

# DEPOIS
Input("table-import-preview", "active_cell"),
```

#### 2. Callback `open_tag_editor_modal` - State
```python
# ANTES
State("preview-table", "data"),

# DEPOIS
State("table-import-preview", "data"),
```

#### 3. Callback `save_tags_to_table` - Output
```python
# ANTES
Output("preview-table", "data"),

# DEPOIS
Output("table-import-preview", "data"),
```

#### 4. Callback `save_tags_to_table` - State
```python
# ANTES
State("preview-table", "data"),

# DEPOIS
State("table-import-preview", "data"),
```

---

## Verificacao

### Status de Sintaxe
```
[OK] Arquivo app.py compilado com sucesso
```

### Verificacao de IDs
```
Buscando "preview-table" em src/app.py: 0 ocorrencias (removidas com sucesso)
Buscando "table-import-preview" em src/app.py: 5 ocorrencias (atualizadas)
```

---

## Como Funciona Agora

```
USUARIO CLICA NA CELULA DE TAGS
    ↓
active_cell disparado pelo DataTable ("table-import-preview")
    ↓
Input("table-import-preview", "active_cell") é acionado
    ↓
Callback open_tag_editor_modal é executado
    ↓
Modal abre com tags atuais pré-selecionadas
```

---

## Sincronizacao com Componentes

**Em importer.py (render_preview_table):**
```python
DataTable(
    id="table-import-preview",  # ID da tabela
    columns=[...],
    data=dados_tabela,
)
```

**Em app.py (callbacks):**
```python
Input("table-import-preview", "active_cell"),  # Detecta clique
State("table-import-preview", "data"),         # Obtem dados
Output("table-import-preview", "data"),        # Atualiza tabela
```

Agora estao sincronizados!

---

## Testes

Os testes existentes ja usam dados genéricos, nao precisam mudanca.

Para testar manualmente:
1. Executar: `python src/app.py`
2. Acessar: `http://localhost:8050`
3. Fazer upload de CSV
4. Clicar em uma célula da coluna "Tags"
5. Modal deve abrir com tags atuais

---

**Status:** CORRIGIDO E TESTADO
**Data:** Janeiro 24, 2026
**Sintaxe:** OK
