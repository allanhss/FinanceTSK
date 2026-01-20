"""
Modelos SQLAlchemy para o banco de dados FinanceTSK.

Define as estruturas de dados para Categorias, Transações e demais
entidades do sistema de gestão financeira.
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path para importações funcionarem
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Float, Date
from sqlalchemy import ForeignKey, Text, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped

from src.database.connection import Base

# Formas de pagamento padrão
FORMAS_PAGAMENTO_PADRAO = [
    "dinheiro",
    "pix",
    "credito",
    "debito",
    "transferencia",
    "boleto",
]

# Frequências de recorrência padrão
FREQUENCIAS_RECORRENCIA = [
    "diaria",
    "semanal",
    "quinzenal",
    "mensal",
    "trimestral",
    "anual",
]


class Categoria(Base):
    """
    Modelo de Categoria para classificação de transações.

    Representa categorias como Alimentação, Transporte, Moradia, etc.
    Cada categoria possui uma cor e ícone opcionais para identificação
    visual na interface. Suporta separação entre Receitas e Despesas.

    Attributes:
        id: Identificador único da categoria
        nome: Nome da categoria
        tipo: Tipo de categoria ('receita' ou 'despesa')
        cor: Cor em formato hexadecimal (#RRGGBB)
        icone: Emoji ou nome do ícone para exibição
        created_at: Data/hora de criação
        transacoes: Relacionamento com transações vinculadas
    """

    __tablename__ = "categorias"

    # Tipos válidos de categoria
    TIPO_RECEITA = "receita"
    TIPO_DESPESA = "despesa"
    TIPOS_VALIDOS = [TIPO_RECEITA, TIPO_DESPESA]

    # Colunas
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    nome: str = Column(String(100), nullable=False, index=True)
    tipo: str = Column(String(10), nullable=False, index=True)
    cor: str = Column(String(7), nullable=False, default="#6B7280")
    icone: Optional[str] = Column(String(50), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.now)

    # Relacionamentos
    transacoes: Mapped[List["Transacao"]] = relationship(
        "Transacao",
        back_populates="categoria",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # Índices adicionais
    __table_args__ = (
        UniqueConstraint("nome", "tipo", name="uq_categoria_nome_tipo"),
        Index("idx_categoria_tipo", "tipo"),
        Index("idx_categoria_created_at", "created_at"),
    )

    def __init__(
        self,
        nome: str,
        tipo: str,
        cor: str = "#6B7280",
        icone: Optional[str] = None,
    ) -> None:
        """
        Inicializa uma nova categoria com validação de cor hex e tipo.

        Args:
            nome: Nome da categoria (obrigatório)
            tipo: Tipo de categoria ('receita' ou 'despesa')
            cor: Cor em formato hex #RRGGBB (padrão: #6B7280)
            icone: Emoji ou nome do ícone (opcional)

        Raises:
            ValueError: Se o formato da cor não for hex válido ou tipo
                inválido

        Example:
            >>> cat = Categoria(
            ...     nome="Alimentação",
            ...     tipo="despesa",
            ...     cor="#22C55E",
            ...     icone="🍔"
            ... )
        """
        if not nome or not nome.strip():
            raise ValueError("Nome da categoria não pode estar vazio")

        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido '{tipo}'. Use 'receita' ou 'despesa'.")

        # Validar formato de cor hexadecimal
        if not self._validar_cor_hex(cor):
            raise ValueError(f"Cor inválida '{cor}'. Use formato hex: #RRGGBB")

        self.nome = nome.strip()
        self.tipo = tipo
        self.cor = cor
        self.icone = icone

    @staticmethod
    def _validar_cor_hex(cor: str) -> bool:
        """
        Valida se a cor está em formato hexadecimal válido.

        Args:
            cor: String de cor para validar

        Returns:
            True se válida, False caso contrário
        """
        padrão_hex = r"^#[0-9A-Fa-f]{6}$"
        return bool(re.match(padrão_hex, cor))

    def __repr__(self) -> str:
        """
        Representação em string legível da categoria.

        Returns:
            String no formato: Categoria(id=1, nome='Alimentação',
                tipo='despesa')
        """
        return f"Categoria(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a categoria para dicionário.

        Inclui todos os campos e informações derivadas como contagem
        de transações. Datas são convertidas para formato ISO.

        Returns:
            Dicionário com dados da categoria

        Example:
            >>> cat.to_dict()
            {
                'id': 1,
                'nome': 'Alimentação',
                'tipo': 'despesa',
                'cor': '#22C55E',
                'icone': '🍔',
                'created_at': '2026-01-18T10:30:00',
                'total_transacoes': 15
            }
        """
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "cor": self.cor,
            "icone": self.icone,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "total_transacoes": len(self.transacoes) if self.transacoes else 0,
        }


