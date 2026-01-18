# 📋 FinanceTSK - TODO List Completo

## 🎯 FASE 1 - MVP FUNCIONAL (Substituir Planilha Atual)

### 1.1 Setup e Configuração Inicial

#### 1.1.1 Ambiente de Desenvolvimento
- [x] Criar repositório GitHub (FinanceTSK)
- [x] Estrutura de pastas criada
- [x] Arquivos de configuração (.gitignore, .env, requirements.txt)
- [x] Instruções do Copilot configuradas
- [x] Instalar todas as dependências
- [x] Testar ambiente virtual funcionando
- [x] Configurar path da pasta sincronizada no .env
- [x] Primeiro commit no GitHub

#### 1.1.2 Configuração do Banco de Dados
- [ ] Criar `src/database/__init__.py`
- [ ] Criar engine SQLAlchemy em `database/connection.py`
- [ ] Configurar sessionmaker e Base declarativa
- [ ] Testar conexão com SQLite
- [ ] Criar função para inicializar banco na pasta configurada
- [ ] Script de criação de tabelas (create_all)

**Prompt Sugerido**:
```python
# COPILOT: Crie módulo connection.py com SQLAlchemy
# - Engine SQLite apontando para DATA_PATH/.env
# - SessionLocal configurada
# - Base declarativa
# - Função get_db() que retorna session com context manager
# - Função init_database() para criar todas as tabelas
```

**Estimativa**: 45min | **Prioridade**: 🔴 CRÍTICA

---

### 1.2 Modelos de Dados (database/models.py)

#### 1.2.1 Modelo Categoria
- [ ] Classe Categoria com SQLAlchemy
  - [ ] Campos: id, nome, cor, icone, created_at
  - [ ] Constraint unique em nome
  - [ ] Validação de cor (formato hex)
  - [ ] Método `to_dict()`
  - [ ] Método `__repr__()`
- [ ] Testar criação manual de categoria

**Prompt Sugerido**:
```python
# COPILOT: Modelo SQLAlchemy para Categoria
# Campos: id (PK auto), nome (str 100, unique, not null), 
#         cor (str 7, default '#6B7280', validar hex),
#         icone (str 50, nullable),
#         created_at (datetime, default now)
# Incluir to_dict() e __repr__ legível
```

**Estimativa**: 30min | **Prioridade**: 🔴 CRÍTICA

---

#### 1.2.2 Modelo Transacao
- [ ] Classe Transacao com SQLAlchemy
  - [ ] Campos: id, tipo, descricao, valor, data, categoria_id
  - [ ] Campos opcionais: pessoa_origem, observacoes
  - [ ] Campo tags (JSON stored as string)
  - [ ] Timestamps: created_at, updated_at
  - [ ] Foreign Key para Categoria
  - [ ] Relationship com Categoria
  - [ ] Validação: valor > 0
  - [ ] Validação: tipo in ['receita', 'despesa']
  - [ ] Método `to_dict()` com categoria aninhada
  - [ ] Método `__repr__()`
- [ ] Testar criação manual de transação

**Prompt Sugerido**:
```python
# COPILOT: Modelo SQLAlchemy para Transacao
# Campos obrigatórios: id, tipo (receita/despesa), descricao (200 chars),
#                      valor (float, >0), data (date), categoria_id (FK)
# Campos opcionais: pessoa_origem (100 chars), observacoes (text), tags (JSON)
# Timestamps: created_at, updated_at (auto)
# Relationship: categoria (lazy='joined')
# Validar tipo e valor no __init__
# Incluir to_dict() com categoria_nome
```

**Estimativa**: 1h | **Prioridade**: 🔴 CRÍTICA

---

#### 1.2.3 Dados Iniciais
- [ ] Script para popular categorias padrão
  - [ ] Alimentação 🍔
  - [ ] Transporte 🚗
  - [ ] Moradia 🏠
  - [ ] Lazer 🎮
  - [ ] Saúde ⚕️
  - [ ] Educação 📚
  - [ ] Outros ❓
- [ ] Função `seed_database()` em script separado
- [ ] Executar seed apenas se banco estiver vazio

**Estimativa**: 20min | **Prioridade**: 🟡 ALTA

---

### 1.3 Operações CRUD (database/operations.py)

