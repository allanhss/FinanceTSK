# 🎓 Técnicas de Prompt Engineering

## Princípio #1: Contexto é Rei 👑

Crie uma função para salvar uma receita no banco SQLite
Contexto: Tabela 'receitas' com colunas: id, descricao, valor, data, pessoa_origem, categoria
Deve usar SQLAlchemy Session, fazer commit e retornar o ID ou None se erro
Incluir type hints e docstring completa

## Princípio #2: Seja Específico sobre Formato

Valide CPF brasileiro
Input: string com ou sem formatação (123.456.789-10 ou 12345678910)
Output: tuple (bool, str) onde bool indica validade e str a mensagem de erro
Regras: verificar dígitos verificadores, remover formatação antes de validar
Exemplo: validate_cpf("123.456.789-10") -> (True, "") ou (False, "CPF inválido")

## Princípio #3: Use Estrutura em Blocos
=============================================================================
Sistema de Categorização Automática de Despesas

OBJETIVO:
Criar classe que analisa descrição de despesa e sugere categoria

REQUISITOS:
1. Classe CategoryPredictor com método predict(descricao: str) -> str
2. Usar palavras-chave em dicionário KEYWORDS = {"Alimentação": [...], ...}
3. Se nenhuma palavra-chave corresponder, retornar "Outros"
4. Método deve ser case-insensitive
5. Incluir método add_keyword(categoria: str, palavra: str) para aprendizado

CATEGORIAS INICIAIS:
- Alimentação: mercado, padaria, restaurante, ifood, delivery
- Transporte: uber, taxi, gasolina, combustível, pedágio
- Moradia: aluguel, condomínio, água, luz, energia
- Lazer: cinema, streaming, netflix, spotify

EXEMPLO DE USO:
predictor = CategoryPredictor()
predictor.predict("Compra no mercado Extra") -> "Alimentação"
predictor.predict("Uber para escritório") -> "Transporte"
=============================================================================

## Princípio #4: Peça Exemplos e Testes
=============================================================================
Função para formatar valor monetário brasileiro
Input: float (ex: 1234.56)
Output: string formatada "R$ 1.234,56"

INCLUA:
- Type hints completos
- Docstring com 3 exemplos
- Tratamento de valores negativos (mostrar com sinal -)
- Teste unitário no final (usando assert)
#
Exemplo esperado:
>>> format_brl(1234.56)
'R$ 1.234,56'
>>> format_brl(-500)
'R$ -500,00'
=============================================================================

# 🎯 Prompts por Contexto

## Para Models (database/models.py)
=============================================================================
Defina o modelo SQLAlchemy para a tabela 'transacoes'

SCHEMA:
- id: Integer, primary key, autoincrement
- tipo: String(20), não nulo, valores: 'receita' ou 'despesa'
- descricao: String(200), não nulo
- valor: Float, não nulo, deve ser positivo
- data: Date, não nulo
- categoria_id: Integer, foreign key para tabela 'categorias'
- pessoa: String(100), nullable (apenas para receitas)
- tags: String(500), nullable, armazena JSON de lista
- created_at: DateTime, default now()
- updated_at: DateTime, onupdate now()

REQUISITOS:
- Usar declarative_base() como Base
- Incluir __repr__ legível
- Incluir método to_dict() que retorna dicionário
- Validar valor > 0 no __init__
- Converter tags de/para JSON automaticamente
=============================================================================


## Para Operations (database/operations.py)
=============================================================================
Função CRUD para criar nova despesa

ASSINATURA:
def create_despesa(
    descricao: str,
    valor: float,
    data: date,
    categoria: str,
    tags: List[str] = None
) -> Tuple[Optional[int], str]

COMPORTAMENTO:
1. Validar inputs (valor > 0, descricao não vazia, data não futura)
2. Criar sessão SQLAlchemy com context manager
3. Verificar se categoria existe, criar se não existir
4. Criar objeto Transacao com tipo='despesa'
5. Fazer commit e retornar (id_criado, "Sucesso")
6. Em caso de erro, fazer rollback e retornar (None, "mensagem_erro")
7. Sempre fechar sessão no finally
8. Logar operações com logging.info/error

INCLUA:
- Docstring completa com exemplos
- Type hints em tudo
- Tratamento de todas as exceções possíveis
- Log estruturado
=============================================================================

## Para Callbacks Dash (pages/despesas.py)
=============================================================================
Callback para salvar despesa via formulário

INPUTS (State):
- input-descricao: value (str)
- input-valor: value (str, será convertido)
- input-data: date (str no formato YYYY-MM-DD)
- dropdown-categoria: value (str)
- input-tags: value (str, separado por vírgulas)

