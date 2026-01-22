"""
Componente de Interface para Gestão de Categorias.

Fornece uma interface CRUD para visualizar, adicionar e remover categorias,
separadas por tipo (Receita vs Despesa). Utiliza pattern matching IDs
para os botões de exclusão.
"""

import logging
from typing import List, Dict, Any

import dash_bootstrap_components as dbc
from dash import dcc, html

logger = logging.getLogger(__name__)

# Lista vasta de opções de emojis financeiros e de estilo de vida
_EMOJI_RAW = [
    "💰",  # Dinheiro
    "💸",  # Dinheiro indo
    "💵",  # Dólar
    "💴",  # Iene
    "💶",  # Euro
    "💷",  # Libra
    "💳",  # Cartão de crédito
    "🏦",  # Banco
    "💼",  # Pasta/Trabalho
    "💻",  # Computador
    "📱",  # Celular
    "📊",  # Gráfico
    "📈",  # Gráfico para cima
    "📉",  # Gráfico para baixo
    "💹",  # Até/Bolsa
    "🏠",  # Casa
    "🏡",  # Casa com jardim
    "🏘️",  # Casas
    "🏢",  # Prédio comercial
    "🏬",  # Loja
    "🏪",  # Loja pequena
    "🏭",  # Fábrica
    "🏗️",  # Construção
    "🏛️",  # Prédio histórico
    "🚗",  # Carro
    "🚙",  # SUV
    "🚕",  # Táxi
    "🚌",  # Ônibus
    "🚎",  # Ônibus articulado
    "🏎️",  # Carro de corrida
    "🚓",  # Viatura policial
    "🚑",  # Ambulância
    "🚒",  # Bombeiros
    "🚐",  # Van
    "🛻",  # Caminhonete
    "🚚",  # Caminhão
    "🚛",  # Caminhão grande
    "🚜",  # Trator
    "⛽",  # Gasolina
    "🛣️",  # Estrada
    "🛤️",  # Trilho
    "🛢️",  # Tambor de óleo
    "✈️",  # Avião
    "🛫",  # Avião decolando
    "🛬",  # Avião pousando
    "🚁",  # Helicóptero
    "🚂",  # Trem
    "🚆",  # Trem expresso
    "🚇",  # Metrô
    "🚊",  # Bonde
    "🚝",  # Teleférico
    "🍕",  # Pizza
    "🍔",  # Hambúrguer
    "🍟",  # Batata frita
    "🌭",  # Cachorro quente
    "🥪",  # Sanduíche
    "🥙",  # Kebab
    "🧆",  # Falafel
    "🌮",  # Taco
    "🌯",  # Burrito
    "🥗",  # Salada
    "🥘",  # Paella
    "🍜",  # Macarrão
    "🍝",  # Espaguete
    "🍛",  # Curry
    "🍲",  # Sopa
    "🍥",  # Bolo de peixe
    "🥟",  # Dumpling
    "🥠",  # Biscoito da sorte
    "🥮",  # Bolo de lua
    "🍱",  # Caixa de bento
    "🍣",  # Sushi
    "🍢",  # Espetinho
    "🍙",  # Bolinha de arroz
    "🍚",  # Arroz cozido
    "🍤",  # Camarão frito
    "🦪",  # Ostra
    "🍖",  # Perna de frango
    "🍗",  # Frango frito
    "🥓",  # Bacon
    "🥚",  # Ovo
    "🍳",  # Ovos fritos
    "🧈",  # Manteiga
    "🥞",  # Panqueca
    "🧇",  # Waffle
    "🥐",  # Croissant
    "🥯",  # Bagel
    "🍞",  # Pão
    "🥖",  # Baguete
    "🥨",  # Pretzel
    "🧀",  # Queijo
    "🥜",  # Amendoim
    "🌰",  # Castanha
    "🍯",  # Potinho de mel
    "🥛",  # Leite
    "🍼",  # Mamadeira
    "☕",  # Café
    "🍵",  # Chá
    "🍶",  # Saquê
    "🍾",  # Garrafa de champagne
    "🍷",  # Taça de vinho
    "🍸",  # Coquetel
    "🍹",  # Bebida tropical
    "🍺",  # Cerveja
    "🍻",  # Cervejas brindando
    "🥂",  # Taças tintilando
    "🥃",  # Caneca de cidra quente
    "🥤",  # Copo com canudo
    "🧃",  # Caixa de suco
    "🧉",  # Mate
    "🎓",  # Chapéu de formatura
    "📚",  # Livros
    "📖",  # Livro aberto
    "📝",  # Bloco de anotações
    "✏️",  # Lápis
    "✒️",  # Caneta
    "🖋️",  # Pena
    "🖊️",  # Caneta esferográfica
    "🖌️",  # Pincel
    "🖍️",  # Giz de cera
    "📐",  # Transferidor
    "📏",  # Régua
    "📓",  # Caderno
    "📔",  # Caderno com decoração
    "📒",  # Livro maior
    "📕",  # Livro vermelho fechado
    "📗",  # Livro verde fechado
    "📘",  # Livro azul fechado
    "📙",  # Livro laranja fechado
    "📎",  # Clipe
    "🖇️",  # Clipes ligados
    "📌",  # Percevejo
    "📍",  # Pino redondo
    "🎒",  # Mochila
    "⏱️",  # Cronômetro
    "⏰",  # Relógio despertador
    "⌚",  # Relógio
    "⏲️",  # Timer
    "☎️",  # Telefone antigo
    "📲",  # Telefone com seta
    "⌨️",  # Teclado
    "🖥️",  # Desktop
    "🖨️",  # Impressora
    "🖱️",  # Mouse
    "🖲️",  # Trackball
    "🕹️",  # Joystick
    "🗜️",  # Clipe
    "💽",  # Disco compacto
    "💾",  # Disquete
    "💿",  # DVD
    "📀",  # CD
    "📼",  # Fita cassete
    "🎥",  # Câmera de vídeo
    "🎬",  # Filme
    "🎞️",  # Bobina de filme
    "📽️",  # Projetor de filme
    "🎦",  # Sala de cinema
    "📺",  # Televisão
    "📷",  # Câmera fotográfica
    "📸",  # Câmera com flash
    "📹",  # Câmera de vídeo
    "🎙️",  # Microfone
    "🎚️",  # Slider
    "🎛️",  # Controlador
    "🧭",  # Bússola
    "🔧",  # Chave inglesa
    "🔨",  # Martelo
    "⛏️",  # Picareta
    "⚒️",  # Martelo e picareta
    "🛠️",  # Martelo e chave
    "🗡️",  # Espada
    "⚔️",  # Espadas cruzadas
    "🔫",  # Pistola
    "🪃",  # Bumerangue
    "🛡️",  # Escudo
    "🚬",  # Cigarro
    "⚰️",  # Caixão
    "⚱️",  # Urna funerária
    "🏺",  # Ânfora
    "🔮",  # Bola de cristal
    "📿",  # Contas de oração
    "💈",  # Barbeiro
    "⚗️",  # Alambique
    "⚙️",  # Engrenagem
    "🧱",  # Tijolo
    "⛓️",  # Corrente
    "🧲",  # Ímã
    "🔩",  # Parafuso
    "⚖️",  # Balança
    "🧰",  # Caixa de ferramentas
    "🔗",  # Link
    "🪝",  # Gancho
    "🧩",  # Peça de quebra-cabeça
    "💣",  # Bomba
    "🪀",  # Ioiô
    "🪁",  # Pipa
    "🔐",  # Cadeado fechado
    "🔒",  # Cadeado
    "🔓",  # Cadeado aberto
    "🔑",  # Chave
    "🗝️",  # Chave antiga
    "🚪",  # Porta
    "🪑",  # Cadeira
    "🚽",  # Vaso sanitário
    "🚿",  # Chuveiro
    "🛁",  # Banheira
    "🛒",  # Carrinho de compras
    "💡",  # Lâmpada
    "🔦",  # Lanterna
    "🏮",  # Lanterna vermelha
    "🍽️",  # Garfo e faca
    "🥄",  # Colher
    "🧂",  # Sal
    "⛪",  # Igreja
    "🕌",  # Mesquita
    "🕍",  # Sinagoga
    "🛕",  # Templo hindu
    "💒",  # Casamento
    "🏛️",  # Museu (removido duplicado)
    "⛩️",  # Santuário
    "🎪",  # Circo
    "🎭",  # Artes do espetáculo
    "🎨",  # Paleta de arte
    "🎤",  # Microfone
    "🎧",  # Fones de ouvido
    "🎼",  # Partitura
    "🎹",  # Piano
    "🥁",  # Bateria
    "🎷",  # Saxofone
    "🎺",  # Trompete
    "🎸",  # Guitarra
    "🪕",  # Banjo
    "🎻",  # Violino
    "🎲",  # Dado
    "♟️",  # Peão de xadrez
    "🎯",  # Alvo
    "🎳",  # Boliche
    "🎮",  # Videogame
    "🎰",  # Máquina caça-níqueis
    "🏍️",  # Motocicleta
    "🏋️",  # Levantamento de peso
    "⛹️",  # Basquete
    "🤸",  # Acrobacia
    "⛸️",  # Patinação no gelo
    "🎣",  # Pesca
    "🎽",  # Uniforme de corrida
    "🎿",  # Esqui
    "⛷️",  # Esquiador
    "🛷",  # Trenó
    "🥌",  # Curling
    "🪀",  # Ioiô (removido duplicado)
    "🪁",  # Pipa (removido duplicado)
    "⛳",  # Bandeira de golfe
    "🏅",  # Medalha
    "🏆",  # Troféu
    "🥇",  # Medalha de ouro
    "🥈",  # Medalha de prata
    "🥉",  # Medalha de bronze
    "⭐",  # Estrela
    "⛅",  # Sol atrás de nuvem pequena
    "⛈️",  # Nuvem com raio
    "💧",  # Gota d'água
    "❓",  # Ponto de interrogação vermelho
    "❔",  # Ponto de interrogação branco
    "❕",  # Ponto de exclamação branco
    "❗",  # Ponto de exclamação vermelho
    "❌",  # X
    "⭕",  # O
    "🟠",  # Círculo laranja
    "🟡",  # Círculo amarelo
    "🟢",  # Círculo verde
    "🔵",  # Círculo azul
    "🟣",  # Círculo roxo
    "🟤",  # Círculo marrom
]

