
# ============================================================
# CONTROLLER DE PRODUTOS — NOVA ADEGA
# ============================================================

import math
import os
import shutil

from fastapi import (
    APIRouter, Depends, Request, Form,
    UploadFile, File, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.auth import get_usuario_logado, get_admin


router = APIRouter(prefix="/produtos", tags=["Produtos"])

templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# ORDENAÇÃO
# ============================================================

def aplicar_ordenacao(query, ordenacao):

    opcoes = {
        "nome_asc": Produto.nome.asc(),
        "nome_desc": Produto.nome.desc(),
        "preco_asc": Produto.preco.asc(),
        "preco_desc": Produto.preco.desc(),
        "estoque_asc": Produto.estoque_atual.asc(),
        "estoque_desc": Produto.estoque_atual.desc(),
    }

    if ordenacao not in opcoes:
        ordenacao = "nome_asc"

    query = query.order_by(
        opcoes[ordenacao],
        Produto.id.asc()
    )

    return query, ordenacao


# ============================================================
# LISTAGEM DE PRODUTOS
# ============================================================

@router.get("/")
def listar_produtos(
    request: Request,
    busca: str = "",
    categoria_id: int = 0,
    ordenacao: str = "nome_asc",
    pagina: int = 1,
    por_pagina: int = 14,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    query = db.query(Produto).filter(
        Produto.ativo == True
    )

    # BUSCA POR NOME
    if busca:
        query = query.filter(
            Produto.nome.ilike(f"%{busca}%")
        )

    # FILTRO POR CATEGORIA
    if categoria_id:
        query = query.filter(
            Produto.categoria_id == categoria_id
        )

    # ORDENAÇÃO
    query, ordenacao = aplicar_ordenacao(
        query,
        ordenacao
    )

    # TOTAL DE PRODUTOS
    total_produtos = query.count()

    # PAGINAÇÃO
    pagina = max(pagina, 1)
    por_pagina = max(por_pagina, 1)

    total_paginas = (
        math.ceil(total_produtos / por_pagina)
        if total_produtos
        else 1
    )

    # Evita páginas inexistentes
    pagina = min(pagina, total_paginas)

    offset = (pagina - 1) * por_pagina

    produtos = (
        query
        .offset(offset)
        .limit(por_pagina)
        .all()
    )

    # CATEGORIAS ATIVAS
    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    return templates.TemplateResponse(
        request,
        "produtos/index.html",
        {
            "request": request,
            "usuario": usuario,
            "produtos": produtos,
            "categorias": categorias,

            "busca": busca,
            "categoria_id": categoria_id,
            "ordenacao": ordenacao,

            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_produtos": total_produtos,
            "total_paginas": total_paginas
        }
    )


# ============================================================
# CADASTRO
# ============================================================

@router.get("/novo")
def form_novo_produto(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    return templates.TemplateResponse(
        request,
        "produtos/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": None,
            "categorias": categorias
        }
    )


@router.post("/novo")
async def criar_produto(
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    # VERIFICA NOME DUPLICADO
    if db.query(Produto).filter(
        Produto.nome.ilike(nome)
    ).first():

        return templates.TemplateResponse(
            request,
            "produtos/form.html",
            {
                "request": request,
                "usuario": admin,
                "editando": None,
                "categorias": categorias,
                "erro": "Já existe um produto com este nome.",
                "valores": {
                    "nome": nome,
                    "preco": preco,
                    "estoque_atual": estoque_atual,
                    "categoria_id": categoria_id
                }
            },
            status_code=400
        )

    imagem_path = await _salvar_imagem(imagem)

    produto = Produto(
        nome=nome,
        preco=preco,
        estoque_atual=estoque_atual,
        categoria_id=categoria_id or None,
        imagem_path=imagem_path
    )

    db.add(produto)
    db.commit()

    return RedirectResponse(
        url="/produtos/?criado=ok",
        status_code=302
    )


# ============================================================
# PRODUTOS POR CATEGORIA
# ============================================================

@router.get("/categoria/{categoria_nome}")
def produtos_por_categoria(
    categoria_nome: str,
    request: Request,
    pagina: int = 1,
    por_pagina: int = 3,
    ordenacao: str = "nome_asc",
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    categoria = db.query(Categoria).filter(
        Categoria.nome.ilike(categoria_nome),
        Categoria.ativo == True
    ).first()

    if not categoria:
        return RedirectResponse(
            url="/produtos/",
            status_code=302
        )

    query = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.categoria_id == categoria.id
    )

    # APLICA A MESMA ORDENAÇÃO
    query, ordenacao = aplicar_ordenacao(
        query,
        ordenacao
    )

    total_produtos = query.count()

    pagina = max(pagina, 1)
    por_pagina = max(por_pagina, 1)

    total_paginas = (
        math.ceil(total_produtos / por_pagina)
        if total_produtos
        else 1
    )

    pagina = min(pagina, total_paginas)

    offset = (pagina - 1) * por_pagina

    produtos = (
        query
        .offset(offset)
        .limit(por_pagina)
        .all()
    )

    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    return templates.TemplateResponse(
        request,
        "produtos/index.html",
        {
            "request": request,
            "usuario": usuario,

            "produtos": produtos,
            "categorias": categorias,

            "busca": "",
            "categoria_id": categoria.id,
            "ordenacao": ordenacao,

            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_produtos": total_produtos,
            "total_paginas": total_paginas,

            "categoria_selecionada": categoria.nome
        }
    )


# ============================================================
# DETALHE DO PRODUTO
# ============================================================

@router.get("/{produto_id}")
def detalhe_produto(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    produto = db.query(Produto).filter(
        Produto.id == produto_id,
        Produto.ativo == True
    ).first()

    if not produto:
        return RedirectResponse(
            url="/produtos/",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "produtos/detalhe.html",
        {
            "request": request,
            "usuario": usuario,
            "produto": produto
        }
    )


# ============================================================
# EDIÇÃO
# ============================================================

@router.get("/{produto_id}/editar")
def form_editar_produto(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    editando = db.query(Produto).filter(
        Produto.id == produto_id
    ).first()

    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    if not editando:
        return RedirectResponse(
            url="/produtos/",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "produtos/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": editando,
            "categorias": categorias
        }
    )


@router.post("/{produto_id}/editar")
async def editar_produto(
    produto_id: int,
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    editando = db.query(Produto).filter(
        Produto.id == produto_id
    ).first()

    categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).all()

    if not editando:
        return RedirectResponse(
            url="/produtos/",
            status_code=302
        )

    # VERIFICA CONFLITO DE NOME
    conflito = db.query(Produto).filter(
        Produto.nome.ilike(nome),
        Produto.id != produto_id
    ).first()

    if conflito:
        return templates.TemplateResponse(
            request,
            "produtos/form.html",
            {
                "request": request,
                "usuario": admin,
                "editando": editando,
                "categorias": categorias,
                "erro": "Já existe outro produto com este nome."
            },
            status_code=400
        )

    # PROCESSA NOVA IMAGEM
    nova_imagem_path = await _salvar_imagem(imagem)

    if nova_imagem_path:
        _remover_imagem(editando.imagem_path)
        editando.imagem_path = nova_imagem_path

    editando.nome = nome
    editando.preco = preco
    editando.estoque_atual = estoque_atual
    editando.categoria_id = categoria_id or None

    db.commit()

    return RedirectResponse(
        url=f"/produtos/{produto_id}?editado=ok",
        status_code=302
    )


# ============================================================
# DESATIVAR PRODUTO
# ============================================================

@router.post("/{produto_id}/desativar")
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):

    produto = db.query(Produto).filter(
        Produto.id == produto_id
    ).first()

    if produto:
        produto.ativo = False
        db.commit()

    return RedirectResponse(
        url="/produtos/?desativado=ok",
        status_code=302
    )


# ============================================================
# FUNÇÕES AUXILIARES DE IMAGEM
# ============================================================

async def _salvar_imagem(
    imagem: UploadFile | None
) -> str | None:

    if not imagem or not imagem.filename:
        return None

    extensoes_permitidas = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    _, ext = os.path.splitext(
        imagem.filename.lower()
    )

    if ext not in extensoes_permitidas:
        return None

    nome_arquivo = imagem.filename

    caminho_completo = os.path.join(
        UPLOAD_DIR,
        nome_arquivo
    )

    with open(caminho_completo, "wb") as buffer:
        shutil.copyfileobj(
            imagem.file,
            buffer
        )

    return f"uploads/{nome_arquivo}"


def _remover_imagem(
    imagem_path: str | None
) -> None:

    if not imagem_path:
        return

    caminho = os.path.join(
        "app/static",
        imagem_path
    )

    if os.path.exists(caminho):
        os.remove(caminho)