OUTPUTS:
- modal-sucesso: is_open (bool) - abrir modal de sucesso
- alert-erro: children (str) - mensagem de erro se houver
- input-descricao: value (str) - limpar campo após salvar
- input-valor: value (str) - limpar campo após salvar
- tabela-despesas: data (list) - atualizar com nova despesa

TRIGGER:
- btn-salvar: n_clicks

FLUXO:
1. Validar se todos os campos obrigatórios estão preenchidos
2. Converter valor de string para float (tratar vírgula e ponto)
3. Converter data de string para objeto date
4. Parsear tags (split por vírgula, strip espaços)
5. Chamar create_despesa() do operations.py
6. Se sucesso: abrir modal, limpar campos, atualizar tabela
7. Se erro: mostrar alerta com mensagem
8. Use prevent_initial_call=True

INCLUA:
- Type hints completos
- Docstring clara
- Tratamento de valores inválidos
- Feedback visual sempre
=============================================================================

Para Componentes (components/forms.py)
Componente de formulário reutilizável para receitas/despesas

FUNÇÃO:
def create_transaction_form(tipo: Literal['receita', 'despesa']) -> html.Div

RETORNO:
Dash html.Div contendo:
1. dbc.Input para descrição (obrigatório)
2. dbc.Input para valor (type="number", obrigatório)
3. dcc.DatePickerSingle para data (default hoje)
4. dbc.Select para categoria (carregar do banco)
5. dbc.Input para tags (placeholder: "tag1, tag2, tag3")
6. Se tipo=='receita': dbc.Input para pessoa_origem
7. dbc.Button para salvar

ESTILO:
- Use dbc.Row e dbc.Col para layout responsivo
- Labels descritivos em português
- Placeholders úteis
- IDs dos componentes seguir padrão: f"{tipo}-input-{campo}"

VALIDAÇÃO CLIENT-SIDE:
- Campos obrigatórios com required=True
- Input de valor com min=0.01, step=0.01
- Data não pode ser futura

INCLUA:
- Docstring com exemplo de uso
- Type hints
- Comentários explicando cada seção
=============================================================================

## Para Utils (utils/formatters.py)
=============================================================================
Módulo de formatação de dados brasileiros

CRIE AS SEGUINTES FUNÇÕES:

1. format_currency(valor: float, simbolo: bool = True) -> str
   Formata para R$ 1.234,56 ou apenas 1.234,56

2. parse_currency(texto: str) -> float
   Converte "R$ 1.234,56" ou "1.234,56" para 1234.56
   Deve aceitar tanto ponto quanto vírgula como separador decimal

3. format_date_br(data: date) -> str
   Converte date para "DD/MM/YYYY"

4. parse_date_br(texto: str) -> Optional[date]
   Converte "DD/MM/YYYY" para objeto date
   Retorna None se inválido

5. format_cpf(cpf: str) -> str
   Formata "12345678910" para "123.456.789-10"

6. clean_cpf(cpf: str) -> str
   Remove formatação, retorna apenas dígitos

REQUISITOS PARA TODAS:
- Type hints completos
- Docstrings com múltiplos exemplos
- Tratamento de erros (não crashar)
- Testes unitários no final do arquivo (comentados)

Use biblioteca babel para formatação de moeda se disponível

=============================================================================

# 💬 Copilot Chat vs Inline

## Use INLINE quando:

Completar função já iniciada
Gerar código repetitivo (getters/setters)
Criar estruturas simples (loops, if/else)
Escrever docstrings

## Use CHAT quando:

Planejar arquitetura de função complexa
Debugar erros
Refatorar código existente
Pedir explicações sobre código
Gerar múltiplos arquivos relacionados

# Comandos Úteis do Chat

- /explain - Explica código selecionado
- /fix - Sugere correção para erro
- /tests - Gera testes unitários
- /doc - Gera documentação

# Workflow

## Para Cada Feature Nova:

Para Cada Feature Nova:

1. Planeje com Chat
   Você: Preciso implementar importação de extratos bancários CSV.
   Como devo estruturar isso considerando a arquitetura do projeto?

2. Crie Estrutura com Prompts Inline
[seu prompt detalhado aqui]
   # Tab Tab Tab para aceitar

3. Teste Interativamente

if __name__ == "__main__":
       # COPILOT: Crie código de teste manual
       # Testar com dados reais do arquivo exemplo

4. Refatore com Chat
   Você: /fix ou /optimize
   [Selecione o código]

5. Documente
    # COPILOT: Adicione docstring completa estilo Google
    # para esta função com 3 exemplos de uso