# Nubank Importer UI Component - Documentação

## Visão Geral

O módulo `src/components/importer.py` fornece a interface Dash completa para importação de extratos CSV do Nubank, incluindo upload, pré-visualização editável e confirmação.

---

## Funções Disponíveis

### `render_importer_page() -> dbc.Container`

Função principal que renderiza a página completa de importação.

**Componentes inclusos:**
- Upload area com drag-and-drop
- Store temporário para dados
- Container de pré-visualização
- Botões de ação (Confirmar, Limpar)
- Div de feedback de mensagens

**Exemplo:**
```python
from src.components.importer import render_importer_page

page = render_importer_page()
# Use em app.py como:
# html.Div(render_importer_page(), id="importador-page")
```

---

### `render_preview_table(data: List[Dict]) -> dbc.Card`

Renderiza a tabela de pré-visualização das transações.

**Parâmetros:**
- `data` (List[Dict]): Lista de dicionários com transações

**Estrutura de cada transação:**
```python
{
    "data": "2025-01-15",           # ISO format
    "descricao": "Padaria do Joao", # String
    "valor": 45.50,                 # Float
    "tipo": "despesa",              # "receita" ou "despesa"
    "categoria": "Alimentacao"      # String
}
```

**Retorna:**
- `dbc.Card` com `DataTable` editável se houver dados
- `html.Div` vazio se `data` estiver vazio

**Características da tabela:**
- ✅ Linhas deletáveis (X button)
- ✅ Coluna "Descrição" editável
- ✅ Coluna "Categoria" editável
- ✅ Formatação monetária brasileira (R$ X,XX)
- ✅ Ícones para Receita (💰) e Despesa (💸)
- ✅ Alternância de cores de linha (striped)

**Exemplo:**
```python
from src.components.importer import render_preview_table

dados = [
    {
        "data": "2025-01-15",
        "descricao": "Padaria",
        "valor": 45.50,
        "tipo": "despesa",
        "categoria": "Alimentacao"
    }
]

table = render_preview_table(dados)
```

---

### `render_import_success(count: int) -> dbc.Alert`

Renderiza alerta de sucesso após importação.

**Parâmetros:**
- `count` (int): Número de transações importadas

**Exemplo:**
```python
alert = render_import_success(42)
# Mostra: "✅ Importação Concluída com Sucesso! Foram importadas 42 transações..."
```

---

### `render_import_error(message: str) -> dbc.Alert`

Renderiza alerta de erro.

**Parâmetros:**
- `message` (str): Mensagem de erro

**Exemplo:**
```python
alert = render_import_error("Arquivo CSV inválido")
# Mostra: "❌ Erro na Importação: Arquivo CSV inválido"
```

---

### `render_import_info(message: str) -> dbc.Alert`

Renderiza alerta informativo.

**Parâmetros:**
- `message` (str): Mensagem informativa

**Exemplo:**
```python
alert = render_import_info("Processando arquivo...")
# Mostra: "Processando arquivo..." em tom informativo
```

---

## IDs de Componentes

Para usar com callbacks Dash:

| ID | Tipo | Descrição |
|----|------|-----------|
| `upload-data` | `dcc.Upload` | Área de upload de arquivo |
| `upload-status` | `html.Div` | Status da upload (preenchido por callback) |
| `store-import-data` | `dcc.Store` | Store com dados das transações |
| `store-import-status` | `dcc.Store` | Store com status da importação |
| `preview-container` | `html.Div` | Container para a tabela de pré-visualização |
| `table-import-preview` | `DataTable` | Tabela de dados (quando renderizada) |
| `btn-save-import` | `dbc.Button` | Botão de confirmar importação |
| `btn-clear-import` | `dbc.Button` | Botão de limpar dados |
| `import-feedback` | `html.Div` | Container para mensagens de feedback |

---

## Integração com Callbacks

### Exemplo 1: Upload e Parser

```python
from dash import callback, Input, Output, State
from dash.exceptions import PreventUpdate
import base64
from src.utils.importers import parse_upload_content
from src.components.importer import render_preview_table

@callback(
    Output("store-import-data", "data"),
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def process_upload(contents, filename):
    if not contents:
        raise PreventUpdate
    
    try:
        # Extract base64 from Dash format
        content_type, encoded = contents.split(",")
        
        # Parse CSV
        transactions = parse_upload_content(encoded, filename)
        
        # Store data and show preview
        return (
            transactions,  # Store data
            html.Div(
                f"Carregado: {filename} ({len(transactions)} transacoes)",
                className="alert alert-success"
            )
        )
    except ValueError as e:
        return (
            None,
            html.Div(str(e), className="alert alert-danger")
        )
```

