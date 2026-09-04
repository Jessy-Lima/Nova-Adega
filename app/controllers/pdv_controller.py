# ============================================================
# controllers/pdv_controller.py — Ponto de Venda
#
# O PDV funciona assim:
# 1. GET /pdv        → tela com produtos + campo de cliente
# 2. O carrinho vive inteiro no JavaScript
# 3. POST /pdv/finalizar → recebe um JSON com os itens
#                          cria Venda + ItemVenda + baixa estoque
# ============================================================

import json

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
    """
    Carrega a tela do PDV com todos os produtos ativos
    e a lista de clientes para seleção.
    """

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
    """
    Recebe o carrinho como JSON, valida os produtos,
    calcula os totais, registra a venda e baixa o estoque.

    Formato esperado:

    [
        {
            "produto_id": 1,
            "nome": "Caneta",
            "preco": 2.50,
            "quantidade": 3
        },
        {
            "produto_id": 2,
            "nome": "Caderno",
            "preco": 15.00,
            "quantidade": 1
        }
    ]
    """

    # ========================================================
    # Lê o JSON do carrinho
    # ========================================================

    try:
        itens = json.loads(carrinho_json)

    except (json.JSONDecodeError, ValueError):

        return RedirectResponse(
            url="/pdv?erro=json",
            status_code=302
        )

    # ========================================================
    # Verifica se o carrinho está vazio
    # ========================================================

    if not itens:

        return RedirectResponse(
            url="/pdv?erro=vazio",
            status_code=302
        )

    # ========================================================
    # Busca o cliente
    # ========================================================

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

        # Se o ID foi enviado, mas o cliente não existe,
        # a venda fica sem cliente.

        if not cliente:
            cliente_id = 0

    # ========================================================
    # Valida estoque e calcula subtotal
    # ========================================================

    total_bruto = 0.0

    itens_validados = []

    for item in itens:

        produto = (
            db.query(Produto)
            .filter(
                Produto.id == item["produto_id"],
                Produto.ativo == True
            )
            .first()
        )

        # ----------------------------------------------------
        # Produto inexistente
        # ----------------------------------------------------

        if not produto:

            return RedirectResponse(
                url=(
                    f"/pdv?erro=produto_inexistente"
                    f"&id={item['produto_id']}"
                ),
                status_code=302
            )

        # ----------------------------------------------------
        # Quantidade
        # ----------------------------------------------------

        try:
            qtd = int(item["quantidade"])

        except (ValueError, TypeError):

            return RedirectResponse(
                url="/pdv?erro=quantidade",
                status_code=302
            )

        if qtd <= 0:

            return RedirectResponse(
                url="/pdv?erro=quantidade",
                status_code=302
            )

        # ----------------------------------------------------
        # Estoque
        # ----------------------------------------------------

        if produto.estoque_atual < qtd:

            return RedirectResponse(
                url=f"/pdv?erro=estoque&produto={produto.nome}",
                status_code=302
            )

        # ----------------------------------------------------
        # Subtotal do produto
        # ----------------------------------------------------

        subtotal = produto.preco * qtd

        total_bruto += subtotal

        itens_validados.append(
            {
                "produto": produto,
                "quantidade": qtd,
                "preco": produto.preco,
                "produto_nome": produto.nome,
            }
        )

    # ========================================================
    # Total da venda
    #
    # Não existe mais desconto de associado.
    # ========================================================


    total_liquido = total_bruto

    # ========================================================
    # Cria a venda
    # ========================================================

    venda = Venda(
        cliente_id=cliente_id or None,

        usuario_id=usuario.get("id"),

        total_bruto=round(total_bruto, 2),

        total_liquido=round(total_liquido, 2),

        observacao=observacao.strip() or None,
    )

    db.add(venda)

    # Gera o ID da venda sem fazer commit ainda
    db.flush()

    # ========================================================
    # Cria os itens da venda e baixa o estoque
    # ========================================================

    for item in itens_validados:

        db.add(
            ItemVenda(
                venda_id=venda.id,

                produto_id=item["produto"].id,

                produto_nome=item["produto_nome"],

                quantidade=item["quantidade"],

                preco_unitario=item["preco"],
            )
        )

        # Baixa o estoque

        item["produto"].estoque_atual -= item["quantidade"]

    # ========================================================
    # Salva tudo
    # ========================================================

    db.commit()

    # ========================================================
    # Vai para o comprovante
    # ========================================================

    return RedirectResponse(
        url=f"/pdv/venda/{venda.id}?sucesso=ok",
        status_code=302
    )


# ============================================================
# COMPROVANTE DA VENDA
# ============================================================

@router.get("/venda/{venda_id}")
def detalhe_venda(
    venda_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """
    Exibe o comprovante da venda
    imediatamente após finalizar.
    """

    venda = (
        db.query(Venda)
        .filter(
            Venda.id == venda_id
        )
        .first()
    )

    if not venda:

        return RedirectResponse(
            url="/pdv",
            status_code=302
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
# HISTÓRICO DE VENDAS
# ============================================================

@router.get("/historico")
def historico_vendas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    """
    Exibe o histórico das últimas 100 vendas.
    """

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