#### 1.3.1 CRUD de Categorias
- [ ] `create_categoria(nome, cor, icone) -> Tuple[Optional[int], str]`
  - [ ] Validar nome não vazio
  - [ ] Validar formato de cor hex
  - [ ] Verificar duplicatas
  - [ ] Retornar ID criado ou erro
- [ ] `get_categoria(id) -> Optional[Dict]`
- [ ] `get_all_categorias() -> List[Dict]`
- [ ] `update_categoria(id, **kwargs) -> Tuple[bool, str]`
- [ ] `delete_categoria(id) -> Tuple[bool, str]`
  - [ ] Verificar se tem transações vinculadas
  - [ ] Não permitir deletar se tiver transações
- [ ] Testes manuais de cada função

**Estimativa**: 1h30min | **Prioridade**: 🟡 ALTA

---

#### 1.3.2 CRUD de Transações (Receitas)
- [ ] `create_receita(descricao, valor, data, categoria_id, pessoa_origem, tags) -> Tuple[Optional[int], str]`
  - [ ] Validar campos obrigatórios
  - [ ] Validar valor > 0
  - [ ] Validar data não futura (warning, não erro)
  - [ ] Validar categoria existe
  - [ ] Converter tags para JSON
  - [ ] Logging de operação
- [ ] `get_receita(id) -> Optional[Dict]`
- [ ] `get_receitas_by_periodo(data_inicio, data_fim) -> List[Dict]`
- [ ] `get_receitas_by_pessoa(pessoa) -> List[Dict]`
- [ ] `update_receita(id, **kwargs) -> Tuple[bool, str]`
- [ ] `delete_receita(id) -> Tuple[bool, str]`
- [ ] Testes manuais

**Estimativa**: 2h | **Prioridade**: 🔴 CRÍTICA

---

#### 1.3.3 CRUD de Transações (Despesas)
- [ ] `create_despesa(descricao, valor, data, categoria_id, tags, observacoes) -> Tuple[Optional[int], str]`
  - [ ] Validações similares a receita
  - [ ] Sem campo pessoa_origem
- [ ] `get_despesa(id) -> Optional[Dict]`
- [ ] `get_despesas_by_periodo(data_inicio, data_fim) -> List[Dict]`
- [ ] `get_despesas_by_categoria(categoria_id) -> List[Dict]`
- [ ] `update_despesa(id, **kwargs) -> Tuple[bool, str]`
- [ ] `delete_despesa(id) -> Tuple[bool, str]`
- [ ] Testes manuais

**Estimativa**: 2h | **Prioridade**: 🔴 CRÍTICA

---

#### 1.3.4 Queries Agregadas (para Dashboard)
- [ ] `get_saldo_periodo(data_inicio, data_fim) -> Dict`
  - [ ] Total receitas
  - [ ] Total despesas
  - [ ] Saldo (receitas - despesas)
  - [ ] Quantidade de transações
- [ ] `get_despesas_por_categoria(data_inicio, data_fim) -> List[Dict]`
  - [ ] Agrupar por categoria
  - [ ] Ordenar por valor DESC
- [ ] `get_evolucao_mensal(ano) -> List[Dict]`
  - [ ] Saldo mês a mês
  - [ ] Receitas e despesas separadas
- [ ] Testes com dados reais

**Estimativa**: 1h30min | **Prioridade**: 🟡 ALTA

---

### 1.4 Utilitários (utils/)

#### 1.4.1 Formatadores (utils/formatters.py)
- [ ] `format_currency(valor: float) -> str` - R$ 1.234,56
- [ ] `parse_currency(texto: str) -> float` - converte para float
- [ ] `format_date_br(data: date) -> str` - DD/MM/YYYY
- [ ] `parse_date_br(texto: str) -> Optional[date]`
- [ ] `format_percentage(valor: float) -> str` - 45,67%
- [ ] Testes unitários (pytest)

**Estimativa**: 45min | **Prioridade**: 🟢 MÉDIA

---

#### 1.4.2 Validadores (utils/validators.py)
- [ ] `validate_valor(valor: Any) -> Tuple[bool, Optional[float], str]`
- [ ] `validate_descricao(desc: str) -> Tuple[bool, str]`
- [ ] `validate_data(data: Any) -> Tuple[bool, Optional[date], str]`
- [ ] `validate_categoria_id(cat_id: int) -> Tuple[bool, str]`
- [ ] Classe `TransactionValidator` agregando tudo
- [ ] Testes unitários

**Estimativa**: 1h | **Prioridade**: 🟡 ALTA

