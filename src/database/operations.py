import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from src.database.connection import get_db
from src.database.models import Categoria, Transacao

logger = logging.getLogger(__name__)


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
        # Validação de tipo
        if tipo not in ["receita", "despesa"]:
            return False, "Tipo deve ser 'receita' ou 'despesa'."

        # Validação de valor
        if valor <= 0:
            return False, "Valor deve ser maior que zero."

        # Validação de descrição
        if not descricao or len(descricao.strip()) == 0:
            return False, "Descrição não pode estar vazia."

        with get_db() as session:
            try:
                # Validar se categoria existe
                categoria = (
                    session.query(Categoria)
                    .filter(Categoria.id == categoria_id)
                    .first()
                )
                if not categoria:
                    return False, "Categoria não encontrada."

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
                            f"Transação recorrente criada: {tipo} - R$ {valor} "
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
                session.commit()

                logger.info(f"Transação criada: {tipo} - R$ {valor} em {data}")
                return True, "Transação registrada com sucesso."

            except Exception as e:
                session.rollback()
                logger.error(f"Erro durante criação de transação: {e}")
                raise

    except Exception as e:
        logger.error(f"Erro ao criar transação: {e}")
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


def get_category_options() -> List[Dict[str, Any]]:
    """
    Retrieves all categories formatted for Dash dcc.Dropdown.

    Returns:
        List of dicts with 'label' (icon + name) and 'value' (id).

    Example:
        >>> get_category_options()
        [{'label': '🍔 Alimentação', 'value': 1}, ...]
    """
    try:
        with get_db() as session:
            categorias = session.query(Categoria).order_by(Categoria.nome).all()

            opcoes = [
                {"label": f"{c.icone} {c.nome}", "value": c.id} for c in categorias
            ]
            logger.info(f"Recuperadas {len(opcoes)} categorias.")
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
