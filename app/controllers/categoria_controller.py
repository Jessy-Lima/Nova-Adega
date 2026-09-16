# controllers/categoria_controller.py — CRUD de categorias

# Categorias são gerenciadas apenas por admins.
# Operadores apenas visualizam (via select no form de produto).
# ============================================================

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.categoria import Categoria
from app.auth import get_admin

router = APIRouter(prefix="/categorias", tags=["Categorias"])

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# LISTAGEM
# ============================================================

@router.get("/")
def listar_categorias(
    request: Request,
    pagina: int = 1,
    por_pagina: int = 3,
    db: Session = Depends(get_db),
    admin = Depends(get_admin)
):
    """
    Lista todas as categorias ordenadas por nome.
    Inclui a contagem de produtos de cada categoria
    para dar contexto ao admin antes de desativar.
    """

    # Evita página inválida
    if pagina < 1:
        pagina = 1

    # Total de categorias
    total_categorias = db.query(Categoria).count()

    # Total de páginas
    total_paginas = max(
        1,
        (total_categorias + por_pagina - 1) // por_pagina
    )

    # Evita ultrapassar a última página
    if pagina > total_paginas:
        pagina = total_paginas

    # Categorias da página atual
    categorias = (
        db.query(Categoria)
        .order_by(Categoria.nome)
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "categorias/index.html",
        {
            "request":    request,
            "usuario":    admin,
            "categorias": categorias,
            "pagina":     pagina,
            "por_pagina": por_pagina,
            "total_categorias": total_categorias,
            "total_paginas": total_paginas,
        }
    )


# ============================================================
# CADASTRO
# ============================================================

@router.get("/nova")
def form_nova_categoria(
    request: Request,
    admin = Depends(get_admin)
):
    """Exibe o formulário de cadastro de categoria."""
    return templates.TemplateResponse(
        request,
        "categorias/form.html",
        {
            "request":  request,
            "usuario":  admin,
            "editando": None,
        }
    )


@router.post("/nova")
def criar_categoria(
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    admin = Depends(get_admin)
):
    """Cria uma nova categoria verificando duplicidade de nome."""

    existente = db.query(Categoria).filter(
        Categoria.nome.ilike(nome)
    ).first()

    if existente:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request":  request,
                "usuario":  admin,
                "editando": None,
                "erro":     "Já existe uma categoria com este nome.",
                "valores":  {"nome": nome},
            },
            status_code=400
        )

    db.add(Categoria(nome=nome.strip()))
    db.commit()

    return RedirectResponse(url="/categorias?criado=ok", status_code=302)


# ============================================================
# EDIÇÃO
# ============================================================

@router.get("/{categoria_id}/editar")
def form_editar_categoria(
    categoria_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_admin)
):
    """Exibe o formulário preenchido com os dados da categoria."""
    editando = db.query(Categoria).filter(
        Categoria.id == categoria_id
    ).first()

    if not editando:
        return RedirectResponse(url="/categorias", status_code=302)

    return templates.TemplateResponse(
        request,
        "categorias/form.html",
        {
            "request":  request,
            "usuario":  admin,
            "editando": editando,
        }
    )


@router.post("/{categoria_id}/editar")
def editar_categoria(
    categoria_id: int,
    request: Request,
    nome: str = Form(...),
    db: Session = Depends(get_db),
    admin = Depends(get_admin)
):
    """Atualiza o nome da categoria."""
    editando = db.query(Categoria).filter(
        Categoria.id == categoria_id
    ).first()

    if not editando:
        return RedirectResponse(url="/categorias", status_code=302)

    # Verifica conflito com outra categoria (ignora a própria)
    conflito = db.query(Categoria).filter(
        Categoria.nome.ilike(nome),
        Categoria.id != categoria_id
    ).first()

    if conflito:
        return templates.TemplateResponse(
            request,
            "categorias/form.html",
            {
                "request":  request,
                "usuario":  admin,
                "editando": editando,
                "erro":     "Já existe outra categoria com este nome.",
            },
            status_code=400
        )

    editando.nome = nome.strip()
    db.commit()

    return RedirectResponse(url="/categorias?editado=ok", status_code=302)


# ============================================================
# TOGGLE ATIVO
# ============================================================

@router.post("/{categoria_id}/toggle-ativo")
def toggle_ativo(
    categoria_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_admin)
):
    """
    Ativa ou desativa uma categoria.

    Não deletamos pois a categoria pode estar vinculada
    a produtos existentes. Desativar apenas esconde do
    select do formulário de produto — os vínculos permanecem.
    """
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id
    ).first()

    if not categoria:
        return RedirectResponse(url="/categorias", status_code=302)

    # Bloqueia desativação se houver produtos ativos vinculados
    if categoria.ativo:
        produtos_ativos = [p for p in categoria.produtos if p.ativo]

        if produtos_ativos:
            return RedirectResponse(
                url=f"/categorias?erro=produtos_vinculados&categoria={categoria.nome}",
                status_code=302
            )

    categoria.ativo = not categoria.ativo
    db.commit()

    return RedirectResponse(url="/categorias", status_code=302)