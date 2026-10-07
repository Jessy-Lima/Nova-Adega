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

DESCONTO_ASSOCIADO = 10.0


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
            "desconto_associado": DESCONTO_ASSOCIADO,
        }
    )


@router.post("/finalizar")
def finalizar_venda(
    request: Request,
    carrinho_json: str = Form(...),
    cliente_id: int = Form(0),
    observacao: str = Form(""),

    # Desconto enviado pelo formulário
    desconto_manual: float = Form(0.0),
    tipo_desconto: str = Form(""),

    # Primeiro pagamento
    forma_pagamento_1: str = Form(""),
    valor_pagamento_1: float = Form(0.0),

    # Segundo pagamento
    forma_pagamento_2: str = Form(""),
    valor_pagamento_2: float = Form(0.0),

    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    # ============================================================
    # LER CARRINHO
    # ============================================================

    try:
        itens = json.loads(carrinho_json)

    except (json.JSONDecodeError, ValueError):
        return RedirectResponse(
            url="/pdv/?erro=json",
            status_code=303
        )

    if not itens:
        return RedirectResponse(
            url="/pdv/?erro=vazio",
            status_code=303
        )

    # ============================================================
    # BUSCAR CLIENTE
    # ============================================================

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

    # ============================================================
    # VALIDAR PRODUTOS E CALCULAR SUBTOTAL
    # ============================================================

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

        if not produto:
            return RedirectResponse(
                url=f"/pdv/?erro=produto_inexistente&id={produto_id}",
                status_code=303
            )

        if produto.estoque_atual < quantidade:
            return RedirectResponse(
                url=f"/pdv/?erro=estoque&produto={produto.nome}",
                status_code=303
            )

        preco = float(produto.preco)

        subtotal = preco * quantidade

        total_bruto += subtotal

        itens_validados.append({
            "produto": produto,
            "quantidade": quantidade,
            "preco": preco,
            "produto_nome": produto.nome,
        })

    # ============================================================
    # DESCONTO DE ASSOCIADO
    # ============================================================

    desconto_associado = 0.0

    if cliente and cliente.is_associado:
        desconto_associado = total_bruto * (
            DESCONTO_ASSOCIADO / 100
        )

    # ============================================================
    # DESCONTO MANUAL
    # ============================================================

    try:
        desconto_manual = float(desconto_manual or 0)
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=desconto",
            status_code=303
        )

    # Não permite desconto negativo
    if desconto_manual < 0:
        return RedirectResponse(
            url="/pdv/?erro=desconto",
            status_code=303
        )

    # O desconto manual não pode ser maior que o valor
    # que ainda pode ser descontado depois do desconto de associado.
    limite_desconto_manual = max(
        0.0,
        total_bruto - desconto_associado
    )

    if desconto_manual > limite_desconto_manual + 0.01:
        return RedirectResponse(
            url="/pdv/?erro=desconto_maior",
            status_code=303
        )

    # ============================================================
    # CALCULAR DESCONTO TOTAL E TOTAL DA VENDA
    # ============================================================

    desconto_total = (
        desconto_associado + desconto_manual
    )

    total_liquido = total_bruto - desconto_total

    if total_liquido < 0:
        total_liquido = 0.0

    total_liquido = round(total_liquido, 2)
    desconto_total = round(desconto_total, 2)
    total_bruto = round(total_bruto, 2)

    # ============================================================
    # VALIDAR PRIMEIRO PAGAMENTO
    # ============================================================

    try:
        valor_pagamento_1 = float(valor_pagamento_1 or 0)
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=pagamento",
            status_code=303
        )

    try:
        valor_pagamento_2 = float(valor_pagamento_2 or 0)
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=pagamento",
            status_code=303
        )

    forma_pagamento_1 = (forma_pagamento_1 or "").strip()
    forma_pagamento_2 = (forma_pagamento_2 or "").strip()

    # Valores negativos não são permitidos
    if valor_pagamento_1 < 0 or valor_pagamento_2 < 0:
        return RedirectResponse(
            url="/pdv/?erro=pagamento",
            status_code=303
        )

    # O primeiro pagamento precisa existir
    if valor_pagamento_1 <= 0:
        return RedirectResponse(
            url="/pdv/?erro=pagamento_1",
            status_code=303
        )

    if not forma_pagamento_1:
        return RedirectResponse(
            url="/pdv/?erro=pagamento_1",
            status_code=303
        )

    # ============================================================
    # VALIDAR SEGUNDO PAGAMENTO
    # ============================================================

    if valor_pagamento_2 > 0 and not forma_pagamento_2:
        return RedirectResponse(
            url="/pdv/?erro=pagamento_2",
            status_code=303
        )

    if valor_pagamento_2 == 0:
        forma_pagamento_2 = None

    # ============================================================
    # VALIDAR TOTAL DOS PAGAMENTOS
    # ============================================================

    total_pago = (
        valor_pagamento_1 +
        valor_pagamento_2
    )

    total_pago = round(total_pago, 2)

    if abs(total_pago - total_liquido) > 0.01:
        return RedirectResponse(
            url="/pdv/?erro=valor_pagamento",
            status_code=303
        )

    # ============================================================
    # USUÁRIO LOGADO
    # ============================================================

    if isinstance(usuario, dict):
        usuario_id = usuario.get("id")
    else:
        usuario_id = usuario.id

    # ============================================================
    # CRIAR VENDA
    # ============================================================

    venda = Venda(
        cliente_id=cliente_id or None,
        usuario_id=usuario_id,

        total_bruto=total_bruto,
        total_liquido=total_liquido,

        desconto=desconto_total,
        tipo_desconto=tipo_desconto or None,

        forma_pagamento_1=forma_pagamento_1,
        valor_pagamento_1=round(
            valor_pagamento_1,
            2
        ),

        forma_pagamento_2=forma_pagamento_2,
        valor_pagamento_2=round(
            valor_pagamento_2,
            2
        ),

        observacao=observacao.strip() or None
    )

    db.add(venda)

    db.flush()

    # ============================================================
    # CRIAR ITENS DA VENDA E BAIXAR ESTOQUE
    # ============================================================

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

    # ============================================================
    # SALVAR NO BANCO
    # ============================================================

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

    # ============================================================
    # IR PARA O COMPROVANTE
    # ============================================================

    return RedirectResponse(
        url=f"/pdv/venda/{venda.id}?sucesso=ok",
        status_code=303
    )


@router.get("/venda/{venda_id}")
def detalhe_venda(
    venda_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    venda = (
        db.query(Venda)
        .filter(Venda.id == venda_id)
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


@router.get("/historico")
def historico_vendas(
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):

    vendas = (
        db.query(Venda)
        .order_by(Venda.criado_em.desc())
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