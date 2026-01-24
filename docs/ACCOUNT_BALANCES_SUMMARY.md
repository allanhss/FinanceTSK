# Função: get_account_balances_summary()

## 📋 Descrição

Calcula e retorna um resumo estruturado de saldos de contas agrupados por tipo para o Dashboard Multi-Contas.

## 🎯 Uso

```python
from src.database.operations import get_account_balances_summary

# Obter resumo de saldos
resumo = get_account_balances_summary()

# Acessar totais
print(f"Liquidez: R$ {resumo['total_disponivel']:,.2f}")
print(f"Investido: R$ {resumo['total_investido']:,.2f}")
print(f"Dívida: R$ {resumo['total_cartoes']:,.2f}")
print(f"Patrimônio Total: R$ {resumo['patrimonio_total']:,.2f}")

# Iterar detalhes por conta
for conta_info in resumo['detalhe_por_conta']:
    print(f"{conta_info['nome']}: R$ {conta_info['saldo']:,.2f}")
```

## 📊 Estrutura de Retorno

```python
{
    "total_disponivel": 5010.0,      # Soma de contas correntes
    "total_investido": 25000.0,      # Soma de investimentos
    "total_cartoes": 2410.10,        # Soma de cartões (dívida)
    "patrimonio_total": 32420.10,    # Soma total de todos os tipos
    "detalhe_por_conta": [           # Lista com detalhe de cada conta
        {
            "id": 1,
            "nome": "Nubank",
            "tipo": "conta",
            "saldo": 5010.0,
            "cor_tipo": "#3B82F6",   # Cor hexadecimal para UI
        },
        {
            "id": 2,
            "nome": "XP Investimentos",
            "tipo": "investimento",
            "saldo": 25000.0,
            "cor_tipo": "#10B981",
        },
        {
            "id": 3,
            "nome": "Visa",
            "tipo": "cartao",
            "saldo": -89.90,
            "cor_tipo": "#EF4444",
        },
    ]
}
```

## 🔍 Tipos de Conta Suportados

| Tipo | Label | Cor | Uso |
|------|-------|-----|-----|
| `conta` | Liquidez/Contas Correntes | #3B82F6 (Azul) | Dinheiro disponível |
| `investimento` | Investimentos | #10B981 (Verde) | Patrimônio investido |
| `cartao` | Dívida/Cartões | #EF4444 (Vermelho) | Dívida de curto prazo |

## ⚙️ Cálculo de Saldo

Para cada conta, o saldo é calculado como:

```
Saldo = Saldo Inicial + Receitas - Despesas
```

Exemplo:
```
Conta Nubank
├─ Saldo Inicial: R$ 5.000
├─ + Receita "Salário": R$ 3.000
├─ - Despesa "Supermercado": R$ -R$ 250
└─ = Saldo Final: R$ 7.750
```

## 📈 Casos de Uso

### 1. Dashboard Principal
Mostrar cards com resumo do patrimônio:

```python
resumo = get_account_balances_summary()

# Cards KPI
total_liquido = resumo['total_disponivel']
total_investido = resumo['total_investido']
patrimonio = resumo['patrimonio_total']
```

### 2. Visualização por Tipo
Agrupar contas por categoria financeira:

```python
# Estruturar dados para gráficos de pizza
categorias = {
    "Liquidez": resumo['total_disponivel'],
    "Investimentos": resumo['total_investido'],
    "Dívida": abs(resumo['total_cartoes']),  # Mostrar como valor absoluto
}
```

### 3. Grid de Contas
Renderizar lista detalhada:

```python
for conta in resumo['detalhe_por_conta']:
    # Renderizar card com:
    # - Nome da conta
    # - Tipo (com ícone)
    # - Saldo (com cor)
```

## 🔧 Implementação Técnica

**Localização:** `src/database/operations.py`

**Dependências:**
- `joinedload()` para evitar "Detached Instance" errors
- Suporte para cálculo dinâmico de saldos
- Session management com context manager

**Tratamento de Erros:**
- Retorna estrutura zerada em caso de erro
- Logs detalhados para debug
- Validação de tipos de conta

## ✅ Testes

Execute a suíte de testes:

```bash
pytest tests/test_account_balances_summary.py -v
```

**Testes implementados:**
- `test_empty_accounts` - Sem contas
- `test_single_account_with_saldo_inicial` - Uma conta com saldo inicial
- `test_multiple_accounts_different_types` - Múltiplos tipos
- `test_accounts_with_transactions` - Com transações
- `test_structure_keys` - Validação de estrutura
- `test_detalhe_per_conta_structure` - Validação de items
- `test_color_mapping` - Validação de cores por tipo

## 🚀 Validação Prática

Execute o script de validação:

```bash
python tests/validation_account_balances.py
```

Este script:
1. Cria dados de exemplo
2. Calcula o resumo
3. Exibe formatado para visualização

## 📝 Notas

- Cores são em formato hexadecimal com prefixo `#` para uso direto em CSS/UI
- Cartões geralmente têm saldo negativo (dívida)
- Função é thread-safe (usa session management)
- Performance: O(n) onde n = número de contas + transações

## 🔮 Possíveis Extensões

1. **Filtro por Data:** Adicionar `start_date` e `end_date` para saldo em período
2. **Conversão de Moeda:** Suportar múltiplas moedas com taxas
3. **Previsão:** Incluir parcelações futuras no cálculo
4. **Histórico:** Retornar evolução do saldo ao longo do tempo
