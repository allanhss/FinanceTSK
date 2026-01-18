# GitHub Copilot Instructions - FinanceTSK

## Contexto do Projeto

Este é um sistema de gestão financeira pessoal desenvolvido em Python usando Dash para interface web local. O projeto tem foco em aprendizado, qualidade de código e uso como portfólio profissional.

## Diretrizes Gerais de Código

### Estilo e Qualidade
- Use **type hints** em todas as funções e métodos
- Docstrings em formato Google Style para todas as funções públicas
- Nomes de variáveis em **português** (mais natural para o contexto brasileiro)
- Nomes de funções e classes em **inglês** (padrão internacional)
- Máximo de 80 caracteres por linha quando possível
- Use **f-strings** para formatação de strings
- Prefira **list/dict comprehensions** quando melhorar legibilidade

### Padrões de Código
```python
# EXEMPLO de função bem documentada:
def calcular_saldo_mensal(receitas: List[float], despesas: List[float]) -> float:
    """
    Calcula o saldo mensal subtraindo despesas das receitas.
    
    Args:
        receitas: Lista com valores de receitas do mês
        despesas: Lista com valores de despesas do mês
        
    Returns:
        Saldo final do mês (positivo = superávit, negativo = déficit)
        
    Example:
        >>> calcular_saldo_mensal([1000, 500], [300, 200])
        1000.0
    """
    total_receitas = sum(receitas)
    total_despesas = sum(despesas)
    return total_receitas - total_despesas
```

## Arquitetura do Projeto

### Banco de Dados
- SQLite local armazenado em pasta sincronizada
- Use SQLAlchemy para operações (não SQL raw)
- Sempre use context managers (with statements)
- Trate exceções de banco explicitamente

### Interface Dash
- Componentes Bootstrap via dash-bootstrap-components
- Callbacks sempre com type hints
- Use dcc.Store para estado global da aplicação
- Prefira componentes funcionais e callbacks separados

### Estrutura de Pastas
- **database/**: Tudo relacionado a persistência de dados
- **pages/**: Páginas completas do Dash (uma por arquivo)
- **components/**: Componentes reutilizáveis (formulários, cards, etc)
- **utils/**: Funções utilitárias e helpers

## Convenções Específicas

### Nomenclatura
```python
# Variáveis e parâmetros: português descritivo
valor_total = 1000.50
data_vencimento = "2026-01-20"
lista_categorias = ["Alimentação", "Transporte"]

# Funções: inglês, verbos no infinitivo
def create_transaction(...)
def update_category(...)
def get_monthly_summary(...)

# Classes: inglês, PascalCase
class Transaction:
class CategoryManager:
class ReportGenerator:

# Constantes: UPPER_CASE
MAX_TRANSACTIONS_PER_PAGE = 50
DEFAULT_CURRENCY = "BRL"
```

### Tratamento de Erros
```python
# SEMPRE use logging ao invés de print
import logging

logger = logging.getLogger(__name__)

try:
    resultado = operacao_banco_dados()
except DatabaseError as e:
    logger.error(f"Erro ao acessar banco: {e}")
    # Retorne erro amigável para o usuário
    return None, "Erro ao salvar dados. Tente novamente."
```

### Callbacks Dash
```python
# Use Input/Output com ids descritivos
@app.callback(
    Output("modal-sucesso", "is_open"),
    Output("tabela-despesas", "data"),
    Input("btn-salvar-despesa", "n_clicks"),
    State("input-valor", "value"),
    State("input-descricao", "value"),
    prevent_initial_call=True
)
def salvar_despesa(
    n_clicks: int,
    valor: float,
    descricao: str
) -> Tuple[bool, List[Dict]]:
    """Salva nova despesa e atualiza tabela."""
    # Implementação
```

## Contexto Brasileiro

### Formatação de Valores
- Moeda: R$ 1.234,56 (ponto para milhar, vírgula para decimal)
- Datas: DD/MM/YYYY ou YYYY-MM-DD para banco
- Use biblioteca babel para formatação de moeda

### Notas Fiscais
- QR Code formato NFC-e/NF-e padrão SEFAZ
- Web scraping deve respeitar robots.txt
- Implemente rate limiting para não sobrecarregar servidores públicos

## Segurança

- NUNCA versione credenciais ou dados pessoais
- Use .env para configurações sensíveis
- Valide TODOS os inputs do usuário
- Sanitize dados antes de inserir no banco

## Performance

- Use lazy loading para grandes datasets
- Implemente paginação em tabelas com +100 registros
- Cache resultados de queries pesadas
- Use Pandas com parcimônia (apenas para análises, não para CRUD simples)

## Testes

```python
# Escreva testes para lógica de negócio crítica
def test_calcular_saldo_negativo():
    """Testa cálculo de saldo com déficit."""
    receitas = [1000]
    despesas = [1500]
    assert calcular_saldo_mensal(receitas, despesas) == -500
```

## Documentação

- README atualizado a cada feature nova
- Comentários explicam "por quê", não "o quê"
- Use TODO/FIXME/HACK para marcar pendências
- Mantenha CHANGELOG.md para versões

## Dicas para Gerar Código Melhor

Ao solicitar código ao Copilot, use comentários detalhados:

```python
# COPILOT: Crie uma função para importar extrato bancário CSV
# Formato esperado: Data;Descrição;Valor;Saldo
# Deve:
# 1. Validar se o arquivo existe e é legível
# 2. Detectar encoding automaticamente (utf-8 ou latin1)
# 3. Converter valores de string "1.234,56" para float
# 4. Retornar DataFrame do pandas
# 5. Logar erros e avisar sobre linhas problemáticas
# 6. Incluir docstring completa
```

---

**Última Atualização**: Janeiro 2026
**Versão das Instruções**: 1.0