---

#### 1.4.3 Logger (utils/logger.py)
- [ ] Configurar logging para arquivo
- [ ] Níveis: DEBUG, INFO, WARNING, ERROR
- [ ] Formato customizado com timestamp
- [ ] Rotação de logs (max 10MB, 5 arquivos)
- [ ] Função helper `get_logger(nome_modulo)`

**Estimativa**: 30min | **Prioridade**: 🟢 MÉDIA

---

### 1.5 Aplicação Dash (src/app.py)

#### 1.5.1 Estrutura Base
- [ ] Inicializar app Dash
- [ ] Configurar tema Bootstrap (dbc.themes.BOOTSTRAP ou DARKLY)
- [ ] Layout base com navegação
  - [ ] Navbar com logo e menu
  - [ ] Container para páginas
  - [ ] Footer com versão
- [ ] Sistema de rotas (dcc.Location)
- [ ] Página 404
- [ ] Executar em localhost:8050

**Prompt Sugerido**:
```python
# COPILOT: App Dash com Bootstrap
# - Usar dash_bootstrap_components
# - Navbar responsivo com links: Dashboard, Receitas, Despesas, Categorias
# - Sistema de rotas com dcc.Location e callback
# - Container central para conteúdo das páginas
# - Footer fixo com "FinanceTSK v1.0"
# - Tema: dbc.themes.FLATLY
```

**Estimativa**: 1h | **Prioridade**: 🔴 CRÍTICA

---

### 1.6 Componentes Reutilizáveis (components/)

#### 1.6.1 Formulários (components/forms.py)
- [ ] `create_transaction_form(tipo: str, categorias: List) -> html.Div`
  - [ ] Input descrição (required)
  - [ ] Input valor (number, required)
  - [ ] DatePicker data (default hoje)
  - [ ] Select categoria
  - [ ] Input tags (separadas por vírgula)
  - [ ] Se receita: Input pessoa_origem
  - [ ] Se despesa: Textarea observações
  - [ ] Botão salvar
- [ ] `create_categoria_form() -> html.Div`
  - [ ] Input nome
  - [ ] Color picker (input type="color")
  - [ ] Input ícone (text ou dropdown futuro)
  - [ ] Botão salvar

**Estimativa**: 1h30min | **Prioridade**: 🟡 ALTA

---

#### 1.6.2 Cards e Indicadores (components/cards.py)
- [ ] `create_metric_card(titulo, valor, icone, cor) -> dbc.Card`
  - [ ] Card estilizado com ícone
  - [ ] Valor em destaque
  - [ ] Subtítulo opcional
- [ ] `create_summary_cards(receitas, despesas, saldo) -> dbc.Row`
  - [ ] 3 cards lado a lado
  - [ ] Verde para receitas
  - [ ] Vermelho para despesas
  - [ ] Azul para saldo
- [ ] `create_empty_state(mensagem, acao_texto) -> html.Div`
  - [ ] Exibir quando não há dados
  - [ ] Botão de ação

**Estimativa**: 1h | **Prioridade**: 🟢 MÉDIA

---

#### 1.6.3 Tabelas (components/tables.py)
- [ ] `create_transactions_table(transacoes: List[Dict]) -> dash_table.DataTable`
  - [ ] Colunas: Data, Descrição, Categoria, Valor, Ações
  - [ ] Formatação de moeda
  - [ ] Paginação (20 itens/página)
  - [ ] Filtros por coluna
  - [ ] Ordenação
  - [ ] Botões editar/deletar por linha
- [ ] `create_categorias_table(categorias: List[Dict]) -> dash_table.DataTable`
  - [ ] Colunas: Nome, Cor (preview), Ícone, Ações

**Estimativa**: 1h30min | **Prioridade**: 🟡 ALTA

---

#### 1.6.4 Modais (components/modals.py)
- [ ] `create_success_modal(mensagem) -> dbc.Modal`
  - [ ] Ícone de sucesso ✓
  - [ ] Mensagem customizável
  - [ ] Botão OK
- [ ] `create_error_modal(mensagem) -> dbc.Modal`
  - [ ] Ícone de erro ✗
  - [ ] Mensagem de erro
  - [ ] Botão fechar
- [ ] `create_confirm_modal(titulo, mensagem) -> dbc.Modal`
  - [ ] Para confirmações (deletar, etc)
  - [ ] Botões Sim/Não

