"""
Componentes de Visualização de Gráficos para o Dashboard.

Fornece gráficos interativos para análise de tendências financeiras,
evolução de receitas/despesas e composição de gastos por categoria.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

logger = logging.getLogger(__name__)


def render_evolution_chart(data: Dict[str, Any]) -> dcc.Graph:
    """
    Renderiza gráfico de evolução financeira com barras de receitas/despesas
    e linha de patrimônio acumulado.

    Exibe:
    - Barras agrupadas: Receitas (verde) e Despesas (vermelho) por mês.
    - Linha sobreposta: Patrimônio Acumulado (roxo) evoluindo ao longo do tempo.
    - Layout com eixo Y único para melhor comparação visual.

    Args:
        data: Dicionário retornado por `get_category_matrix_data` com:
            - "meses": Lista de meses (ex: ["2026-01", "2026-02", ...])
            - "receitas": Lista com dados de receitas por mês
            - "despesas": Lista com dados de despesas por mês
            - "saldos": Lista com saldos acumulados por mês (opcional)

    Returns:
        dcc.Graph com figura Plotly interativa.

    Example:
        >>> matriz = get_category_matrix_data(months_past=3, months_future=3)
        >>> chart = render_evolution_chart(matriz)
    """
    try:
        logger.debug(
            "📈 Renderizando gráfico de evolução financeira com patrimônio acumulado"
        )

        meses = data.get("meses", [])
        receitas_data = data.get("receitas", [])
        despesas_data = data.get("despesas", [])
        saldos = data.get("saldos", [])

        if not meses:
            logger.warning("⚠️ Nenhum mês disponível para gráfico de evolução")
            fig = go.Figure()
            fig.add_annotation(
                text="Sem dados disponíveis",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
            )
            return dcc.Graph(figure=fig, config={"displayModeBar": False})

        # Processar dados da matriz: agregar valores por mês
        # receitas_data e despesas_data são listas de dicts com {"nome", "valores": {mes: total}, ...}
        receitas_valores = []
        despesas_valores = []

        for mes in meses:
            # Somar receitas do mês
            soma_receitas = sum(
                float(cat.get("valores", {}).get(mes, 0) or 0)
                for cat in receitas_data
                if isinstance(cat, dict)
            )
            receitas_valores.append(soma_receitas)

            # Somar despesas do mês
            soma_despesas = sum(
                float(cat.get("valores", {}).get(mes, 0) or 0)
                for cat in despesas_data
                if isinstance(cat, dict)
            )
            despesas_valores.append(soma_despesas)

        # Calcular saldo mensal e montante acumulado
        saldos_mensais = [r - d for r, d in zip(receitas_valores, despesas_valores)]
        montante_acumulado = []
        acumulado = 0.0
        for saldo in saldos_mensais:
            acumulado += saldo
            montante_acumulado.append(acumulado)

        # Verificar se todos os valores são zero (sem histórico)
        total_receitas = sum(receitas_valores)
        total_despesas = sum(despesas_valores)

        if total_receitas == 0 and total_despesas == 0:
            logger.info("ℹ️ Sem histórico recente para exibir gráfico de evolução")
            return html.Div(
                [
                    html.Div(
                        [
                            html.H3("📅", className="mb-3", style={"fontSize": "3rem"}),
                            html.H5(
                                "Sem histórico recente para exibir",
                                className="text-muted",
                            ),
                            html.P(
                                "Realize algumas transações para visualizar a evolução financeira.",
                                className="text-muted small",
                            ),
                        ],
                        className="text-center",
                        style={
                            "padding": "3rem 2rem",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                        },
                    )
                ],
                style={"minHeight": "400px", "display": "flex", "alignItems": "center"},
            )

        logger.info(
            f"✓ Gráfico de evolução: {len(meses)} meses, "
            f"Receitas: {total_receitas:.2f}, "
            f"Despesas: {total_despesas:.2f}, "
            f"Patrimônio Final: {montante_acumulado[-1]:.2f}"
        )

        # Criar figura com barras agrupadas + linha de patrimônio
        fig = go.Figure()

        # Adicionar barra de receitas (verde)
        fig.add_trace(
            go.Bar(
                name="Receitas",
                x=meses,
                y=receitas_valores,
                marker_color="#2ecc71",
                marker_line_width=0,
            )
        )

        # Adicionar barra de despesas (vermelho)
        fig.add_trace(
            go.Bar(
                name="Despesas",
                x=meses,
                y=despesas_valores,
                marker_color="#e74c3c",
                marker_line_width=0,
            )
        )

        # Adicionar barra de saldo mensal (azul)
        fig.add_trace(
            go.Bar(
                name="Saldo do Mês",
                x=meses,
                y=saldos_mensais,
                marker_color="#3498db",
                marker_line_width=0,
            )
        )

        # Adicionar linha de patrimônio acumulado (roxo/azul escuro)
        fig.add_trace(
            go.Scatter(
                name="Patrimônio Acumulado",
                x=meses,
                y=montante_acumulado,
                mode="lines+markers",
                line=dict(color="#9b59b6", width=3),
                marker=dict(size=8),
                fill="tozeroy",
                fillcolor="rgba(155, 89, 182, 0.1)",
            )
        )

        # Configurar layout com eixo Y único
        fig.update_layout(
            barmode="group",
            title="📈 Evolução Financeira - Receitas, Despesas, Saldo e Patrimônio Acumulado",
            xaxis_title="Período",
            yaxis_title="Valores em R$",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Arial, sans-serif", size=12),
            height=400,
            margin=dict(l=60, r=60, t=80, b=60),
        )

        # Remove a cor das linhas da grid (manter apenas o padrão)
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        return dcc.Graph(figure=fig, config={"displayModeBar": False})

    except Exception as e:
        logger.error(
            f"✗ Erro ao renderizar gráfico de evolução: {e}",
            exc_info=True,
        )
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao carregar gráfico: {str(e)}",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        return dcc.Graph(figure=fig, config={"displayModeBar": False})


def render_top_expenses_chart(
    current_month_data: Union[List[Dict[str, Any]], pd.DataFrame],
) -> dcc.Graph:
    """
    Renderiza gráfico de rosca (donut) com as top 5 categorias de despesa
    do mês atual + agregação "Outros".

    Exibe a composição de gastos por categoria, permitindo visualizar rapidamente
    em quais áreas o dinheiro foi mais gasto.

    Args:
        current_month_data: Lista de dicts com transações (ou DataFrame) do mês
            atual. Cada item deve ter:
            - "categoria": Nome da categoria
            - "valor": Valor da transação

    Returns:
        dcc.Graph com figura Plotly interativa (donut chart).

    Example:
        >>> transacoes_mês = [
        ...     {"categoria": "Alimentação", "valor": 500},
        ...     {"categoria": "Transporte", "valor": 200},
        ... ]
        >>> chart = render_top_expenses_chart(transacoes_mês)
    """
    try:
        logger.debug("🍩 Renderizando gráfico de despesas por categoria")

        # Verificar se está vazio desde o início
        if not current_month_data:
            logger.info("ℹ️ Sem despesas no mês atual")
            return html.Div(
                [
                    html.Div(
                        [
                            html.H3("💤", className="mb-3", style={"fontSize": "3rem"}),
                            html.H5(
                                "Sem despesas neste mês (ainda!)",
                                className="text-muted",
                            ),
                            html.P(
                                "Quando registrar gastos, aparecerão aqui.",
                                className="text-muted small",
                            ),
                        ],
                        className="text-center",
                        style={
                            "padding": "3rem 2rem",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                        },
                    )
                ],
                style={"minHeight": "400px", "display": "flex", "alignItems": "center"},
            )

        # Converter para DataFrame se for lista
        if isinstance(current_month_data, list):
            df = pd.DataFrame(current_month_data)
        else:
            df = current_month_data.copy()

        if df.empty:
            logger.info("ℹ️ Sem despesas no mês atual (DataFrame vazio)")
            return html.Div(
                [
                    html.Div(
                        [
                            html.H3("💤", className="mb-3", style={"fontSize": "3rem"}),
                            html.H5(
                                "Sem despesas neste mês (ainda!)",
                                className="text-muted",
                            ),
                            html.P(
                                "Quando registrar gastos, aparecerão aqui.",
                                className="text-muted small",
                            ),
                        ],
                        className="text-center",
                        style={
                            "padding": "3rem 2rem",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                        },
                    )
                ],
                style={"minHeight": "400px", "display": "flex", "alignItems": "center"},
            )

        # Agrupar por categoria e somar valores
        categoria_col = "categoria"
        valor_col = "valor"

        # Converter para formato seguro (garantir que "valor" é float e categoria é string)
        dados_limpos = []
        for item in current_month_data:
            try:
                valor = float(item.get(valor_col, 0) or 0)

                # Extrair nome da categoria (pode ser dict ou string)
                categoria_raw = item.get(categoria_col, "Sem categoria")
                if isinstance(categoria_raw, dict):
                    # Se for dicionário, extrair o campo "nome"
                    categoria = categoria_raw.get("nome", "Sem categoria")
                elif isinstance(categoria_raw, str):
                    # Se for string, usar direto
                    categoria = categoria_raw if categoria_raw else "Sem categoria"
                else:
                    # Se for outro tipo, converter para string seguramente
                    categoria = str(categoria_raw) if categoria_raw else "Sem categoria"

                dados_limpos.append({categoria_col: categoria, valor_col: valor})
            except (TypeError, ValueError):
                # Pular items com valor inválido
                continue

        if not dados_limpos:
            logger.info("ℹ️ Nenhuma despesa válida encontrada no período")
            return html.Div(
                [
                    html.Div(
                        [
                            html.H3("💤", className="mb-3", style={"fontSize": "3rem"}),
                            html.H5(
                                "Sem despesas neste mês (ainda!)",
                                className="text-muted",
                            ),
                            html.P(
                                "Quando registrar gastos, aparecerão aqui.",
                                className="text-muted small",
                            ),
                        ],
                        className="text-center",
                        style={
                            "padding": "3rem 2rem",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                        },
                    )
                ],
                style={"minHeight": "400px", "display": "flex", "alignItems": "center"},
            )

        df = pd.DataFrame(dados_limpos)

        # Agrupar e ordenar
        df_agrupado = (
            df.groupby(categoria_col)[valor_col].sum().sort_values(ascending=False)
        )

        logger.info(
            f"✓ {len(df_agrupado)} categorias encontradas, "
            f"total: R$ {df_agrupado.sum():.2f}"
        )

        # Top 5 + Outros
        top_5 = df_agrupado.head(5)
        resto = df_agrupado.iloc[5:].sum()

        # Montar dados do gráfico
        labels = list(top_5.index)
        valores = list(top_5.values)

        if resto > 0:
            labels.append("Outros")
            valores.append(resto)

        # Criar DataFrame para Plotly Express
        df_grafico = pd.DataFrame(
            {
                "categoria": labels,
                "valor": valores,
            }
        )

        # Definir cores (palette)
        cores = [
            "#3498db",  # Azul
            "#e74c3c",  # Vermelho
            "#2ecc71",  # Verde
            "#f39c12",  # Laranja
            "#9b59b6",  # Roxo
            "#95a5a6",  # Cinza (Outros)
        ]
        cores = cores[: len(labels)]

        # Criar gráfico de rosca
        fig = px.pie(
            df_grafico,
            names="categoria",
            values="valor",
            hole=0.6,
            title="🍩 Despesas por Categoria (Top 5)",
            color_discrete_sequence=cores,
        )

        # Atualizar layout
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Arial, sans-serif", size=12),
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
        )

        # Formatar hover com valores em R$
        fig.update_traces(
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>R$ %{value:.2f}<br>%{percent}"
            "<extra></extra>",
        )

        logger.info("✓ Gráfico de despesas renderizado com sucesso")

        return dcc.Graph(figure=fig, config={"displayModeBar": False})

    except Exception as e:
        logger.error(
            f"✗ Erro ao renderizar gráfico de despesas: {e}",
            exc_info=True,
        )
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao carregar gráfico: {str(e)}",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        return dcc.Graph(figure=fig, config={"displayModeBar": False})