### Exemplo 2: Renderizar Pré-visualização

```python
@callback(
    Output("preview-container", "children"),
    Output("btn-save-import", "disabled"),
    Output("btn-clear-import", "disabled"),
    Input("store-import-data", "data"),
)
def render_preview(data):
    if not data:
        return [], True, True
    
    preview = render_preview_table(data)
    return preview, False, False
```

### Exemplo 3: Confirmar Importação

```python
@callback(
    Output("import-feedback", "children"),
    Output("store-import-data", "data"),
    Output("store-import-status", "data"),
    Input("btn-save-import", "n_clicks"),
    State("table-import-preview", "data"),  # Dados editados
    prevent_initial_call=True,
)
def save_import(n_clicks, edited_data):
    if not edited_data:
        raise PreventUpdate
    
    try:
        # Convert table format back to transaction format
        count = 0
        for row in edited_data:
            # Insert into database
            create_transaction(
                data=row["data"],
                descricao=row["descricao"],
                valor=parse_valor(row["valor"]),  # Parse R$ format
                tipo=parse_tipo(row["tipo"]),     # Extract from emoji
                categoria_nome=row["categoria"],
            )
            count += 1
        
        from src.components.importer import render_import_success
        
        return (
            render_import_success(count),
            None,  # Clear store
            {"imported": True, "count": count}
        )
    except Exception as e:
        from src.components.importer import render_import_error
        return render_import_error(str(e)), None, {"imported": False}
```

### Exemplo 4: Limpar Dados

```python
@callback(
    Output("store-import-data", "data"),
    Output("preview-container", "children"),
    Output("upload-status", "children"),
    Output("btn-save-import", "disabled"),
    Output("btn-clear-import", "disabled"),
    Input("btn-clear-import", "n_clicks"),
    prevent_initial_call=True,
)
def clear_import(n_clicks):
    return None, [], [], True, True
```

---

## Styling e Customização

### Classes CSS Utilizadas

- `.shadow-sm` - Sombra leve nos cards
- `.border-0` - Remove borda padrão
- `.bg-light` - Fundo claro
- `.text-muted` - Texto acinzentado
- `.small` - Texto pequeno
- `.alert` - Alerta de feedback
- `.py-4` - Padding vertical

### Cores Bootstrap

- `success` - Verde (confirmação)
- `danger` - Vermelho (erro)
- `info` - Azul (informação)
- `secondary` - Cinza (cancelamento)

### Customizando Upload Style

```python
# No render_importer_page(), edite o style do Upload:
style={
    "width": "100%",
    "height": "250px",  # Aumentar altura
    "lineHeight": "60px",
    "borderWidth": "3px",  # Borda mais grossa
    "borderStyle": "dashed",
    "borderRadius": "15px",
    "backgroundColor": "#e7f3ff",  # Cor customizada
    # ...
}
```

---

## Tratamento de Erros Comuns

### "Formato CSV não reconhecido"
→ Certifique-se que o arquivo é do Nubank (Cartão ou Conta)
→ Use `parse_upload_content()` do módulo importers.py

### Tabela não aparece
→ Verifique se `store-import-data` tem dados
→ Callback de renderização pode não estar configurado
→ Teste com `render_preview_table([{...}])` diretamente

### Valores não formatados corretamente
→ A formatação (R$ X,XX) é apenas visual
→ Parse o valor parseando com `float()` antes de salvar
→ Use helper: `valor_limpo = float(row["valor"].replace("R$ ", "").replace(",", "."))`

---

## Testes

Execute com:
```bash
python tests/test_importer_component.py
```

Cobertura:
- ✅ Estrutura da página
- ✅ Renderização de tabela com dados
- ✅ Renderização vazia
- ✅ Alertas de sucesso, erro e info
- ✅ Formatação de moeda
- ✅ Ícones de tipo
- ✅ Importação de módulo

---

## Roadmap

- [ ] Suporte a múltiplas uploads simultâneas
- [ ] Validação de regras de negócio (valores mínimos, categorias válidas)
- [ ] Exportar transações rejeitadas em PDF
- [ ] Histórico de importações
- [ ] Desfazer última importação

---

**Versão**: 1.0  
**Data**: Janeiro 22, 2026  
**Status**: Produção
