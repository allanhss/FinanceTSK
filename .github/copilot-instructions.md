# GitHub Copilot Instructions - FinanceTSK

## Contexto do Projeto
Este é um sistema de gestão financeira pessoal desenvolvido em Python usando Dash para interface web local. O projeto tem foco em aprendizado, qualidade de código e uso como portfólio profissional.

---

## 🏗️ Arquitetura do Projeto (MVC Adaptado)

O projeto segue estritamente a separação de responsabilidades:

1.  **Model (`src/database/models.py`)**: Definição das tabelas (SQLAlchemy). Nenhuma lógica de negócio aqui.
2.  **Controller (`src/database/operations.py`)**: Lógica de CRUD e regras de negócio. A UI nunca acessa o Model diretamente, sempre via Controller.
3.  **View Parts (`src/components/`)**: Funções que retornam layouts reutilizáveis (Forms, Tables, Cards).
4.  **View (`src/app.py` e `src/pages/`)**: Montagem da página e Callbacks do Dash.

---

## 📜 Diretrizes Gerais de Código

### Estilo e Qualidade
- **Type Hints**: Obrigatórios em todos os argumentos e retornos.
- **Docstrings**: Google Style obrigatório para todas as funções públicas.
- **Formatação**: Máximo de 80 caracteres por linha (PEP8).
- **Strings**: Use f-strings para formatação.

### Nomenclatura (Híbrida Rigorosa)
- **Variáveis/Parâmetros**: PORTUGUÊS descritivo.
    - Ex: `valor_total`, `lista_categorias`, `data_vencimento`.
- **Funções/Classes**: INGLÊS (Padrão Internacional).
    - Ex: `create_transaction`, `get_dashboard_summary`, `TransactionForm`.
- **Constantes**: UPPER_CASE em INGLÊS.
    - Ex: `DEFAULT_CURRENCY`, `MAX_RETRIES`.

---

## 🤖 Protocolo de Edição e Resposta (Chat Lateral)

Ao editar arquivos existentes (especialmente via Chat Lateral com referência `@arquivo`):

1.  **Ação Imediata**: Não explique o plano antes de agir. Vá direto para a geração/edição do código.
2.  **Targeting Explícito**: Se não usar a ferramenta de edição automática, inicie o bloco de código com o caminho do arquivo comentado na primeira linha (ex: `# src/app.py`).
3.  **Completude**: Gere o código **inteiro e funcional**. É proibido usar placeholders (`# ... código ...`) a menos que o arquivo seja massivo (>300 linhas).
4.  **Limpeza Automática (Refatoração)**: Se identificar código morto, imports não usados ou funções obsoletas após a mudança, remova-os e informe.
5.  **Resumo Pós-Operação**: Ao final, forneça APENAS um checklist (✅) com:
    * Arquivos modificados.
    * Funcionalidades adicionadas.
    * Limpezas realizadas.
6.  **Estilo de Resposta**:
    * ❌ "Aqui está o código atualizado..." (Não use).
    * ✅ "Arquivo atualizado. Resumo das mudanças: ..." (Use).

---

## 🛠️ Padrões Técnicos Específicos

### Banco de Dados (SQLAlchemy)
- Use `SessionLocal` com context manager (`with get_db() as session:`).
- Sempre trate exceções com `rollback()` e logs de erro.
- Retorne Tuplas `(Success: bool, Message: str)` para operações de escrita.

### Interface Dash
- Use exclusivamente `dash-bootstrap-components` (dbc).
- Callbacks:
    - Use `dash.ctx` para identificar qual botão disparou o evento.
    - Use `State` para ler valores de inputs sem disparar o callback.
    - Use `PreventUpdate` para evitar renderizações desnecessárias.

### Tratamento de Erros
- **NUNCA use `print()`**. Use `logging`.
- Log: `logger = logging.getLogger(__name__)`.

---

## 🇧🇷 Contexto Brasileiro
- **Moeda**: Exibir sempre como "R$ 1.234,56".
- **Datas**: Input/Output visual em "DD/MM/YYYY". Banco em `date` objects.

---

**Última Atualização**: Janeiro 2026 (Versão 2.0 - Sniper Workflow)