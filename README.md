# 💰 FinanceTSK - Finance Trisckle Tech

Sistema de gestão financeira pessoal desenvolvido como projeto de portfólio e uso real.

## 🎯 Objetivo

Criar uma ferramenta completa de controle financeiro pessoal com custo zero de operação, utilizando armazenamento em nuvem pessoal (OneDrive/Google Drive).

## ✨ Funcionalidades

### Fase 1 - MVP (Em Desenvolvimento)
- [ ] Cadastro manual de receitas com tags e identificação por pessoa
- [ ] Cadastro manual de despesas com categorização
- [ ] Dashboard com visão geral financeira

### Fase 2 - Planejada
- [ ] Importação de extratos bancários (CSV/OFX)
- [ ] Categorização automática de despesas
- [ ] Análises e projeções financeiras
- [ ] Planejamento de compras futuras

### Fase 3 - Futura
- [ ] OCR de Notas Fiscais via QR Code
- [ ] Exportação de relatórios

## 🛠️ Tecnologias

- **Python 3.11+**
- **Dash** - Framework web interativo
- **SQLite** - Banco de dados local
- **Plotly** - Visualizações interativas
- **Pandas** - Manipulação de dados

## 📋 Pré-requisitos

- Python 3.11 ou superior
- Git
- Pasta sincronizada com OneDrive/Google Drive

## 🚀 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/FinanceTSK.git
cd FinanceTSK

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure a pasta de dados
# Copie .env.example para .env e configure o caminho
cp .env.example .env
# Edite .env e defina DATA_PATH com o caminho da sua pasta sincronizada
```

## 📂 Estrutura do Projeto

```
FinanceTSK/
├── .github/
│   └── copilot-instructions.md    # Instruções globais para Copilot
├── data/                          # Pasta sincronizada (não versionada)
│   ├── finance.db                 # Banco SQLite
│   ├── backups/                   # Backups automáticos
│   └── config.json                # Configurações
├── src/                           # Código fonte
│   ├── database/                  # Camada de dados
│   ├── pages/                     # Páginas do app
│   ├── components/                # Componentes reutilizáveis
│   └── utils/                     # Utilitários
├── tests/                         # Testes automatizados
└── docs/                          # Documentação
```

## 💻 Uso

```bash
# Ative o ambiente virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Execute a aplicação
python src/app.py
```

Acesse http://localhost:8050 no navegador.

## 🤝 Contribuindo

Este é um projeto pessoal de aprendizado, mas sugestões são bem-vindas!

## 📝 Licença

MIT License - Sinta-se livre para usar como base para seus projetos.

## 👤 Autor

Desenvolvido como projeto de portfólio e ferramenta pessoal.

---

**Status do Projeto**: 🟡 Em Desenvolvimento Ativo

**Última Atualização**: Janeiro 2026