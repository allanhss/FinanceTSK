# Nubank CSV Importer - Documentação

## Visão Geral

O módulo `src/utils/importers.py` implementa o parser inteligente para extratos do Nubank em formato CSV, distinguindo automaticamente entre dois formatos:

1. **Cartão de Crédito** - Formato: `date`, `title`, `amount`
2. **Conta Corrente** - Formato: `data`, `descrição`, `valor`

---

## API Pública

### `clean_header(header_list: List[str]) -> List[str]`

Normaliza headers CSV para comparação (lowercase + strip).

**Exemplo:**
```python
from src.utils.importers import clean_header

headers = ["Data", " Valor ", "DESCRIÇÃO"]
result = clean_header(headers)
# ['data', 'valor', 'descrição']
```

---

### `parse_upload_content(contents: str, filename: str) -> List[Dict[str, Any]]`

Parser principal que detecta formato e normaliza dados CSV.

**Parâmetros:**
- `contents` (str): Conteúdo base64 do arquivo CSV
- `filename` (str): Nome original do arquivo (para logging)

**Retorna:**
```python
[
    {
        "data": "2025-01-15",           # ISO format (YYYY-MM-DD)
        "descricao": "Padaria do João", # String
        "valor": 45.50,                 # Float positivo
        "tipo": "despesa",              # "receita" ou "despesa"
        "categoria": "A Classificar"    # Default
    },
    ...
]
```

**Erros:**
- Levanta `ValueError` se formato não for reconhecido
- Levanta `ValueError` se CSV está vazio
- Registra warnings para linhas inválidas (ignora-as)

**Exemplo:**
```python
import base64
from src.utils.importers import parse_upload_content

# Lê arquivo e converte para base64
with open("extrato_cartao.csv", "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

# Parse
try:
    transactions = parse_upload_content(encoded, "extrato_cartao.csv")
    print(f"Importadas {len(transactions)} transações")
except ValueError as e:
    print(f"Erro: {e}")
```

---

## Formatos Suportados

### Cartão de Crédito (Nubank)

**Headers esperados:** `date`, `title`, `amount`

**Formato de data:** `YYYY-MM-DD` (ISO)

**Lógica de sinal:**
| Valor CSV | Tipo Gerado | Motivo |
|-----------|-------------|--------|
| `+50.00` | `despesa` | Gasto no cartão |
| `-10.00` | `receita` | Crédito/Devolução |
| `0.00` | (ignorado) | Não processado |

**Exemplo de CSV:**
```csv
date,title,amount
2025-01-15,Padaria do João,45.50
2025-01-16,Supermercado X,-10.00
2025-01-17,Devolução,0.00
```

**Resultado:**
```python
[
    {
        "data": "2025-01-15",
        "descricao": "Padaria do João",
        "valor": 45.50,
        "tipo": "despesa",
        "categoria": "A Classificar"
    },
    {
        "data": "2025-01-16",
        "descricao": "Supermercado X",
        "valor": 10.00,
        "tipo": "receita",
        "categoria": "A Classificar"
    }
]
```

---

### Conta Corrente (Nubank)

**Headers esperados:** `data`, `descrição`, `valor` (ou `descricao`)

**Formato de data:** `DD/MM/YYYY` (Brasileiro) → Convertido para ISO `YYYY-MM-DD`

**Lógica de sinal:**
| Valor CSV | Tipo Gerado | Motivo |
|-----------|-------------|--------|
| `+500.00` | `receita` | Depósito/Transferência recebida |
| `-150.75` | `despesa` | Saque/Transferência enviada |
| `0.00` | (ignorado) | Não processado |

**Exemplo de CSV:**
```csv
data,descrição,valor
15/01/2025,Transferência recebida,500.00
16/01/2025,Pagamento conta,-150.75
17/01/2025,Depósito,0.00
```

**Resultado:**
```python
[
    {
        "data": "2025-01-15",
        "descricao": "Transferência recebida",
        "valor": 500.00,
        "tipo": "receita",
        "categoria": "A Classificar"
    },
    {
        "data": "2025-01-16",
        "descricao": "Pagamento conta",
        "valor": 150.75,
        "tipo": "despesa",
        "categoria": "A Classificar"
    }
]
```

---

## Tratamento de Casos Especiais

### Valores Zerados
Linhas com valor = 0.00 são automaticamente ignoradas (warning logged).

### Descrição Vazia
Se a descrição estiver vazia, é substituída por `"Sem descrição"`.

### Formato de Números
- **Ponto decimal**: `1234.56` → OK
- **Vírgula decimal** (brasileira): `1234,56` → Convertido automaticamente

### Headers com Espaços
Headers são normalizados (trim + lowercase) antes da comparação.

---

## Integração com Dash Upload

Para integrar com componente de upload Dash:

```python
import base64
from dash.dependencies import Input, Output, State
from src.utils.importers import parse_upload_content

@app.callback(
    Output("transactions-store", "data"),
    Input("upload-button", "n_clicks"),
    State("upload-area", "contents"),
    State("upload-area", "filename"),
)
def handle_upload(n_clicks, contents, filename):
    if not contents:
        return []
    
    try:
        # Extrai base64 do formato Dash
        content_type, encoded = contents.split(",")
        
        # Parse
        transactions = parse_upload_content(encoded, filename)
        
        # Salva no banco de dados
        for tx in transactions:
            create_transaction(
                data=tx["data"],
                descricao=tx["descricao"],
                valor=tx["valor"],
                tipo=tx["tipo"],
                categoria_id=None,
                categoria_nome=tx["categoria"],
            )
        
        return {
            "status": "success",
            "count": len(transactions),
            "message": f"Importadas {len(transactions)} transações"
        }
    
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }
```

---

## Testes

Execute os testes com:
```bash
python tests/test_nubank_importers.py
```

Cobertura de testes:
- ✅ Normalização de headers
- ✅ Parsing de cartão de crédito
- ✅ Parsing de conta corrente
- ✅ Conversão de formatos de data
- ✅ Detecção de formato inválido
- ✅ Casos especiais (valores zero, descrição vazia, etc)

---

## Logging

O módulo usa `logging` em vez de `print()`. Configure o logger:

```python
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("src.utils.importers")
```

**Níveis de log:**
- `WARNING`: Linhas com dados inválidos/incompletos
- `ERROR`: Formato não reconhecido ou erro de processamento
- `INFO`: (reservado para futuros usos)

---

## Limitações Conhecidas

1. **Múltiplos arquivos**: Processa um arquivo por vez (loop necessário no front-end)
2. **Formato flexível**: Não valida se os dados fazem sentido financeiramente
3. **Transações duplicadas**: Não detecta importações duplicadas (fazer no banco de dados)
4. **Categorias automáticas**: Todas as transações recebem categoria "A Classificar" (ML futuro)

---

## Roadmap Futuro

- [ ] Suporte a mais bancos (Itaú, Bradesco, Caixa)
- [ ] Detecção automática de categorias por keywords
- [ ] Suporte a importação recorrente (agendada)
- [ ] Validação de duplicatas no banco antes de insert
- [ ] Formatação automática de descrições (trim, uppercase)

---

**Versão**: 1.0  
**Data**: Janeiro 22, 2026  
**Status**: Produção
