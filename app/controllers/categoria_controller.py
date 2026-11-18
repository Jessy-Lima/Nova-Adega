# controllers/categoria_controller.py — CRUD de categorias
# Administradores e operadores podem gerenciar categorias.

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categoria import Categoria
from app.auth import get_usuario_logado


router = APIRouter(
    prefix="/categorias",
    tags=["Categorias"]
)

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# LISTAGEM DE CATEGORIAS
# ============================================================

@router.get("/")
def listar_categorias(
    request: Request,
    busca: str = "",
    ordenar: str = "nome_az",
    pagina: int = 1,
    por_pagina: int = 14,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Lista, busca e ordena as categorias."""

    if pagina < 1:
        pagina = 1

    por_pagina = max(1, min(por_pagina, 100))

    # --------------------------------------------------------
    # CONSULTA
    # --------------------------------------------------------

    query = db.query(Categoria)

    if busca.strip():
        termo = f"%{busca.strip()}%"

        query = query.filter(
            Categoria.nome.ilike(termo)
        )

    total_categorias = query.count()

    # --------------------------------------------------------
    # BUSCA DAS CATEGORIAS
    # --------------------------------------------------------

    todas_categorias = query.all()

    # --------------------------------------------------------
    # ORDENAÇÃO
    # --------------------------------------------------------

    opcoes_ordenacao = [
        "nome_az",
        "nome_za",
        "mais_produtos",
        "menos_produtos"
    ]

    if ordenar not in opcoes_ordenacao:
        ordenar = "nome_az"

    if ordenar == "nome_az":

        todas_categorias.sort(
            key=lambda c: (c.nome or "").casefold()
        )

    elif ordenar == "nome_za":

        todas_categorias.sort(
            key=lambda c: (c.nome or "").casefold(),
            reverse=True
        )

    elif ordenar == "mais_produtos":

        todas_categorias.sort(
            key=lambda c: (
                -sum(1 for p in c.produtos if p.ativo),
                (c.nome or "").casefold()
            )
        )

    elif ordenar == "menos_produtos":

        todas_categorias.sort(
            key=lambda c: (
                sum(1 for p in c.produtos if p.ativo),
                (c.nome or "").casefold()
            )
        )

    # --------------------------------------------------------
    # PAGINAÇÃO
    # --------------------------------------------------------

    total_paginas = max(
        1,
        (total_categorias + por_pagina - 1) // por_pagina
    )

    if pagina > total_paginas:
        pagina = total_paginas

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    categorias = todas_categorias[inicio:fim]

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request,
        "categorias/index.html",
        {
            "request": request,
            "usuario": usuario,
            "categorias": categorias,
            "busca": busca,
            "ordenar": ordenar,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_categorias": total_categorias,
            "total_paginas": total_paginas,
        }
    )


# ============================================================
# CADASTRO — FORMULÁRIO
# ============================================================

@router.get("/nova")
def form_nova_categoria(
    request: Request,
    usuario=Depends(get_usuario_logado)
):
    """Exibe o formulário para cadastrar uma categoria."""

    return templates.TemplateResponse(
        request,
        "categorias/form.html",
        {
            "request": request,
            "usuario": usuario,
            "editando": None,
        }
    )


# ============================================================
# CADASTRO — CRIAR CATEGORIA
# ============================================================

@router.post("/nova")
def criar_categoria(
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Cria uma categoria verificando se o nome já existe."""

    nome = nome.strip()

    if not nome:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": None,
                "erro": "O nome da categoria é obrigatório.",
                "valores": {"nome": nome},
            },
            status_code=400
        )

    existente = (
        db.query(Categoria)
        .filter(Categoria.nome.ilike(nome))
        .first()
    )

    if existente:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": None,
                "erro": "Já existe uma categoria com este nome.",
                "valores": {"nome": nome},
            },
            status_code=400
        )

    nova_categoria = Categoria(nome=nome)

    db.add(nova_categoria)
    db.commit()

    return RedirectResponse(
        url="/categorias?criado=ok",
        status_code=302
    )


# ============================================================
# EDIÇÃO — FORMULÁRIO
# ============================================================

@router.get("/{categoria_id}/editar")
def form_editar_categoria(
    categoria_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Exibe o formulário preenchido com os dados da categoria."""

    editando = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/categorias/",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "categorias/form.html",
        {
            "request": request,
            "usuario": usuario,
            "editando": editando,
        }
    )


# ============================================================
# EDIÇÃO — SALVAR ALTERAÇÕES
# ============================================================

@router.post("/{categoria_id}/editar")
def editar_categoria(
    categoria_id: int,
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Atualiza o nome de uma categoria."""

    editando = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/categorias/",
            status_code=302
        )

    nome = nome.strip()

    if not nome:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": editando,
                "erro": "O nome da categoria é obrigatório.",
            },
            status_code=400
        )

    conflito = (
        db.query(Categoria)
        .filter(
            Categoria.nome.ilike(nome),
            Categoria.id != categoria_id
        )
        .first()
    )

    if conflito:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": editando,
                "erro": "Já existe outra categoria com este nome.",
            },
            status_code=400
        )

    editando.nome = nome

    db.commit()

    return RedirectResponse(
        url="/categorias?editado=ok",
        status_code=302
    )


# ============================================================
# ATIVAR / DESATIVAR CATEGORIA
# ============================================================

@router.post("/{categoria_id}/toggle-ativo")
def toggle_ativo(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """
    Ativa ou desativa uma categoria.

    Impede desativar uma categoria que tenha produtos ativos
    vinculados a ela.
    """

    categoria = (
        db.query(Categoria)
        .filter(Categoria.id == categoria_id)
        .first()
    )

    if not categoria:
        return RedirectResponse(
            url="/categorias/",
            status_code=302
        )

    if categoria.ativo:

        produtos_ativos = [
            produto
            for produto in categoria.produtos
            if produto.ativo
        ]

        if produtos_ativos:
            return RedirectResponse(
                url="/categorias?erro=produtos_vinculados",
                status_code=302
            )

    categoria.ativo = not categoria.ativo

    db.commit()

    return RedirectResponse(
        url="/categorias/",
        status_code=302
    )