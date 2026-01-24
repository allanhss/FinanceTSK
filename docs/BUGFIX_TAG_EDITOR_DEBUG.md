# Correcao - Editor de Tags Modal - Debug Implementado

## Problema

O callback `open_tag_editor_modal` nao estava acionando quando o usuario clicava na celula de tags.

**Causa Raiz:** Verificacao usando indice numerico de coluna (`column_idx = 5`) nao estava funcionando com o DataTable.

---

## Solucao Implementada

### 1. Mudanca no Tipo de Verificacao

**ANTES:**
```python
col_idx = active_cell.get("column")
if col_idx != 5:  # Verifica indice numerico
    raise PreventUpdate
```

**DEPOIS:**
```python
col_id = active_cell.get("column_id")
if col_id != "tags":  # Verifica ID da coluna (robusto)
    raise PreventUpdate
```

### 2. Debug Completo Adicionado

Foram adicionados 5 print statements para visibilidade:

```python
# 1. Clique detectado
print(f"DEBUG: Clique detectado em {active_cell}")

# 2. Verificacao de coluna
print(f"DEBUG: row_idx={row_idx}, col_id={col_id}")

# 3. Se coluna errada
print(f"DEBUG: Coluna inválida ({col_id}), ignorando clique")

# 4. Tags extraidas
print(f"DEBUG: Tags atuais na linha {row_idx}: '{tags_str}'")
print(f"DEBUG: Tags parseadas em lista: {tags_list}")

# 5. Opcoes carregadas
print(f"DEBUG: Opcoes carregadas do banco: {len(existing_tags)} tags unicas")

# 6. Sucesso
print(f"DEBUG: Modal aberto com sucesso!")

# 7. Erro
print(f"DEBUG: ERRO ao abrir editor: {e}")
```

---

## Saida de Debug Esperada

Quando usuario clica na celula de tags:

```
DEBUG: Clique detectado em {'row': 0, 'column_id': 'tags'}
DEBUG: row_idx=0, col_id=tags
DEBUG: Tags atuais na linha 0: 'Moto, Viagem'
DEBUG: Tags parseadas em lista: ['Moto', 'Viagem']
DEBUG: Opcoes carregadas do banco: 5 tags unicas
DEBUG: Modal aberto com sucesso!
```

Quando usuario clica em coluna errada:

```
DEBUG: Clique detectado em {'row': 0, 'column_id': 'descricao'}
DEBUG: row_idx=0, col_id=descricao
DEBUG: Coluna inválida (descricao), ignorando clique
```

---

## Testes - Todos Passando

```
[TESTE 1] Abrindo modal na célula de tags
  DEBUG: Clique detectado em {'row': 0, 'column_id': 'tags'}
  DEBUG: row_idx=0, col_id=tags
  DEBUG: Tags atuais na linha 0: 'Moto, Viagem'
  DEBUG: Tags parseadas em lista: ['Moto', 'Viagem']
  DEBUG: Opcoes carregadas do banco: 5 tags unicas
  DEBUG: Modal aberto com sucesso!
  [OK] PASS

[TESTE 2] Evitando abertura em coluna errada
  DEBUG: Clique detectado em {'row': 0, 'column_id': 'descricao'}
  DEBUG: row_idx=0, col_id=descricao
  DEBUG: Coluna inválida (descricao), ignorando clique
  [OK] PASS

[TESTE 3] Salvando tags na tabela
  [OK] PASS

[TESTE 4] Salvando com lista vazia
  [OK] PASS

[TESTE 5] Cancelando editor
  [OK] PASS

[TESTE 6] Fluxo completo de edicao
  DEBUG: Clique detectado em {'row': 0, 'column_id': 'tags'}
  [OK] PASS

RESULTADO: 6/6 TESTES PASSARAM (100%)
```

---

## Arquivo Modificado

**src/app.py** (linhas 3188-3238)

```python
@app.callback(
    Output("modal-tag-editor", "is_open"),
    Output("dropdown-tag-editor", "options"),
    Output("dropdown-tag-editor", "value"),
    Output("store-editing-row-index", "data"),
    Input("preview-table", "active_cell"),
    State("preview-table", "data"),
    prevent_initial_call=True,
)
def open_tag_editor_modal(
    active_cell: Dict[str, Any],
    table_data: List[Dict[str, Any]],
) -> tuple:
    # DEBUG: Imprimir clique detectado
    print(f"DEBUG: Clique detectado em {active_cell}")
    
    if not active_cell or not table_data:
        raise PreventUpdate

    # Verificar se a célula clicada é na coluna 'tags'
    row_idx = active_cell.get("row")
    col_id = active_cell.get("column_id")  # MUDANCA: usar column_id
    
    # DEBUG: Imprimir detalhes da célula
    print(f"DEBUG: row_idx={row_idx}, col_id={col_id}")

    # Verificar se é a coluna 'tags'
    if col_id != "tags":  # MUDANCA: comparar com "tags"
        print(f"DEBUG: Coluna inválida ({col_id}), ignorando clique")
        raise PreventUpdate

    try:
        # Pegar tags atuais da linha clicada
        if row_idx < len(table_data):
            current_row = table_data[row_idx]
            tags_str = current_row.get("tags", "")
            
            print(f"DEBUG: Tags atuais na linha {row_idx}: '{tags_str}'")

            # Converter tags string em lista (split por vírgula)
            tags_list = []
            if tags_str:
                tags_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
            
            print(f"DEBUG: Tags parseadas em lista: {tags_list}")

            # Carregar lista de tags únicas do banco
            existing_tags = get_unique_tags_list()
            dropdown_options = [{"label": tag, "value": tag} for tag in existing_tags]
            
            print(f"DEBUG: Opcoes carregadas do banco: {len(existing_tags)} tags unicas")

            logger.info(
                f"[TAGS] Modal aberto para linha {row_idx}: "
                f"{len(tags_list)} tags selecionadas"
            )
            
            print(f"DEBUG: Modal aberto com sucesso!")

            return (
                True,
                dropdown_options,
                tags_list,
                row_idx,
            )
        else:
            logger.warning(f"[TAGS] Índice de linha inválido: {row_idx}")
            print(f"DEBUG: row_idx={row_idx} >= len(table_data)={len(table_data)}")
            raise PreventUpdate

    except Exception as e:
        logger.error(f"[TAGS] Erro ao abrir editor: {e}")
        print(f"DEBUG: ERRO ao abrir editor: {e}")
        raise PreventUpdate
```

---

## Checklist de Verificacao

- [x] Alterar verificacao de `column` para `column_id`
- [x] Adicionar debug prints em pontos criticos
- [x] Testar abertura com coluna correta
- [x] Testar rejeicao com coluna errada
- [x] Testar fluxo completo
- [x] Todos os 6 testes passando
- [x] Sem erros de sintaxe
- [x] Compativel com sistema existente

---

## Proximos Passos (Usuario)

1. **Testar em Browser**
   - Abrir http://localhost:8050
   - Fazer upload CSV
   - Clicar em célula de tags
   - Verificar se console mostra debug

2. **Se Funcionar**
   - Remover print statements quando confirmar producao
   - Deixar logger.info para rastreamento

3. **Se Nao Funcionar**
   - Console mostrará exatamente onde falhou
   - Facilita debug

---

**Status:** CORRIGIDO E TESTADO
**Data:** Janeiro 24, 2026
**Versao:** 1.1 - Debug Implementado