**Estimativa**: 45min | **Prioridade**: 🟢 MÉDIA

---

### 1.7 Páginas da Aplicação (pages/)

#### 1.7.1 Dashboard (pages/dashboard.py)
- [ ] Layout da página
  - [ ] Cards de resumo (receitas, despesas, saldo)
  - [ ] Filtro de período (mês atual default)
  - [ ] 2 gráficos principais
- [ ] Callback para atualizar resumo ao mudar período
- [ ] Gráfico: Evolução mensal (linha)
  - [ ] Eixo X: meses
  - [ ] Eixo Y: valor
  - [ ] 2 linhas: receitas e despesas
- [ ] Gráfico: Despesas por categoria (pizza)
  - [ ] Top 5 categorias + "Outros"
  - [ ] Cores das categorias
- [ ] Tabela: Últimas 10 transações
  - [ ] Link para página completa

**Estimativa**: 2h30min | **Prioridade**: 🔴 CRÍTICA

---

#### 1.7.2 Receitas (pages/receitas.py)
- [ ] Layout da página
  - [ ] Título e botão "Nova Receita"
  - [ ] Formulário em modal ou colapsável
  - [ ] Tabela de receitas
  - [ ] Filtros: período, pessoa, categoria
- [ ] Callback: Salvar nova receita
  - [ ] Validar campos
  - [ ] Chamar create_receita()
  - [ ] Mostrar sucesso/erro
  - [ ] Atualizar tabela
  - [ ] Limpar formulário
- [ ] Callback: Editar receita
  - [ ] Carregar dados no formulário
  - [ ] Atualizar no banco
- [ ] Callback: Deletar receita
  - [ ] Modal de confirmação
  - [ ] Deletar do banco
  - [ ] Atualizar tabela
- [ ] Callback: Aplicar filtros na tabela

**Estimativa**: 3h | **Prioridade**: 🔴 CRÍTICA

---

#### 1.7.3 Despesas (pages/despesas.py)
- [ ] Layout da página
  - [ ] Estrutura similar a receitas
  - [ ] Formulário específico de despesas
  - [ ] Tabela de despesas
  - [ ] Filtros: período, categoria
  - [ ] Total de despesas no período
- [ ] Callback: Salvar nova despesa
- [ ] Callback: Editar despesa
- [ ] Callback: Deletar despesa
- [ ] Callback: Aplicar filtros

**Estimativa**: 3h | **Prioridade**: 🔴 CRÍTICA

---

#### 1.7.4 Categorias (pages/categorias.py)
- [ ] Layout da página
  - [ ] Lista/Grid de categorias existentes
  - [ ] Formulário para nova categoria
  - [ ] Preview da cor escolhida
- [ ] Callback: Criar categoria
- [ ] Callback: Editar categoria
- [ ] Callback: Deletar categoria
  - [ ] Verificar se tem transações
  - [ ] Avisar se não puder deletar
- [ ] Exibir quantidade de transações por categoria

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

### 1.8 Testes e Refinamentos

#### 1.8.1 Testes de Integração
- [ ] Testar fluxo completo: criar receita → visualizar no dashboard
- [ ] Testar fluxo: criar despesa → visualizar no dashboard
- [ ] Testar criação de categoria → usar em transação
- [ ] Testar edição de transações
- [ ] Testar deleção (com confirmação)
- [ ] Testar filtros e buscas
- [ ] Testar com banco vazio (empty states)

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

#### 1.8.2 UX e Polimento
- [ ] Adicionar loading spinners em operações
- [ ] Mensagens de feedback amigáveis
- [ ] Validação client-side nos formulários
- [ ] Tooltips em botões
- [ ] Responsividade mobile
- [ ] Paleta de cores consistente
- [ ] Ícones em botões e cards

**Estimativa**: 2h | **Prioridade**: 🟢 MÉDIA

---

#### 1.8.3 Documentação Fase 1
- [ ] Atualizar README com screenshots
- [ ] Documentar como executar o projeto
- [ ] Criar CHANGELOG.md
- [ ] Documentar estrutura de pastas
- [ ] Adicionar comentários em código complexo
- [ ] Tutorial de primeiro uso

**Estimativa**: 1h30min | **Prioridade**: 🟢 MÉDIA

---

### 1.9 Deploy MVP
- [ ] Testar executável com PyInstaller
  - [ ] Configurar spec file
  - [ ] Incluir dependências
  - [ ] Testar em máquina limpa