# Remove duplicatas mantendo a ordem de primeiro aparecimento
EMOJI_OPTIONS = list(dict.fromkeys(_EMOJI_RAW))


def render_icon_selector(id_suffix: str, placeholder_icon: str = "💰") -> html.Div:
    """
    Renderiza um seletor de ícones em grid (3 colunas) dentro de um Popover.

    Args:
        id_suffix: Sufixo para os IDs (ex: "receita", "despesa", "edit").
        placeholder_icon: Ícone inicial a exibir no botão.

    Returns:
        html.Div contendo o botão e o popover com seletor em grid.
    """
    return html.Div(
        [
            dbc.Button(
                placeholder_icon,
                id=f"btn-icon-{id_suffix}",
                color="light",
                size="md",
                className="border",
                style={"fontSize": "1.5rem", "padding": "8px 12px"},
            ),
            dbc.Popover(
                [
                    dcc.RadioItems(
                        id=f"radio-icon-{id_suffix}",
                        options=[],
                        value=placeholder_icon,
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(3, 1fr)",
                            "gap": "5px",
                            "maxHeight": "300px",
                            "overflowY": "auto",
                            "padding": "10px",
                        },
                        labelStyle={
                            "display": "inline-block",
                            "cursor": "pointer",
                            "padding": "5px",
                            "fontSize": "1.2rem",
                            "border": "1px solid #eee",
                            "borderRadius": "4px",
                            "textAlign": "center",
                            "flex": "1",
                        },
                        inputStyle={"display": "none"},
                    )
                ],
                id=f"popover-icon-{id_suffix}",
                target=f"btn-icon-{id_suffix}",
                trigger="legacy",
                is_open=False,
            ),
        ],
        className="d-flex gap-2 align-items-center",
    )


