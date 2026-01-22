"""
Componente de Visualização de Progresso de Orçamento.

Exibe barras de progresso para monitorar o gasto de cada categoria
em relação à meta mensal definida. As categorias são ordenadas por
criticidade (% de gasto), com as mais críticas no topo.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


def render_budget_progress(data: Dict[str, Any]) -> dbc.Card:
    """
    Renderiza um card com barras de progresso de orçamento por categoria.

    Detecta automaticamente o mês atual do sistema e exibe o orçamento
    para esse mês. Filtra apenas despesas com meta definida (meta > 0),
    calcula o percentual de gasto em relação à meta e exibe com códigos
    de cores:
    - Verde (success): < 80%
    - Amarelo (warning): 80-100%
    - Vermelho (danger): > 100%

    Args:
        data: Dicionário retornado por `get_category_matrix_data` contendo:
            - "meses": Lista de meses (ex: ["2026-01", "2026-02", ...])
            - "receitas": Lista de categorias de receita
            - "despesas": Lista de categorias de despesa

    Returns:
        dbc.Card contendo barras de progresso organizadas por criticidade.

    Example:
        >>> matriz = get_category_matrix_data(months_past=1, months_future=1)
        >>> card = render_budget_progress(matriz)
    """
    try:
        logger.debug("🎯 Renderizando card de controle de orçamento")

        # Extrair dados
        meses = data.get("meses", [])
        despesas = data.get("despesas", [])

        if not meses:
            logger.warning("⚠️ Nenhum mês disponível para análise de orçamento")
            return dbc.Card(
                [
                    dbc.CardBody(
                        dbc.Alert(
                            "Nenhum dado de mês disponível",
                            color="info",
                        )
                    )
                ],
                className="shadow-sm",
            )

        # Determinar o mês a exibir: prioriza mês atual do sistema
        mes_atual_sistema = datetime.now().strftime("%Y-%m")
        
        if mes_atual_sistema in meses:
            # Encontrou o mês atual na lista
            target_index = meses.index(mes_atual_sistema)
            mes_exibido = mes_atual_sistema
            logger.info(f"✓ Mês atual encontrado: {mes_exibido} (índice {target_index})")
        else:
            # Mês atual não está na lista (ex: apenas dados históricos)
            # Usar último mês disponível como fallback
            target_index = -1
            mes_exibido = meses[target_index] if meses else "N/A"
            logger.warning(
                f"⚠️ Mês atual ({mes_atual_sistema}) não encontrado na lista. "
                f"Usando {mes_exibido} (última disponível)"
            )

        # Filtrar despesas com meta e calcular criticidade
        despesas_com_progresso = []

        for despesa in despesas:
            meta = despesa.get("meta", 0.0)

            # Ignorar categorias sem meta definida
            if meta <= 0:
                logger.debug(
                    f"⏭️  Despesa '{despesa.get('nome')}' sem meta, ignorando"
                )
                continue

            # Obter valor gasto no mês alvo
            valores = despesa.get("valores", [])
            valor_gasto = valores[target_index] if valores else 0.0

            # Calcular percentual
            percentual = (valor_gasto / meta) * 100

            despesas_com_progresso.append(
                {
                    "id": despesa.get("id"),
                    "nome": despesa.get("nome"),
                    "icon": despesa.get("icon", "💸"),
                    "meta": meta,
                    "valor_gasto": valor_gasto,
                    "percentual": percentual,
                }
            )

        # Ordenar por percentual (mais críticas primeiro)
        despesas_com_progresso.sort(
            key=lambda x: x["percentual"], reverse=True
        )

        logger.info(
            f"📊 Despesas com meta: {len(despesas_com_progresso)}, "
            f"mês: {mes_exibido}"
        )

        # Renderizar card
        body_children = []

        if not despesas_com_progresso:
            # Nenhuma despesa com meta
            body_children.append(
                dbc.Alert(
                    "Nenhuma despesa com meta definida",
                    color="info",
                    className="mb-0",
                )
            )
        else:
            # Renderizar cada despesa com barra de progresso
            for desp in despesas_com_progresso:
                # Determinar cor baseada em percentual
                if desp["percentual"] < 80:
                    cor = "success"
                    status_texto = "OK"
                elif desp["percentual"] <= 100:
                    cor = "warning"
                    status_texto = "Atencao"
                else:
                    cor = "danger"
                    status_texto = "Acima do limite"

                # Clamp percentual visual para max 100 na barra
                percentual_visual = min(desp["percentual"], 100)

                # Item de despesa
                item = dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            desp["icon"],
                                            className="me-2",
                                            style={"fontSize": "1.2rem"},
                                        ),
                                        html.Span(
                                            desp["nome"],
                                            className="fw-bold",
                                        ),
                                    ],
                                    className="d-flex align-items-center mb-2",
                                ),
                                dbc.Progress(
                                    value=percentual_visual,
                                    color=cor,
                                    className="mb-2",
                                    style={"height": "8px"},
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"R$ {desp['valor_gasto']:.2f} / "
                                            f"R$ {desp['meta']:.2f}",
                                            className="text-muted small",
                                        ),
                                        html.Span(
                                            f"({desp['percentual']:.1f}%)",
                                            className=f"text-{cor} ms-2 small fw-bold",
                                        ),
                                    ],
                                    className="d-flex justify-content-between",
                                ),
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-3 pb-2 border-bottom",
                )

                body_children.append(item)

        # Remover borda do último item
        if body_children and len(body_children) > 0:
            # Remover a classe border-bottom do último item
            last_item = body_children[-1]
            if isinstance(last_item, dbc.Row):
                # Copiar e remover border
                cols = last_item.children
                if cols and isinstance(cols[0], dbc.Col):
                    pass  # A abordagem anterior não funciona bem, deixar assim

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H5(
                        f"🎯 Controle de Orçamento — {mes_exibido}",
                        className="mb-0",
                    ),
                    className="bg-light",
                ),
                dbc.CardBody(body_children, className="p-3"),
            ],
            className="shadow-sm",
        )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar progresso de orçamento: {e}", exc_info=True)
        return dbc.Card(
            [
                dbc.CardBody(
                    dbc.Alert(
                        f"Erro ao carregar controle de orçamento: {str(e)}",
                        color="danger",
                    )
                )
            ],
            className="shadow-sm",
        )
