import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from src.database.connection import get_db
from src.database.models import Categoria, Transacao

logger = logging.getLogger(__name__)


# ===== FUNÇÕES DE GERENCIAMENTO DE CATEGORIAS =====


def create_category(
    nome: str, tipo: str, cor: str = "#6B7280", icone: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Creates a new category for transactions.

    Args:
        nome: Category name (e.g., 'Alimentação').
        tipo: Category type ('receita' or 'despesa').
        cor: Color in hex format #RRGGBB (default: #6B7280).
        icone: Optional emoji or icon name.

    Returns:
        Tuple with (success: bool, message: str).

    Raises:
        ValueError: If icon already exists for the given type and a
            different category, or if name and icon are both in use.

    Example:
        >>> create_category(
        ...     nome='Salário',
        ...     tipo='receita',
        ...     cor='#22C55E',
        ...     icone='💰'
        ... )
        (True, 'Categoria criada com sucesso.')
    """
    try:
        logger.debug(f"🔄 Tentando criar categoria: {nome} ({tipo})")

        # Validação de tipo
        if tipo not in Categoria.TIPOS_VALIDOS:
            logger.error(f"❌ Tipo inválido: {tipo}")
            return False, "Tipo deve ser 'receita' ou 'despesa'."

        with get_db() as session:
            try:
                # Validar unicidade de ícone por tipo
                if icone:
                    categoria_com_icone = (
                        session.query(Categoria)
                        .filter(
                            Categoria.tipo == tipo,
                            Categoria.icone == icone,
                            Categoria.nome != nome,
                        )
                        .first()
                    )
                    if categoria_com_icone:
                        logger.warning(
                            f"⚠️ Ícone '{icone}' já existe para tipo '{tipo}' "
                            f"na categoria '{categoria_com_icone.nome}'"
                        )
                        return (
                            False,
                            f"Ícone '{icone}' já está em uso nesta categoria. "
                            f"Escolha outro ícone.",
                        )

                # Criar nova categoria
                logger.debug(f"📝 Criando objeto Categoria: {nome}")
                nova_categoria = Categoria(nome=nome, tipo=tipo, cor=cor, icone=icone)
                session.add(nova_categoria)
                logger.debug(f"➕ Categoria adicionada à sessão")

                session.commit()
                logger.info(f"✅ Categoria criada com sucesso: {nome} ({tipo})")
                return True, "Categoria criada com sucesso."

            except IntegrityError as ie:
                session.rollback()
                logger.warning(
                    f"⚠️ Erro de integridade (duplicata): {nome} ({tipo}) - {ie}"
                )
                return False, "Categoria com esse nome e tipo já existe."

            except ValueError as ve:
                session.rollback()
                logger.error(f"❌ Erro de validação: {ve}")
                return False, str(ve)

            except Exception as e:
                session.rollback()
                logger.error(
                    f"❌ Erro inesperado ao criar categoria: {e}", exc_info=True
                )
                raise

    except Exception as e:
        logger.error(f"❌ Erro ao criar categoria: {e}", exc_info=True)
        return False, "Erro ao salvar categoria. Tente novamente."


def get_categories(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves categories, optionally filtered by type.

    Args:
        tipo: Optional type filter ('receita' or 'despesa').

    Returns:
        List of category dictionaries, ordered by name.

    Example:
        >>> get_categories(tipo='despesa')
        [
            {'id': 1, 'nome': 'Alimentação', 'tipo': 'despesa', ...},
            ...
        ]
    """
    try:
        with get_db() as session:
            query = session.query(Categoria)

            if tipo:
                query = query.filter(Categoria.tipo == tipo)

            categorias = query.order_by(Categoria.nome).all()

            lista_categorias = [cat.to_dict() for cat in categorias]
            logger.info(
                f"Recuperadas {len(lista_categorias)} categorias."
                + (f" (tipo: {tipo})" if tipo else "")
            )
            return lista_categorias

    except Exception as e:
        logger.error(f"Erro ao recuperar categorias: {e}")
        return []


def delete_category(category_id: int) -> Tuple[bool, str]:
    """
    Deletes a category by ID.

    Note: Due to cascade delete, associated transactions will also
    be deleted if the foreign key cascade is configured.

    Args:
        category_id: ID of the category to delete.

    Returns:
        Tuple with (success: bool, message: str).

    Example:
        >>> delete_category(5)
        (True, 'Categoria removida com sucesso.')
    """
    try:
        with get_db() as session:
            try:
                categoria = (
                    session.query(Categoria).filter(Categoria.id == category_id).first()
                )

                if not categoria:
                    return False, "Categoria não encontrada."

                nome_categoria = categoria.nome
                session.delete(categoria)
                session.commit()

                logger.info(f"Categoria removida: {nome_categoria} (ID: {category_id})")
                return True, "Categoria removida com sucesso."

            except Exception as e:
                session.rollback()
                logger.error(f"Erro ao remover categoria: {e}")
                raise

    except Exception as e:
        logger.error(f"Erro ao deletar categoria: {e}")
        return False, "Erro ao remover categoria. Tente novamente."


def initialize_default_categories() -> Tuple[bool, str]:
    """
    Initializes default categories if database is empty.

    Creates standard income and expense categories if no categories
    exist in the database.

    Returns:
        Tuple with (success: bool, message: str).

    Example:
        >>> initialize_default_categories()
        (True, 'Categorias padrão inicializadas: 12 categorias criadas.')
    """
    # Padrão de Receitas
    CATEGORIAS_RECEITA = [
        {"nome": "Salário", "cor": "#10B981", "icone": "💼"},
        {"nome": "Mesada", "cor": "#06B6D4", "icone": "🎁"},
        {"nome": "Vendas", "cor": "#F59E0B", "icone": "🛒"},
        {"nome": "Investimentos", "cor": "#8B5CF6", "icone": "📈"},
        {"nome": "Outros", "cor": "#6B7280", "icone": "❓"},
    ]

    # Padrão de Despesas
    CATEGORIAS_DESPESA = [
        {"nome": "Alimentação", "cor": "#22C55E", "icone": "🍔"},
        {"nome": "Moradia", "cor": "#EF4444", "icone": "🏠"},
        {"nome": "Transporte", "cor": "#0EA5E9", "icone": "🚗"},
        {"nome": "Lazer", "cor": "#A855F7", "icone": "🎬"},
        {"nome": "Saúde", "cor": "#FB923C", "icone": "⚕️"},
        {"nome": "Educação", "cor": "#06B6D4", "icone": "📚"},
        {"nome": "Outros", "cor": "#6B7280", "icone": "❓"},
    ]

    try:
        with get_db() as session:
            # Verificar se já existem categorias
            total_categorias = session.query(Categoria).count()

            if total_categorias > 0:
                logger.info("Categorias já existem no banco. Inicialização abortada.")
                return True, "Categorias já foram inicializadas anteriormente."

            # Criar categorias de receita
            for cat_info in CATEGORIAS_RECEITA:
                nova_categoria = Categoria(
                    nome=cat_info["nome"],
                    tipo=Categoria.TIPO_RECEITA,
                    cor=cat_info["cor"],
                    icone=cat_info["icone"],
                )
                session.add(nova_categoria)

            # Criar categorias de despesa
            for cat_info in CATEGORIAS_DESPESA:
                nova_categoria = Categoria(
                    nome=cat_info["nome"],
                    tipo=Categoria.TIPO_DESPESA,
                    cor=cat_info["cor"],
                    icone=cat_info["icone"],
                )
                session.add(nova_categoria)

            session.commit()

            total_criadas = len(CATEGORIAS_RECEITA) + len(CATEGORIAS_DESPESA)

            logger.info(
                f"Categorias padrão inicializadas: "
                f"{total_criadas} categorias criadas."
            )
            return (
                True,
                f"Categorias padrão inicializadas: {total_criadas} categorias criadas.",
            )

    except Exception as e:
        logger.error(f"Erro ao inicializar categorias padrão: {e}")
        return False, "Erro ao inicializar categorias padrão. Tente novamente."


def create_transaction(
    tipo: str,
    descricao: str,
    valor: float,
    data: date,
    categoria_id: int,
    observacoes: Optional[str] = None,
    pessoa_origem: Optional[str] = None,
    tags: Optional[str] = None,
    forma_pagamento: Optional[str] = None,
    numero_parcelas: int = 1,
    is_recorrente: bool = False,
    frequencia_recorrencia: Optional[str] = None,
    data_limite_recorrencia: Optional[date] = None,
    origem: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Creates one or more transactions with support for installments and recurrence.

    If numero_parcelas > 1, creates multiple transactions with sequential dates
    and reduced values (total_value / numero_parcelas).

    If is_recorrente=True with frequencia_recorrencia='mensal', generates monthly
    recurring transactions up to data_limite_recorrencia or 12 months ahead.

    Args:
        tipo: Transaction type ('receita' or 'despesa').
        descricao: Brief description of the transaction.
        valor: Transaction amount (must be positive).
        data: Transaction date (first installment or first occurrence).
        categoria_id: ID of the associated category.
        observacoes: Optional additional notes.
        pessoa_origem: Optional name of origin person/entity.
        tags: Optional comma-separated tags for organization.
        forma_pagamento: Optional payment method (dinheiro, pix, credito, etc).
        numero_parcelas: Number of installments (default 1).
        is_recorrente: Whether transaction is recurring (default False).
        frequencia_recorrencia: Recurrence frequency (diaria, semanal, quinzenal, mensal, etc).
        data_limite_recorrencia: End date for recurrence (optional).
        origem: Origin of transaction for income (ex: Banco X).

    Returns:
        Tuple with (success: bool, message: str).

    Example:
        >>> # Create a purchase in 3 installments
        >>> create_transaction(
        ...     tipo='despesa',
        ...     descricao='Compra',
        ...     valor=300.0,
        ...     data=date(2026, 1, 18),
        ...     categoria_id=1,
        ...     numero_parcelas=3,
        ...     forma_pagamento='credito'
        ... )
        # Creates 3 transactions: 100 each, on 18/01, 18/02, 18/03
    """
    try:
        logger.debug(f"🔄 Tentando criar transação: {tipo} - R$ {valor} - {descricao}")

        # Validação de tipo
        if tipo not in ["receita", "despesa"]:
            logger.error(f"❌ Tipo inválido: {tipo}")
            return False, "Tipo deve ser 'receita' ou 'despesa'."

        # Validação de valor
        if valor <= 0:
            logger.error(f"❌ Valor inválido: {valor}")
            return False, "Valor deve ser maior que zero."

        # Validação de descrição
        if not descricao or len(descricao.strip()) == 0:
            logger.error("❌ Descrição vazia")
            return False, "Descrição não pode estar vazia."

        logger.debug(f"📝 Validações OK. Abrindo sessão do banco...")
        with get_db() as session:
            try:
                logger.debug(f"🔍 Verificando categoria ID: {categoria_id}")
                # Validar se categoria existe
                categoria = (
                    session.query(Categoria)
                    .filter(Categoria.id == categoria_id)
                    .first()
                )
                if not categoria:
                    logger.error(f"❌ Categoria não encontrada: ID {categoria_id}")
                    return False, "Categoria não encontrada."

                logger.debug(f"✓ Categoria encontrada: {categoria.nome}")

                # ===== LÓGICA DE PARCELAMENTO =====
                if numero_parcelas > 1:
                    valor_parcela = valor / numero_parcelas
                    descricao_base = descricao.strip()

                    for parcela_num in range(1, numero_parcelas + 1):
                        data_parcela = data + relativedelta(months=parcela_num - 1)
                        descricao_parcela = (
                            f"{descricao_base} ({parcela_num}/{numero_parcelas})"
                        )

                        transacao = Transacao(
                            tipo=tipo,
                            descricao=descricao_parcela,
                            valor=valor_parcela,
                            data=data_parcela,
                            categoria_id=categoria_id,
                            observacoes=observacoes,
                            pessoa_origem=pessoa_origem,
                            tags=tags,
                            forma_pagamento=forma_pagamento,
                            numero_parcelas=numero_parcelas,
                            parcela_atual=parcela_num,
                            is_recorrente=False,
                            frequencia_recorrencia=None,
                            data_limite_recorrencia=None,
                            origem=origem,
                        )
                        session.add(transacao)

                    session.commit()
                    logger.info(
                        f"Transação parcelada criada: {tipo} - R$ {valor} "
                        f"em {numero_parcelas}x de R$ {valor_parcela:.2f}"
                    )
                    return (
                        True,
                        f"Transação registrada em {numero_parcelas} parcelas.",
                    )

                # ===== LÓGICA DE RECORRÊNCIA =====
                elif is_recorrente and frequencia_recorrencia:
                    if frequencia_recorrencia == "mensal":
                        # Projetar 12 meses para frente, ou até data_limite
                        data_fim = data_limite_recorrencia or (
                            data + relativedelta(months=12)
                        )
                        data_atual = data
                        descricao_base = descricao.strip()
                        occorrencia = 1

                        while data_atual <= data_fim:
                            descricao_recorrente = (
                                f"{descricao_base} (Recorrência #{occorrencia})"
                            )

                            transacao = Transacao(
                                tipo=tipo,
                                descricao=descricao_recorrente,
                                valor=valor,
                                data=data_atual,
                                categoria_id=categoria_id,
                                observacoes=observacoes,
                                pessoa_origem=pessoa_origem,
                                tags=tags,
                                forma_pagamento=forma_pagamento,
                                numero_parcelas=1,
                                parcela_atual=None,
                                is_recorrente=True,
                                frequencia_recorrencia=frequencia_recorrencia,
                                data_limite_recorrencia=data_fim,
                                origem=origem,
                            )
                            session.add(transacao)
                            data_atual = data_atual + relativedelta(months=1)
                            occorrencia += 1

                        session.commit()
                        logger.info(
                            f"✅ Transação recorrente criada: {tipo} - R$ {valor} "
                            f"mensalmente até {data_fim}"
                        )
                        return True, "Transação recorrente registrada com sucesso."
                    else:
                        # Outras frequências: apenas registra a primeira
                        logger.warning(
                            f"Frequência '{frequencia_recorrencia}' ainda não suportada. "
                            f"Registrando apenas a primeira ocorrência."
                        )

                # ===== TRANSAÇÃO SIMPLES (SEM PARCELAMENTO OU RECORRÊNCIA) =====
                transacao = Transacao(
                    tipo=tipo,
                    descricao=descricao.strip(),
                    valor=valor,
                    data=data,
                    categoria_id=categoria_id,
                    observacoes=observacoes,
                    pessoa_origem=pessoa_origem,
                    tags=tags,
                    forma_pagamento=forma_pagamento,
                    numero_parcelas=1,
                    parcela_atual=None,
                    is_recorrente=False,
                    frequencia_recorrencia=None,
                    data_limite_recorrencia=None,
                    origem=origem,
                )
                session.add(transacao)
                logger.debug(f"➕ Transação adicionada à sessão")
                session.commit()
                logger.info(
                    f"✅ Transação criada com sucesso: {tipo} - R$ {valor} em {data}"
                )
                return True, "Transação registrada com sucesso."

            except Exception as e:
                session.rollback()
                logger.error(
                    f"❌ Erro durante criação de transação: {e}", exc_info=True
                )
                raise

    except Exception as e:
        logger.error(f"❌ Erro ao criar transação: {e}", exc_info=True)
        return False, "Erro ao salvar transação. Tente novamente."


def get_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict]:
    """
    Retrieves transactions filtered by date range.

    Args:
        start_date: Start of date range (inclusive).
        end_date: End of date range (inclusive).

    Returns:
        List of transaction dictionaries, ordered by date (newest first).
    """
    try:
        with get_db() as session:
            query = session.query(Transacao)

            if start_date:
                query = query.filter(Transacao.data >= start_date)
            if end_date:
                query = query.filter(Transacao.data <= end_date)

            transacoes = query.order_by(Transacao.data.desc()).all()

            lista_transacoes = [transacao.to_dict() for transacao in transacoes]
            logger.info(f"Recuperadas {len(lista_transacoes)} transações.")
            return lista_transacoes

    except Exception as e:
        logger.error(f"Erro ao recuperar transações: {e}")
        return []


def get_category_options(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves all categories formatted for Dash dcc.Dropdown.

    Args:
        tipo: Optional type filter ('receita' or 'despesa').

    Returns:
        List of dicts with 'label' (icon + name) and 'value' (id).

    Example:
        >>> get_category_options(tipo='despesa')
        [{'label': '🍔 Alimentação', 'value': 1}, ...]
    """
    try:
        with get_db() as session:
            query = session.query(Categoria)

            if tipo:
                query = query.filter(Categoria.tipo == tipo)

            categorias = query.order_by(Categoria.nome).all()

            opcoes = [
                {"label": f"{c.icone} {c.nome}", "value": c.id} for c in categorias
            ]
            logger.info(
                f"Recuperadas {len(opcoes)} categorias."
                + (f" (tipo: {tipo})" if tipo else "")
            )
            return opcoes

    except Exception as e:
        logger.error(f"Erro ao recuperar categorias: {e}")
        return []


def get_dashboard_summary(month: int, year: int) -> Dict[str, float]:
    """
    Calculates summary metrics for a specific month.

    Args:
        month: Month number (1-12).
        year: Year in 4-digit format.

    Returns:
        Dictionary with 'total_receitas', 'total_despesas', 'saldo'.
    """
    try:
        with get_db() as session:
            # Query for income
            total_receitas = (
                session.query(func.sum(Transacao.valor))
                .filter(
                    Transacao.tipo == "receita",
                    Transacao.data >= date(year, month, 1),
                    Transacao.data
                    <= date(
                        year if month < 12 else year + 1,
                        month + 1 if month < 12 else 1,
                        1,
                    )
                    - __import__("datetime").timedelta(days=1),
                )
                .scalar()
                or 0.0
            )

            # Query for expenses
            total_despesas = (
                session.query(func.sum(Transacao.valor))
                .filter(
                    Transacao.tipo == "despesa",
                    Transacao.data >= date(year, month, 1),
                    Transacao.data
                    <= date(
                        year if month < 12 else year + 1,
                        month + 1 if month < 12 else 1,
                        1,
                    )
                    - __import__("datetime").timedelta(days=1),
                )
                .scalar()
                or 0.0
            )

            saldo = float(total_receitas) - float(total_despesas)

            resumo = {
                "total_receitas": float(total_receitas),
                "total_despesas": float(total_despesas),
                "saldo": saldo,
            }

            logger.info(f"Resumo {month}/{year}: R$ {saldo:.2f}")
            return resumo

    except Exception as e:
        logger.error(f"Erro ao calcular resumo do dashboard: {e}")
        return {
            "total_receitas": 0.0,
            "total_despesas": 0.0,
            "saldo": 0.0,
        }


def get_cash_flow_data(
    months_past: int = 6, months_future: int = 6
) -> List[Dict[str, Any]]:
    """
    Calcula fluxo de caixa mensal para análise de padrões financeiros.

    Gera dados de receitas, despesas e saldo para cada mês dentro do intervalo
    especificado (N meses passados até M meses futuros). Meses sem transações
    aparecem com valores zerados.

    Args:
        months_past: Número de meses para trás a partir de hoje (default 6).
        months_future: Número de meses para frente a partir de hoje (default 6).

    Returns:
        Lista de dicts ordenada cronologicamente:
            [
                {
                    "mes": "2026-01",
                    "receitas": 1000.0,
                    "despesas": 500.0,
                    "saldo": 500.0
                },
                ...
            ]

    Example:
        >>> fluxo = get_cash_flow_data(months_past=3, months_future=3)
        >>> print(fluxo[0])
        {'mes': '2025-10', 'receitas': 0.0, 'despesas': 0.0, 'saldo': 0.0}
    """
    try:
        hoje = date.today()
        data_inicio = hoje - relativedelta(months=months_past)
        data_fim = hoje + relativedelta(months=months_future)

        # Gerar lista de todos os meses no intervalo
        meses_intervalo = []
        data_atual = data_inicio.replace(day=1)

        while data_atual <= data_fim:
            mes_str = data_atual.strftime("%Y-%m")
            meses_intervalo.append(mes_str)
            data_atual = data_atual + relativedelta(months=1)

        # Inicializar dicionário com todos os meses zerados
        fluxo_dict = {
            mes: {"receitas": 0.0, "despesas": 0.0, "saldo": 0.0}
            for mes in meses_intervalo
        }

        with get_db() as session:
            # Query de receitas agrupadas por mês
            receitas_query = (
                session.query(
                    func.strftime("%Y-%m", Transacao.data).label("mes"),
                    func.sum(Transacao.valor).label("total"),
                )
                .filter(
                    Transacao.tipo == "receita",
                    Transacao.data >= data_inicio,
                    Transacao.data <= data_fim,
                )
                .group_by("mes")
                .all()
            )

            # Query de despesas agrupadas por mês
            despesas_query = (
                session.query(
                    func.strftime("%Y-%m", Transacao.data).label("mes"),
                    func.sum(Transacao.valor).label("total"),
                )
                .filter(
                    Transacao.tipo == "despesa",
                    Transacao.data >= data_inicio,
                    Transacao.data <= data_fim,
                )
                .group_by("mes")
                .all()
            )

            # Preencher dicionário com dados reais
            for mes, total in receitas_query:
                if mes in fluxo_dict:
                    fluxo_dict[mes]["receitas"] = float(total) if total else 0.0

            for mes, total in despesas_query:
                if mes in fluxo_dict:
                    fluxo_dict[mes]["despesas"] = float(total) if total else 0.0

        # Calcular saldo para cada mês e construir resultado final
        resultado = []
        for mes in meses_intervalo:
            receitas = fluxo_dict[mes]["receitas"]
            despesas = fluxo_dict[mes]["despesas"]
            saldo = receitas - despesas

            resultado.append(
                {
                    "mes": mes,
                    "receitas": receitas,
                    "despesas": despesas,
                    "saldo": saldo,
                }
            )

        logger.info(
            f"Fluxo de caixa calculado: {len(resultado)} meses "
            f"({meses_intervalo[0]} até {meses_intervalo[-1]})"
        )
        return resultado

    except Exception as e:
        logger.error(f"Erro ao calcular fluxo de caixa: {e}")
        return []
