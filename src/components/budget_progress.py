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


def render_budget_progress(
    data: Dict[str, Any], month_index: Optional[int] = None
) -> dbc.Card:
    """
    Renderiza um card com barras de progresso de orçamento por categoria.

    Se `month_index` for fornecido, analisa esse mês específico.
    Caso contrário, detecta automaticamente o mês atual do sistema e exibe o
    orçamento para esse mês. Filtra apenas despesas com meta definida (meta > 0),
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
        month_index: Índice do mês a analisar (opcional). Se None, auto-detecta.

    Returns:
        dbc.Card contendo barras de progresso organizadas por criticidade.

    Example:
        >>> matriz = get_category_matrix_data(months_past=1, months_future=1)
        >>> card = render_budget_progress(matriz)  # Auto-detecta mês atual
        >>> card = render_budget_progress(matriz, month_index=0)  # Primeiro mês
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

        # Determinar o mês a exibir
        if month_index is not None:
            # Usar o índice fornecido
            if abs(month_index) > len(meses):
                logger.warning(f"⚠️ Índice {month_index} fora dos limites")
                target_index = -1
            else:
                target_index = month_index
            mes_exibido = meses[target_index]
            eh_mes_atual = mes_exibido == datetime.now().strftime("%Y-%m")
            logger.info(
                f"✓ Usando mês fornecido: {mes_exibido} (índice {target_index})"
            )
        else:
            # Auto-detectar mês atual do sistema
            mes_atual_sistema = datetime.now().strftime("%Y-%m")

            if mes_atual_sistema in meses:
                # Encontrou o mês atual na lista
                target_index = meses.index(mes_atual_sistema)
                mes_exibido = mes_atual_sistema
                eh_mes_atual = True
                logger.info(
                    f"✓ Mês atual encontrado: {mes_exibido} (índice {target_index})"
                )
            else:
                # Mês atual não está na lista (ex: apenas dados históricos)
                # Usar último mês disponível como fallback
                target_index = -1
                mes_exibido = meses[target_index] if meses else "N/A"
                eh_mes_atual = False
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
                logger.debug(f"⏭️  Despesa '{despesa.get('nome')}' sem meta, ignorando")
                continue

            # Obter valor gasto no mês alvo
            valores = despesa.get("valores", {})
            target_month_str = data["meses"][target_index]

            # Tratar ambos os formatos: dict (chave=data) e list (índice)
            if isinstance(valores, dict):
                valor_gasto = valores.get(target_month_str, 0.0)
            elif isinstance(valores, list):
                try:
                    valor_gasto = valores[target_index]
                except IndexError:
                    valor_gasto = 0.0
            else:
                valor_gasto = 0.0

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
        despesas_com_progresso.sort(key=lambda x: x["percentual"], reverse=True)

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


def render_budget_dashboard(data: Dict[str, Any]) -> dbc.Row:
    """
    Renderiza um dashboard temporal de orçamento com cards para cada mês.

    Cria uma galeria de orçamentos permitindo visualizar a situação
    financeira de cada mês individualmente em um layout responsivo.
    O mês atual é destacado visualmente com uma borda/estilo especial.

    Args:
        data: Dicionário retornado por `get_category_matrix_data` contendo:
            - "meses": Lista de meses (ex: ["2026-01", "2026-02", ...])
            - "receitas": Lista de categorias de receita
            - "despesas": Lista de categorias de despesa

    Returns:
        dbc.Row contendo colunas responsivas com cards de orçamento para cada mês.

    Example:
        >>> matriz = get_category_matrix_data(months_past=3, months_future=3)
        >>> dashboard = render_budget_dashboard(matriz)
    """
    try:
        logger.debug("📊 Renderizando dashboard temporal de orçamento")

        meses = data.get("meses", [])

        if not meses:
            logger.warning("⚠️ Nenhum mês disponível para dashboard")
            return dbc.Row(
                dbc.Col(
                    dbc.Alert(
                        "Nenhum dado disponível para análise",
                        color="info",
                    )
                )
            )

        # Identificar o mês atual do sistema
        mes_atual_sistema = datetime.now().strftime("%Y-%m")
        mes_atual_index = None
        if mes_atual_sistema in meses:
            mes_atual_index = meses.index(mes_atual_sistema)

        # Construir lista de cards para cada mês
        colunas = []

        for idx, mes in enumerate(meses):
            # Renderizar card para este mês
            card = render_budget_progress(data, month_index=idx)

            # Destacar mês atual (se aplicável)
            if idx == mes_atual_index:
                # Adicionar estilo de destaque
                card.className = "shadow-lg border-primary border-3"
                logger.info(f"✨ Mês atual destacado: {mes} (índice {idx})")

            # Envolver card em coluna responsiva
            col = dbc.Col(
                card,
                width=12,
                md=6,
                xl=4,
                className="mb-4",
            )

            colunas.append(col)

        logger.info(f"📊 Dashboard gerado com {len(colunas)} card(s) de orçamento")

        # Retornar grid responsivo
        return dbc.Row(colunas, className="g-4")

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar dashboard de orçamento: {e}", exc_info=True)
        return dbc.Row(
            dbc.Col(
                dbc.Alert(
                    f"Erro ao carregar dashboard: {str(e)}",
                    color="danger",
                )
            )
        )


def render_budget_matrix(data: Dict[str, Any]) -> dbc.Card:
    """
    Renderiza uma matriz de orçamento (tabela densa) mostrando a evolução
    ao longo dos meses.

    A tabela mostra:
    - Coluna 1: Nome da categoria (despesas com meta > 0 OU com gastos)
    - Colunas 2+: Um mês cada, com valores e cores condicionais
    - Cores para categorias COM meta: Verde (<80%), Amarelo (80-100%), Vermelho (>100%)
    - Cores para categorias SEM meta: Amarelo suave (#fff3cd) se houver gasto, transparente se zero
    - Destaque: Coluna do mês atual fica com borda/fundo destacado

    Args:
        data: Dicionário retornado por `get_category_matrix_data` contendo:
            - "meses": Lista de meses (ex: ["2026-01", "2026-02", ...])
            - "receitas": Lista de categorias de receita
            - "despesas": Lista de categorias de despesa

    Returns:
        dbc.Card contendo a tabela de evolução do orçamento.

    Example:
        >>> matriz = get_category_matrix_data(months_past=3, months_future=3)
        >>> card = render_budget_matrix(matriz)
    """
    try:
        logger.debug("📊 Renderizando matriz de orçamento")

        meses = data.get("meses", [])
        despesas = data.get("despesas", [])

        if not meses:
            logger.warning("⚠️ Nenhum mês disponível para matriz de orçamento")
            return dbc.Card(
                [
                    dbc.CardBody(
                        dbc.Alert(
                            "Nenhum dado disponível",
                            color="info",
                        )
                    )
                ],
                className="shadow-sm",
            )

        # Identificar mês atual
        mes_atual_sistema = datetime.now().strftime("%Y-%m")
        mes_atual_index = (
            meses.index(mes_atual_sistema) if mes_atual_sistema in meses else -1
        )

        # Filtrar despesas: incluir se (meta > 0) OU (tem gasto em algum período)
        despesas_filtradas = []
        for d in despesas:
            meta = d.get("meta", 0)
            valores = d.get("valores", {})

            # Calcular soma total de gastos
            if isinstance(valores, dict):
                soma_gastos = sum(valores.values())
            elif isinstance(valores, list):
                soma_gastos = sum(valores)
            else:
                soma_gastos = 0

            # Incluir se tem meta OU se tem gastos
            if meta > 0 or soma_gastos > 0:
                despesas_filtradas.append(d)

        if not despesas_filtradas:
            logger.warning("⚠️ Nenhuma despesa com meta ou gasto definida")
            return dbc.Card(
                [
                    dbc.CardBody(
                        dbc.Alert(
                            "Nenhuma categoria com orçamento ou gasto registrado",
                            color="info",
                        )
                    )
                ],
                className="shadow-sm",
            )

        logger.info(
            f"📊 Matriz: {len(despesas_filtradas)} categorias x {len(meses)} meses"
        )

        # Construir cabeçalho
        header_cells = [html.Th("Categoria", className="text-center align-middle")]

        for idx, mes in enumerate(meses):
            # Destacar coluna do mês atual
            eh_mes_atual = idx == mes_atual_index
            estilo_coluna = {
                "borderRight": "3px solid #0d6efd" if eh_mes_atual else "none",
                "backgroundColor": "#e7f1ff" if eh_mes_atual else "transparent",
                "fontWeight": "600" if eh_mes_atual else "400",
            }

            label_mes = f"{mes}{'*' if eh_mes_atual else ''}"
            header_cells.append(
                html.Th(
                    label_mes,
                    className="text-center align-middle",
                    style=estilo_coluna,
                )
            )

        thead = html.Thead(html.Tr(header_cells))

        # Construir corpo
        body_rows = []

        for despesa in despesas_filtradas:
            nome = despesa.get("nome", "?")
            meta = despesa.get("meta", 0)
            valores = despesa.get("valores", {})

            # Primeira célula: nome da categoria
            row_cells = [
                html.Td(
                    html.Span(
                        f"{despesa.get('icon', '📁')} {nome}", className="fw-bold"
                    ),
                    className="align-middle",
                )
            ]

            # Célula por mês
            for idx, mes in enumerate(meses):
                eh_mes_atual = idx == mes_atual_index

                # Obter valor gasto
                if isinstance(valores, dict):
                    valor_gasto = valores.get(mes, 0.0)
                elif isinstance(valores, list):
                    try:
                        valor_gasto = valores[idx]
                    except IndexError:
                        valor_gasto = 0.0
                else:
                    valor_gasto = 0.0

                # CASO 1: Com Meta (meta > 0)
                if meta > 0:
                    # Calcular percentual
                    percentual = (valor_gasto / meta * 100) if meta > 0 else 0
                    percentual_visual = min(percentual, 100)  # Limitar a 100% para CSS

                    # Determinar cor da barra (gradiente)
                    if percentual < 80:
                        cor_barra = "#d1e7dd"  # Verde suave
                        cor_texto = "#155724"  # Verde escuro
                    elif percentual <= 100:
                        cor_barra = "#fff3cd"  # Amarelo suave
                        cor_texto = "#856404"  # Marrom escuro
                    else:
                        cor_barra = "#f8d7da"  # Vermelho suave
                        cor_texto = "#721c24"  # Vermelho escuro

                    # Formatar texto
                    texto_valor = f"R$ {valor_gasto:.0f}"
                    texto_meta = f"R$ {meta:.0f}"
                    texto_percentual = f"({percentual:.0f}%)"
                    conteudo = html.Div(
                        [
                            html.Small(
                                f"{texto_valor} / {texto_meta}", className="d-block"
                            ),
                            html.Small(texto_percentual, className="d-block fw-bold"),
                        ],
                        style={
                            "color": cor_texto,
                            "position": "relative",
                            "zIndex": "2",
                        },
                    )

                    # Aplicar estilo da célula com gradiente de progresso
                    estilo_celula = {
                        "background": f"linear-gradient(90deg, {cor_barra} {percentual_visual}%, transparent {percentual_visual}%)",
                        "borderRight": "2px solid #0d6efd" if eh_mes_atual else "none",
                        "whiteSpace": "nowrap",
                        "padding": "8px 4px",
                        "fontWeight": "600" if percentual > 100 else "400",
                        "position": "relative",
                    }

                # CASO 2: Sem Meta (meta == 0)
                else:
                    # Apenas mostrar valor gasto
                    if valor_gasto > 0:
                        # Gasto não planejado: amarelo suave
                        cor_barra = "#fff3cd"
                        cor_texto = "#856404"  # Laranja/marrom
                        conteudo = html.Div(
                            [
                                html.Small(
                                    f"R$ {valor_gasto:.0f}", className="d-block"
                                ),
                                html.Small("(sem meta)", className="d-block fw-bold"),
                            ],
                            style={
                                "color": cor_texto,
                                "position": "relative",
                                "zIndex": "2",
                            },
                        )
                        # Barra sem gradiente: apenas fundo sólido
                        estilo_celula = {
                            "backgroundColor": cor_barra,
                            "borderRight": (
                                "2px solid #0d6efd" if eh_mes_atual else "none"
                            ),
                            "whiteSpace": "nowrap",
                            "padding": "8px 4px",
                            "position": "relative",
                        }
                    else:
                        # Sem gasto e sem meta: transparente
                        conteudo = html.Div(
                            [
                                html.Small("R$ 0,00", className="d-block"),
                                html.Small("-", className="d-block fw-bold"),
                            ],
                            style={
                                "color": "#6c757d",
                                "position": "relative",
                                "zIndex": "2",
                            },
                        )
                        estilo_celula = {
                            "backgroundColor": "transparent",
                            "borderRight": (
                                "2px solid #0d6efd" if eh_mes_atual else "none"
                            ),
                            "whiteSpace": "nowrap",
                            "padding": "8px 4px",
                            "position": "relative",
                        }

                row_cells.append(
                    html.Td(
                        conteudo,
                        className="text-center align-middle small",
                        style=estilo_celula,
                    )
                )

            body_rows.append(html.Tr(row_cells, className="border-bottom"))

        tbody = html.Tbody(body_rows)

        # Construir tabela
        table = dbc.Table(
            [thead, tbody],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            className="mb-0 table-sm",
        )

        # Nota de rodapé
        rodape = html.Div(
            [
                html.Small(
                    "* Indica o mês atual do sistema. Com Meta: Verde <80% | Amarelo 80-100% | Vermelho >100%. Sem Meta: Amarelo se houver gasto não planejado.",
                    className="text-muted d-block mt-2",
                )
            ],
            className="text-center",
        )

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H5(
                        "🎯 Evolução do Orçamento (Realizado vs Meta)",
                        className="mb-0",
                    ),
                    className="bg-light",
                ),
                dbc.CardBody([table, rodape], className="p-3"),
            ],
            className="shadow-sm",
        )

    except Exception as e:
        logger.error(f"✗ Erro ao renderizar matriz de orçamento: {e}", exc_info=True)
        return dbc.Card(
            [
                dbc.CardBody(
                    dbc.Alert(
                        f"Erro ao carregar matriz de orçamento: {str(e)}",
                        color="danger",
                    )
                )
            ],
            className="shadow-sm",
        )