- [ ] Criar instalador (opcional)
- [ ] Documentar processo de instalação
- [ ] Testar sincronização com OneDrive
- [ ] Release v1.0.0 no GitHub

**Estimativa**: 2h | **Prioridade**: 🟢 MÉDIA

---

## 🎯 FASE 2 - FUNCIONALIDADES INTERMEDIÁRIAS

**Objetivo**: Adicionar automação e análises avançadas  
**Prazo Estimado**: 3-4 semanas  
**Critério de Sucesso**: Reduzir tempo de cadastro em 50%

### 2.1 Sistema de Tags Avançado

#### 2.1.1 Gerenciamento de Tags
- [ ] Modelo Tag no banco
  - [ ] id, nome, cor, categoria_id (opcional)
  - [ ] Many-to-many com Transacao
- [ ] CRUD completo de tags
- [ ] Página de gerenciamento de tags
- [ ] Autocomplete de tags em formulários
- [ ] Filtro por tags nas listagens

**Estimativa**: 3h | **Prioridade**: 🟡 ALTA

---

#### 2.1.2 Categorização Automática
- [ ] Classe CategoryPredictor
  - [ ] Dicionário de palavras-chave
  - [ ] Método predict(descricao) -> categoria
  - [ ] Case-insensitive
- [ ] Popular palavras-chave iniciais
- [ ] Sugerir categoria ao digitar descrição (callback)
- [ ] Sistema de aprendizado (quando usuário corrige)
  - [ ] Salvar padrão aprendido
  - [ ] Usar em próximas previsões
- [ ] Página de revisão de aprendizados

**Estimativa**: 4h | **Prioridade**: 🟡 ALTA

---

### 2.2 Importação de Extratos Bancários

#### 2.2.1 Parser de CSV
- [ ] Classe ExtratoParser
  - [ ] Suporte Banco do Brasil
  - [ ] Suporte Itaú
  - [ ] Suporte Nubank
  - [ ] Suporte Caixa
- [ ] Detectar formato automaticamente
- [ ] Converter para formato padrão
- [ ] Página de upload de extrato
- [ ] Preview antes de importar
- [ ] Mapear para categorias automaticamente

**Estimativa**: 5h | **Prioridade**: 🔴 CRÍTICA

---

#### 2.2.2 Parser de OFX
- [ ] Biblioteca ofxparse
- [ ] Suporte a arquivos OFX
- [ ] Mesma interface de preview
- [ ] Salvar histórico de importações

**Estimativa**: 3h | **Prioridade**: 🟢 MÉDIA

---

#### 2.2.3 Deduplicação
- [ ] Detectar transações duplicadas
  - [ ] Mesma data + valor + descrição similar
- [ ] Marcar duplicatas em preview
- [ ] Opção de ignorar ou mesclar
- [ ] Log de importações

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

### 2.3 Planejamento Financeiro

#### 2.3.1 Sistema de Envelopes (Budgeting)
- [ ] Modelo Envelope
  - [ ] nome, valor_planejado, categoria_id
  - [ ] mes_referencia
- [ ] Página de planejamento mensal
  - [ ] Definir orçamento por categoria
  - [ ] Visualizar gastos vs planejado
  - [ ] Progress bars
- [ ] Alertas de orçamento
  - [ ] Avisar quando atingir 80%
  - [ ] Avisar quando ultrapassar

**Estimativa**: 4h | **Prioridade**: 🟡 ALTA

---

#### 2.3.2 Metas de Economia
- [ ] Modelo Meta
  - [ ] nome, valor_alvo, prazo
  - [ ] valor_acumulado
- [ ] Página de metas
  - [ ] Criar/editar metas
  - [ ] Adicionar contribuições
  - [ ] Visualizar progresso
- [ ] Dashboard de metas
  - [ ] Gráfico de evolução
  - [ ] Previsão de conclusão

**Estimativa**: 3h | **Prioridade**: 🟢 MÉDIA

---

#### 2.3.3 Projeções Futuras
- [ ] Calcular tendência de gastos
- [ ] Prever saldo futuro (3, 6, 12 meses)
- [ ] Considerar receitas/despesas recorrentes
- [ ] Gráfico de projeção
- [ ] Cenários: otimista, realista, pessimista

**Estimativa**: 4h | **Prioridade**: 🟢 MÉDIA

---

### 2.4 Dashboards Avançados

