from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cliente import Cliente
from app.auth import get_admin


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# LISTAR CLIENTES
# ============================================================

@router.get("/")
def listar_clientes(
    request: Request,
    busca: str = "",
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    query = db.query(Cliente)

    if busca:
        query = query.filter(
            Cliente.nome.ilike(f"%{busca}%") |
            Cliente.telefone.ilike(f"%{busca}%")
        )

    clientes = (
        query
        .order_by(Cliente.nome)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "clientes/index.html",
        {
            "request": request,
            "usuario": admin,
            "clientes": clientes,
            "busca": busca,
        }
    )


# ============================================================
# NOVO CLIENTE — FORMULÁRIO
# ============================================================

@router.get("/novo")
def form_novo(
    request: Request,
    admin=Depends(get_admin)
):
    return templates.TemplateResponse(
        request,
        "clientes/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": None
        }
    )


# ============================================================
# CRIAR CLIENTE
# ============================================================

@router.post("/novo")
def criar(
    request: Request,
    nome: str = Form(...),
    telefone: str = Form(""),
    is_associado: bool = Form(False),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    cliente = Cliente(
        nome=nome.strip(),
        telefone=telefone.strip() or None,
        is_associado=is_associado,
    )

    db.add(cliente)
    db.commit()

    return RedirectResponse(
        url="/clientes?criado=ok",
        status_code=302
    )


# ============================================================
# FORMULÁRIO DE EDIÇÃO
# ============================================================

@router.get("/{cliente_id}/editar")
def form_editar(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    editando = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/clientes",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "clientes/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": editando
        }
    )


# ============================================================
# EDITAR CLIENTE
# ============================================================

@router.post("/{cliente_id}/editar")
def editar(
    cliente_id: int,
    nome: str = Form(...),
    telefone: str = Form(""),
    is_associado: bool = Form(False),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    editando = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/clientes",
            status_code=302
        )

    editando.nome = nome.strip()
    editando.telefone = telefone.strip() or None
    editando.is_associado = is_associado

    db.commit()

    return RedirectResponse(
        url="/clientes?editado=ok",
        status_code=302
    )


# ============================================================
# ATIVAR / DESATIVAR CLIENTE
# ============================================================

@router.post("/{cliente_id}/toggle-ativo")
def toggle_ativo(
    cliente_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if cliente:
        cliente.ativo = not cliente.ativo
        db.commit()

    return RedirectResponse(
        url="/clientes",
        status_code=302
    )