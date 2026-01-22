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
    nome: str,
    tipo: str,
    cor: str = "#6B7280",
    icone: Optional[str] = None,
    teto_mensal: float = 0.0,
) -> Tuple[bool, str]:
    """
    Creates a new category for transactions.

    Args:
        nome: Category name (e.g., 'Alimentação').
        tipo: Category type ('receita' or 'despesa').
        cor: Color in hex format #RRGGBB (default: #6B7280).
        icone: Optional emoji or icon name.
        teto_mensal: Monthly budget/ceiling for the category (default 0.0).

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
        ...     icone='💰',
        ...     teto_mensal=5000.0
        ... )
        (True, 'Categoria criada com sucesso.')
    """
    try:
        logger.debug(f"🔄 Tentando criar categoria: {nome} ({tipo})")

        # Validação de tipo
        if tipo not in Categoria.TIPOS_VALIDOS:
            logger.error(f"❌ Tipo inválido: {tipo}")
            return False, "Tipo deve ser 'receita' ou 'despesa'."

        # Validar e normalizar teto_mensal
        meta_valor = 0.0
        if teto_mensal is not None:
            try:
                meta_valor = float(teto_mensal)
                if meta_valor < 0:
                    meta_valor = 0.0
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Meta inválida: {teto_mensal}, usando 0.0")
                meta_valor = 0.0

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
                nova_categoria = Categoria(
                    nome=nome,
                    tipo=tipo,
                    cor=cor,
                    icone=icone,
                    teto_mensal=meta_valor,
                )
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


def get_used_icons(tipo: str) -> List[str]:
    """
    Retrieves all icons already used for a given category type.

    Args:
        tipo: Category type ('receita' or 'despesa').

    Returns:
        List of icon strings (emojis) already in use for the type.

    Example:
        >>> get_used_icons(tipo='receita')
        ['💰', '💸', '🏦']
    """
    try:
        with get_db() as session:
            icons = (
                session.query(Categoria.icone)
                .filter(
                    Categoria.tipo == tipo,
                    Categoria.icone.isnot(None),
                )
                .all()
            )
            # Extrair apenas os valores (tuples contém um elemento)
            icons_list = [icon[0] for icon in icons]
            logger.debug(f"Icones usados para '{tipo}': {len(icons_list)} encontrados")
            return icons_list

    except Exception as e:
        logger.error(f"Erro ao recuperar icones usados: {e}")
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