#### 2.4.1 Análises por Período
- [ ] Comparativo mês vs mês anterior
- [ ] Comparativo ano vs ano anterior
- [ ] Métricas de crescimento (%)
- [ ] Identificar anomalias (gastos atípicos)

**Estimativa**: 3h | **Prioridade**: 🟢 MÉDIA

---

#### 2.4.2 Análises por Categoria
- [ ] Evolução de cada categoria ao longo do tempo
- [ ] Ranking de categorias
- [ ] Sazonalidade (meses com mais gasto)
- [ ] Sugestões de redução

**Estimativa**: 2h30min | **Prioridade**: 🟢 MÉDIA

---

#### 2.4.3 Visualizações Adicionais
- [ ] Gráfico de fluxo de caixa (sankey)
- [ ] Heatmap de gastos (dia da semana x categoria)
- [ ] Treemap de despesas
- [ ] Gráfico de barras empilhadas (receitas/despesas/saldo)

**Estimativa**: 3h | **Prioridade**: 🟢 MÉDIA

---

### 2.5 Melhorias de Performance

#### 2.5.1 Otimizações
- [ ] Implementar cache de queries frequentes
- [ ] Paginação em todas as tabelas grandes
- [ ] Lazy loading de gráficos
- [ ] Índices no banco de dados
- [ ] Otimizar queries agregadas

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

#### 2.5.2 Backup Automático
- [ ] Sistema de backup periódico
  - [ ] Copiar .db para /backups a cada 7 dias
  - [ ] Manter últimos 10 backups
  - [ ] Comprimir backups antigos
- [ ] Botão de backup manual
- [ ] Restaurar de backup
- [ ] Verificar integridade do backup

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

### 2.6 Exportação e Relatórios

#### 2.6.1 Exportar Dados
- [ ] Exportar transações para CSV
- [ ] Exportar transações para Excel
- [ ] Filtros de exportação (período, categoria)
- [ ] Incluir totais e resumos

**Estimativa**: 2h | **Prioridade**: 🟢 MÉDIA

---

#### 2.6.2 Relatórios PDF
- [ ] Biblioteca reportlab ou weasyprint
- [ ] Relatório mensal em PDF
  - [ ] Resumo executivo
  - [ ] Gráficos principais
  - [ ] Tabela detalhada
  - [ ] Insights e recomendações
- [ ] Relatório anual
- [ ] Customizar template

**Estimativa**: 4h | **Prioridade**: 🟢 MÉDIA

---

### 2.7 Testes e Documentação Fase 2
- [ ] Testes de integração de importação
- [ ] Testes de categorização automática
- [ ] Documentar novos recursos
- [ ] Tutorial de importação de extratos
- [ ] Atualizar README
- [ ] Release v2.0.0

**Estimativa**: 2h | **Prioridade**: 🟢 MÉDIA

---

## 🚀 FASE 3 - FUNCIONALIDADES AVANÇADAS

**Objetivo**: OCR, IA e recursos premium  
**Prazo Estimado**: 4-6 semanas  
**Critério de Sucesso**: Sistema completo e diferenciado

### 3.1 OCR de Notas Fiscais

#### 3.1.1 Leitura de QR Code
- [ ] Biblioteca pyzbar
- [ ] Página de upload de foto/scan
- [ ] Extrair URL do QR Code NFC-e
- [ ] Testar com diferentes tipos de QR Code

**Estimativa**: 2h | **Prioridade**: 🟡 ALTA

---

#### 3.1.2 Web Scraping da SEFAZ
- [ ] Acessar URL da nota fiscal
- [ ] Parsear HTML da página
- [ ] Extrair dados:
  - [ ] Estabelecimento
  - [ ] Data e hora
  - [ ] Valor total
  - [ ] Lista de produtos
  - [ ] Método de pagamento
- [ ] Rate limiting (respeitar servidor)
- [ ] Tratamento de erros (nota não encontrada)

**Estimativa**: 4h | **Prioridade**: 🟡 ALTA

---

#### 3.1.3 Categorização de Produtos
- [ ] Identificar categoria de cada item
- [ ] Agrupar itens similares
- [ ] Criar múltiplas despesas por categoria
- [ ] Opção de criar despesa única ou detalhada

**Estimativa**: 3h | **Prioridade**: 🟢 MÉDIA

---

#### 3.1.4 Interface de Upload
- [ ] Página de scan de nota
- [ ] Upload de imagem (foto