"""
Componente de Matriz Analítica para visualização de tags vs meses.

Renderiza uma tabela interativa onde linhas são tags (entidades como "Mãe", "Trabalho")
e colunas são meses. Cada célula contém o saldo líquido (Receitas - Despesas) daquela
tag naquele mês. Os nomes das tags funcionam como botões clicáveis para drill-down.
"""

from typing import Any, Dict

import dash_bootstrap_components as dbc
from dash import html, dcc


def format_currency(valor: float) -> str:
    """
    Formata um valor numérico para moeda brasileira (R$).

    Args:
        valor: Valor a ser formatado.

    Returns:
        String formatada como "R$ 1.234,56" ou "-" se valor é 0.

    Example:
        >>> format_currency(500.0)
        'R$ 500,00'
        >>> format_currency(-200.50)
        '-R$ 200,50'
    """
    if valor == 0.0:
        return "-"

    is_negative = valor < 0
    valor_abs = abs(valor)

    formatted = (
        f"R$ {valor_abs:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    if is_negative:
        return f"-{formatted}"
    return formatted


def get_cell_color_class(valor: float) -> str:
    """
    Retorna classe Bootstrap para colorir célula baseado no valor.

    Args:
        valor: Saldo líquido.

    Returns:
        Classe CSS para estilo (text-success, text-danger, text-muted).

    Example:
        >>> get_cell_color_class(500.0)
        'text-success'
        >>> get_cell_color_class(-200.0)
        'text-danger'
    """
    if valor > 0:
        return "text-success"  # Verde - A receber
    elif valor < 0:
        return "text-danger"  # Vermelho - A pagar
    else:
        return "text-muted"  # Cinza - Zerado


def format_month_header(mes_str: str) -> str:
    """
    Formata string de mês de "2026-01" para "Jan/26".

    Args:
        mes_str: Mês em formato "YYYY-MM".

    Returns:
        String formatada como "Jan/26".

    Example:
        >>> format_month_header("2026-01")
        'Jan/26'
    """
    meses_abrev = {
        "01": "Jan",
        "02": "Fev",
        "03": "Mar",
        "04": "Abr",
        "05": "Mai",
        "06": "Jun",
        "07": "Jul",
        "08": "Ago",
        "09": "Set",
        "10": "Out",
        "11": "Nov",
        "12": "Dez",
    }
    ano, mes = mes_str.split("-")
    mes_abrev = meses_abrev.get(mes, mes)
    ano_abrev = ano[-2:]
    return f"{mes_abrev}/{ano_abrev}"


def render_tag_matrix(data: Dict[str, Any]) -> html.Div:
    """
    Renderiza tabela cruzada de tags vs meses com saldos líquidos.

    Cria uma tabela interativa (dbc.Table) onde:
    - Linhas: Tags/Entidades (Mãe, Trabalho, etc)
    - Colunas: Meses (formatados como "Jan/26")
    - Células: Saldo líquido formatado em R$
      * Verde (>0): A receber
      * Vermelho (<0): A pagar
      * Cinza (=0): Zerado

    Os nomes das tags são botões clicáveis que disparam evento
    para drill-down de detalhes (similar ao componente de categorias).

    Args:
        data: Dict retornado por `get_tag_matrix_data()` com
            estrutura:
            {
                "meses": ["2026-01", "2026-02", ...],
                "tags": [
                    {"nome": "Mãe", "valores": {"2026-01": 500.0, ...}},
                    {"nome": "Trabalho", "valores": {"2026-01": -200.0, ...}},
                    ...
                ]
            }

    Returns:
        html.Div contendo a tabela formatada com estilo responsivo.

    Example:
        >>> data = {
        ...     "meses": ["2026-01"],
        ...     "tags": [{"nome": "Mãe", "valores": {"2026-01": 500.0}}]
        ... }
        >>> matriz = render_tag_matrix(data)
    """
    meses = data.get("meses", [])
    tags = data.get("tags", [])

    if not meses or not tags:
        return dbc.Alert(
            "Nenhuma tag com transações encontrada.",
            color="info",
            className="mt-3",
        )

    # Cabeçalho da tabela: Tags + Meses
    header_cells = [html.Th("Tag")]
    for mes in meses:
        header_cells.append(
            html.Th(format_month_header(mes), style={"textAlign": "center"})
        )
    header_cells.append(html.Th("Total"))

    # Linhas da tabela: Uma por tag
    body_rows = []

    for tag_data in tags:
        tag_nome = tag_data["nome"]
        valores = tag_data["valores"]

        # Primeira célula: Nome da tag como botão
        tag_cell = html.Td(
            html.A(
                f"🏷️ {tag_nome}",
                id={"type": "btn-tag-detail", "index": tag_nome},
                href="#",
                className="text-primary",
                style={"cursor": "pointer", "textDecoration": "none"},
            )
        )

        row_cells = [tag_cell]

        # Células de valor por mês
        total_tag = 0.0
        for mes in meses:
            valor = valores.get(mes, 0.0)
            total_tag += valor

            cell_content = format_currency(valor)
            color_class = get_cell_color_class(valor)

            row_cells.append(
                html.Td(
                    cell_content,
                    className=color_class,
                    style={"textAlign": "right", "fontWeight": "500"},
                )
            )

        # Última célula: Total da tag
        total_content = format_currency(total_tag)
        total_color = get_cell_color_class(total_tag)
        row_cells.append(
            html.Td(
                total_content,
                className=total_color,
                style={"textAlign": "right", "fontWeight": "bold", "fontSize": "1.1em"},
            )
        )

        body_rows.append(html.Tr(row_cells))

    # Rodapé: Total por mês
    footer_cells = [html.Th("Total")]
    total_geral = 0.0

    for mes in meses:
        mes_total = sum(tag.get("valores", {}).get(mes, 0.0) for tag in tags)
        total_geral += mes_total

        footer_content = format_currency(mes_total)
        footer_color = get_cell_color_class(mes_total)

        footer_cells.append(
            html.Th(
                footer_content,
                className=footer_color,
                style={"textAlign": "right", "fontWeight": "bold"},
            )
        )

    # Total geral
    footer_content = format_currency(total_geral)
    footer_color = get_cell_color_class(total_geral)
    footer_cells.append(
        html.Th(
            footer_content,
            className=footer_color,
            style={"textAlign": "right", "fontWeight": "bold", "fontSize": "1.1em"},
        )
    )

    # Construir tabela
    tabela = dbc.Table(
        [
            html.Thead(html.Tr(header_cells)),
            html.Tbody(body_rows),
            html.Tfoot(html.Tr(footer_cells)),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
        className="mt-3",
        style={"minWidth": "1000px"},
    )

    return html.Div(tabela, style={"overflowX": "auto"})