class Transacao(Base):
    """
    Modelo de Transação (Receita ou Despesa).

    Representa movimentações financeiras com classificação por categoria,
    data e tipo (receita ou despesa). Suporta pagamentos parcelados,
    transações recorrentes e detalhes de forma de pagamento.

    Attributes:
        id: Identificador único da transação
        tipo: Tipo ('receita' ou 'despesa')
        descricao: Descrição da transação
        valor: Valor em reais (sempre positivo)
        data: Data da transação
        categoria_id: Foreign key para Categoria
        categoria: Relacionamento com Categoria
        pessoa_origem: Pessoa que originou (para receitas)
        observacoes: Observações adicionais
        tags: Tags para classificação adicional
        forma_pagamento: Forma de pagamento (dinheiro, pix, credito, etc)
        numero_parcelas: Total de parcelas (default 1)
        parcela_atual: Número da parcela atual (ex: 1 para 1/10)
        is_recorrente: Se a transação é recorrente
        frequencia_recorrencia: Frequência (diaria, semanal, mensal, etc)
        data_limite_recorrencia: Data limite para repetição da recorrência
        origem: Origem da transação (para receitas, ex: Banco X)
        created_at: Data/hora de criação
        updated_at: Data/hora da última atualização
    """

    __tablename__ = "transacoes"

    # Tipos válidos de transação
    TIPO_RECEITA = "receita"
    TIPO_DESPESA = "despesa"
    TIPOS_VALIDOS = [TIPO_RECEITA, TIPO_DESPESA]

    # Colunas
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    tipo: str = Column(String(10), nullable=False, index=True)
    descricao: str = Column(String(200), nullable=False)
    valor: float = Column(Float, nullable=False)
    data: datetime.date = Column(Date, nullable=False, index=True)
    categoria_id: int = Column(
        Integer, ForeignKey("categorias.id"), nullable=False, index=True
    )
    pessoa_origem: Optional[str] = Column(String(100), nullable=True)
    observacoes: Optional[str] = Column(Text, nullable=True)
    tag: Optional[str] = Column(String(50), nullable=True, index=True)
    tags: Optional[str] = Column(String(500), nullable=True)
    forma_pagamento: Optional[str] = Column(String(50), nullable=True)
    numero_parcelas: int = Column(Integer, nullable=True, default=1)
    parcela_atual: Optional[int] = Column(Integer, nullable=True)
    is_recorrente: bool = Column(Boolean, nullable=True, default=False)
    frequencia_recorrencia: Optional[str] = Column(String(50), nullable=True)
    data_limite_recorrencia: Optional[datetime.date] = Column(Date, nullable=True)
    origem: Optional[str] = Column(String(100), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.now)
    updated_at: datetime = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # Relacionamentos
    categoria: Mapped[Categoria] = relationship(
        "Categoria", back_populates="transacoes", lazy="joined"
    )

    # Índices adicionais
    __table_args__ = (
        Index("idx_transacao_tipo_data", "tipo", "data"),
        Index("idx_transacao_categoria", "categoria_id"),
        Index("idx_transacao_created_at", "created_at"),
    )

    def __init__(
        self,
        tipo: str,
        descricao: str,
        valor: float,
        data: datetime.date,
        categoria_id: int,
        pessoa_origem: Optional[str] = None,
        observacoes: Optional[str] = None,
        tag: Optional[str] = None,
        tags: Optional[str] = None,
        forma_pagamento: Optional[str] = None,
        numero_parcelas: int = 1,
        parcela_atual: Optional[int] = None,
        is_recorrente: bool = False,
        frequencia_recorrencia: Optional[str] = None,
        data_limite_recorrencia: Optional[datetime.date] = None,
        origem: Optional[str] = None,
    ) -> None:
        """
        Inicializa uma nova transação com validações.

        Args:
            tipo: 'receita' ou 'despesa'
            descricao: Descrição da transação
            valor: Valor em reais (deve ser positivo)
            data: Data da transação
            categoria_id: ID da categoria
            pessoa_origem: Pessoa que originou (opcional)
            observacoes: Observações adicionais (opcional)
            tag: Tag/Entidade transversal para agrupamento (opcional, ex: 'Mãe', 'Trabalho')
            tags: Tags separadas por vírgula (opcional)
            forma_pagamento: Forma de pagamento (opcional)
            numero_parcelas: Total de parcelas (default 1)
            parcela_atual: Número da parcela atual (opcional)
            is_recorrente: Se a transação é recorrente (default False)
            frequencia_recorrencia: Frequência da recorrência (opcional)
            data_limite_recorrencia: Data limite para recorrência (opcional)
            origem: Origem da transação (opcional)

        Raises:
            ValueError: Se tipo, valor ou data forem inválidos

        Example:
            >>> from datetime import date
            >>> t = Transacao(
            ...     tipo="despesa",
            ...     descricao="Compra no mercado",
            ...     valor=150.50,
            ...     data=date(2026, 1, 18),
            ...     categoria_id=1,
            ...     tags="supermercado,alimentação",
            ...     forma_pagamento="credito",
            ...     numero_parcelas=3,
            ...     parcela_atual=1
            ... )
        """
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo inválido '{tipo}'. Use: {', '.join(self.TIPOS_VALIDOS)}"
            )

        if valor <= 0:
            raise ValueError(f"Valor deve ser maior que zero, recebido: {valor}")

        if not descricao or not descricao.strip():
            raise ValueError("Descrição não pode estar vazia")

        self.tipo = tipo
        self.descricao = descricao.strip()
        self.valor = valor
        self.data = data
        self.categoria_id = categoria_id
        self.pessoa_origem = pessoa_origem
        self.observacoes = observacoes
        self.tag = tag
        self.tags = tags
        self.forma_pagamento = forma_pagamento
        self.numero_parcelas = numero_parcelas if numero_parcelas else 1
        self.parcela_atual = parcela_atual
        self.is_recorrente = is_recorrente
        self.frequencia_recorrencia = frequencia_recorrencia
        self.data_limite_recorrencia = data_limite_recorrencia
        self.origem = origem

    def __repr__(self) -> str:
        """
        Representação em string legível da transação.

        Returns:
            String no formato: Transacao(id=1, tipo='despesa', valor=150.50)
        """
        return f"Transacao(id={self.id}, tipo='{self.tipo}', valor={self.valor})"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a transação para dicionário.

        Inclui informações da categoria vinculada, detalhes de pagamento,
        parcelamento e recorrência. Datas são convertidas para formato ISO.

        Returns:
            Dicionário com dados da transação

        Example:
            >>> t.to_dict()
            {
                'id': 1,
                'tipo': 'despesa',
                'descricao': 'Compra no mercado',
                'valor': 150.50,
                'data': '2026-01-18',
                'categoria': {'id': 1, 'nome': 'Alimentação', ...},
                'pessoa_origem': None,
                'observacoes': None,
                'tags': 'supermercado,alimentação',
                'forma_pagamento': 'credito',
                'numero_parcelas': 3,
                'parcela_atual': 1,
                'is_recorrente': False,
                'frequencia_recorrencia': None,
                'data_limite_recorrencia': None,
                'origem': None,
                'created_at': '2026-01-18T10:30:00',
                'updated_at': '2026-01-18T10:30:00'
            }
        """
        return {
            "id": self.id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "valor": self.valor,
            "data": self.data.isoformat() if self.data else None,
            "categoria": (self.categoria.to_dict() if self.categoria else None),
            "pessoa_origem": self.pessoa_origem,
            "observacoes": self.observacoes,
            "tag": self.tag,
            "tags": self.tags,
            "forma_pagamento": self.forma_pagamento,
            "numero_parcelas": self.numero_parcelas,
            "parcela_atual": self.parcela_atual,
            "is_recorrente": self.is_recorrente,
            "frequencia_recorrencia": self.frequencia_recorrencia,
            "data_limite_recorrencia": (
                self.data_limite_recorrencia.isoformat()
                if self.data_limite_recorrencia
                else None
            ),
            "origem": self.origem,
            "created_at": (self.created_at.isoformat() if self.created_at else None),
            "updated_at": (self.updated_at.isoformat() if self.updated_at else None),
        }


if __name__ == "__main__":
    import logging
    from sqlalchemy import select, delete  # <--- Importamos delete

    from src.database.connection import init_database, get_db

    logging.basicConfig(level=logging.INFO)

    try:
        print("🗄️ Inicializando banco de dados...")
        init_database()

        print("\n📝 Testando criação de categoria...")
        with get_db() as session:
            # 1. LIMPEZA: Tenta apagar as categorias de teste antiga se elas existirem
            # Isso garante que o teste possa rodar múltiplas vezes
            session.query(Categoria).filter(Categoria.nome == "Teste Receita").delete()
            session.query(Categoria).filter(Categoria.nome == "Teste Despesa").delete()
            session.commit()  # Confirma a exclusão

            # 2. CRIAÇÃO: Agora podemos criar sem medo de duplicidade
            cat_receita = Categoria(
                nome="Teste Receita",
                tipo="receita",
                cor="#22C55E",
                icone="💰",
            )
            cat_despesa = Categoria(
                nome="Teste Despesa",
                tipo="despesa",
                cor="#EF4444",
                icone="💸",
            )
            session.add(cat_receita)
            session.add(cat_despesa)
            session.commit()  # Commit para salvar e gerar o ID

            print(f"✓ Categoria Receita criada: {cat_receita}")
            print(f"✓ Categoria Despesa criada: {cat_despesa}")

            # 3. LEITURA: Buscar para confirmar
            stmt = select(Categoria).where(Categoria.nome == "Teste Receita")
            cat_recuperada = session.execute(stmt).scalar_one_or_none()

            if cat_recuperada:
                print(f"\n✓ Categoria recuperada: " f"{cat_recuperada.to_dict()}")
            else:
                print("✗ Erro: Categoria não encontrada.")

    except Exception as e:
        print(f"\n✗ Erro durante teste: {e}")