def update_category(
    category_id: int,
    novo_nome: Optional[str] = None,
    novo_icone: Optional[str] = None,
    novo_teto: Optional[float] = None,
) -> Tuple[bool, str]:
    """
    Updates a category with new name, icon, and/or budget ceiling.

    Only updates fields that are provided (not None). Validates all inputs
    before making changes.

    Args:
        category_id: ID of the category to update.
        novo_nome: New category name (optional).
        novo_icone: New icon/emoji (optional).
        novo_teto: New monthly budget ceiling in R$ (optional).

    Returns:
        Tuple with (success: bool, message: str).

    Raises:
        ValueError: If validation fails (invalid color, etc).

    Example:
        >>> update_category(5, novo_nome="Saúde", novo_teto=500.0)
        (True, 'Categoria atualizada com sucesso.')
    """
    try:
        logger.debug(f"🔄 Tentando atualizar categoria ID: {category_id}")

        with get_db() as session:
            try:
                # Buscar categoria existente
                categoria = (
                    session.query(Categoria).filter(Categoria.id == category_id).first()
                )

                if not categoria:
                    logger.warning(f"❌ Categoria não encontrada: ID {category_id}")
                    return False, "Categoria não encontrada."

                # Log do estado anterior
                nome_anterior = categoria.nome
                icone_anterior = categoria.icone
                teto_anterior = categoria.teto_mensal

                # Atualizar nome se fornecido
                if novo_nome is not None:
                    novo_nome = novo_nome.strip()
                    if not novo_nome:
                        logger.warning("⚠️ Nome vazio fornecido")
                        return False, "Nome da categoria não pode estar vazio."
                    categoria.nome = novo_nome
                    logger.debug(f"   Nome: '{nome_anterior}' → '{novo_nome}'")

                # Atualizar ícone se fornecido
                if novo_icone is not None:
                    # Validar que ícone não está em uso por outra categoria do mesmo tipo
                    icone_duplicado = (
                        session.query(Categoria)
                        .filter(
                            Categoria.tipo == categoria.tipo,
                            Categoria.icone == novo_icone,
                            Categoria.id != category_id,  # Excluir a própria categoria
                        )
                        .first()
                    )
                    if icone_duplicado:
                        logger.warning(
                            f"⚠️ Ícone '{novo_icone}' já em uso por outra categoria"
                        )
                        return (
                            False,
                            f"Ícone '{novo_icone}' já está em uso em outra categoria.",
                        )
                    categoria.icone = novo_icone
                    logger.debug(f"   Ícone: '{icone_anterior}' → '{novo_icone}'")

                # Atualizar teto mensal se fornecido
                if novo_teto is not None:
                    # Validar e normalizar teto
                    try:
                        teto_valor = float(novo_teto)
                        if teto_valor < 0:
                            teto_valor = 0.0
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Teto inválido: {novo_teto}")
                        return False, "Teto mensal deve ser um número válido."
                    categoria.teto_mensal = teto_valor
                    logger.debug(
                        f"   Teto: R$ {teto_anterior:.2f} → R$ {teto_valor:.2f}"
                    )

                # Commit das mudanças
                session.commit()
                logger.info(
                    f"✅ Categoria atualizada: {categoria.nome} (ID: {category_id})"
                )
                return True, "Categoria atualizada com sucesso."

            except IntegrityError as ie:
                session.rollback()
                logger.warning(f"⚠️ Erro de integridade (possível duplicata): {ie}")
                return False, "Categoria com esse nome e tipo já existe."

            except ValueError as ve:
                session.rollback()
                logger.error(f"❌ Erro de validação: {ve}")
                return False, str(ve)

            except Exception as e:
                session.rollback()
                logger.error(f"❌ Erro inesperado ao atualizar categoria: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar categoria: {e}", exc_info=True)
        return False, "Erro ao atualizar categoria. Tente novamente."


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
        {"nome": "Salário", "cor": "#10B981", "icone": "💼", "teto_mensal": 5000.0},
        {"nome": "Mesada", "cor": "#06B6D4", "icone": "🎁", "teto_mensal": 500.0},
        {"nome": "Vendas", "cor": "#F59E0B", "icone": "🛒", "teto_mensal": 2000.0},
        {
            "nome": "Investimentos",
            "cor": "#8B5CF6",
            "icone": "📈",
            "teto_mensal": 1000.0,
        },
        {"nome": "Outros", "cor": "#6B7280", "icone": "❓", "teto_mensal": 0.0},
    ]

    # Padrão de Despesas
    CATEGORIAS_DESPESA = [
        {"nome": "Alimentação", "cor": "#22C55E", "icone": "🍔", "teto_mensal": 1000.0},
        {"nome": "Moradia", "cor": "#EF4444", "icone": "🏠", "teto_mensal": 2000.0},
        {"nome": "Transporte", "cor": "#0EA5E9", "icone": "🚗", "teto_mensal": 500.0},
        {"nome": "Lazer", "cor": "#A855F7", "icone": "🎬", "teto_mensal": 500.0},
        {"nome": "Saúde", "cor": "#FB923C", "icone": "⚕️", "teto_mensal": 300.0},
        {"nome": "Educação", "cor": "#06B6D4", "icone": "📚", "teto_mensal": 800.0},
        {"nome": "Outros", "cor": "#6B7280", "icone": "❓", "teto_mensal": 0.0},
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
                    teto_mensal=cat_info.get("teto_mensal", 0.0),
                )
                session.add(nova_categoria)

            # Criar categorias de despesa
            for cat_info in CATEGORIAS_DESPESA:
                nova_categoria = Categoria(
                    nome=cat_info["nome"],
                    tipo=Categoria.TIPO_DESPESA,
                    cor=cat_info["cor"],
                    icone=cat_info["icone"],
                    teto_mensal=cat_info.get("teto_mensal", 0.0),
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
    tag: Optional[str | List[str]] = None,
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
        tag: Optional tag(s) for cross-cutting grouping. Can be:
            - Single string: 'Mãe' → stored as 'Mãe'
            - List of strings: ['Mãe', 'Saúde'] → stored as 'Mãe,Saúde'
        tags: Optional comma-separated tags for organization (legacy).
        forma_pagamento: Optional payment method (dinheiro, pix, credito, etc).
        numero_parcelas: Number of installments (default 1).
        is_recorrente: Whether transaction is recurring (default False).
        frequencia_recorrencia: Recurrence frequency (diaria, semanal, quinzenal, mensal, etc).
        data_limite_recorrencia: End date for recurrence (optional).
        origem: Origin of transaction for income (ex: Banco X).

    Returns:
        Tuple with (success: bool, message: str).

    Example:
        >>> # Create a purchase in 3 installments with multiple tags
        >>> create_transaction(
        ...     tipo='despesa',
        ...     descricao='Compra',
        ...     valor=300.0,
        ...     data=date(2026, 1, 18),
        ...     categoria_id=1,
        ...     numero_parcelas=3,
        ...     forma_pagamento='credito',
        ...     tag=['Mãe', 'Saúde']
        ... )
        # Creates 3 transactions: 100 each, on 18/01, 18/02, 18/03, each with tags 'Mãe,Saúde'
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

        # Normalizar tag: converter lista para string CSV, ou deixar None
        tag_normalizada: Optional[str] = None
        if tag:
            if isinstance(tag, list):
                # Lista de tags: juntar com vírgula
                tag_normalizada = ",".join(str(t).strip() for t in tag if t)
            else:
                # String única: usar diretamente
                tag_normalizada = str(tag).strip() if tag else None

        logger.debug(f"📝 Validações OK. Tag normalizada: {tag_normalizada}")
        logger.debug(f"🔓 Abrindo sessão do banco...")
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
                            tag=tag_normalizada,
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
                                tag=tag_normalizada,
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
                    tag=tag_normalizada,
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
    tag: Optional[str] = None,
) -> List[Dict]:
    """
    Retrieves transactions filtered by date range and optional tag.

    Args:
        start_date: Start of date range (inclusive).
        end_date: End of date range (inclusive).
        tag: Optional tag filter for cross-cutting grouping (ex: 'Mãe', 'Trabalho').

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
            if tag:
                query = query.filter(Transacao.tag == tag)

            transacoes = query.order_by(Transacao.data.desc()).all()

            lista_transacoes = [transacao.to_dict() for transacao in transacoes]
            logger.info(f"Recuperadas {len(lista_transacoes)} transações.")
            return lista_transacoes

    except Exception as e:
        logger.error(f"Erro ao recuperar transações: {e}")
        return []


def get_all_tags() -> List[str]:
    """
    Retrieves all unique tags already used in transactions.

    Handles CSV-formatted tags (e.g., 'Mãe,Saúde') by splitting and
    deduplicating across all transactions.

    Returns:
        Sorted list of unique tag strings used in database.

    Example:
        >>> tags = get_all_tags()
        >>> 'Mãe' in tags
        True
        >>> 'Saúde' in tags
        True
    """
    try:
        with get_db() as session:
            tags_raw = (
                session.query(Transacao.tag)
                .filter(Transacao.tag.isnot(None))
                .distinct()
                .all()
            )

            # Coletar todas as tags individuais
            todas_tags_set: set[str] = set()
            for tag_tuple in tags_raw:
                tag_str = tag_tuple[0] if tag_tuple else None
                if tag_str:
                    # Se houver vírgula, é CSV: splitá-la
                    if "," in tag_str:
                        tags_individuais = [
                            t.strip() for t in tag_str.split(",") if t.strip()
                        ]
                        todas_tags_set.update(tags_individuais)
                    else:
                        # Tag simples
                        todas_tags_set.add(tag_str.strip())

            lista_tags = sorted(list(todas_tags_set))
            logger.debug(f"Tags únicas recuperadas: {len(lista_tags)}")
            return lista_tags

    except Exception as e:
        logger.error(f"Erro ao recuperar tags: {e}")
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


def get_category_matrix_data(
    months_past: int = 6, months_future: int = 6
) -> Dict[str, Any]:
    """
    Gera matriz analítica de transações agrupadas por categoria e mês.

    Prepara dados para visualização de tabela cruzada onde linhas são
    categorias (com ícones) e colunas são meses. Cada célula contém
    a soma das transações daquela categoria naquele mês.

    Args:
        months_past: Número de meses para trás a partir de hoje (default 6).
        months_future: Número de meses para frente a partir de hoje (default 6).

    Returns:
        Dict com estrutura:
            {
                "meses": ["2026-01", "2026-02", ...],
                "receitas": [
                    {
                        "id": 1,
                        "nome": "Salário",
                        "icon": "💰",
                        "meta": 5000.0,
                        "valores": {"2026-01": 5000.0, "2026-02": 5000.0, ...}
                    },
                    ...
                ],
                "despesas": [
                    {
                        "id": 5,
                        "nome": "Alimentação",
                        "icon": "🍔",
                        "meta": 1000.0,
                        "valores": {"2026-01": 800.0, ...}
                    },
                    ...
                ]
            }

    Example:
        >>> matriz = get_category_matrix_data(months_past=3, months_future=3)
        >>> print(matriz["meses"])
        ['2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03']
        >>> print(len(matriz["receitas"]))
        3
    """
    try:
        hoje = date.today()
        data_inicio = hoje - relativedelta(months=months_past)
        data_fim = hoje + relativedelta(months=months_future)

        # Gerar lista de todos os meses no intervalo (reutiliza lógica get_cash_flow_data)
        meses_intervalo = []
        data_atual = data_inicio.replace(day=1)

        while data_atual <= data_fim:
            mes_str = data_atual.strftime("%Y-%m")
            meses_intervalo.append(mes_str)
            data_atual = data_atual + relativedelta(months=1)

        with get_db() as session:
            # Query: Agrupar transações por categoria e mês
            query = (
                session.query(
                    Categoria.id,
                    Categoria.nome,
                    Categoria.icone,
                    Categoria.tipo,
                    Categoria.teto_mensal,
                    func.strftime("%Y-%m", Transacao.data).label("mes"),
                    func.sum(Transacao.valor).label("total"),
                )
                .join(Transacao, Categoria.id == Transacao.categoria_id)
                .filter(
                    Transacao.data >= data_inicio,
                    Transacao.data <= data_fim,
                )
                .group_by(
                    Categoria.id,
                    Categoria.nome,
                    Categoria.icone,
                    Categoria.tipo,
                    Categoria.teto_mensal,
                    "mes",
                )
                .all()
            )

            # Estruturar dados: {categoria_id: {tipo, nome, icone, meta, valores: {mes: total}}}
            categorias_dict = {}

            for categoria_id, nome, icone, tipo, teto_mensal, mes, total in query:
                if categoria_id not in categorias_dict:
                    # Tratar None como 0.0
                    meta_valor = teto_mensal if teto_mensal is not None else 0.0
                    categorias_dict[categoria_id] = {
                        "id": categoria_id,
                        "nome": nome,
                        "icon": icone or "📊",  # Ícone padrão se não houver
                        "tipo": tipo,
                        "meta": float(meta_valor),
                        "valores": {mes_col: 0.0 for mes_col in meses_intervalo},
                    }

                # Preencher valor do mês específico
                if mes in categorias_dict[categoria_id]["valores"]:
                    categorias_dict[categoria_id]["valores"][mes] = (
                        float(total) if total else 0.0
                    )

            # Separar por tipo e remover chave 'tipo'
            receitas_list = []
            despesas_list = []

            for categoria_id, cat_data in categorias_dict.items():
                categoria_info = {
                    "id": cat_data["id"],
                    "nome": cat_data["nome"],
                    "icon": cat_data["icon"],
                    "meta": cat_data["meta"],
                    "valores": cat_data["valores"],
                }

                if cat_data["tipo"] == "receita":
                    receitas_list.append(categoria_info)
                elif cat_data["tipo"] == "despesa":
                    despesas_list.append(categoria_info)

            # Ordenar por nome para consistência
            receitas_list.sort(key=lambda x: x["nome"])
            despesas_list.sort(key=lambda x: x["nome"])

            resultado = {
                "meses": meses_intervalo,
                "receitas": receitas_list,
                "despesas": despesas_list,
            }

            logger.info(
                f"Matriz de categorias calculada: {len(receitas_list)} receitas, "
                f"{len(despesas_list)} despesas, {len(meses_intervalo)} meses"
            )
            return resultado

    except Exception as e:
        logger.error(f"Erro ao calcular matriz de categorias: {e}")
        return {
            "meses": [],
            "receitas": [],
            "despesas": [],
        }


def get_tag_matrix_data(months_past: int = 6, months_future: int = 6) -> Dict[str, Any]:
    """
    Gera matriz analítica de transações agrupadas por tag e mês.

    Prepara dados para visualização de tabela cruzada onde linhas são
    tags (entidades) e colunas são meses. Cada célula contém o saldo
    líquido (receitas - despesas) daquela tag naquele mês.

    Ignora transações com tag = NULL (queremos ver apenas entidades marcadas).

    Para transações com múltiplas tags (ex: 'Mãe,Saúde'), a transação
    é "explodida" e conta para CADA tag individualmente.

    Args:
        months_past: Número de meses para trás a partir de hoje (default 6).
        months_future: Número de meses para frente a partir de hoje (default 6).

    Returns:
        Dict com estrutura:
            {
                "meses": ["2026-01", "2026-02", ...],
                "tags": [
                    {
                        "nome": "Mãe",
                        "valores": {"2026-01": 500.0, "2026-02": -200.0, ...}
                    },
                    ...
                ]
            }
        Nota: Valores positivos = A receber, Negativos = A pagar.

    Example:
        >>> matriz = get_tag_matrix_data(months_past=3, months_future=3)
        >>> print(matriz["meses"])
        ['2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03']
        >>> print(len(matriz["tags"]))
        3
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

        with get_db() as session:
            # Query: Buscar transações COM tag no período (sem agregar)
            transacoes = (
                session.query(
                    Transacao.tag,
                    Transacao.data,
                    Transacao.tipo,
                    Transacao.valor,
                )
                .filter(
                    Transacao.data >= data_inicio,
                    Transacao.data <= data_fim,
                    Transacao.tag.isnot(None),  # Ignorar tags NULL
                )
                .all()
            )

            # Estruturar dados: {tag: {mes: saldo_liquido}}
            # Com processamento Python para suportar multi-tags
            tags_dict: Dict[str, Dict[str, float]] = {}

            for transacao_row in transacoes:
                tag_str, data_transacao, tipo, valor = transacao_row

                if not tag_str:
                    continue

                # Extrair mês
                if hasattr(data_transacao, "strftime"):
                    mes_key = data_transacao.strftime("%Y-%m")
                else:
                    # String ISO
                    mes_key = str(data_transacao)[:7]

                # Calcular saldo: receita positiva, despesa negativa
                valor_sinal = float(valor) if tipo == "receita" else -float(valor)

                # EXPLODIR: Se houver múltiplas tags, processar cada uma
                if "," in tag_str:
                    # CSV: Dividir por vírgula
                    tags_individuais = [
                        t.strip() for t in tag_str.split(",") if t.strip()
                    ]
                else:
                    # Tag simples
                    tags_individuais = [tag_str.strip()]

                # Acumular a transação para CADA tag
                for tag_individual in tags_individuais:
                    if tag_individual not in tags_dict:
                        tags_dict[tag_individual] = {
                            mes: 0.0 for mes in meses_intervalo
                        }

                    if mes_key in tags_dict[tag_individual]:
                        tags_dict[tag_individual][mes_key] += valor_sinal

            # Converter para lista de tags com valores
            tags_list = []
            for tag_nome in sorted(tags_dict.keys()):
                tags_list.append(
                    {
                        "nome": tag_nome,
                        "valores": tags_dict[tag_nome],
                    }
                )

            resultado = {
                "meses": meses_intervalo,
                "tags": tags_list,
            }

            logger.info(
                f"Matriz de tags calculada: {len(tags_list)} tags, "
                f"{len(meses_intervalo)} meses (com suporte a multi-tags)"
            )
            return resultado

    except Exception as e:
        logger.error(f"Erro ao calcular matriz de tags: {e}")
        return {
            "meses": [],
            "tags": [],
        }