def render_category_manager(
    receitas: List[Dict[str, Any]], despesas: List[Dict[str, Any]]
) -> dbc.Card:
    """
    Renderiza a interface de gestão de categorias.

    Exibe duas colunas lado a lado: uma para categorias de receita (verde)
    e outra para categorias de despesa (vermelha). Cada coluna contém um
    seletor de ícones, um campo de entrada para adicionar novas categorias
    e uma lista de categorias existentes com botões de exclusão.

    Args:
        receitas: Lista de dicionários com categorias de receita.
                  Cada item deve ter 'id', 'nome', 'icone' (opcional).
        despesas: Lista de dicionários com categorias de despesa.
                  Cada item deve ter 'id', 'nome', 'icone' (opcional).

    Returns:
        dbc.Card contendo o layout de gerenciamento de categorias com
        seletor de ícones integrado.

    Example:
        >>> receitas = [
        ...     {'id': 1, 'nome': 'Salário', 'icone': '💼'},
        ...     {'id': 2, 'nome': 'Freelance', 'icone': '💻'},
        ... ]
        >>> despesas = [
        ...     {'id': 3, 'nome': 'Aluguel', 'icone': '🏠'},
        ... ]
        >>> card = render_category_manager(receitas, despesas)
    """
    logger.debug("🎯 Renderizando gerenciador de categorias")

    # Extrair ícones já utilizados
    icones_receita_usados = {cat.get("icone") for cat in receitas if cat.get("icone")}
    icones_despesa_usados = {cat.get("icone") for cat in despesas if cat.get("icone")}

    # Remover ícones usados da lista de opções
    icones_receita_disponiveis = [
        e for e in EMOJI_OPTIONS if e not in icones_receita_usados
    ]
    icones_despesa_disponiveis = [
        e for e in EMOJI_OPTIONS if e not in icones_despesa_usados
    ]

    return dbc.Card(
        [
            dbc.CardBody(
                dbc.Row(
                    [
                        # ===== COLUNA 1: RECEITAS (VERDE) =====
                        dbc.Col(
                            [
                                html.H4(
                                    "💰 Categorias de Receita",
                                    className="text-success mb-4",
                                ),
                                dbc.InputGroup(
                                    [
                                        render_icon_selector("receita", "💰"),
                                        dbc.Input(
                                            id="input-cat-receita",
                                            placeholder="Nome da Categoria...",
                                            type="text",
                                        ),
                                        dbc.Input(
                                            id="input-cat-meta-receita",
                                            placeholder="Meta R$",
                                            type="number",
                                            step=0.01,
                                            min=0,
                                            style={"maxWidth": "100px"},
                                        ),
                                        dbc.Button(
                                            "Adicionar",
                                            id="btn-add-cat-receita",
                                            color="success",
                                            outline=True,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                (
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Span(
                                                                    cat.get(
                                                                        "icone", ""
                                                                    ),
                                                                    className="me-2",
                                                                ),
                                                                html.Span(
                                                                    cat.get(
                                                                        "nome",
                                                                        "Sem nome",
                                                                    )
                                                                ),
                                                                html.Span(
                                                                    f" (Meta: R$ {cat.get('teto_mensal', 0):.2f})",
                                                                    className="text-muted small ms-2",
                                                                ),
                                                            ],
                                                            className="d-flex align-items-center",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                dbc.Button(
                                                                    "✏️",
                                                                    id={
                                                                        "type": "btn-edit-cat",
                                                                        "index": cat.get(
                                                                            "id"
                                                                        ),
                                                                    },
                                                                    color="info",
                                                                    size="sm",
                                                                    outline=True,
                                                                    className="me-1",
                                                                ),
                                                                dbc.Button(
                                                                    "X",
                                                                    id={
                                                                        "type": (
                                                                            "btn-delete-"
                                                                            "category"
                                                                        ),
                                                                        "index": cat.get(
                                                                            "id"
                                                                        ),
                                                                    },
                                                                    color="danger",
                                                                    size="sm",
                                                                    outline=True,
                                                                ),
                                                            ],
                                                            width="auto",
                                                        ),
                                                    ],
                                                    className="align-items-center",
                                                ),
                                                className="d-flex "
                                                "justify-content-between "
                                                "align-items-center py-2",
                                            )
                                            for cat in receitas
                                        ],
                                        flush=True,
                                        className="mt-3",
                                    )
                                    if receitas
                                    else dbc.Alert(
                                        "Nenhuma categoria de receita",
                                        color="info",
                                        className="mt-3",
                                    )
                                ),
                            ],
                            md=6,
                            className="mb-4 mb-md-0",
                        ),
                        # ===== COLUNA 2: DESPESAS (VERMELHO) =====
                        dbc.Col(
                            [
                                html.H4(
                                    "💸 Categorias de Despesa",
                                    className="text-danger mb-4",
                                ),
                                dbc.InputGroup(
                                    [
                                        render_icon_selector("despesa", "💸"),
                                        dbc.Input(
                                            id="input-cat-despesa",
                                            placeholder="Nome da Categoria...",
                                            type="text",
                                        ),
                                        dbc.Input(
                                            id="input-cat-meta-despesa",
                                            placeholder="Meta R$",
                                            type="number",
                                            step=0.01,
                                            min=0,
                                            style={"maxWidth": "100px"},
                                        ),
                                        dbc.Button(
                                            "Adicionar",
                                            id="btn-add-cat-despesa",
                                            color="danger",
                                            outline=True,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                (
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem(
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.Span(
                                                                    cat.get(
                                                                        "icone", ""
                                                                    ),
                                                                    className="me-2",
                                                                ),
                                                                html.Span(
                                                                    cat.get(
                                                                        "nome",
                                                                        "Sem nome",
                                                                    )
                                                                ),
                                                                html.Span(
                                                                    f" (Meta: R$ {cat.get('teto_mensal', 0):.2f})",
                                                                    className="text-muted small ms-2",
                                                                ),
                                                            ],
                                                            className="d-flex align-items-center",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                dbc.Button(
                                                                    "✏️",
                                                                    id={
                                                                        "type": "btn-edit-cat",
                                                                        "index": cat.get(
                                                                            "id"
                                                                        ),
                                                                    },
                                                                    color="info",
                                                                    size="sm",
                                                                    outline=True,
                                                                    className="me-1",
                                                                ),
                                                                dbc.Button(
                                                                    "X",
                                                                    id={
                                                                        "type": (
                                                                            "btn-delete-"
                                                                            "category"
                                                                        ),
                                                                        "index": cat.get(
                                                                            "id"
                                                                        ),
                                                                    },
                                                                    color="danger",
                                                                    size="sm",
                                                                    outline=True,
                                                                ),
                                                            ],
                                                            width="auto",
                                                        ),
                                                    ],
                                                    className="align-items-center",
                                                ),
                                                className="d-flex "
                                                "justify-content-between "
                                                "align-items-center py-2",
                                            )
                                            for cat in despesas
                                        ],
                                        flush=True,
                                        className="mt-3",
                                    )
                                    if despesas
                                    else dbc.Alert(
                                        "Nenhuma categoria de despesa",
                                        color="info",
                                        className="mt-3",
                                    )
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="g-4",
                )
            ),
            # ===== MODAL DE EDIÇÃO DE CATEGORIA =====
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Editar Categoria"),
                        close_button=True,
                    ),
                    dbc.ModalBody(
                        dbc.InputGroup(
                            [
                                render_icon_selector("edit", "💰"),
                                dbc.Input(
                                    id="input-edit-cat-nome",
                                    placeholder="Nome da Categoria...",
                                    type="text",
                                ),
                                dbc.Input(
                                    id="input-edit-cat-meta",
                                    placeholder="Meta R$",
                                    type="number",
                                    step=0.01,
                                    min=0,
                                ),
                            ],
                            className="d-flex gap-2",
                        )
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Salvar",
                                id="btn-save-edit-cat",
                                color="success",
                                className="ms-auto",
                            ),
                        ]
                    ),
                ],
                id="modal-edit-category",
                is_open=False,
                centered=True,
            ),
            # Store para guardar ID da categoria sendo editada
            dcc.Store(id="store-edit-cat-id"),
        ],
        className="shadow-sm",
    )
