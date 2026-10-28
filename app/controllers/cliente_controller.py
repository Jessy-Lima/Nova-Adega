from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cliente import Cliente
from app.auth import get_usuario_logado


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
    pagina: int = 1,
    por_pagina: int = 10,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Lista os clientes com busca e paginação."""

    # Garante que a página seja válida
    if pagina < 1:
        pagina = 1

    # Limita a quantidade de registros por página
    por_pagina = max(1, min(por_pagina, 100))

    # Consulta os clientes
    query = db.query(Cliente)

    # Filtra por nome ou telefone
    if busca.strip():
        termo = f"%{busca.strip()}%"

        query = query.filter(
            Cliente.nome.ilike(termo) |
            Cliente.telefone.ilike(termo)
        )

    # Total de clientes encontrados
    total_clientes = query.count()

    # Calcula o total de páginas
    total_paginas = max(
        1,
        (total_clientes + por_pagina - 1) // por_pagina
    )

    # Evita acessar uma página inexistente
    if pagina > total_paginas:
        pagina = total_paginas

    # Busca os clientes da página atual
    clientes = (
        query
        .order_by(Cliente.nome)
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "clientes/index.html",
        {
            "request": request,
            "usuario": usuario,
            "clientes": clientes,
            "busca": busca,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_clientes": total_clientes,
            "total_paginas": total_paginas,
        }
    )


# ============================================================
# NOVO CLIENTE — FORMULÁRIO
# ============================================================

@router.get("/novo")
def form_novo(
    request: Request,
    usuario=Depends(get_usuario_logado)
):
    """Exibe o formulário de cadastro de cliente."""

    return templates.TemplateResponse(
        request,
        "clientes/form.html",
        {
            "request": request,
            "usuario": usuario,
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
    usuario=Depends(get_usuario_logado)
):
    """Cadastra um novo cliente."""

    nome = nome.strip()
    telefone = telefone.strip()

    # Valida o nome
    if not nome:
        return templates.TemplateResponse(
            request,
            "clientes/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": None,
                "erro": "O nome do cliente é obrigatório.",
                "valores": {
                    "nome": nome,
                    "telefone": telefone,
                    "is_associado": is_associado
                }
            },
            status_code=400
        )

    # Cria o cliente
    cliente = Cliente(
        nome=nome,
        telefone=telefone or None,
        is_associado=is_associado,
        ativo=True
    )

    db.add(cliente)
    db.commit()
    db.refresh(cliente)

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
    usuario=Depends(get_usuario_logado)
):
    """Exibe o formulário de edição do cliente."""

    editando = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/clientes/",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "clientes/form.html",
        {
            "request": request,
            "usuario": usuario,
            "editando": editando
        }
    )


# ============================================================
# EDITAR CLIENTE
# ============================================================

@router.post("/{cliente_id}/editar")
def editar(
    cliente_id: int,
    request: Request,
    nome: str = Form(...),
    telefone: str = Form(""),
    is_associado: bool = Form(False),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """Atualiza os dados de um cliente."""

    editando = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if not editando:
        return RedirectResponse(
            url="/clientes/",
            status_code=302
        )

    nome = nome.strip()
    telefone = telefone.strip()

    # Valida o nome
    if not nome:
        return templates.TemplateResponse(
            request,
            "clientes/form.html",
            {
                "request": request,
                "usuario": usuario,
                "editando": editando,
                "erro": "O nome do cliente é obrigatório."
            },
            status_code=400
        )

    # Atualiza os dados
    editando.nome = nome
    editando.telefone = telefone or None
    editando.is_associado = is_associado

    db.commit()
    db.refresh(editando)

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
    usuario=Depends(get_usuario_logado)
):
    """Ativa ou desativa um cliente."""

    cliente = (
        db.query(Cliente)
        .filter(Cliente.id == cliente_id)
        .first()
    )

    if cliente:
        cliente.ativo = not cliente.ativo
        db.commit()

    return RedirectResponse(
        url="/clientes/",
        status_code=302
    )