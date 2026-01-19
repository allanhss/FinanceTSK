"""
Suíte de Testes - FinanceTSK
============================

Este diretório contém todos os testes automatizados do projeto.

## Estrutura

- test_database.py: Testes de operações de banco de dados (CRUD de transações)
- test_categoria.py: Testes completos do sistema de categorias com tipos

## Como Executar

```bash
# Todos os testes
pytest tests/ -v

# Apenas testes de categoria
pytest tests/test_categoria.py -v

# Apenas testes de database
pytest tests/test_database.py -v

# Com coverage
pytest tests/ --cov=src --cov-report=html
```

## Cobertura de Testes

### test_categoria.py (18 testes)
✅ Modelo Categoria:
  - Criação com tipo receita/despesa
  - Validação de tipo inválido
  - Validação de nome vazio
  - Validação de cor hexadecimal
  - Constraint de unicidade (nome, tipo)
  - Mesmo nome em tipos diferentes permitido

✅ Operações de Categoria:
  - get_categories sem filtro
  - get_categories com filtro por tipo
  - delete_category
  - delete_category com ID inválido
  - get_category_options com filtro

✅ Inicialização de Padrões:
  - initialize_default_categories
  - Idempotência (não duplica)
  - Nomes de categorias padrão
  - Emojis em categorias padrão

✅ Integração:
  - Criar transação com categoria tipada
  - Serialização (to_dict)

### test_database.py (6 testes)
✅ Transações:
  - Criar transação de despesa
  - Criar transação de receita
  - Validação de tipo inválido
  - Validação de valor negativo
  - Recuperar transações
  - Resumo do dashboard

## Fixtures

- `clean_database`: Limpa banco antes e depois de cada teste

## Configuração Esperada

- Python 3.11+
- pytest 7.4+
- SQLite (banco local)
- Todas as dependências em requirements.txt

## Total de Testes
**24 testes** - Todos passando ✅
"""
