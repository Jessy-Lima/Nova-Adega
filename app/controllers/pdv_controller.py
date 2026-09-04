# ============================================================
# controllers/pdv_controller.py
# PONTO DE VENDA - NOVA ADEGA
# ============================================================

import json

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.venda import Venda, ItemVenda
from app.models.produto import Produto
from app.models.cliente import Cliente
from app.auth import get_usuario_logado


router = APIRouter(
    prefix="/pdv",
    tags=["PDV"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# TELA DO PDV
# ============================================================

@router.get("/")
def tela_pdv(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    produtos = (
        db.query(Produto)
        .filter(
            Produto.ativo == True,
            Produto.estoque_atual > 0
        )
        .order_by(Produto.nome)
        .all()
    )

    clientes = (
        db.query(Cliente)
        .filter(
            Cliente.ativo == True
        )
        .order_by(Cliente.nome)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "pdv/index.html",
        {
            "request": request,
            "usuario": usuario,
            "produtos": produtos,
            "clientes": clientes,
        }
    )


# ============================================================
# FINALIZAR VENDA
# ============================================================

@router.post("/finalizar")
def finalizar_venda(
    request: Request,
    carrinho_json: str = Form(...),
    cliente_id: int = Form(0),
    observacao: str = Form(""),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    # --------------------------------------------------------
    # LER CARRINHO
    # --------------------------------------------------------

    try:
        itens = json.loads(carrinho_json)

    except (json.JSONDecodeError, ValueError):

        return RedirectResponse(
            url="/pdv/?erro=json",
            status_code=303
        )

    # --------------------------------------------------------
    # CARRINHO VAZIO
    # --------------------------------------------------------

    if not itens:

        return RedirectResponse(
            url="/pdv/?erro=vazio",
            status_code=303
        )

    # --------------------------------------------------------
    # CLIENTE
    # --------------------------------------------------------

    cliente = None

    if cliente_id:

        cliente = (
            db.query(Cliente)
            .filter(
                Cliente.id == cliente_id,
                Cliente.ativo == True
            )
            .first()
        )

        if not cliente:
            cliente_id = 0

    # --------------------------------------------------------
    # VALIDAR PRODUTOS
    # --------------------------------------------------------

    total_bruto = 0.0

    itens_validados = []

    for item in itens:

        produto_id = item.get("produto_id")

        try:
            quantidade = int(item.get("quantidade"))

        except (ValueError, TypeError):

            return RedirectResponse(
                url="/pdv/?erro=quantidade",
                status_code=303
            )

        if quantidade <= 0:

            return RedirectResponse(
                url="/pdv/?erro=quantidade",
                status_code=303
            )

        produto = (
            db.query(Produto)
            .filter(
                Produto.id == produto_id,
                Produto.ativo == True
            )
            .first()
        )

        # ----------------------------------------------------
        # PRODUTO NÃO ENCONTRADO
        # ----------------------------------------------------

        if not produto:

            return RedirectResponse(
                url=f"/pdv/?erro=produto_inexistente&id={produto_id}",
                status_code=303
            )

        # ----------------------------------------------------
        # ESTOQUE
        # ----------------------------------------------------

        if produto.estoque_atual < quantidade:

            return RedirectResponse(
                url=(
                    f"/pdv/?erro=estoque"
                    f"&produto={produto.nome}"
                ),
                status_code=303
            )

        # ----------------------------------------------------
        # SUBTOTAL
        # ----------------------------------------------------

        subtotal = produto.preco * quantidade

        total_bruto += subtotal

        itens_validados.append(
            {
                "produto": produto,
                "quantidade": quantidade,
                "preco": produto.preco,
                "produto_nome": produto.nome,
            }
        )

    # --------------------------------------------------------
    # SEM DESCONTO
    # --------------------------------------------------------

    total_liquido = total_bruto

    # --------------------------------------------------------
    # CRIAR VENDA
    # --------------------------------------------------------

    venda = Venda(
        cliente_id=cliente_id or None,
        usuario_id=usuario.get("id"),
        total_bruto=round(total_bruto, 2),
        total_liquido=round(total_liquido, 2),
        observacao=observacao.strip() or None
    )

    db.add(venda)

    # Gera o ID da venda
    db.flush()

    # --------------------------------------------------------
    # CRIAR ITENS E BAIXAR ESTOQUE
    # --------------------------------------------------------

    for item in itens_validados:

        item_venda = ItemVenda(
            venda_id=venda.id,
            produto_id=item["produto"].id,
            produto_nome=item["produto_nome"],
            quantidade=item["quantidade"],
            preco_unitario=item["preco"]
        )

        db.add(item_venda)

        item["produto"].estoque_atual -= item["quantidade"]

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    try:

        db.commit()

    except Exception as erro:

        db.rollback()

        print("ERRO AO FINALIZAR VENDA:")
        print(erro)

        return RedirectResponse(
            url="/pdv/?erro=salvar",
            status_code=303
        )

    # --------------------------------------------------------
    # COMPROVANTE
    # --------------------------------------------------------

    return RedirectResponse(
        url=f"/pdv/venda/{venda.id}?sucesso=ok",
        status_code=303
    )


# ============================================================
# COMPROVANTE
# ============================================================

@router.get("/venda/{venda_id}")
def detalhe_venda(
    venda_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    venda = (
        db.query(Venda)
        .filter(
            Venda.id == venda_id
        )
        .first()
    )

    if not venda:

        return RedirectResponse(
            url="/pdv/",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "pdv/comprovante.html",
        {
            "request": request,
            "usuario": usuario,
            "venda": venda
        }
    )


# ============================================================
# HISTÓRICO
# ============================================================

@router.get("/historico")
def historico_vendas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    vendas = (
        db.query(Venda)
        .order_by(
            Venda.criado_em.desc()
        )
        .limit(100)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "pdv/historico.html",
        {
            "request": request,
            "usuario": usuario,
            "vendas": vendas
        }
    )